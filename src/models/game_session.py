"""Game session model definitions."""

from dataclasses import dataclass


@dataclass(slots=True)
class GameSession:
    """Tracks a single Hangman play session for a user."""

    id: int | None
    user_id: int
    word_id: int
    language: str
    level: str
    category: str
    result: str
    attempts_used: int
    max_attempts: int
    letters_correct: int
    letters_wrong: int
    guessed_letters: str = ""
    time_taken_seconds: float | None = None
    played_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
