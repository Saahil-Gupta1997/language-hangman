"""Learning session model for multi-round practice."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.utils.helpers import utc_now_iso


@dataclass(slots=True)
class LearningSession:
    """Represents one active or completed multi-round practice session."""

    user_id: int
    language: str
    practice_mode: str
    planned_rounds: int
    selected_categories: list[str] = field(default_factory=list)
    difficulty_filter: list[str] = field(default_factory=list)
    review_policy: str = "prefer_review"
    show_hint_immediately: bool = True
    game_mode: str = "easy"
    situation: str | None = None
    selected_category: str | None = None
    session_id: int | None = None
    completed_rounds: int = 0
    wins: int = 0
    losses: int = 0
    total_correct_letters: int = 0
    total_wrong_letters: int = 0
    round_ids: list[int] = field(default_factory=list)
    words_practiced: list[str] = field(default_factory=list)
    practiced_word_ids: list[int] = field(default_factory=list)
    categories_practiced: list[str] = field(default_factory=list)
    round_reviews: list[dict[str, object]] = field(default_factory=list)
    status: str = "active"
    started_at: str = field(default_factory=utc_now_iso)
    completed_at: str | None = None
    recommendation: str | None = None

    @property
    def current_round_number(self) -> int:
        """Return the 1-based round number currently being played."""
        return min(self.completed_rounds + 1, self.planned_rounds)

    @property
    def remaining_rounds(self) -> int:
        """Return how many rounds are still left in the session."""
        return max(self.planned_rounds - self.completed_rounds, 0)

    @property
    def session_accuracy(self) -> float:
        """Return overall letter accuracy for the session."""
        total_guesses = self.total_correct_letters + self.total_wrong_letters
        if total_guesses == 0:
            return 0.0
        return round((self.total_correct_letters / total_guesses) * 100, 2)

    @property
    def is_complete(self) -> bool:
        """Return whether the planned session is complete."""
        return self.status == "completed" or self.completed_rounds >= self.planned_rounds
