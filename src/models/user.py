"""User model definitions."""

from dataclasses import dataclass


@dataclass(slots=True)
class User:
    """Represents a player profile stored in the local database."""

    id: int | None
    username: str
    email: str | None
    target_language: str
    self_declared_level: str
    calibrated_level: str | None
    effective_level: str
    assessment_completed: bool
    preferred_categories: list[str]
    last_builder_settings: dict[str, object]
    created_at: str | None = None
    updated_at: str | None = None
