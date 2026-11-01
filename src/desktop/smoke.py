"""Exercise the native desktop in disposable profiles (requires a GUI desktop).

This is a functional journey driven through the application's own handlers and on-screen
buttons, plus real process termination for crash recovery. It is not evidence of keyboard,
focus or screen-reader behaviour; those are manual checks in docs/ACCEPTANCE.md. Each check
is recorded only after it has passed, and the result file is written even when one fails.
"""

import contextlib
import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from tkinter import messagebox

import customtkinter as ctk
from customtkinter.windows.widgets.scaling import ScalingTracker

from src import __version__
from src.desktop.application import HangmanDesktop
from src.desktop.practice_view import REVIEW_WORDS
from src.desktop.recovery import RecoveryWindow
from src.services.auth_service import AuthService
from src.services.desktop_storage import (
    DatabaseUnavailableError,
    backup_database,
    progress_report,
    restore_database,
)

NAME, PASSWORD = "smoke", "smoke-password-123"
OTHER_NAME, OTHER_PASSWORD = "smoke-two", "second-password-456"
CRASH_EXIT_CODE = 3


@contextlib.contextmanager
def _auto_confirm():
    """Answer "Yes" to confirmations and dismiss information boxes during the journey."""
    saved = messagebox.askyesno, messagebox.showinfo
    messagebox.askyesno = lambda *args, **kwargs: True
    messagebox.showinfo = lambda *args, **kwargs: None
    try:
        yield
    finally:
        messagebox.askyesno, messagebox.showinfo = saved


def _screenshot(window, output, name, shots):
    # Only ever the app's own window: a screen-region grab could record other programs.
    try:
        from src.desktop.capture import capture_window

        capture_window(window).save(output / name)
        shots.append(name)
    except (OSError, ImportError, AttributeError):
        pass  # No window capture here (e.g. not Windows); never fall back to the screen.


def _descendants(parent):
    for child in parent.winfo_children():
        yield child
        yield from _descendants(child)


def _on_screen_button(app, prefix):
    return next(
        widget
        for widget in _descendants(app.body)
        if isinstance(widget, ctk.CTkButton) and widget.cget("text").startswith(prefix)
    )


def _sign_in(app, name=NAME, password=PASSWORD, register=False):
    app.show_login(register=register)
    app.username_entry.insert(0, name)
    app.password_entry.insert(0, password)
    if register:
        app.confirm_entry.insert(0, password)
    app.authenticate(register=register)


def _guess(app, letters):
    for letter in letters:
        app.guess_entry.insert(0, letter)
        app.submit_guess()


def _play_rounds(app, count):
    """Win ``count`` rounds of the current session; return the word ids played."""
    played = []
    for index in range(count):
        played.append(app.payload["round"]["word_id"])
        _guess(app, sorted(set(app.payload["round"]["word"])))
        assert app.payload["round"]["saved"]
        if index < count - 1:
            app.advance()
    app.end_session()
    return played


def _profile_journey(data, output, checks, shots):
    app = HangmanDesktop(data / "app.db", data)
    failures = []
    app.report_callback_exception = lambda kind, value, trace: failures.append(repr(value))
    try:
        _sign_in(app, register=True)
        checks.append("registration")

        app.show_practice()
        app.focus.set(REVIEW_WORDS)
        app.start_session()
        assert app.practice.load(app.user["id"]) is None
        _screenshot(app, output, "review-unavailable.png", shots)
        _on_screen_button(app, "Play all").invoke()
        assert app.payload["session"]["practice_mode"] == "standard"
        checks.append("review refused for a new profile; all words offered")

        _guess(app, [next(c for c in "zqxjkvwy" if c not in app.payload["round"]["word"])])
        wrong = app.payload["round"]["wrong_letters"][0]
        app.show_home()
        app.show_practice()
        assert wrong in app.payload["round"]["wrong_letters"]
        assert "meaning" in app.payload["round"]["revealed_hint_keys"]
        checks.append("clue after wrong guess; session resumes")
        _screenshot(app, output, "practice.png", shots)

        practised = _play_rounds(app, 3)
        report = progress_report(app.db_path, app.user["id"])
        assert (report["rounds"], report["sessions"]) == (3, 1)
        checks.append("three rounds recorded in reports")

        app.show_practice()
        app.focus.set(REVIEW_WORDS)
        app.start_session()
        assert app.payload["session"]["planned_rounds"] == 3
        _screenshot(app, output, "review.png", shots)
        assert sorted(_play_rounds(app, 3)) == sorted(practised)
        checks.append("review uses only practised words, each once")

        app.show_practice()
        app.mode.set("Hard")
        app.start_session()
        word = app.payload["round"]["word"]
        _guess(app, [c for c in "abcdefghijklmnopqrstuvwxyz" if c not in word][:5])
        assert app.payload["round"]["result"] == "lost"
        app.end_session()  # a finished word makes this a completed session
        report = progress_report(app.db_path, app.user["id"])
        assert (report["rounds"], report["wins"], report["losses"]) == (7, 6, 1)
        assert report["sessions"] == 3
        app.show_reports()
        _screenshot(app, output, "reports.png", shots)
        checks.append("lost round and ended session reported correctly")

        export = data / "profile-export.json"
        app.show_settings()
        app.save_path = lambda extension, title: str(export)
        with _auto_confirm():
            app.export_user()
        text = export.read_text(encoding="utf-8")
        assert len(json.loads(text)["game_sessions"]) == 7 and "password_hash" not in text
        checks.append("profile export contains progress and no credentials")

        app.logout()
        _sign_in(app, OTHER_NAME, OTHER_PASSWORD, register=True)
        app.show_settings()
        app.password_delete.insert(0, OTHER_PASSWORD)
        with _auto_confirm():
            app.delete_user()
        assert app.user is None
        assert AuthService(app.db_path).authenticate_user(OTHER_NAME, OTHER_PASSWORD) is None
        _sign_in(app)
        assert progress_report(app.db_path, app.user["id"])["rounds"] == 7
        checks.append("profile deletion keeps other profiles intact")

        backup = backup_database(app.db_path, data / "backup.sqlite")
        restore_database(app.db_path, backup)
        checks.append("backup and restore")
        app.show_settings()
        app.set_scale("Large")
        assert ScalingTracker.widget_scaling == 1.15
        app.set_scale("Standard")
        checks.append("text size change after dropdown screens")
        app.show_practice()
        app.language.set("German")
        app.start_session()
        app.update()
        assert app.payload["round"]["language"] == "german"
        assert app.payload["session"]["difficulty_filter"] == ["beginner"]
        assert len(app.board._keys) == 26
        app.end_session()  # nothing finished, so this one is not counted
        assert progress_report(app.db_path, app.user["id"])["sessions"] == 3
        checks.append("German list plays on A-Z; an empty session is not counted")
        app.show_help()
        app.logout()
        app.start_guest()
        app.show_practice()
        app.start_session()
        app.logout()
        checks.append("guest practice and sign out")
        assert not failures, failures
    finally:
        app.close_application()
    return backup


