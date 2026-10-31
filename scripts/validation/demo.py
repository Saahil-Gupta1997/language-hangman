"""Record the captioned demo of a release candidate.

    <python with imageio-ffmpeg> -m scripts.validation.demo <output.mp4> <revision>

Run from a clean checkout of the revision being recorded. The app is driven through its own
controls and handlers; no operating-system keystrokes are sent, and every frame is a capture
of the application's own window, so nothing else on the computer can appear. Needs
imageio-ffmpeg, which is not a project dependency: install it in a scratch environment.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from tkinter import filedialog, messagebox

from PIL import Image, ImageDraw, ImageFont

from src import __version__
from src.desktop.application import HangmanDesktop
from src.desktop.capture import capture_window
from src.desktop.recovery import RecoveryWindow
from src.services.desktop_storage import DatabaseUnavailableError

FPS, WIDTH, HEIGHT, BAND = 10, 1360, 1100, 96
PACE = 1.3  # slower than real time, so each caption can be read
PROFILE, PASSWORD = "maya", "travel-2026"


def font(size):
    for name in ("segoeui.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(rf"C:\Windows\Fonts\{name}", size)
        except OSError:
            continue
    return ImageFont.load_default()


class Recorder:
    def __init__(self, output):
        import imageio_ffmpeg

        self.writer = imageio_ffmpeg.write_frames(
            str(output),
            (WIDTH, HEIGHT),
            fps=FPS,
            codec="libx264",
            pix_fmt_out="yuv420p",
            quality=7,
            macro_block_size=2,
        )
        self.writer.send(None)
        self.seconds = 0.0
        self.caption_font, self.card_font = font(30), font(22)

    def emit(self, frame, seconds):
        seconds *= PACE
        data = frame.tobytes()
        for _ in range(max(1, round(seconds * FPS))):
            self.writer.send(data)
        self.seconds += seconds

    def show(self, window, caption, seconds):
        image = capture_window(window)
        frame = Image.new("RGB", (WIDTH, HEIGHT), (30, 41, 59))
        area = (WIDTH, HEIGHT - BAND)
        shrunk = image.copy()
        shrunk.thumbnail(area)
        frame.paste(shrunk, ((area[0] - shrunk.width) // 2, (area[1] - shrunk.height) // 2))
        draw = ImageDraw.Draw(frame)
        draw.rectangle((0, HEIGHT - BAND, WIDTH, HEIGHT), fill=(15, 23, 42))
        draw.text((32, HEIGHT - BAND + 30), caption, font=self.caption_font, fill=(248, 250, 252))
        self.emit(frame, seconds)

    def card(self, lines, seconds):
        frame = Image.new("RGB", (WIDTH, HEIGHT), (21, 94, 117))
        draw = ImageDraw.Draw(frame)
        y = 300
        for index, line in enumerate(lines):
            draw.text(
                (90, y),
                line,
                font=self.caption_font if not index else self.card_font,
                fill=(255, 255, 255),
            )
            y += 70 if not index else 44
        self.emit(frame, seconds)

    def close(self):
        self.writer.close()


def record(output, revision):
    output = Path(output)
    film = Recorder(output)
    messagebox.askyesno = lambda *args, **kwargs: True  # the demo answers its own dialogs
    messagebox.showinfo = lambda *args, **kwargs: None
    data = Path(tempfile.mkdtemp(prefix="hangman-demo-"))

    def type_into(window, entry, text, caption):
        for character in text:
            entry.insert("end", character)
            film.show(window, caption, 0.2)

    def guess(app, letter, caption, seconds):
        app.guess_entry.delete(0, "end")
        app.guess_entry.insert(0, letter)
        app.submit_guess()
        film.show(app, caption, seconds)

    def win_round(app, caption, per_letter=0.5):
        for letter in sorted(set(app.payload["round"]["word"])):
            if not app.payload["round"]["saved"]:
                guess(app, letter, caption, per_letter)

    def button(app, prefix):
        from src.desktop.smoke import _on_screen_button

        return _on_screen_button(app, prefix)

    def sign_in(app, caption):
        app.show_login()
        type_into(app, app.username_entry, PROFILE, caption)
        type_into(app, app.password_entry, PASSWORD, caption)
        app.authenticate()

    film.card(
        [
            f"Language Hangman {__version__} (release candidate)",
            "Offline Windows desktop app for English travel vocabulary "
            "(Python, CustomTkinter, SQLite).",
            "Rule-based software built with AI assistance. 30 curated words: "
            "Restaurant, Airport, Hotel.",
            f"Scripted run of revision {revision}; captures the app window only.",
        ],
        6,
    )
    app = HangmanDesktop(data / "app.db", data)
    film.show(app, "Sign-in: local profiles only. No cloud account; passwords are hashed.", 4)
    app.show_login(register=True)
    type_into(app, app.username_entry, PROFILE, "Create a local profile")
    type_into(app, app.password_entry, PASSWORD, "Create a local profile")
    type_into(app, app.confirm_entry, PASSWORD, "Create a local profile")
    app.authenticate(register=True)
    film.show(app, "Home: progress so far and how the game difficulty works", 4)
    app.show_practice()
    film.show(app, "Practice setup: situation, difficulty, rounds and focus", 4)
    app.focus.set("Review")
    film.show(app, "A new learner chooses Review...", 2.5)
    app.start_session()
    film.show(app, "...but Review only uses words already practised, so Standard is offered", 5)
    button(app, "Start Standard practice").invoke()
    film.show(app, "Standard session: Restaurant, Easy (7 lives), 3 rounds", 4)
    wrong = next(c for c in "zqxjkvwy" if c not in app.payload["round"]["word"])
    guess(app, wrong, "A wrong guess costs a life, draws the figure and reveals a clue", 4)
    win_round(app, "Guess a letter: type it, or click a letter key")
    film.show(app, "After each round: meaning, example, pronunciation and a usage note", 6)
    app.advance()
    win_round(app, "Round 2", per_letter=0.3)
    film.show(app, "Round 2 won", 2)
    app.advance()
    for letter in [
        c for c in "abcdefghijklmnopqrstuvwxyz" if c not in app.payload["round"]["word"]
    ][:7]:
        if not app.payload["round"]["saved"]:
            guess(app, letter, "Round 3: running out of lives", 0.5)
    film.show(app, "A lost round is saved and scheduled for review", 4)
    button(app, "Finish session").invoke()
    film.show(app, "Reports: every metric states its denominator", 6)
    app.show_practice()
    app.focus.set("Review")
    app.rounds.set("5")
    app.start_session()
    film.show(app, "Review now uses only the practised words and says why it is shorter", 6)
    film.show(app, "Close the app at any point...", 2.5)
    app.close_application()
    app = HangmanDesktop(data / "app.db", data)
    sign_in(app, "Sign in again")
    app.show_practice()
    film.show(app, "...and the session resumes with its guesses and clues", 5)
    app.show_words()
    film.show(app, "Word cards: all 30 curated words with examples and usage notes", 4)
    app.show_settings()
    app.set_scale("Large")
    film.show(app, "Text size: Large (also Ctrl +)", 3.5)
    app.set_scale("Standard")
    film.show(app, "Settings: full backup, restore, export, delete and privacy-safe diagnostics", 4)
    app.close_application()

    # Make a backup the way Settings does, so the recovery scene restores data that contains
    # this profile. The daily automatic backup is taken at first launch, before the profile
    # exists, so restoring it would sign the learner in to an empty database.
    from src.services.desktop_storage import backup_database

    saved_backup = data / "my-backup.sqlite"
    backup_database(data / "app.db", saved_backup)

    film.card(["Simulated damage: the data file is corrupted while the app is closed."], 3)
    database = data / "app.db"
    damaged = bytearray(database.read_bytes())
    damaged[:100] = b"\0" * 100
    database.write_bytes(bytes(damaged))
    try:
        HangmanDesktop(database, data)
        raise AssertionError("the damaged database opened; the demo would be misleading")
    except DatabaseUnavailableError as error:
        recovery = RecoveryWindow(database, data, str(error))
    film.show(recovery, "Instead of failing, the app opens recovery; nothing is deleted", 6)
    filedialog.askopenfilename = lambda *args, **kwargs: str(saved_backup)
    next(
        child
        for child in recovery.body.winfo_children()
        if hasattr(child, "cget") and str(child.cget("text")).startswith("Choose a backup file")
    ).invoke()
    app = HangmanDesktop(database, data)
    sign_in(app, "Backup restored (the damaged file is kept); sign in again")
    film.show(app, "Progress is back", 4)
    app.close_application()
    film.card(
        [
            "Evidence and status",
            f"Revision {revision}: automated suite, lint and content checks pass; "
            "native smoke journey passed.",
            "Installer (build machine): install, upgrade, beta import, recovery, "
            "uninstall verified.",
            "Still pending: clean-computer install, manual checks, educator review, "
            "five learner sessions.",
            "Details: README.md, docs/VERIFICATION.md and docs/ACCEPTANCE.md.",
        ],
        8,
    )
    film.close()
    size = output.stat().st_size / 1_048_576
    print(f"recorded {film.seconds:.0f} s to {output.name} ({size:.1f} MB)")


if __name__ == "__main__":
    record(sys.argv[1], sys.argv[2])
