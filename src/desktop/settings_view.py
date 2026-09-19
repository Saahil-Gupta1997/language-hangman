"""Native desktop app: profiles, durable practice, reports and local recovery."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from tkinter import filedialog, messagebox

import customtkinter as ctk

from src import __version__
from src.services.curated_content import seed_curated
from src.services.desktop_storage import (
    backup_database,
    delete_profile,
    export_diagnostics,
    export_profile,
    restore_database,
)

BLUE = "#155E75"


class SettingsView:
    def show_settings(self):
        self.clear("Settings")
        self.heading("Settings and recovery")
        self.text("Text size (Ctrl + plus / minus)")
        scale = ctk.CTkOptionMenu(self.body, values=["Standard", "Large"], command=self.set_scale)
        scale.set(self.scale)
        scale.pack(anchor="w", padx=22, pady=8)
        self.text(
            "Backups contain all local profiles and password hashes. Keep them private. "
            "The most recent seven daily backups are kept automatically."
        )
        if not self.guest:
            self.button(self.body, "Create full backup", self.backup)
            self.button(self.body, "Restore full backup", self.restore)
            self.button(self.body, "Export my progress", self.export_user)
            self.password_delete = self.entry(
                "Re-enter password to delete this profile", password=True
            )
            self.button(self.body, "Delete my profile", self.delete_user)
        else:
            self.text(
                "Guest profiles are temporary. Create a local profile for persistent progress."
            )
        self.button(self.body, "Export diagnostics", self.diagnostics)
        self.text(
            "Diagnostics include only application/schema versions and database health. "
            "They exclude profile names, passwords, gameplay and local file paths."
        )

    def set_scale(self, value):
        self.scale = value
        ctk.set_widget_scaling(1.15 if value == "Large" else 1.0)
        path = self.data_dir / "settings.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"text_size": value}), encoding="utf-8")
        temporary.replace(path)

    def save_path(self, extension, title):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        return filedialog.asksaveasfilename(
            parent=self,
            title=title,
            defaultextension=extension,
            initialfile=f"hangman-{stamp}{extension}",
            filetypes=[("Hangman export", "*" + extension)],
        )

    def backup(self):
        path = self.save_path(".sqlite", "Save full backup")
        if path:
            backup_database(self.db_path, path)
            messagebox.showinfo(
                "Backup saved", "All local profiles and progress were backed up.", parent=self
            )

    def restore(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Choose a Hangman database backup",
            filetypes=[("SQLite database", "*.sqlite *.db *.sqlite3")],
        )
        if path and messagebox.askyesno(
            "Replace all local profiles?",
            "This replaces ALL local "
            "profiles and progress with the selected backup. A safety "
            "backup is made first. You will be signed out.",
            parent=self,
        ):
            if self.user:
                self.practice.pause(self.user["id"])
            restore_database(self.db_path, path)
            seed_curated(self.db_path)
            self.logout()
            messagebox.showinfo(
                "Restored",
                "Backup restored. Sign in using a profile from "
                "that backup. A safety copy of the previous data was retained.",
                parent=self,
            )

    def export_user(self):
        path = self.save_path(".json", "Export this profile's progress")
        if path:
            export_profile(self.db_path, self.user["id"], path)
            messagebox.showinfo(
                "Export saved",
                "Readable progress exported without credentials. "
                "Use a full backup for restoration.",
                parent=self,
            )

    def diagnostics(self):
        path = self.save_path(".zip", "Export privacy-safe diagnostics")
        if path:
            export_diagnostics(self.active_db, path)
            messagebox.showinfo(
                "Diagnostics saved", "The diagnostic archive is ready.", parent=self
            )

    def delete_user(self):
        if not self.auth.authenticate_user(self.user["username"], self.password_delete.get()):
            raise ValueError("Re-enter your current password to delete this profile.")
        if messagebox.askyesno(
            "Permanently delete profile?",
            "This deletes your profile and its "
            "progress from the active database. Other profiles are unchanged. "
            "Existing backups still contain older copies.",
            parent=self,
        ):
            delete_profile(self.db_path, self.user["id"])
            self.user = None
            self.show_login()

    def show_help(self):
        self.clear("Help")
        self.heading("Help and about", f"Language Hangman {__version__}")
        self.text(
            "1. Create a local profile or try temporary guest practice.\n"
            "2. Choose a travel situation, game difficulty and session length.\n"
            "3. Enter a single letter; press Enter to submit. Repeated guesses cost no lives.\n"
            "4. Read the example and usage note after each round.\n"
            "5. Close at any time. Profile sessions resume with saved guesses and clues."
        )
        self.text(
            "Keyboard: Tab / Shift+Tab move between controls. Enter submits a guess. "
            "Escape returns home. Ctrl plus/minus changes text size. "
            "Letters with accents are accepted as single Unicode characters."
        )
        self.text(
            "English starter scope: 30 introductory words across Restaurant, Airport and "
            "Hotel. Difficulty describes the game, not your proficiency. Other languages "
            "from the older prototype are not offered in this desktop release."
        )
        self.text(
            "Privacy: no account server, telemetry or cloud sync. Local passwords protect "
            "in-app access; the database is not encrypted against someone with access to "
            "your computer. There is no email password reset."
        )
        self.text(
            "Recovery: Settings → full backup/restore. To import the older app, select its "
            "data/app.db using Restore on the sign-in screen. Never import an untrusted file. "
            "Older results remain in reports; new practice uses the starter pack."
        )
        self.text(
            "Updates: close Hangman, create a backup, then run the newer installer. "
            "Program updates and uninstall preserve your local data. To reset everything, "
            "close the app and remove its data folder after making a backup."
        )
        self.text(f"Data folder: {self.data_dir}")
        self.text(
            "If saving fails, check disk space and permissions, then reopen Practice and "
            "retry. If a backup is rejected, your current data stays unchanged. "
            "Send diagnostics, version, OS, reproduction steps and expected/actual results "
            "when reporting a bug. Do not send your full database publicly."
        )
        self.text(
            "Release candidate: independent educator review, external learner acceptance "
            "and Windows installer validation are required before a final 1.0 release."
        )
