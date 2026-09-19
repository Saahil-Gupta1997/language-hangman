"""Release risks: partial writes, retries, recovery, upgrades and privacy."""

import copy
import json
import sqlite3
from dataclasses import asdict
from zipfile import ZipFile

import pytest

from src.db.database import create_connection, init_db
from src.models.game_round import GameRound
from src.models.learning_session import LearningSession
from src.services.auth_service import AuthService
from src.services.curated_content import CuratedWordService, seed_curated
from src.services.desktop_storage import (
    backup_database,
    delete_profile,
    export_diagnostics,
    export_profile,
    progress_report,
    restore_database,
)
from src.services.game_service import GameService
from src.services.practice_service import PracticeService


@pytest.fixture
def account(tmp_path):
    path = tmp_path / "app.db"
    init_db(path, seed_words=False)
    seed_curated(path)
    user = AuthService(path).register_user("learner", "password123")
    return path, user


def settings(situation="restaurant", mode="easy"):
    return dict(
        language="english",
        categories=["noun", "verb", "adjective", "adverb"],
        difficulties=["beginner"],
        rounds=3,
        situation=situation,
        game_mode=mode,
        practice_mode="standard",
        review_policy="prefer_review",
    )


def win(service, user, state):
    for letter in sorted(set(state["round"]["word"])):
        if letter.isalpha():
            state = service.guess(user, letter, state["round"]["round_key"])
    return state


def test_completion_retry_survives_process_restart(account):
    path, user = account
    service = PracticeService(path, curated=True)
    initial = service.start(user, settings())
    old_session = LearningSession(**initial["session"])
    finished = win(service, user, initial)
    # Retry using the pre-completion session and the same persistent round key.
    round_state = GameRound(**finished["round"])
    round_state.saved = False
    round_state.session_id = None
    outcome = GameService(path).finalize_round(user, round_state, old_session)
    assert outcome["learning_session"].completed_rounds == 1
    with create_connection(path) as connection:
        assert connection.execute("SELECT count(*) FROM game_sessions").fetchone()[0] == 1
        assert connection.execute("SELECT wins FROM word_progress").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM completion_receipts").fetchone()[0] == 1


@pytest.mark.parametrize("stage", ["progress", "review", "session", "snapshot"])
def test_failed_final_guess_rolls_back_everything(account, monkeypatch, stage):
    path, user = account
    service = PracticeService(path, curated=True)
    state = service.start(user, settings())
    letters = sorted(set(state["round"]["word"]))
    for letter in letters[:-1]:
        state = service.guess(user, letter, state["round"]["round_key"])
    before = copy.deepcopy(state)

    def fail(*args, **kwargs):
        raise sqlite3.OperationalError("simulated disk failure")

    targets = {
        "progress": (service.game, "_update_word_progress_for_round"),
        "review": (service.game, "_schedule_review_for_round"),
        "session": (service.game.learning_session_repository, "update_learning_session"),
        "snapshot": (service, "_write"),
    }
    target, attribute = targets[stage]
    original = getattr(target, attribute)
    monkeypatch.setattr(target, attribute, fail)
    with pytest.raises(sqlite3.OperationalError):
        service.guess(user, letters[-1], state["round"]["round_key"])
    assert service.load(user["id"]) == before
    with create_connection(path) as connection:
        for table in ("game_sessions", "word_progress", "completion_receipts", "review_queue"):
            assert connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0
    monkeypatch.setattr(target, attribute, original)
    recovered = service.guess(user, letters[-1], state["round"]["round_key"])
    assert recovered["round"]["saved"]
    assert recovered["session"]["completed_rounds"] == 1


def test_failed_finalize_preserves_caller_objects(account, monkeypatch):
    path, user = account
    game = GameService(path)
    session, state = game.start_learning_session(user)
    for letter in sorted(state.unique_letters):
        game.record_guess(state, letter)
    before = asdict(state), asdict(session)

    def fail(**kwargs):
        raise RuntimeError("injected")

    monkeypatch.setattr(game, "_schedule_review_for_round", fail)
    with pytest.raises(RuntimeError):
        game.finalize_round(user, state, session)
    assert (asdict(state), asdict(session)) == before


