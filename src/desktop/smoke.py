"""Exercise native widgets in a disposable profile (requires a GUI desktop)."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from src.desktop.application import HangmanDesktop
from src.services.desktop_storage import backup_database, progress_report, restore_database


def run(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="hangman-smoke-") as temporary:
        data = Path(temporary)
        app = HangmanDesktop(data / "app.db", data)
        failures = []
        app.report_callback_exception = lambda kind, value, trace: failures.append(str(value))
        try:
            app.update()
            app.show_login(register=True)
            app.username_entry.insert(0, "smoke")
            app.password_entry.insert(0, "smoke-password-123")
            app.confirm_entry.insert(0, "smoke-password-123")
            app.authenticate(register=True)
            app.show_practice()
            app.start_session()
            state = app.payload
            wrong = next(c for c in "abcdefghijklmnopqrstuvwxyz" if c not in state["round"]["word"])
            app.guess_entry.insert(0, wrong)
            app.submit_guess()
            app.show_home()
            app.show_practice()
            assert wrong in app.payload["round"]["wrong_letters"]
            assert "meaning" in app.payload["round"]["revealed_hint_keys"]
            app.update()
            screenshots = []
            try:
                from PIL import ImageGrab

                bounds = (
                    app.winfo_rootx(),
                    app.winfo_rooty(),
                    app.winfo_rootx() + app.winfo_width(),
                    app.winfo_rooty() + app.winfo_height(),
                )
                ImageGrab.grab(bbox=bounds).save(output / "practice.png")
                screenshots.append("practice.png")
            except OSError:
                pass  # Screenshots may be unavailable on a Windows service desktop.
            for index in range(3):
                for letter in sorted(set(app.payload["round"]["word"])):
                    app.guess_entry.insert(0, letter)
                    app.submit_guess()
                assert app.payload["round"]["saved"]
                if index < 2:
                    app.advance()
            user = app.user
            app.finish_session()
            app.update()
            assert progress_report(app.db_path, user["id"])["rounds"] == 3
            backup = backup_database(app.db_path, data / "backup.sqlite")
            restore_database(app.db_path, backup)
            app.show_words()
            app.update()
            app.show_settings()
            app.set_scale("Large")
            app.update()
            app.show_help()
            app.update()
            app.logout()
            app.start_guest()
            app.show_practice()
            app.start_session()
            app.logout()
            assert not failures, failures
            (output / "desktop-smoke.json").write_text(
                json.dumps(
                    {
                        "passed": True,
                        "checks": [
                            "registration",
                            "hints",
                            "resume",
                            "three rounds",
                            "reports",
                            "backup restore",
                            "word cards",
                            "text scaling",
                            "guest",
                            "logout",
                        ],
                        "screenshots": screenshots,
                    },
                    indent=2,
                )
            )
        finally:
            app.close_application()
    return 0
