"""Tests for Step 7 hygiene, auth safety, and selection-trust behavior."""

from __future__ import annotations

import random

import pytest

from src.db.database import init_db
from src.db.repository import GameSessionRepository, ReviewQueueRepository
from src.models.learning_session import LearningSession
from src.services.auth_service import AuthService
from src.services.game_service import GameService
from src.services.word_service import WordService


def test_review_only_build_next_round_stays_strict(tmp_path) -> None:
    db_path = tmp_path / "review_only_strict.db"
    init_db(db_path=db_path, seed_words=True)

    auth_service = AuthService(db_path=db_path)
    game_service = GameService(db_path=db_path)
    review_repository = ReviewQueueRepository(db_path=db_path)
    word_service = WordService(db_path=db_path)
    user = auth_service.register_user(
        username="strictreview",
        password="secret123",
        target_language="english",
        level="beginner",
        preferred_categories=["verb"],
    )

    review_word = word_service.get_words("english", category="verb", difficulty="beginner")[0]
    review_repository.upsert_review_item(
        user_id=user["id"],
        word_id=review_word["id"],
        language="english",
        category="verb",
        priority_score=1.0,
        review_due_at="2026-04-20T00:00:00+00:00",
        last_reviewed_at="2026-04-19T00:00:00+00:00",
        last_result="lost",
        last_accuracy=0.2,
        is_active=True,
    )

    learning_session = LearningSession(
        user_id=user["id"],
        language="english",
        practice_mode="review",
        planned_rounds=2,
        selected_categories=["verb"],
        difficulty_filter=["beginner"],
        review_policy="review_only",
        selected_category="verb",
        practiced_word_ids=[review_word["id"]],
    )

    with pytest.raises(ValueError, match="review words remain"):
        game_service.build_next_round(
            user=user,
            learning_session=learning_session,
            rng=random.Random(7),
        )


def test_new_only_build_next_round_warns_before_fallback(tmp_path) -> None:
    db_path = tmp_path / "new_only_warning.db"
    init_db(db_path=db_path, seed_words=True)

    auth_service = AuthService(db_path=db_path)
    game_service = GameService(db_path=db_path)
    session_repository = GameSessionRepository(db_path=db_path)
    word_service = WordService(db_path=db_path)
    user = auth_service.register_user(
        username="strictnew",
        password="secret123",
        target_language="english",
        level="beginner",
        preferred_categories=["noun"],
    )

    seen_words = word_service.get_words("english", category="noun", difficulty="beginner")
    for index, seen_word in enumerate(seen_words):
        session_repository.create_session(
            user_id=user["id"],
            word_id=seen_word["id"],
            language="english",
            level="beginner",
            category="noun",
            result="won",
            attempts_used=4,
            max_attempts=6,
            letters_correct=4,
            letters_wrong=0,
            guessed_letters="a,p,l,e",
            time_taken_seconds=8.0,
            started_at=f"2026-04-29T00:{index:02d}:00+00:00",
            completed_at=f"2026-04-29T00:{index:02d}:08+00:00",
            played_at=f"2026-04-29T00:{index:02d}:08+00:00",
            practice_mode="category",
        )

    learning_session = LearningSession(
        user_id=user["id"],
        language="english",
        practice_mode="category",
        planned_rounds=2,
        selected_categories=["noun"],
        difficulty_filter=["beginner"],
        review_policy="new_only",
        selected_category="noun",
    )
    round_state = game_service.build_next_round(
        user=user,
        learning_session=learning_session,
        rng=random.Random(11),
    )

    assert round_state.word_id in {word["id"] for word in seen_words}
    assert round_state.selection_warning is not None
    assert "fell back" in round_state.selection_warning.lower()
