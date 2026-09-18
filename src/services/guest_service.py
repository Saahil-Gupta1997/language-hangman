"""Private, disposable storage for a browser's guest practice session."""

from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory

from src.db.database import init_db
from src.services.auth_service import AuthService


class GuestSession:
    """Keep guest progress separate from all registered learners."""

    def __init__(self) -> None:
        self.storage = TemporaryDirectory(prefix="language-hangman-guest-")
        self.db_path = init_db(db_path=Path(self.storage.name) / "guest.db")
        auth = AuthService(db_path=self.db_path)
        user = auth.register_user("guest", token_urlsafe(32))
        self.user = auth.save_assessment_result(int(user["id"]), "beginner")

    def close(self) -> None:
        self.storage.cleanup()