def test_guesses_and_hints_resume(account):
    path, user = account
    service = PracticeService(path, curated=True)
    state = service.start(user, settings())
    wrong = next(
        letter for letter in "abcdefghijklmnopqrstuvwxyz" if letter not in state["round"]["word"]
    )
    state = service.guess(user, wrong, state["round"]["round_key"])
    service.pause(user["id"])
    restored = PracticeService(path, curated=True).load(user["id"])
    assert restored["round"]["wrong_letters"] == [wrong]
    assert "meaning" in restored["round"]["revealed_hint_keys"]
    assert restored["round"]["active_seconds"] >= 0


@pytest.mark.parametrize("situation", ["restaurant", "airport", "hotel"])
@pytest.mark.parametrize("mode", ["easy", "hard"])
@pytest.mark.parametrize("round_count", [3, 5, 10])
def test_supported_journey_and_reports(account, situation, mode, round_count):
    path, user = account
    service = PracticeService(path, curated=True)
    config = settings(situation, mode)
    config["rounds"] = round_count
    state = service.start(user, config)
    for index in range(round_count):
        state = win(service, user, state)
        if index < round_count - 1:
            # Resume the between-round learning card in a new controller.
            service = PracticeService(path, curated=True)
            assert service.load(user["id"])["round"]["saved"]
            state = service.next_round(user["id"])
    report = progress_report(path, user["id"])
    assert report["rounds"] == report["wins"] == round_count
    assert report["sessions"] == 1
    assert report["guess_accuracy"] == report["win_rate"] == 100
    service.discard(user["id"])
    assert service.load(user["id"]) is None
    assert progress_report(path, user["id"])["sessions"] == 1


def test_lost_round_and_repeated_guess(account):
    path, user = account
    service = PracticeService(path, curated=True)
    state = service.start(user, settings(mode="hard"))
    wrong = [
        letter for letter in "abcdefghijklmnopqrstuvwxyz" if letter not in state["round"]["word"]
    ]
    state = service.guess(user, wrong[0], state["round"]["round_key"])
    state = service.guess(user, wrong[0], state["round"]["round_key"])
    assert len(state["round"]["wrong_letters"]) == 1
    for letter in wrong[1:5]:
        state = service.guess(user, letter, state["round"]["round_key"])
    assert state["round"]["result"] == "lost"
    assert progress_report(path, user["id"])["losses"] == 1


def test_stale_event_cannot_guess_next_round(account):
    path, user = account
    service = PracticeService(path, curated=True)
    state = service.start(user, settings())
    key = state["round"]["round_key"]
    win(service, user, state)
    service.next_round(user["id"])
    with pytest.raises(ValueError, match="changed"):
        service.guess(user, "a", key)


def test_backup_restore_profiles_progress_and_active_session(account, tmp_path):
    path, user = account
    service = PracticeService(path, curated=True)
    state = service.start(user, settings())
    state = win(service, user, state)
    backup = backup_database(path, tmp_path / "backup.sqlite")
    service.discard(user["id"])
    AuthService(path).register_user("later", "password123")
    safety = restore_database(path, backup)
    assert safety.exists()
    assert AuthService(path).authenticate_user("learner", "password123")
    assert AuthService(path).authenticate_user("later", "password123") is None
    assert PracticeService(path).load(user["id"]) == state
    assert progress_report(path, user["id"])["rounds"] == 1


@pytest.mark.parametrize("kind", ["text", "future", "unrelated"])
def test_bad_restore_leaves_current_database_unchanged(account, tmp_path, kind):
    path, user = account
    bad = tmp_path / "bad.sqlite"
    if kind == "text":
        bad.write_text("not a database")
    elif kind == "future":
        backup_database(path, bad)
        with sqlite3.connect(bad) as connection:
            connection.execute("PRAGMA user_version=999")
    else:
        with sqlite3.connect(bad) as connection:
            connection.execute("CREATE TABLE unrelated(id)")
    before = path.read_bytes()
    with pytest.raises(ValueError):
        restore_database(path, bad)
    assert path.read_bytes() == before
    assert AuthService(path).authenticate_user("learner", "password123")


