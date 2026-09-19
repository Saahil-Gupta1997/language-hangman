"""Native desktop app: profiles, durable practice, reports and local recovery."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from src import __version__
from src.desktop.auth_view import AuthView
from src.desktop.practice_view import PracticeView
from src.desktop.reports_view import ReportsView
from src.desktop.runtime import (
    close_logging,
    configure_logging,
    failure_location,
    fix_dropdown_scaling_leak,
    log_event,
)
from src.desktop.settings_view import SettingsView
from src.desktop.widgets import (
    BLUE,
    TEXT_SCALING,
    fit_to_work_area,
    keyboard_button,
    release_window,
    saved_text_size,
    scroll_into_view,
    wrap_to_width,
)
from src.services.auth_service import AuthService
from src.services.curated_content import seed_curated
from src.services.desktop_storage import backup_database, open_live_database
from src.services.practice_service import PracticeService
from src.utils.config import DATA_DIR, DATABASE_PATH

WARNING_BACKGROUND = "#FEF3C7"
# Supported minimum (logical pixels): fits a 1080p screen at 150% scaling.
MINIMUM_WINDOW = (800, 600)


class HangmanDesktop(AuthView, PracticeView, ReportsView, SettingsView, ctk.CTk):
    def __init__(self, db_path=DATABASE_PATH, data_dir=DATA_DIR):
        fix_dropdown_scaling_leak()
        # Open the data before creating a window: failures raise DatabaseUnavailableError
        # so the launcher can offer recovery instead of a half-built window.
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger = configure_logging(self.data_dir)
        try:
            self.db_path = open_live_database(db_path)
        except Exception as error:
            log_event("startup", "open_database", error.__cause__ or error)
            raise
        seed_curated(self.db_path)
        super().__init__()
        self.title(f"Language Hangman · {__version__}")
        fit_to_work_area(self, 1060, 760, minimum=MINIMUM_WINDOW)
        self.auth = AuthService(self.db_path)
        self.practice = PracticeService(self.db_path, curated=True)
        self.user = None
        self.guest = None
        self.payload = None
        self.page = ""
        self.protocol("WM_DELETE_WINDOW", self.close_application)
        self.bind("<Escape>", lambda event: self.show_home() if self.user else None)
        # "+" needs Shift on most keyboards, so accept Ctrl+= and the numeric keypad too.
        for sequence in ("<Control-plus>", "<Control-equal>", "<Control-KP_Add>"):
            self.bind(sequence, lambda event: self.set_scale("Large"))
        for sequence in ("<Control-minus>", "<Control-KP_Subtract>"):
            self.bind(sequence, lambda event: self.set_scale("Standard"))
        self.scale = saved_text_size(self.data_dir)
        ctk.set_appearance_mode("light")
        ctk.set_widget_scaling(TEXT_SCALING[self.scale])
        self.header = ctk.CTkFrame(self, corner_radius=0, fg_color=BLUE)
        self.header.pack(fill="x")
        ctk.CTkLabel(
            self.header, text="Language Hangman", text_color="white", font=("Arial", 24, "bold")
        ).pack(side="left", padx=24, pady=18)
        self.backup_warning = self.automatic_backup()
        if self.backup_warning:
            wrap_to_width(
                ctk.CTkLabel(
                    self,
                    text=self.backup_warning,
                    fg_color=WARNING_BACKGROUND,
                    text_color="#78350F",
                    corner_radius=8,
                    justify="left",
                    font=("Arial", 14, "bold"),
                )
            ).pack(fill="x", padx=20, pady=(10, 0), ipady=6)
        self.navigation = ctk.CTkFrame(self, fg_color="transparent")
        self.navigation.pack(fill="x", padx=20, pady=(10, 0))
        self.body = ctk.CTkScrollableFrame(self, fg_color="#F5F7FA", corner_radius=12)
        self.body.pack(fill="both", expand=True, padx=20, pady=12)
        ctk.CTkLabel(
            self,
            text="Local English vocabulary practice · Progress stays on this device",
            font=("Arial", 12),
            text_color="#475569",
        ).pack(pady=(0, 10))
        self.show_login()

    def report_callback_exception(self, exception, value, traceback):
        # Log codes and the error type only; messages can contain paths or user input.
        operation, stage = failure_location(traceback)
        log_event(operation, getattr(value, "stage", stage), value.__cause__ or value)
        if isinstance(value, ValueError):
            message = str(value)
        elif isinstance(value, FileExistsError):
            message = (
                "That file already exists. Choose a new filename to preserve the existing file."
            )
        elif isinstance(value, PermissionError):
            message = "Permission was denied. Choose a writable folder and retry."
        elif isinstance(value, sqlite3.Error):
            message = (
                "Your changes could not be saved. Check free disk space and folder "
                "permissions, then retry. Previously committed progress is preserved."
            )
        else:
            message = (
                "This action could not be completed. Reopen Practice to load the last "
                "saved state. You can export diagnostics from Settings."
            )
        messagebox.showerror("Action could not be completed", message, parent=self)

    def automatic_backup(self):
        """Keep one backup per day (seven retained); return a warning instead of failing.

        The live database has already opened and passed its check, so a failed backup
        must not stop the learner from practising; it is reported on screen and logged.
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        destination = self.data_dir / "backups" / f"daily-{today}.sqlite"
        try:
            if not destination.exists():
                backup_database(self.db_path, destination)
            daily = sorted((self.data_dir / "backups").glob("daily-*.sqlite"))
            for old in daily[:-7]:
                old.unlink()
        except (OSError, sqlite3.Error, ValueError) as error:
            log_event("startup", "automatic_backup", error)
            return (
                "Automatic backup is unavailable today, so backup protection is reduced. "
                "Your progress is still saved. Free some disk space or check folder "
                "permissions, then create a full backup from Settings."
            )
        return None

    def clear(self, page):
        if self.page == "Practice" and self.user:
            self.practice.pause(self.user["id"])
        self.page = page
        self.unbind("<Return>")
        for child in self.body.winfo_children():
            child.destroy()
        for child in self.navigation.winfo_children():
            child.destroy()
        if self.user:
            for index, (label, command) in enumerate(
                [
                    ("Home", self.show_home),
                    ("Practice", self.show_practice),
                    ("Reports", self.show_reports),
                    ("Word cards", self.show_words),
                    ("Settings", self.show_settings),
                    ("Help", self.show_help),
                    ("Sign out", self.logout),
                ]
            ):
                # Tk forbids mixing pack and grid in one frame, so these are gridded only.
                control = self.button(self.navigation, label, command, width=130, pack=False)
                control.grid(row=index // 4, column=index % 4, sticky="ew", padx=4, pady=4)
                self.navigation.grid_columnconfigure(index % 4, weight=1)
        else:
            self.button(self.navigation, "Help", self.show_help, side="left")
            self.button(self.navigation, "Restore / import old database", self.restore, side="left")
            self.button(self.navigation, "Sign in", self.show_login, side="left")

    def heading(self, text, description=""):
        ctk.CTkLabel(self.body, text=text, anchor="w", font=("Arial", 27, "bold")).pack(
            fill="x", padx=22, pady=(20, 6)
        )
        if description:
            self.text(description)

    def text(self, text, parent=None, bold=False):
        label = ctk.CTkLabel(
            parent or self.body,
            text=text,
            anchor="w",
            justify="left",
            font=("Arial", 15, "bold" if bold else "normal"),
            text_color="#172B4D",
        )
        wrap_to_width(label).pack(fill="x", padx=22, pady=7)
        return label

    def button(self, parent, label, command, side=None, width=180, pack=True):
        button = keyboard_button(parent, label, command, width=width)
        if pack:
            button.pack(
                side=side or "top",
                padx=5 if side else 22,
                pady=8,
                anchor="w" if not side else "center",
            )
        return button

    def entry(self, label, password=False):
        self.text(label)
        entry = ctk.CTkEntry(self.body, width=340, height=38, show="•" if password else "")
        entry.pack(anchor="w", padx=22, pady=(0, 8))
        entry.bind("<FocusIn>", lambda event: scroll_into_view(entry), add="+")
        return entry

    @property
    def active_db(self):
        return self.guest.db_path if self.guest else self.db_path

    def close_application(self):
        if self.user:
            self.practice.pause(self.user["id"])
        if self.guest:
            self.guest.close()
        release_window(self)
        close_logging()
