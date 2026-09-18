"""Review queue model used for lightweight spaced practice."""

from dataclasses import dataclass


@dataclass(slots=True)
class ReviewItem:
    """Represents one stored word review item."""

    id: int | None
    user_id: int
    word_id: int
    language: str
    category: str
    priority_score: float
    review_due_at: str
    review_count: int
    last_reviewed_at: str | None
    last_result: str | None
    last_accuracy: float
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None