def test_legacy_upgrade_preserves_data_and_takes_backup(account):
    path, user = account
    with create_connection(path) as connection:
        connection.execute("DROP TABLE completion_receipts")
        connection.execute("DROP TABLE active_practice")
        connection.execute("PRAGMA user_version=0")
    init_db(path, seed_words=False)
    assert AuthService(path).authenticate_user("learner", "password123")
    assert list((path.parent / "backups").glob("pre-upgrade-*.sqlite"))


def test_failed_upgrade_preserves_original(account, monkeypatch):
    import src.db.database as database

    path, user = account
    with create_connection(path) as connection:
        connection.execute("PRAGMA user_version=0")
    before = path.read_bytes()

    def fail(*args, **kwargs):
        raise RuntimeError("migration failure")

    monkeypatch.setattr(database, "_run_migrations", fail)
    with pytest.raises(RuntimeError):
        init_db(path, seed_words=False)
    assert path.read_bytes() == before


def test_profile_deletion_export_and_diagnostics_are_scoped(account, tmp_path):
    path, user = account
    other = AuthService(path).register_user("other", "different-password")
    service = PracticeService(path, curated=True)
    state = service.start(user, settings())
    win(service, user, state)
    exported = tmp_path / "profile.json"
    export_profile(path, user["id"], exported)
    text = exported.read_text()
    assert "password_hash" not in text and "other" not in text
    diagnostics = tmp_path / "diagnostics.zip"
    export_diagnostics(path, diagnostics)
    with ZipFile(diagnostics) as archive:
        data = json.loads(archive.read("diagnostics.json"))
        assert set(data) == {
            "application_version",
            "schema_version",
            "integrity_ok",
            "foreign_keys_ok",
        }
    delete_profile(path, user["id"])
    assert AuthService(path).get_user_by_id(other["id"])
    assert PracticeService(path).load(user["id"]) is None
    with create_connection(path) as connection:
        for table in ("game_sessions", "word_progress", "completion_receipts", "learning_sessions"):
            assert connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0


def test_legacy_content_is_excluded_from_new_practice(account):
    path, user = account
    # Simulates restoring a database with the old 324-word corpus.
    init_db(path, seed_words=True)
    seed_curated(path)
    words = CuratedWordService(path).get_words("english")
    assert len(words) == 30
    assert all(word["source"] == "desktop-core" for word in words)


def test_unicode_composed_letter_is_accepted():
    state = GameRound(
        word_id=1,
        word="café",
        language="french",
        level="beginner",
        category="noun",
        difficulty="beginner",
        hint="drink",
        translation="coffee",
        example_sentence="Un café.",
    )
    result = GameService().record_guess(state, "e\u0301")
    assert result["accepted"]
    assert state.correct_letters == ["é"]


def test_desktop_single_instance_lock(tmp_path):
    from src.desktop.runtime import InstanceLock

    path = tmp_path / "app.lock"
    first = InstanceLock(path)
    try:
        with pytest.raises(RuntimeError, match="already running"):
            InstanceLock(path)
    finally:
        first.close()
    InstanceLock(path).close()


def test_corrupted_password_hash_is_rejected(account):
    path, user = account
    with create_connection(path) as connection:
        connection.execute(
            "UPDATE users SET password_hash=? WHERE id=?",
            ("pbkdf2_sha256$nope$bad$hash", user["id"]),
        )
    assert AuthService(path).authenticate_user("learner", "password123") is None


def test_restore_rejects_incomplete_current_schema(account, tmp_path):
    path, user = account
    bad = backup_database(path, tmp_path / "incomplete.sqlite")
    with sqlite3.connect(bad) as connection:
        connection.execute("DROP TABLE word_progress")
    before = path.read_bytes()
    with pytest.raises(ValueError, match="missing required"):
        restore_database(path, bad)
    assert path.read_bytes() == before
