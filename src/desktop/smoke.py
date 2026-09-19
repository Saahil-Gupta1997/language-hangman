"""Exercise the native desktop in disposable profiles (requires a GUI desktop).

This is a functional journey driven through the application's own handlers and on-screen
buttons. It is not evidence of keyboard, focus or screen-reader behaviour; those are manual
checks in docs/ACCEPTANCE.md. Each check is recorded only after it has passed, and the
result file is written even when a check fails.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from tkinter import messagebox

import customtkinter as ctk
from customtkinter.windows.widgets.scaling import ScalingTracker

from src import __version__
from src.desktop.application import HangmanDesktop
from src.desktop.recovery import RecoveryWindow
from src.services.desktop_storage import (
    DatabaseUnavailableError,
    backup_database,
    progress_report,
    restore_database,
)

PASSWORD = "smoke-password-123"


def _screenshot(window, output, name, shots):
    # Only ever the app's own window: a screen-region grab could record other programs.
    try:
        from src.desktop.capture import capture_window

        capture_window(window).save(output / name)
        shots.append(name)
    except (OSError, ImportError, AttributeError):
        pass  # No window capture here (e.g. not Windows); never fall back to the screen.


def _on_screen_button(app, prefix):
    return next(
        widget
        for widget in app.body.winfo_children()
        if isinstance(widget, ctk.CTkButton) and widget.cget("text").startswith(prefix)
    )


def _play_rounds(app, count):
    """Win ``count`` rounds of the current session; return the word ids played."""
    played = []
    for index in range(count):
        played.append(app.payload["round"]["word_id"])
        for letter in sorted(set(app.payload["round"]["word"])):
            app.guess_entry.insert(0, letter)
            app.submit_guess()
        assert app.payload["round"]["saved"]
        if index < count - 1:
            app.advance()
    app.finish_session()
    return played


def _profile_journey(data, output, checks, shots):
    app = HangmanDesktop(data / "app.db", data)
    failures = []
    app.report_callback_exception = lambda kind, value, trace: failures.append(repr(value))
    try:
        app.update()
        app.show_login(register=True)
        app.username_entry.insert(0, "smoke")
        app.password_entry.insert(0, PASSWORD)
        app.confirm_entry.insert(0, PASSWORD)
        app.authenticate(register=True)
        checks.append("registration")

        app.show_practice()
        app.focus.set("Review")
        app.start_session()
        assert app.practice.load(app.user["id"]) is None
        _screenshot(app, output, "review-unavailable.png", shots)
        _on_screen_button(app, "Start Standard practice").invoke()
        assert app.payload["session"]["practice_mode"] == "standard"
        checks.append("review refused for a new profile; standard offered")

        wrong = next(
            c for c in "abcdefghijklmnopqrstuvwxyz" if c not in app.payload["round"]["word"]
        )
        app.guess_entry.insert(0, wrong)
        app.submit_guess()
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
        app.focus.set("Review")
        app.rounds.set("10")
        app.start_session()
        assert app.payload["session"]["planned_rounds"] == 3
        assert "Only 3 review word(s)" in app.payload["notice"]
        _screenshot(app, output, "review-shortened.png", shots)
        assert sorted(_play_rounds(app, 3)) == sorted(practised)
        checks.append("review uses only practised words and explains the shorter session")

        backup = backup_database(app.db_path, data / "backup.sqlite")
        restore_database(app.db_path, backup)
        checks.append("backup and restore")
        app.show_words()
        app.show_settings()
        app.set_scale("Large")
        assert ScalingTracker.widget_scaling == 1.15
        app.set_scale("Standard")
        checks.append("text size change after dropdown screens")
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
    confirm, inform = messagebox.askyesno, messagebox.showinfo
    messagebox.askyesno = lambda *args, **kwargs: True
    messagebox.showinfo = lambda *args, **kwargs: None
    try:
        _screenshot(window, output, "recovery.png", shots)
        window.restore_from(backup)
    finally:
        messagebox.askyesno, messagebox.showinfo = confirm, inform
    assert window.restored
    quarantine = next((data / "backups").glob("quarantine-*"))
    assert (quarantine / "damaged-app.db").read_bytes() == bytes(damaged)
    checks.append("backup restored over damaged database; damaged bytes quarantined")

    app = HangmanDesktop(live, data)
    try:
        app.show_login()
        app.username_entry.insert(0, "smoke")
        app.password_entry.insert(0, PASSWORD)
        app.authenticate()
        assert progress_report(app.db_path, app.user["id"])["rounds"] == 6
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
            _recovery_journey(data, backup, output, checks, shots)
        result["passed"] = True
    finally:
        (output / "desktop-smoke.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0
