"""Reproduce the three reported P0 defects against the checked-out revision.

Run from the project root. Prints REPRODUCED / NOT REPRODUCED for each defect.
"""

import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from src.db.database import init_db  # noqa: E402
from src.services.auth_service import AuthService  # noqa: E402
from src.services.curated_content import seed_curated  # noqa: E402
from src.services.desktop_storage import backup_database, restore_database  # noqa: E402
from src.services.game_service import GameService  # noqa: E402
from src.services.practice_service import PracticeService  # noqa: E402


def settings(situation, practice_mode, rounds=3):
    review = practice_mode == "review"
    return {
        "language": "english",
        "categories": ["noun", "verb", "adjective", "adverb"],
        "difficulties": ["beginner"],
        "rounds": rounds,
        "game_mode": "easy",
        "situation": situation,
        "practice_mode": "review" if review else "standard",
        "review_policy": "review_only" if review else "prefer_review",
        "show_hint_immediately": False,
    }


def word_source(db, word_id):
    with sqlite3.connect(db) as connection:
        return connection.execute(
            "SELECT word, source FROM words WHERE id=?", (word_id,)
        ).fetchone()


root = Path(tempfile.mkdtemp(prefix="hangman-repro-"))

# D1: fresh profile starts Review and receives an unseen word.
db1 = init_db(root / "d1.db", seed_words=False)
seed_curated(db1)
user = AuthService(db1).register_user("fresh", "password123", target_language="english")
try:
    payload = PracticeService(db1, curated=True).start(user, settings("restaurant", "review"))
    word, source = word_source(db1, payload["round"]["word_id"])
    print(f"D1 REPRODUCED: fresh profile started Review with unseen word {word!r} ({source})")
except ValueError as error:
    print(f"D1 NOT REPRODUCED: Review refused: {error}")

# D2: legacy review items from an imported database leak into desktop Review.
db2 = init_db(root / "d2.db", seed_words=True)  # legacy 324-word banks, as in an old app.db
legacy_user = AuthService(db2).register_user("legacy", "password123", target_language="english")
legacy_game = GameService(db2)
start = legacy_game.start_custom_learning_session(legacy_user, settings("restaurant", "standard", 5))
session, current = start["learning_session"], start["first_round"]
for _ in range(5):  # lose legacy rounds so they enter the review queue
    for letter in "qxzjvkwy":
        if current.is_complete:
            break
        legacy_game.record_guess(current, letter)
    if not current.is_complete:
        current.result = "lost"
    outcome = legacy_game.finalize_round(legacy_user, current, session)
    current = outcome["next_round"]
    if current is None:
        break
with sqlite3.connect(db2) as connection:  # an imported database has older history
    connection.execute("UPDATE game_sessions SET played_at='2026-08-01T10:00:00+00:00'")
    connection.execute("UPDATE review_queue SET review_due_at='2026-08-02T10:00:00+00:00'")
for _ in range(2):  # later legacy practice elsewhere pushes those rounds out of the recent window
    later = legacy_game.start_custom_learning_session(legacy_user, settings("office", "standard", 5))
    later_session, later_round = later["learning_session"], later["first_round"]
    while later_round is not None:
        for letter in sorted(set(later_round.word)):
            legacy_game.record_guess(later_round, letter)
        later_round = legacy_game.finalize_round(legacy_user, later_round, later_session)[
            "next_round"
        ]
seed_curated(db2)  # desktop start-up seeds the curated pack into the imported database
desktop = PracticeService(db2, curated=True)
seen = []
try:
    payload = desktop.start(legacy_user, settings("restaurant", "review", 5))
    while True:
        word, source = word_source(db2, payload["round"]["word_id"])
        seen.append((word, source))
        state = payload["round"]
        for letter in sorted(set(state["word"])):
            payload = desktop.guess(legacy_user, letter, state["round_key"])
        if not payload["next_round"]:
            break
        payload = desktop.next_round(legacy_user["id"])
except ValueError as error:
    seen.append(("<refused>", str(error)))
legacy_hits = [item for item in seen if item[0] != "<refused>" and item[1] != "desktop-core"]
print(("D2 REPRODUCED" if legacy_hits else "D2 NOT REPRODUCED") + f": review words {seen}")

# D3: corrupt live database blocks both startup and restore.
db3 = init_db(root / "d3.db", seed_words=False)
seed_curated(db3)
AuthService(db3).register_user("keeper", "password123", target_language="english")
backup = backup_database(db3, root / "good-backup.sqlite")
data = bytearray(db3.read_bytes())
data[0:100] = b"\x00" * 100  # destroy the SQLite header
db3.write_bytes(bytes(data))
try:
    init_db(db3, seed_words=False)
    print("D3 startup: init_db succeeded on corrupt file")
except Exception as error:  # noqa: BLE001
    print(f"D3 startup fails: {type(error).__name__}: {error}")
try:
    restore_database(db3, backup)
    print("D3 NOT REPRODUCED: restore over corrupt database succeeded")
except Exception as error:  # noqa: BLE001
    print(f"D3 REPRODUCED: restore failed: {type(error).__name__}: {error}")
