"""Measure desktop operations and window layout for the release record.

    python -m scripts.validation.measure performance <dataset folder>
    python -m scripts.validation.measure round [<language> <level>]
    python -m scripts.validation.measure scaling <output folder>

Performance figures are single-machine observations, not guarantees: every line reports its
sample count, and the environment belongs in the record beside them. Scaling runs at this
display's real setting plus two emulated factors; only a person can check the real Windows
setting (ACCEPTANCE M3).
"""

from __future__ import annotations

import json
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

import customtkinter as ctk

from src import __version__
from src.services.auth_service import AuthService
from src.services.desktop_storage import backup_database, open_live_database, progress_report
from src.services.practice_service import PracticeService

SETTINGS = {
    "language": "english",
    "categories": ["noun", "verb", "adjective", "adverb"],
    "difficulties": ["beginner"],
    "rounds": 10,
    "game_mode": "easy",
    "situation": "hotel",
    "practice_mode": "standard",
    "review_policy": "prefer_review",
    "show_hint_immediately": False,
}


def timed(action, runs):
    samples = []
    for _ in range(runs):
        start = time.perf_counter()
        action()
        samples.append((time.perf_counter() - start) * 1000)
    return samples


def report(name, samples):
    ordered = sorted(samples)
    index = min(len(ordered) - 1, round(0.95 * (len(ordered) - 1)))
    print(
        f"{name:<44} n={len(samples):<4} median {statistics.median(samples):8.1f} ms"
        f"   p95 {ordered[index]:8.1f} ms   max {max(samples):8.1f} ms"
    )


def performance(dataset):
    work = Path(tempfile.mkdtemp(prefix="hangman-perf-"))
    shutil.copy2(Path(dataset) / "app.db", work / "app.db")
    database = work / "app.db"
    print(f"version {__version__}; database {database.stat().st_size / 1_048_576:.2f} MB")
    report("open + upgrade check + quick_check", timed(lambda: open_live_database(database), 10))
    counter = iter(range(1000))
    report(
        "full backup (copy + validation)",
        timed(lambda: backup_database(database, work / f"b{next(counter)}.sqlite"), 5),
    )
    heavy = AuthService(database).authenticate_user("heavy", "heavy-pass-2026")
    report(
        "progress report, large profile", timed(lambda: progress_report(database, heavy["id"]), 20)
    )

    service = PracticeService(database, curated=True)
    ordinary, completing = [], []
    while len(completing) < 30:
        payload = service.start(heavy, SETTINGS)
        while True:
            for letter in sorted(set(payload["round"]["word"])):
                start = time.perf_counter()
                payload = service.guess(heavy, letter, payload["round"]["round_key"])
                elapsed = (time.perf_counter() - start) * 1000
                (completing if payload["round"]["saved"] else ordinary).append(elapsed)
            if not payload["next_round"]:
                service.discard(heavy["id"])
                break
            payload = service.next_round(heavy["id"])
    report("guess (round continues)", ordinary)
    report("guess that completes a round (all writes)", completing)

    from src.desktop.application import HangmanDesktop

    app = HangmanDesktop(database, work)
    try:
        app.show_login()
        app.username_entry.insert(0, "heavy")
        app.password_entry.insert(0, "heavy-pass-2026")
        app.authenticate()

        def render(screen):
            def run():
                screen()
                app.update()

            return run

        report("screen: Home", timed(render(app.show_home), 5))
        report("screen: Reports (full history table)", timed(render(app.show_reports), 5))
        report("screen: Practice setup", timed(render(app.show_practice), 5))
        report("screen: Word cards (travel)", timed(render(app.show_words), 5))

        def level_list():
            app.show_words()
            app.cards_language.set("Italian")
            app.cards_language_changed("Italian")
            app.update()

        report("screen: Word cards (one level list)", timed(level_list, 5))
    finally:
        app.close_application()
    shutil.rmtree(work, ignore_errors=True)


