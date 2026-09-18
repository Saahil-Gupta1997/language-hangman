"""Authentication helpers for local user account flows."""

from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
from pathlib import Path
from typing import Any

from src.db.repository import UserRepository
from src.utils.constants import (
    DEFAULT_DAILY_GOAL_SESSIONS,
    DEFAULT_DAILY_GOAL_WORDS,
    DEFAULT_LANGUAGE,
    DEFAULT_LEVEL,
    DEFAULT_PREFERRED_CATEGORIES,
    MIN_PASSWORD_LENGTH,
)
from src.utils.helpers import (
    deserialize_json_object,
    deserialize_string_list,
    serialize_json,
    serialize_string_list,
)


class AuthService:
    """Provides password hashing and local account operations."""

    algorithm = "pbkdf2_sha256"
    iterations = 390000

    def __init__(self, db_path: Path | None = None) -> None:
        self.user_repository = UserRepository(db_path=db_path)

    def hash_password(self, password: str) -> str:
        """Return a salted password hash that can be stored in SQLite."""
        salt = os.urandom(16).hex()
        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            self.iterations,
        ).hex()
        return f"{self.algorithm}${self.iterations}${salt}${password_hash}"

    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Compare a plain password against a stored PBKDF2 hash."""
        try:
            algorithm, iterations, salt, password_hash = stored_hash.split("$", maxsplit=3)
        except ValueError:
            return False

        if algorithm != self.algorithm:
            return False

        candidate_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            int(iterations),
        ).hex()
        return hmac.compare_digest(candidate_hash, password_hash)

    def register_user(
        self,
        username: str,
        password: str,
        target_language: str = DEFAULT_LANGUAGE,
        level: str = DEFAULT_LEVEL,
        preferred_categories: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new local user account and return the stored profile."""
        normalized_username = username.strip().lower()
        normalized_password = password
        categories = preferred_categories or list(DEFAULT_PREFERRED_CATEGORIES)

        if not normalized_username:
            raise ValueError("Username is required.")

        if len(normalized_password) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")

        if self.user_repository.get_by_username(normalized_username):
            raise ValueError("That username is already taken.")

        password_hash = self.hash_password(normalized_password)
        synthetic_email = self._build_local_email(normalized_username)

        try:
            user_id = self.user_repository.create_user(
                username=normalized_username,
                email=synthetic_email,
                password_hash=password_hash,
                target_language=target_language.lower(),
                level=level.lower(),
                preferred_categories=serialize_string_list(categories),
                last_builder_settings=serialize_json({}),
                daily_goal_words=DEFAULT_DAILY_GOAL_WORDS,
                daily_goal_sessions=DEFAULT_DAILY_GOAL_SESSIONS,
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("Unable to create that account.") from error

        return self.get_user_by_id(user_id)

    def authenticate_user(self, username: str, password: str) -> dict[str, Any] | None:
        """Return a user profile if the credentials are valid."""
        user_row = self.user_repository.get_by_username(username.strip().lower())
        if not user_row:
            return None

        if not self.verify_password(password, user_row["password_hash"]):
            return None

        return self._row_to_user_record(user_row)

    def get_user_by_id(self, user_id: int) -> dict[str, Any]:
        """Return a user profile by id."""
        user_row = self.user_repository.get_by_id(user_id)
        if not user_row:
            raise ValueError("User not found.")
        return self._row_to_user_record(user_row)

    def update_preferences(
        self,
        user_id: int,
        target_language: str,
        level: str,
        preferred_categories: list[str],
    ) -> dict[str, Any]:
        """Update language, self-declared level, and category preferences for a user."""
        categories = preferred_categories or list(DEFAULT_PREFERRED_CATEGORIES)
        self.user_repository.update_preferences(
            user_id=user_id,
            target_language=target_language.lower(),
            level=level.lower(),
            preferred_categories=serialize_string_list(categories),
        )
        return self.get_user_by_id(user_id)

    def save_assessment_result(self, user_id: int, calibrated_level: str) -> dict[str, Any]:
        """Persist the calibrated level produced by the assessment flow."""
        self.user_repository.update_assessment_result(
            user_id=user_id,
            calibrated_level=calibrated_level.lower(),
            assessment_completed=True,
        )
        return self.get_user_by_id(user_id)

    def save_last_builder_settings(
        self,
        user_id: int,
        builder_settings: dict[str, Any],
    ) -> dict[str, Any]:
        """Persist the most recent custom builder settings for a user."""
        self.user_repository.update_last_builder_settings(
            user_id=user_id,
            last_builder_settings=serialize_json(builder_settings),
        )
        return self.get_user_by_id(user_id)

    def update_daily_goals(
        self,
        user_id: int,
        daily_goal_words: int,
        daily_goal_sessions: int,
    ) -> dict[str, Any]:
        """Update the user's simple daily practice targets."""
        if daily_goal_words < 1:
            raise ValueError("Daily word goal must be at least 1.")
        if daily_goal_sessions < 1:
            raise ValueError("Daily session goal must be at least 1.")

        self.user_repository.update_daily_goals(
            user_id=user_id,
            daily_goal_words=daily_goal_words,
            daily_goal_sessions=daily_goal_sessions,
        )
        return self.get_user_by_id(user_id)

    def _row_to_user_record(self, row: sqlite3.Row) -> dict[str, Any]:
        """Convert a SQLite row into a UI-friendly user record."""
        self_declared_level = row["level"]
        calibrated_level = row["calibrated_level"]
        effective_level = calibrated_level or self_declared_level
        return {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "target_language": row["target_language"],
            "level": self_declared_level,
            "self_declared_level": self_declared_level,
            "calibrated_level": calibrated_level,
            "assessment_completed": bool(row["assessment_completed"]),
            "effective_level": effective_level,
            "preferred_categories": deserialize_string_list(
                row["preferred_categories"],
                default=DEFAULT_PREFERRED_CATEGORIES,
            ),
            "last_builder_settings": deserialize_json_object(
                row["last_builder_settings"],
                default={},
            ),
            "daily_goal_words": int(row["daily_goal_words"] or DEFAULT_DAILY_GOAL_WORDS),
            "daily_goal_sessions": int(row["daily_goal_sessions"] or DEFAULT_DAILY_GOAL_SESSIONS),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _build_local_email(self, username: str) -> str:
        """Build a predictable local-only email placeholder for SQLite uniqueness."""
        return f"{username}@local.languagehangman"