def crash_child(data_dir, stage):
    """Child process: reach ``stage``, then end abruptly with no clean shutdown."""
    data = Path(data_dir)
    app = HangmanDesktop(data / "app.db", data)
    _sign_in(app)
    app.show_practice()
    if stage == "mid_round":
        app.level.set("Novice")
        app.start_session()
        _guess(app, [next(c for c in "zqxjkvwy" if c not in app.payload["round"]["word"])])
    else:  # between_rounds: finish the resumed round and leave its learning card open
        _guess(app, sorted(set(app.payload["round"]["word"])))
    os._exit(CRASH_EXIT_CODE)


def _run_crash_child(data, stage):
    if getattr(sys, "frozen", False):
        command = [sys.executable]
    else:
        command = [sys.executable, str(Path(__file__).resolve().parents[2] / "desktop_app.py")]
    completed = subprocess.run(
        [*command, "--smoke-crash", str(data), stage], timeout=180, check=False
    )
    assert completed.returncode == CRASH_EXIT_CODE, completed.returncode


def _crash_journey(data, checks):
    _run_crash_child(data, "mid_round")
    app = HangmanDesktop(data / "app.db", data)
    try:
        _sign_in(app)
        app.show_practice()
        assert not app.payload["round"]["saved"] and app.payload["round"]["wrong_letters"]
        checks.append("round resumes after the app process is ended mid-round")
    finally:
        app.close_application()

    _run_crash_child(data, "between_rounds")
    app = HangmanDesktop(data / "app.db", data)
    try:
        _sign_in(app)
        app.show_practice()
        assert app.payload["round"]["saved"] and app.payload["next_round"]
        app.advance()
        assert not app.payload["round"]["saved"]
        app.end_session()
        checks.append("learning card and next round resume after the process ends between rounds")
    finally:
        app.close_application()


def _recovery_journey(data, backup, output, checks, shots):
    live = data / "app.db"
    damaged = bytearray(live.read_bytes())
    damaged[:100] = b"\x00" * 100
    live.write_bytes(bytes(damaged))
    try:
        HangmanDesktop(live, data)
    except DatabaseUnavailableError as error:
        reason = str(error)
    else:
        raise AssertionError("A damaged database must not open normally.")
    checks.append("damaged database detected at start-up")

    window = RecoveryWindow(live, data, reason)
    _screenshot(window, output, "recovery.png", shots)
    with _auto_confirm():
        window.restore_from(backup)
    assert window.restored
    quarantine = next((data / "backups").glob("quarantine-*"))
    assert (quarantine / "damaged-app.db").read_bytes() == bytes(damaged)
    checks.append("backup restored over damaged database; damaged bytes quarantined")

    app = HangmanDesktop(live, data)
    try:
        _sign_in(app)
        assert progress_report(app.db_path, app.user["id"])["rounds"] == 7
        checks.append("sign in and progress after recovery")
    finally:
        app.close_application()


def run(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    checks, shots = [], []
    result = {"passed": False, "version": __version__, "checks": checks, "screenshots": shots}
    try:
        with TemporaryDirectory(prefix="hangman-smoke-") as temporary:
            data = Path(temporary)
            backup = _profile_journey(data, output, checks, shots)
            _crash_journey(data, checks)
            _recovery_journey(data, backup, output, checks, shots)
        result["passed"] = True
    finally:
        (output / "desktop-smoke.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0
