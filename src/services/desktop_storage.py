"""Validated SQLite backups, profile controls and privacy-safe diagnostics."""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from src import __version__
from src.db.database import SCHEMA_SQL, SCHEMA_VERSION, _run_migrations, create_connection, init_db
from src.db.transaction import transaction


def _stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")


def validate_backup(path):
    path = Path(path).resolve()
    if not path.is_file() or path.stat().st_size > 512 * 1024 * 1024:
        raise ValueError("Choose a Hangman SQLite backup smaller than 512 MB.")
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    try:
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("The selected backup is damaged.")
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version > SCHEMA_VERSION:
            raise ValueError("This backup needs a newer version of the application.")
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if not {"users", "words", "game_sessions", "learning_sessions"} <= tables:
            raise ValueError("This file is not a supported Hangman database.")
        if connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('trigger','view')"
        ).fetchone():
            raise ValueError("Backups with custom triggers or views are not supported.")
        if connection.execute("PRAGMA foreign_key_check").fetchone():
            raise ValueError("The backup has inconsistent profile or progress records.")
        # Validate fields used by the application, not merely table names.
        for table, columns in {
            "users": "id,username,password_hash,target_language,level",
            "words": "id,word,language,category,difficulty",
            "game_sessions": "id,user_id,word_id,result",
            "learning_sessions": "id,user_id,status",
        }.items():
            connection.execute(f"SELECT {columns} FROM {table} LIMIT 0")
        if version == SCHEMA_VERSION:
            expected = sqlite3.connect(":memory:")
            expected.row_factory = sqlite3.Row
            try:
                expected.executescript(SCHEMA_SQL)
                _run_migrations(expected)
                required = {
                    row[0]
                    for row in expected.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' "
                        "AND name != 'sqlite_sequence'"
                    )
                }
                for table in required:
                    columns = {row[1] for row in expected.execute(f"PRAGMA table_info({table})")}
                    actual = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
                    if not columns <= actual:
                        raise ValueError("The backup is missing required data structures.")
                connection.execute(
                    "SELECT round_key,user_id,payload FROM completion_receipts LIMIT 0"
                )
                connection.execute(
                    "SELECT user_id,payload,revision,updated_at FROM active_practice LIMIT 0"
                )
            finally:
                expected.close()
        if "active_practice" in tables:
            for row in connection.execute("SELECT user_id,payload FROM active_practice"):
                from src.models.game_round import GameRound
                from src.models.learning_session import LearningSession

                data = json.loads(row[1])
                if data["schema"] != 1 or data["session"]["user_id"] != row[0]:
                    raise ValueError("The backup contains an incompatible saved session.")
                GameRound(**data["round"])
                LearningSession(**data["session"])
    except (sqlite3.Error, KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("This backup is damaged or incompatible.") from error
    finally:
        connection.close()


def backup_database(db_path, destination):
    destination = Path(destination)
    if destination.resolve() == Path(db_path).resolve():
        raise ValueError("Choose a location different from the active database.")
    if destination.exists():
        raise ValueError("Choose a new backup filename; existing files are preserved.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(suffix=".sqlite", dir=destination.parent)
    os.close(descriptor)
    temporary = Path(name)
    try:
        with create_connection(db_path) as source, create_connection(temporary) as target:
            source.backup(target)
        validate_backup(temporary)
        # Exclusive create avoids overwriting a file created after the initial check.
        with destination.open("xb") as output, temporary.open("rb") as source:
            import shutil

            shutil.copyfileobj(source, output)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def restore_database(db_path, source):
    """Stage and validate upgrades before atomically replacing the live file."""
    db_path, source = Path(db_path), Path(source)
    validate_backup(source)
    descriptor, name = tempfile.mkstemp(prefix="restore-", suffix=".sqlite", dir=db_path.parent)
    os.close(descriptor)
    staging = Path(name)
    try:
        origin = sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            with create_connection(staging) as target:
                origin.backup(target)
        finally:
            origin.close()
        init_db(staging, seed_words=False)
        validate_backup(staging)
        safety = db_path.parent / "backups" / f"before-restore-{_stamp()}.sqlite"
        backup_database(db_path, safety)
        os.replace(staging, db_path)
    finally:
        staging.unlink(missing_ok=True)
    return safety


def delete_profile(db_path, user_id):
    with transaction(db_path) as connection:
        connection.execute("DELETE FROM users WHERE id=?", (user_id,))


def export_profile(db_path, user_id, destination):
    """Human-readable export; excludes credentials and other profiles."""
    payload = {"format": 1, "application_version": __version__}
    with transaction(db_path) as connection:
        user = connection.execute(
            "SELECT username,target_language,level,created_at FROM users WHERE id=?", (user_id,)
        ).fetchone()
        if not user:
            raise ValueError("Profile no longer exists.")
        payload["profile"] = dict(user)
        for table in ("game_sessions", "learning_sessions", "word_progress", "review_queue"):
            payload[table] = [
                dict(row)
                for row in connection.execute(f"SELECT * FROM {table} WHERE user_id=?", (user_id,))
            ]
    with Path(destination).open("x", encoding="utf-8") as output:
        json.dump(payload, output, ensure_ascii=False, indent=2)


def progress_report(db_path, user_id):
    """Derive all displayed metrics directly from completed game rows."""
    with transaction(db_path) as connection:
        rounds = [
            dict(row)
            for row in connection.execute(
                "SELECT g.*, w.word FROM game_sessions g JOIN words w ON w.id=g.word_id "
                "WHERE user_id=? AND result IN ('won','lost') ORDER BY played_at DESC,id DESC",
                (user_id,),
            )
        ]
        count = len(rounds)
        wins = sum(row["result"] == "won" for row in rounds)
        guesses = sum(row["attempts_used"] for row in rounds)
        correct = sum(row["letters_correct"] for row in rounds)
        sessions = connection.execute(
            "SELECT count(*) FROM learning_sessions WHERE user_id=? AND status='completed'",
            (user_id,),
        ).fetchone()[0]
    return {
        "rounds": count,
        "wins": wins,
        "losses": count - wins,
        "win_rate": 100 * wins / count if count else 0,
        "guess_accuracy": 100 * correct / guesses if guesses else 0,
        "guesses": guesses,
        "correct_guesses": correct,
        "sessions": sessions,
        "words": len({row["word_id"] for row in rounds}),
        "history": rounds,
    }


def export_diagnostics(db_path, destination):
    # Deliberately omit logs, local paths, names, words and saved-session payloads.
    with create_connection(db_path) as connection:
        payload = {
            "application_version": __version__,
            "schema_version": connection.execute("PRAGMA user_version").fetchone()[0],
            "integrity_ok": connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok",
            "foreign_keys_ok": not bool(connection.execute("PRAGMA foreign_key_check").fetchone()),
        }
    with zipfile.ZipFile(destination, "x", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("diagnostics.json", json.dumps(payload, indent=2))