def round_redraw(language=None, level=None, rounds=12):
    """Time a guess from submission to redrawn screen, on a fresh profile.

    Travel cards by default; name a language and level to time a level list instead.
    """
    from src.desktop.application import HangmanDesktop

    data = Path(tempfile.mkdtemp(prefix="hangman-round-"))
    app = HangmanDesktop(data / "app.db", data)
    app.show_login(register=True)
    app.username_entry.insert(0, "timer")
    app.password_entry.insert(0, "timer-pass-2026")
    app.confirm_entry.insert(0, "timer-pass-2026")
    app.authenticate(register=True)
    samples = []
    for _ in range(rounds):
        app.show_practice()
        if not app.payload:
            if language:
                app.language.set(language)
                app.language_changed(language)
                app.level.set(level)
                app.word_set_changed(level)
            app.rounds.set("10")
            app.start_session()
        for letter in sorted({c.lower() for c in app.payload["round"]["word"] if c.isalpha()}):
            if app.payload["round"]["saved"]:
                break
            start = time.perf_counter()
            app.guess_entry.delete(0, "end")
            app.guess_entry.insert(0, letter)
            app.submit_guess()
            app.update()
            samples.append((time.perf_counter() - start) * 1000)
        if app.payload["next_round"]:
            app.advance()
        else:
            app.practice.discard(app.user["id"])
    app.close_application()
    words = f"{language} {level}" if language else "travel cards"
    report(f"guess to redrawn screen, {words}", samples)


def settle(window, factor, size):
    """CustomTkinter pins a window's size for about a second after a scaling change."""
    from src.desktop.widgets import TEXT_SCALING

    ctk.set_window_scaling(factor)
    ctk.set_widget_scaling(factor * TEXT_SCALING[size])
    deadline = time.monotonic() + 1.2
    while time.monotonic() < deadline:
        window.update()
        time.sleep(0.02)


def scaling(output, real_percent=125):
    """Capture both windows at their minimum size, at three scalings and two text sizes."""
    sys.path.insert(0, str(Path.cwd() / "tests"))
    from gui_scenarios import assert_text_fits, signed_in_app  # the same checks the tests use

    from src.desktop.application import MINIMUM_WINDOW, HangmanDesktop  # noqa: F401
    from src.desktop.capture import capture_window
    from src.desktop.recovery import RecoveryWindow

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    reason = "The data file could not be opened (DatabaseError)."
    print(f"real display scaling {real_percent}%; 0.8 and 1.2 emulate lower and higher settings")
    for label, factor in (
        ("100-emulated", 0.8),
        (f"{real_percent}-real", 1.0),
        ("150-emulated", 1.2),
    ):
        for size in ("Standard", "Large"):
            data = Path(tempfile.mkdtemp(prefix="hangman-scale-"))
            (data / "backups").mkdir()
            for name in ("daily-a.sqlite", "before-restore-b.sqlite", "pre-upgrade-c.sqlite"):
                (data / "backups" / name).write_bytes(b"")
            (data / "settings.json").write_text(json.dumps({"text_size": size}))
            window = RecoveryWindow(data / "app.db", data, reason)
            try:
                settle(window, factor, size)
                window.geometry("640x480")
                window.update()
                assert_text_fits(window.body, f"recovery {label} {size}")
                capture_window(window).save(output / f"recovery-{label}-{size.lower()}-minimum.png")
                print(f"recovery window, {label}, {size} text, minimum size: text fits")
            finally:
                window.close()
            app = signed_in_app(data)
            try:
                settle(app, factor, size)
                app.geometry(f"{MINIMUM_WINDOW[0]}x{MINIMUM_WINDOW[1]}")
                app.show_practice()
                app.start_session()
                app.update()
                assert_text_fits(app.body, f"practice round {label} {size}")
                capture_window(app).save(output / f"round-{label}-{size.lower()}-minimum.png")
                for page in (app.show_home, app.show_settings, app.show_help):
                    page()
                    app.update()
                    assert_text_fits(app.body, f"{page.__name__} {label} {size}")
                print(f"main window round, Home, Settings and Help, {label}, {size}: text fits")
            finally:
                app.close_application()
                ctk.set_window_scaling(1.0)
                ctk.set_widget_scaling(1.0)


if __name__ == "__main__":
    {"performance": performance, "round": round_redraw, "scaling": scaling}[sys.argv[1]](
        *sys.argv[2:]
    )
