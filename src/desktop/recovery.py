"""Recovery window shown when the saved data cannot be opened at start-up."""

from __future__ import annotations

import os
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from src import __version__
from src.desktop.runtime import log_event
from src.desktop.widgets import BLUE, keyboard_button
from src.services.curated_content import seed_curated
from src.services.desktop_storage import restore_database

AUTOMATIC_BACKUPS = {
    "daily-": "daily backup",
    "before-restore-": "safety backup",
    "pre-upgrade-": "pre-upgrade backup",
}


def automatic_backups(data_dir, limit=5):
    """Return the newest automatic backups in the data folder, newest first."""
    folder = Path(data_dir) / "backups"
    if not folder.is_dir():
        return []
    found = [
        path
        for path in folder.glob("*.sqlite")
        if path.is_file() and path.name.startswith(tuple(AUTOMATIC_BACKUPS))
    ]
    return sorted(found, key=lambda path: path.stat().st_mtime, reverse=True)[:limit]


def describe_backup(path):
    kind = next(
        label for prefix, label in AUTOMATIC_BACKUPS.items() if path.name.startswith(prefix)
    )
    saved = datetime.fromtimestamp(path.stat().st_mtime).strftime("%d %b %Y %H:%M")
    return f"{kind} saved {saved}"


class RecoveryWindow(ctk.CTk):
    """Restore a backup without opening the damaged live database."""

    def __init__(self, db_path, data_dir, reason):
        super().__init__()
        self.db_path, self.data_dir = Path(db_path), Path(data_dir)
        self.restored = False
        self.title(f"Language Hangman · Recovery · {__version__}")
        self.geometry("820x640")
        self.minsize(640, 480)
        ctk.set_appearance_mode("light")
        header = ctk.CTkFrame(self, corner_radius=0, fg_color=BLUE)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text="Language Hangman", text_color="white", font=("Arial", 24, "bold")
        ).pack(side="left", padx=24, pady=18)
        self.body = ctk.CTkScrollableFrame(self, fg_color="#F5F7FA", corner_radius=12)
        self.body.pack(fill="both", expand=True, padx=20, pady=12)
        self._label("Your saved data could not be opened", size=24)
        self._label(reason, bold=True)
        self._label(
            "Nothing has been deleted. To continue, restore a full backup. Restoring replaces "
            "ALL local profiles and progress on this computer with the backup. Before the "
            "switch, the current data file is kept in the backups folder: as a normal safety "
            "backup if it can still be read, otherwise as an exact quarantine copy."
        )
        buttons = []
        backups = automatic_backups(self.data_dir)
        if backups:
            self._label("Automatic backups on this computer, newest first:", bold=True)
            for path in backups:
                buttons.append(
                    self._button(
                        f"Restore {describe_backup(path)}",
                        lambda chosen=path: self.restore_from(chosen),
                    )
                )
        else:
            self._label("No automatic backups were found in the data folder.", bold=True)
        buttons.append(self._button("Choose a backup file…", self.choose_backup))
        buttons.append(self._button("Open data folder", self.open_data_folder))
        buttons.append(self._button("Quit", self.destroy))
        self._label(
            "If a restore fails, the message explains why and your current data file stays "
            "unchanged. After recovery, you can export diagnostics from Settings."
        )
        self.bind("<Escape>", lambda event: self.destroy())
        buttons[0].focus_set()

    def _label(self, text, bold=False, size=15):
        ctk.CTkLabel(
            self.body,
            text=text,
            anchor="w",
            justify="left",
            wraplength=680,
            font=("Arial", size, "bold" if bold or size > 15 else "normal"),
            text_color="#172B4D",
        ).pack(fill="x", padx=22, pady=7)

    def _button(self, label, command):
        button = keyboard_button(self.body, label, command, width=320)
        button.pack(anchor="w", padx=22, pady=6)
        return button

    def choose_backup(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Choose a Language Hangman backup",
            filetypes=[("SQLite database", "*.sqlite *.db *.sqlite3")],
        )
        if path:
            self.restore_from(Path(path))

    def restore_from(self, path):
        if not messagebox.askyesno(
            "Replace all local profiles?",
            f"Restore “{Path(path).name}”?\n\nThis replaces ALL local profiles and progress on "
            "this computer with the backup. The current data file is kept in the backups "
            "folder first.",
            parent=self,
        ):
            return
        try:
            preserved = restore_database(self.db_path, path)
            seed_curated(self.db_path)
        except ValueError as error:  # invalid backup or RestoreError with a stage
            log_event(
                "recovery.restore", getattr(error, "stage", "validate"), error.__cause__ or error
            )
            messagebox.showerror("Backup not restored", str(error), parent=self)
            return
        except Exception as error:  # noqa: BLE001 - report and keep the window usable
            log_event("recovery.restore", "unexpected", error)
            messagebox.showerror(
                "Backup not restored",
                "The backup could not be restored and your current data file was not "
                "replaced. Try another backup, or keep this window open and contact support "
                "with the version number shown in the title bar.",
                parent=self,
            )
            return
        kept = (
            f"\n\nThe previous data file was kept as backups/{preserved.name}."
            if preserved is not None
            else ""
        )
        messagebox.showinfo(
            "Backup restored",
            "The backup was restored. Language Hangman will now start; sign in with a "
            f"profile from the backup.{kept}",
            parent=self,
        )
        self.restored = True
        self.destroy()

    def open_data_folder(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if hasattr(os, "startfile"):
            os.startfile(self.data_dir)  # noqa: S606 - opens the user's own data folder
        else:
            webbrowser.open(self.data_dir.as_uri())
