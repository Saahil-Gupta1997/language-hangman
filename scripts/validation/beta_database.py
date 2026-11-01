"""Create a v1.0.0-beta database with the beta's own code, for the import check.

Run from the v1.0.0-beta worktree (023f2bd):
    python <path to>/beta_database.py <output database>

The original beta database used for rc2 and rc3 was lost with a temporary folder, so this
rebuilds an equivalent one: a profile with completed rounds, written by the beta's services
and its 324-word banks. It deliberately plays two words the desktop's curated pack also has
and one the pack retired, so an import shows retired words staying in history only.
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from src.db.database import init_db  # noqa: E402
from src.services.auth_service import AuthService  # noqa: E402
from src.services.game_service import GameService  # noqa: E402
from src.services.maintenance_service import MaintenanceService  # noqa: E402

NAME, PASSWORD = "beta-learner", "beta-pass-2026"
WORDS = ("clean", "early", "small")

database = Path(sys.argv[1])
database.parent.mkdir(parents=True, exist_ok=True)
init_db(database)
MaintenanceService(db_path=database).seed_word_banks()
user = AuthService(database).register_user(NAME, PASSWORD, target_language="english")
service = GameService(database)
session, _ = service.start_learning_session(user, planned_rounds=len(WORDS))

connection = sqlite3.connect(database)
connection.row_factory = sqlite3.Row
played = []
for target in WORDS:
    row = connection.execute(
        "SELECT * FROM words WHERE word = ? AND language = 'english' LIMIT 1", (target,)
    ).fetchone()
    if row is None:
        print(f"skipped {target}: not in the beta word bank")
        continue
    chosen = dict(row)
    chosen.setdefault("situations", [])
    round_state = service.build_round(
        chosen_word=chosen,
        level=user.get("level") or "beginner",
        learning_session_id=session.session_id,
        game_mode="easy",
    )
    for letter in sorted(set(round_state.word)):
        service.record_guess(round_state, letter)
    service.finalize_round(user, round_state, session)
    played.append(round_state.word)

print(
    "beta database:",
    f"schema {connection.execute('PRAGMA user_version').fetchone()[0]}",
    f"| profiles {connection.execute('SELECT count(*) FROM users').fetchone()[0]}",
    f"| rounds {connection.execute('SELECT count(*) FROM game_sessions').fetchone()[0]}",
    f"| words in bank {connection.execute('SELECT count(*) FROM words').fetchone()[0]}",
    f"| played {played}",
)
connection.close()
