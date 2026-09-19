"""Recovery from a damaged live database (D-03) and diagnostics (T-06).

The degraded start-up check for D-07 needs a window and lives in tests/gui_scenarios.py.
"""

import json
import logging
import sqlite3
import sys
import zipfile

import pytest

import src.services.desktop_storage as storage
from src.db.database import init_db
from src.desktop.runtime import close_logging, configure_logging, log_event, recent_events
from src.services.auth_service import AuthService
from src.services.curated_content import seed_curated
from src.services.desktop_storage import (
    DatabaseUnavailableError,
    RestoreError,
    backup_database,
    database_is_healthy,
    export_diagnostics,
    open_live_database,
    progress_report,
    restore_database,
)
from src.services.practice_service import PracticeService


def practice_settings():
    return {
        "language": "english",
        "categories": ["noun", "verb", "adjective", "adverb"],
        "difficulties": ["beginner"],
        "rounds": 3,
        "game_mode": "easy",
        "situation": "hotel",
        "practice_mode": "standard",
        "review_policy": "prefer_review",
        "show_hint_immediately": False,
    }


@pytest.fixture
def saved_state(tmp_path):
    """A profile with one won round and a paused session, plus a valid full backup."""
    path = init_db(tmp_path / "app.db", seed_words=False)
    seed_curated(path)
    user = AuthService(path).register_user("keeper", "password123", target_language="english")
    service = PracticeService(path, curated=True)
    payload = service.start(user, practice_settings())
    for letter in sorted(set(payload["round"]["word"])):
        payload = service.guess(user, letter, payload["round"]["round_key"])
    payload = service.next_round(user["id"])
    wrong = next(c for c in "zqxjkvwy" if c not in payload["round"]["word"])
    service.guess(user, wrong, payload["round"]["round_key"])
    backup = backup_database(path, tmp_path / "good.sqlite")
    return path, user, backup, wrong


def corrupt_header(path):
    data = bytearray(path.read_bytes())
    data[:100] = b"\x00" * 100
    path.write_bytes(bytes(data))
    return bytes(data)


def backups_in(path):
    folder = path.parent / "backups"
    return sorted(item.name for item in folder.iterdir()) if folder.exists() else []


def test_valid_backup_restores_a_corrupt_live_database(saved_state):
    path, user, backup, wrong = saved_state
    damaged = corrupt_header(path)
    with pytest.raises(DatabaseUnavailableError):
        open_live_database(path)

    preserved = restore_database(path, backup)

    assert preserved.name.startswith("quarantine-")
    assert (preserved / "damaged-app.db").read_bytes() == damaged
    assert (preserved / "README.txt").exists()
    assert open_live_database(path) == path
    restored_user = AuthService(path).authenticate_user("keeper", "password123")
    assert restored_user is not None
    assert progress_report(path, user["id"])["rounds"] == 1
    service = PracticeService(path, curated=True)
    payload = service.load(user["id"])  # the paused session, mid-round, survives
    assert wrong in payload["round"]["wrong_letters"]
    for letter in sorted(set(payload["round"]["word"])):
        payload = service.guess(restored_user, letter, payload["round"]["round_key"])
    assert payload["round"]["saved"]
    assert progress_report(path, user["id"])["rounds"] == 2


def test_page_corruption_is_detected_at_start_up(saved_state):
    path = saved_state[0]
    data = bytearray(path.read_bytes())
    data[4096 * 2 : 4096 * 3] = bytes(range(256)) * 16  # garbage over a b-tree page
    path.write_bytes(bytes(data))
    assert not database_is_healthy(path)
    with pytest.raises(DatabaseUnavailableError, match="integrity"):
        open_live_database(path)


@pytest.mark.parametrize("kind", ["text", "future", "corrupt"])
def test_invalid_backup_leaves_a_corrupt_live_database_unchanged(saved_state, tmp_path, kind):
    path = saved_state[0]
    bad = tmp_path / f"bad-{kind}.sqlite"
    if kind == "text":
        bad.write_text("not a database", encoding="utf-8")
    elif kind == "future":
        backup_database(path, bad)
        connection = sqlite3.connect(bad)
        connection.execute("PRAGMA user_version = 99")
        connection.close()
    else:
        backup_database(path, bad)
        corrupt_header(bad)
    damaged = corrupt_header(path)
    before = backups_in(path)
    with pytest.raises(ValueError):
        restore_database(path, bad)
    assert path.read_bytes() == damaged
    assert backups_in(path) == before
    assert not list(path.parent.glob("restore-*.sqlite"))


