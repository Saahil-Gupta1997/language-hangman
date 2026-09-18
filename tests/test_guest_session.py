"""Guest profiles cannot read or overwrite another browser's progress."""

from src.db.database import create_connection
from src.services.guest_service import GuestSession


def test_guest_storage_is_isolated_and_disposable():
    first, second = GuestSession(), GuestSession()
    try:
        assert first.db_path != second.db_path
        assert first.user["assessment_completed"]
        with create_connection(first.db_path) as connection:
            assert connection.execute("SELECT COUNT(*) FROM words").fetchone()[0] >= 300
            connection.execute("UPDATE users SET username = 'changed'")
        with create_connection(second.db_path) as connection:
            assert connection.execute("SELECT username FROM users").fetchone()[0] == "guest"
    finally:
        first.close()
        second.close()
    assert not first.db_path.exists()
