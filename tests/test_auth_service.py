"""Tests for local registration and login logic."""

import pytest

from src.db.database import init_db
from src.services.auth_service import AuthService


def test_register_user_saves_hashed_password_and_preferences(tmp_path) -> None:
    db_path = tmp_path / "auth.db"
    init_db(db_path=db_path, seed_words=False)
    service = AuthService(db_path=db_path)

    user = service.register_user(
        username="LearnerOne",
        password="secret123",
        target_language="english",
        level="beginner",
        preferred_categories=["noun", "verb"],
    )
    stored_user = service.user_repository.get_by_username("learnerone")

    assert user["username"] == "learnerone"
    assert "password_hash" not in user
    assert stored_user is not None
    assert stored_user["password_hash"] != "secret123"
    assert user["preferred_categories"] == ["noun", "verb"]
    assert user["daily_goal_words"] == 5
    assert user["daily_goal_sessions"] == 1


def test_register_user_enforces_minimum_password_length(tmp_path) -> None:
    db_path = tmp_path / "short_password.db"
    init_db(db_path=db_path, seed_words=False)
    service = AuthService(db_path=db_path)

    with pytest.raises(ValueError, match="at least 8 characters"):
        service.register_user(
            username="shortpass",
            password="short7",
            target_language="english",
            level="beginner",
        )


def test_register_user_prevents_duplicate_username(tmp_path) -> None:
    db_path = tmp_path / "duplicate_user.db"
    init_db(db_path=db_path, seed_words=False)
    service = AuthService(db_path=db_path)

    service.register_user(
        username="duplicate",
        password="secret123",
        target_language="english",
        level="beginner",
    )

    with pytest.raises(ValueError):
        service.register_user(
            username="duplicate",
            password="another123",
            target_language="english",
            level="beginner",
        )


def test_authenticate_user_verifies_password(tmp_path) -> None:
    db_path = tmp_path / "login.db"
    init_db(db_path=db_path, seed_words=False)
    service = AuthService(db_path=db_path)

    service.register_user(
        username="player",
        password="secret123",
        target_language="english",
        level="intermediate",
    )

    authenticated_user = service.authenticate_user("player", "secret123")
    failed_login = service.authenticate_user("player", "wrong-password")

    assert authenticated_user is not None
    assert failed_login is None


def test_effective_level_prefers_calibrated_level_when_available(tmp_path) -> None:
    db_path = tmp_path / "effective_level.db"
    init_db(db_path=db_path, seed_words=False)
    service = AuthService(db_path=db_path)

    user = service.register_user(
        username="calibratedplayer",
        password="secret123",
        target_language="english",
        level="beginner",
    )
    updated_user = service.save_assessment_result(
        user_id=user["id"],
        calibrated_level="advanced",
    )

    assert updated_user["self_declared_level"] == "beginner"
    assert updated_user["calibrated_level"] == "advanced"
    assert updated_user["effective_level"] == "advanced"
    assert updated_user["assessment_completed"] is True
