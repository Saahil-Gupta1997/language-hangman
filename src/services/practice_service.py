"""Durable desktop workflows; each user action is an atomic unit of work."""

from __future__ import annotations

import json
import time
from dataclasses import asdict

from src.db.transaction import transaction
from src.models.game_round import GameRound
from src.models.learning_session import LearningSession
from src.services.game_service import GameService
from src.services.hint_service import sync_auto_revealed_hints
from src.utils.constants import ENDLESS_ROUNDS
from src.utils.helpers import utc_now_iso


class PracticeService:
    def __init__(self, db_path, curated=False):
        self.db_path = db_path
        self.game = GameService(db_path)
        if curated:
            from src.services.curated_content import CuratedWordService

            self.game.word_service = CuratedWordService(db_path)
        self._last_tick = None

    def load(self, user_id):
        with transaction(self.db_path) as connection:
            row = connection.execute(
                "SELECT payload FROM active_practice WHERE user_id=?", (user_id,)
            ).fetchone()
        self._last_tick = time.monotonic()
        return json.loads(row[0]) if row else None

    def _read(self, connection, user_id):
        row = connection.execute(
            "SELECT payload FROM active_practice WHERE user_id=?", (user_id,)
        ).fetchone()
        if not row:
            raise ValueError("No saved session. Start a new practice session.")
        payload = json.loads(row[0])
        if payload.get("schema") != 1:
            raise ValueError("This saved session requires a newer application.")
        return payload

    def _write(self, connection, user_id, payload):
        connection.execute(
            "INSERT INTO active_practice(user_id,payload) VALUES(?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET payload=excluded.payload, "
            "revision=active_practice.revision+1, updated_at=CURRENT_TIMESTAMP",
            (user_id, json.dumps(payload, ensure_ascii=False)),
        )

    def start(self, user, settings):
        with transaction(self.db_path) as connection:
            if connection.execute(
                "SELECT 1 FROM active_practice WHERE user_id=?", (user["id"],)
            ).fetchone():
                raise ValueError("Resume or discard your saved session first.")
            result = self.game.start_custom_learning_session(user, settings)
            result["first_round"].active_seconds = 0.0
            payload = {
                "schema": 1,
                "session": asdict(result["learning_session"]),
                "round": asdict(result["first_round"]),
                "next_round": None,
                "review": None,
                "summary": None,
                "message": "Guess one letter at a time.",
                # Explains adjustments such as a shortened Review session; optional key,
                # so saved sessions from 1.0.0rc1 remain loadable.
                "notice": " ".join(result["warnings"]) or None,
            }
            self._write(connection, user["id"], payload)
        self._last_tick = time.monotonic()
        return payload

    def guess(self, user, guess, round_key):
        now = time.monotonic()
        with transaction(self.db_path) as connection:
            payload = self._read(connection, user["id"])
            game_round = GameRound(**payload["round"])
            if game_round.round_key != round_key:
                raise ValueError("The session has changed. Reopen Practice to refresh it.")
            if game_round.saved:
                return payload
            if self._last_tick is not None:
                game_round.active_seconds = (game_round.active_seconds or 0) + (
                    now - self._last_tick
                )
            result = self.game.record_guess(game_round, guess)
            payload["message"] = result["message"]
            sync_auto_revealed_hints(game_round)
            if game_round.is_complete:
                session = LearningSession(**payload["session"])
                outcome = self.game.finalize_round(user, game_round, session)
                payload["session"] = asdict(session)
                payload["review"] = outcome["learning_review"]
                payload["summary"] = outcome["session_summary"]
                next_round = outcome["next_round"]
                if next_round:
                    next_round.active_seconds = 0.0
                elif session.completed_rounds < session.planned_rounds:
                    planned = (
                        ""
                        if session.planned_rounds >= ENDLESS_ROUNDS
                        else f" of {session.planned_rounds}"
                    )
                    payload["notice"] = (
                        f"This session ended after {session.completed_rounds}{planned} "
                        "rounds because no more eligible words remain for it. "
                        "Completed rounds are saved."
                    )
                payload["next_round"] = asdict(next_round) if next_round else None
            payload["round"] = asdict(game_round)
            self._write(connection, user["id"], payload)
        self._last_tick = now
        return payload

    def next_round(self, user_id):
        with transaction(self.db_path) as connection:
            payload = self._read(connection, user_id)
            if not payload["next_round"]:
                raise ValueError("This session has no next round.")
            payload["round"] = payload["next_round"]
            payload["next_round"] = None
            payload["review"] = None
            payload["message"] = "Guess one letter at a time."
            payload["notice"] = None
            self._write(connection, user_id, payload)
        self._last_tick = time.monotonic()
        return payload

    def pause(self, user_id):
        """Save active practice time; closed/paused time is not counted."""
        if self._last_tick is None:
            return
        now = time.monotonic()
        with transaction(self.db_path) as connection:
            row = connection.execute(
                "SELECT payload FROM active_practice WHERE user_id=?", (user_id,)
            ).fetchone()
            if row:
                payload = json.loads(row[0])
                if not payload["round"]["saved"]:
                    payload["round"]["active_seconds"] = (
                        (payload["round"].get("active_seconds") or 0) + now - self._last_tick
                    )
                    self._write(connection, user_id, payload)
        self._last_tick = None

    def end(self, user_id):
        """Stop now: finished words stay saved and the unfinished word is dropped.

        The session counts as completed if at least one word was finished.
        """
        with transaction(self.db_path) as connection:
            row = connection.execute(
                "SELECT payload FROM active_practice WHERE user_id=?", (user_id,)
            ).fetchone()
            if row:
                session = json.loads(row[0])["session"]
                finished = session["completed_rounds"] > 0
                connection.execute(
                    "UPDATE learning_sessions SET status=?, completed_at=? "
                    "WHERE id=? AND user_id=? AND status='active'",
                    (
                        "completed" if finished else "abandoned",
                        utc_now_iso() if finished else None,
                        session["session_id"],
                        user_id,
                    ),
                )
            connection.execute("DELETE FROM active_practice WHERE user_id=?", (user_id,))
        self._last_tick = None

    def discard(self, user_id):
        with transaction(self.db_path) as connection:
            row = connection.execute(
                "SELECT payload FROM active_practice WHERE user_id=?", (user_id,)
            ).fetchone()
            if row:
                payload = json.loads(row[0])
                connection.execute(
                    "UPDATE learning_sessions SET status='abandoned' "
                    "WHERE id=? AND user_id=? AND status='active'",
                    (payload["session"]["session_id"], user_id),
                )
            connection.execute("DELETE FROM active_practice WHERE user_id=?", (user_id,))
        self._last_tick = None
