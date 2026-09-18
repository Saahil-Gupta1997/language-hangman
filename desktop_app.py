"""Desktop launcher that shows the CustomTkinter login before Streamlit."""

from __future__ import annotations

import subprocess
import sys

from src.db.database import init_db
from src.services.auth_service import AuthService
from src.services.desktop_login_handoff import write_desktop_login_handoff
from src.ui.login_page import LoginPage
from src.utils.config import PROJECT_ROOT


class DesktopLoginController:
    """Wire the provided CustomTkinter login page into the Streamlit app."""

    def __init__(self) -> None:
        self.database_path = init_db()
        self.auth_service = AuthService(db_path=self.database_path)
        self.login_page = LoginPage(
            on_sign_in=self.sign_in,
            on_create_account=self.show_create_account_note,
            on_guest=self.show_guest_note,
        )

    def run(self) -> None:
        self.login_page.mainloop()

    def sign_in(self, username: str, password: str, remember_me: bool) -> None:
        user = self.auth_service.authenticate_user(username=username, password=password)
        if user is None:
            self.login_page.show_error("Login Failed", "Invalid username or password.")
            return

        write_desktop_login_handoff(user_id=int(user["id"]), remember_me=remember_me)
        self.launch_streamlit_app()
        self.login_page.destroy()

    def show_create_account_note(self) -> None:
        # TODO: Add a CustomTkinter registration screen if desktop-only signup is required.
        self.login_page.show_info(
            "Create Account",
            "Create account is available in the Streamlit app for now.",
        )

    def show_guest_note(self) -> None:
        self.login_page.show_info(
            "Demo Game",
            "Guest/demo play is not available in this local beta yet.",
        )

    def launch_streamlit_app(self) -> None:
        subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", str(PROJECT_ROOT / "app.py")],
            cwd=PROJECT_ROOT,
        )


def main() -> None:
    DesktopLoginController().run()


if __name__ == "__main__":
    main()
