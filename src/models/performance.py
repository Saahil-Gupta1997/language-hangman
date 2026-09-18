"""Performance summary model definitions."""

from dataclasses import dataclass


@dataclass(slots=True)
class PerformanceSummary:
    """Stores aggregate player performance for a language and category."""

    id: int | None
    user_id: int
    language: str
    category: str
    total_games: int = 0
    wins: int = 0
    losses: int = 0
    accuracy: float = 0.0
    avg_attempts: float = 0.0
    mastery_score: float = 0.0
    last_played_at: str | None = None
    updated_at: str | None = None
