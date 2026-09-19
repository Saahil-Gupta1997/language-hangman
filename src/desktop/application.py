"""Native desktop app: profiles, durable practice, reports and local recovery."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from src import __version__
from src.db.database import init_db
from src.desktop.auth_view import AuthView
from src.desktop.practice_view import PracticeView
from src.desktop.reports_view import ReportsView
from src.desktop.runtime import configure_logging
from src.desktop.settings_view import SettingsView
from src.services.auth_service import AuthService
from src.services.curated_content import seed_curated
from src.services.desktop_storage import (
    backup_database,
)
from src.services.practice_service import PracticeService
from src.utils.config import DATA_DIR, DATABASE_PATH

BLUE = "#155E75"


class HangmanDesktop(AuthView, PracticeView, ReportsView, SettingsView, ctk.CTk):
    def __init__(self, db_path=DATABASE_PATH, data_dir=DATA_DIR):
        super().__init__()
        self.title(f"Language Hangman · {__version__}")
        self.geometry("1060x760")
        self.minsize(820, 640)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger = configure_logging(self.data_dir)
        self.db_path = init_db(db_path, seed_words=False)
        seed_curated(self.db_path)
        self.auth = AuthService(self.db_path)
        self.practice = PracticeService(self.db_path, curated=True)
        self.user = None
        self.guest = None
        self.payload = None
        self.page = ""
        self.protocol("WM_DELETE_WINDOW", self.close_application)
        self.bind("<Escape>", lambda event: self.show_home() if self.user else None)
        self.bind("<Control-plus>", lambda event: self.set_scale("Large"))
        self.bind("<Control-minus>", lambda event: self.set_scale("Standard"))
        self.scale = "Standard"
        settings_path = self.data_dir / "settings.json"
        try:
            self.scale = json.loads(settings_path.read_text())["text_size"]
        except (OSError, ValueError, KeyError, TypeError):
            pass
        ctk.set_appearance_mode("light")
        ctk.set_widget_scaling(1.15 if self.scale == "Large" else 1.0)
        self.header = ctk.CTkFrame(self, corner_radius=0, fg_color=BLUE)
        self.header.pack(fill="x")
        ctk.CTkLabel(
            self.header, text="Language Hangman", text_color="white", font=("Arial", 24, "bold")
        ).pack(side="left", padx=24, pady=18)
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
        self.automatic_backup()
        self.show_login()

    def report_callback_exception(self, exception, value, traceback):
        # Log event type only; exception messages can contain paths or user input.
        self.logger.error("Callback failed: %s", exception.__name__)
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
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        destination = self.data_dir / "backups" / f"daily-{today}.sqlite"
        if not destination.exists():
            backup_database(self.db_path, destination)
        daily = sorted((self.data_dir / "backups").glob("daily-*.sqlite"))
        for old in daily[:-7]:
            old.unlink()

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
                control = self.button(self.navigation, label, command, width=130)
                control.pack_forget()
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
            wraplength=600,
            font=("Arial", 15, "bold" if bold else "normal"),
            text_color="#172B4D",
        )
        label.pack(fill="x", padx=22, pady=7)
        return label

    def button(self, parent, label, command, side=None, width=180):
        button = ctk.CTkButton(
            parent,
            text=label,
            command=command,
            width=width,
            height=38,
            fg_color=BLUE,
            hover_color="#0E4657",
            font=("Arial", 14),
        )
        # CTk's canvas must be explicitly focusable for keyboard activation.
        button._canvas.configure(takefocus=1)

        def activate(event):
            button.invoke()
            return "break"

        button.bind("<Return>", activate)
        button.bind("<space>", activate)
        button.bind(
            "<FocusIn>", lambda event: button.configure(border_width=3, border_color="#F59E0B")
        )
        button.bind("<FocusOut>", lambda event: button.configure(border_width=0))
        button.pack(
            side=side or "top", padx=5 if side else 22, pady=8, anchor="w" if not side else "center"
        )
        return button

    def entry(self, label, password=False):
        self.text(label)
        entry = ctk.CTkEntry(self.body, width=340, height=38, show="•" if password else "")
        entry.pack(anchor="w", padx=22, pady=(0, 8))
        return entry

    @property
    def active_db(self):
        return self.guest.db_path if self.guest else self.db_path

    def close_application(self):
        if self.user:
            self.practice.pause(self.user["id"])
        if self.guest:
            self.guest.close()
        self.destroy()
