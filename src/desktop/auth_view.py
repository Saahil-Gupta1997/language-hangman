"""Native desktop app: profiles, durable practice, reports and local recovery."""

from __future__ import annotations

from src.services.curated_content import seed_curated
from src.services.guest_service import GuestSession
from src.services.practice_service import PracticeService

BLUE = "#155E75"


class AuthView:
    def show_login(self, register=False):
        self.clear("Login")
        self.heading(
            "Create a local profile" if register else "Welcome back",
            "Practice English for restaurants, airports and hotels. "
            "Profiles and passwords are local to this computer; there is no cloud account.",
        )
        self.username_entry = self.entry("Profile name")
        self.password_entry = self.entry("Password (at least 8 characters)", password=True)
        if register:
            self.confirm_entry = self.entry("Confirm password", password=True)
        self.text(
            "No email recovery is available. Keep a backup of your progress. "
            "A forgotten password cannot be recovered by email."
        )
        self.button(
            self.body,
            "Create profile" if register else "Sign in",
            lambda: self.authenticate(register),
            variant="primary",
            width=220,
        )
        self.button(
            self.body,
            "I already have a profile" if register else "Create a profile",
            lambda: self.show_login(not register),
        )
        self.button(self.body, "Try guest practice", self.start_guest, variant="quiet")
        self.bind("<Return>", lambda event: self.authenticate(register))
        self.username_entry.focus_set()

    def authenticate(self, register=False):
        name, password = self.username_entry.get(), self.password_entry.get()
        if register:
            if password != self.confirm_entry.get():
                raise ValueError("The passwords do not match.")
            user = self.auth.register_user(name, password, target_language="english")
        else:
            user = self.auth.authenticate_user(name, password)
            if not user:
                raise ValueError("The profile name or password is incorrect.")
        self.user = user
        self.show_home()

    def start_guest(self):
        self.guest = GuestSession()
        seed_curated(self.guest.db_path)
        self.user = self.guest.user
        self.practice = PracticeService(self.guest.db_path, curated=True)
        self.show_home()

    def logout(self):
        if self.user:
            self.practice.pause(self.user["id"])
        if self.guest:
            self.guest.close()
            self.guest = None
        self.user = None
        self.payload = None
        self.practice = PracticeService(self.db_path, curated=True)
        self.show_login()