def test_replace_failure_keeps_the_original_and_its_side_files(saved_state, monkeypatch):
    path, _, backup, _ = saved_state
    original = path.read_bytes()
    journal = path.with_name("app.db-journal")
    journal.write_bytes(b"left over from a crash")
    real_replace = storage.os.replace

    def refuse_live_file(source, destination):
        if str(destination) == str(path):
            raise PermissionError("in use")
        return real_replace(source, destination)

    monkeypatch.setattr(storage.os, "replace", refuse_live_file)
    with pytest.raises(RestoreError, match="could not be replaced") as caught:
        restore_database(path, backup)
    assert caught.value.stage == "replace"
    assert path.read_bytes() == original
    assert journal.read_bytes() == b"left over from a crash"
    assert not list(path.parent.glob("restore-*.sqlite"))


def test_side_files_are_set_aside_so_they_cannot_replay(saved_state):
    path, user, backup, _ = saved_state
    journal = path.with_name("app.db-journal")
    journal.write_bytes(b"stale journal")
    restore_database(path, backup)
    assert not journal.exists()
    assert any(name.endswith("app.db-journal") for name in backups_in(path))
    assert AuthService(path).authenticate_user("keeper", "password123") is not None


@pytest.mark.parametrize("stage", ["stage", "protect"])
def test_failures_before_the_switch_leave_data_unchanged(saved_state, monkeypatch, stage):
    path, _, backup, _ = saved_state
    damaged = corrupt_header(path)
    if stage == "stage":
        monkeypatch.setattr(
            storage.tempfile, "mkstemp", lambda **kwargs: (_ for _ in ()).throw(PermissionError())
        )
    else:
        monkeypatch.setattr(
            storage, "quarantine_database", lambda *args: (_ for _ in ()).throw(OSError())
        )
    with pytest.raises(RestoreError) as caught:
        restore_database(path, backup)
    assert caught.value.stage == stage
    assert "unchanged" in str(caught.value)
    assert path.read_bytes() == damaged


def test_newer_schema_live_file_is_quarantined_not_blocking(saved_state):
    path, _, backup, _ = saved_state
    connection = sqlite3.connect(path)  # closed explicitly: Windows locks open files
    connection.execute("PRAGMA user_version = 99")
    connection.close()
    with pytest.raises(DatabaseUnavailableError, match="newer version"):
        open_live_database(path)
    preserved = restore_database(path, backup)
    assert preserved.name.startswith("quarantine-")
    assert open_live_database(path) == path


def test_healthy_live_file_gets_a_validated_safety_backup(saved_state):
    path, _, backup, _ = saved_state
    preserved = restore_database(path, backup)
    assert preserved.name.startswith("before-restore-")
    assert database_is_healthy(preserved)


def test_launcher_offers_recovery_when_start_up_fails(tmp_path, monkeypatch):
    import desktop_app
    import src.desktop.application as application
    import src.desktop.recovery as recovery
    import src.utils.config as config

    events = []

    class FakeApp:
        attempts = 0

        def __init__(self):
            FakeApp.attempts += 1
            if FakeApp.attempts == 1:
                raise DatabaseUnavailableError("The data file failed its integrity check.")

        def mainloop(self):
            events.append("app")

    class FakeRecovery:
        def __init__(self, db_path, data_dir, reason):
            events.append(("recovery", reason))
            self.restored = True

        def mainloop(self):
            pass

    monkeypatch.setattr(sys, "argv", ["desktop_app.py"])
    monkeypatch.setattr(desktop_app, "DATABASE_PATH", tmp_path / "app.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(application, "HangmanDesktop", FakeApp)
    monkeypatch.setattr(recovery, "RecoveryWindow", FakeRecovery)
    assert desktop_app.main() == 0
    assert events == [("recovery", "The data file failed its integrity check."), "app"]


def test_diagnostics_contain_codes_but_no_personal_data(saved_state, tmp_path):
    path = saved_state[0]
    logs = tmp_path / "diag-data"
    configure_logging(logs)
    try:
        log_event("ui.submit_guess", "finalize_round", ValueError("keeper typed password123"))
        logging.getLogger("hangman").error("Callback failed for keeper at %s", tmp_path)
        events = recent_events(logs)
    finally:
        close_logging()
    assert len(events) == 1
    assert "op=ui.submit_guess stage=finalize_round error=ValueError version=" in events[0]

    corrupt_header(path)  # diagnostics must still work when the database is damaged
    archive = tmp_path / "diagnostics.zip"
    export_diagnostics(path, archive, events=events)
    with zipfile.ZipFile(archive) as bundle:
        text = bundle.read("diagnostics.json").decode("utf-8")
    payload = json.loads(text)
    assert payload["database"].startswith("unavailable")
    assert payload["recent_events"] == events
    for secret in ("keeper", "password123", str(tmp_path), "hotel"):
        assert secret not in text
