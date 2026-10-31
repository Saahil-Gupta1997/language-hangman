"""Check learner data with the application's own services after an upgrade, import or restore.

    python -m scripts.validation.verify upgraded          # credentials, progress, paused round
    python -m scripts.validation.verify beta-import       # an imported v1.0.0-beta profile
    python -m scripts.validation.verify restore-newest <damaged copy>

Run each from a checkout of the release under test, so the code doing the checking is the
code that shipped. Signing in through the installed window is a manual check (ACCEPTANCE M1).
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from scripts.validation.fixtures import PASSWORD, PROFILE, SECOND, SECOND_PASSWORD, SETTINGS
from src import __version__
from src.desktop.recovery import automatic_backups, describe_backup
from src.services.auth_service import AuthService
from src.services.curated_content import seed_curated
from src.services.desktop_storage import open_live_database, progress_report, restore_database
from src.services.game_service import NoReviewWordsError
from src.services.practice_service import PracticeService
from src.utils.config import DATA_DIR, DATABASE_PATH


def upgraded():
    print("code version", __version__)
    database = open_live_database(DATABASE_PATH)
    auth = AuthService(database)
    user = auth.authenticate_user(PROFILE, PASSWORD)
    print("previous-release credentials accepted:", user is not None)
    print("wrong password rejected:", auth.authenticate_user(PROFILE, "not-the-password") is None)
    print("second profile present:", auth.authenticate_user(SECOND, SECOND_PASSWORD) is not None)
    report = progress_report(database, user["id"])
    print("progress:", {key: report[key] for key in ("rounds", "wins", "losses", "sessions")})
    service = PracticeService(database, curated=True)
    payload = service.load(user["id"])
    session = payload["session"]
    where = f"(round {session['completed_rounds'] + 1} of {session['planned_rounds']})"
    print("paused round resumes:", bool(payload["round"]["wrong_letters"]), where)
    for letter in sorted(set(payload["round"]["word"])):
        payload = service.guess(user, letter, payload["round"]["round_key"])
    service.discard(user["id"])
    report = progress_report(database, user["id"])
    finished = {key: report[key] for key in ("rounds", "wins", "losses")}
    print("after finishing the resumed round:", finished)


def beta_import(name="beta-learner", password="beta-pass-2026"):
    database = open_live_database(DATABASE_PATH)
    user = AuthService(database).authenticate_user(name, password)
    print("beta credentials accepted:", user is not None)
    report = progress_report(database, user["id"])
    print("beta history kept:", {key: report[key] for key in ("rounds", "wins", "words")})
    print(
        "profiles from before the import are gone (all profiles are replaced, as documented):",
        AuthService(database).authenticate_user(PROFILE, PASSWORD) is None,
    )
    service = PracticeService(database, curated=True)
    for situation in ("hotel", "airport", "restaurant"):
        settings = dict(
            SETTINGS,
            rounds=5,
            situation=situation,
            practice_mode="review",
            review_policy="review_only",
        )
        try:
            payload = service.start(user, settings)
        except NoReviewWordsError:
            print(f"review in {situation}: refused (no eligible review words)")
            continue
        words = []
        while True:
            words.append(payload["round"]["word"])
            for letter in sorted(set(payload["round"]["word"])):
                payload = service.guess(user, letter, payload["round"]["round_key"])
            if not payload["next_round"]:
                service.discard(user["id"])
                break
            payload = service.next_round(user["id"])
        print(f"review in {situation}: {words}")


def restore_newest(damaged_copy):
    """Do what the recovery window's first button does, and prove the damage was kept."""
    offered = automatic_backups(DATA_DIR)
    print("recovery window would offer:", [describe_backup(p).split(" saved")[0] for p in offered])
    preserved = restore_database(DATABASE_PATH, offered[0])
    seed_curated(DATABASE_PATH)
    print("restored:", describe_backup(offered[0]).split(" saved")[0])
    print(
        "damaged bytes preserved exactly:",
        (preserved / "damaged-app.db").read_bytes() == Path(damaged_copy).read_bytes(),
    )
    database = open_live_database(DATABASE_PATH)
    with sqlite3.connect(database) as connection:
        names = [row[0] for row in connection.execute("SELECT username FROM users ORDER BY id")]
    print("profiles after recovery:", names)
    side_files = [p.name for p in Path(DATABASE_PATH).parent.glob("app.db-*")]
    print("stale side files left behind:", side_files or "none")


if __name__ == "__main__":
    {"upgraded": upgraded, "beta-import": beta_import, "restore-newest": restore_newest}[
        sys.argv[1]
    ](*sys.argv[2:])
