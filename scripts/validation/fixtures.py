"""Build the learner data that release validation needs, using the application's own services.

    python -m scripts.validation.fixtures release-data   # a profile, a win, a loss, a paused round
    python -m scripts.validation.fixtures performance <folder> [profiles] [rounds]
    python -m scripts.validation.fixtures describe <database>

"release-data" writes into the real application data folder, so run it from a checkout of
the release you are upgrading FROM: the point is that the data was created by that release's
own code, not written in by hand (a sentinel file would not prove a data-preserving upgrade).
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from src import __version__
from src.db.database import init_db
from src.services.auth_service import AuthService
from src.services.curated_content import seed_curated
from src.services.practice_service import PracticeService
from src.utils.config import DATABASE_PATH
from src.utils.constants import GENERAL_SITUATION

SETTINGS = {
    "language": "english",
    "categories": ["noun", "verb", "adjective", "adverb"],
    "difficulties": ["beginner"],
    "rounds": 3,
    "game_mode": "easy",
    "situation": GENERAL_SITUATION,
    "practice_mode": "standard",
    "review_policy": "prefer_review",
    "show_hint_immediately": False,
}
PROFILE, PASSWORD = "upgrader", "upgrade-pass-2026"
SECOND, SECOND_PASSWORD = "second", "second-pass-2026"


def release_data(db_path=DATABASE_PATH):
    """One profile with a win, a loss and a session paused mid-round, plus a second profile."""
    database = init_db(db_path, seed_words=False)
    seed_curated(database)
    auth = AuthService(database)
    user = auth.register_user(PROFILE, PASSWORD, target_language="english")
    auth.register_user(SECOND, SECOND_PASSWORD, target_language="english")
    service = PracticeService(database, curated=True)

    payload = service.start(user, SETTINGS)
    for letter in sorted(set(payload["round"]["word"])):  # round 1: won
        payload = service.guess(user, letter, payload["round"]["round_key"])
    payload = service.next_round(user["id"])
    misses = [c for c in "abcdefghijklmnopqrstuvwxyz" if c not in payload["round"]["word"]]
    for letter in misses[: payload["round"]["max_attempts"]]:  # round 2: lost
        payload = service.guess(user, letter, payload["round"]["round_key"])
    payload = service.next_round(user["id"])
    wrong = next(c for c in "zqxjkvwy" if c not in payload["round"]["word"])
    service.guess(user, wrong, payload["round"]["round_key"])  # round 3: paused mid-round
    service.pause(user["id"])
    print(f"created with {__version__}: {describe(database)} | paused wrong letter {wrong}")
    return database


def describe(db_path):
    connection = sqlite3.connect(db_path)
    try:
        counts = {
            name: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for name, table in (
                ("profiles", "users"),
                ("rounds", "game_sessions"),
                ("saved sessions", "active_practice"),
            )
        }
        schema = connection.execute("PRAGMA user_version").fetchone()[0]
    finally:
        connection.close()
    size = Path(db_path).stat().st_size / 1_048_576
    tallies = " | ".join(f"{name} {value}" for name, value in counts.items())
    return f"schema {schema} | {tallies} | {size:.2f} MB"


def performance_data(folder, profiles=5, rounds=5000, played=150):
    """The supported-history dataset: one heavy profile, plus light ones.

    ``played`` rounds go through the application's services; the rest are copies of those
    rows with spread dates, which keeps the build honest about how the data was made.
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    database = init_db(folder / "app.db", seed_words=False)
    seed_curated(database)
    auth = AuthService(database)
    heavy = auth.register_user("heavy", "heavy-pass-2026", target_language="english")
    service = PracticeService(database, curated=True)
    settings = dict(SETTINGS, rounds=10)

    def play(user, count):
        done = 0
        while done < count:
            payload = service.start(user, settings)
            while done < count:
                for letter in sorted(set(payload["round"]["word"])):
                    payload = service.guess(user, letter, payload["round"]["round_key"])
                done += 1
                if not payload["next_round"]:
                    service.discard(user["id"])
                    break
                payload = service.next_round(user["id"])

    play(heavy, played)
    for index in range(profiles - 1):
        light = auth.register_user(f"light{index}", "light-pass-2026", target_language="english")
        play(light, 30)

    connection = sqlite3.connect(database)
    try:
        connection.execute("PRAGMA foreign_keys = OFF")
        columns = [row[1] for row in connection.execute("PRAGMA table_info(game_sessions)")]
        copied = ",".join(column for column in columns if column != "id")
        while (
            connection.execute(
                "SELECT count(*) FROM game_sessions WHERE user_id = ?", (heavy["id"],)
            ).fetchone()[0]
            < rounds
        ):
            connection.execute(
                f"INSERT INTO game_sessions ({copied}) SELECT {copied} FROM game_sessions "
                "WHERE user_id = ? LIMIT 500",
                (heavy["id"],),
            )
        connection.execute(
            "UPDATE game_sessions SET played_at = datetime(played_at, '-' || (id % 400) || ' days')"
            " WHERE user_id = ?",
            (heavy["id"],),
        )
        connection.commit()
        connection.execute("VACUUM")
    finally:
        connection.close()
    print(f"performance dataset: {describe(database)}")
    return database


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "release-data":
        release_data()
    elif command == "performance":
        performance_data(sys.argv[2], *(int(value) for value in sys.argv[3:]))
    else:
        print(describe(sys.argv[2]))
