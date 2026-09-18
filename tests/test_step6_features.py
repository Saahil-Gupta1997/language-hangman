"""Tests for Step 6 guidance, history, mastery, and content behavior."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.db.database import init_db
from src.db.repository import GameSessionRepository, ReviewQueueRepository, WordProgressRepository
from src.models.learning_session import LearningSession
from src.services.auth_service import AuthService
from src.services.game_service import GameService
from src.services.report_service import ReportService
from src.services.word_service import WordService


def _win_round(game_service: GameService, round_state) -> None:
    """Solve a round by guessing each unique letter once."""
    for letter in sorted(round_state.unique_letters):
        if round_state.is_complete:
            break
        game_service.record_guess(round_state, letter)


def test_seeded_word_banks_include_french_language(tmp_path) -> None:
    db_path = tmp_path / "french_seed.db"
    init_db(db_path=db_path, seed_words=True)

    word_service = WordService(db_path=db_path)

    assert "french" in word_service.get_available_languages()
    assert len(word_service.get_words("french")) >= 12


def test_clean_wins_raise_mastery_score_and_space_reviews_farther(tmp_path) -> None:
    db_path = tmp_path / "mastery_spacing.db"
    init_db(db_path=db_path, seed_words=True)

    auth_service = AuthService(db_path=db_path)
    game_service = GameService(db_path=db_path)
    progress_repository = WordProgressRepository(db_path=db_path)
    review_repository = ReviewQueueRepository(db_path=db_path)
    word_service = WordService(db_path=db_path)
    user = auth_service.register_user(
        username="spacinguser",
        password="secret123",
        target_language="english",
        level="beginner",
        preferred_categories=["noun"],
    )

    word = word_service.get_words(
        "english",
        category="noun",
        difficulty="beginner",
        situation="restaurant",
    )[0]
    for _ in range(3):
        learning_session = LearningSession(
            user_id=user["id"],
            language="english",
            practice_mode="standard",
            planned_rounds=1,
            selected_categories=["noun"],
            difficulty_filter=["beginner"],
            situation="restaurant",
        )
        round_state = game_service.build_round(
            chosen_word=word,
            level="beginner",
            practice_mode="standard",
            situation="restaurant",
        )
        _win_round(game_service, round_state)
        game_service.finalize_round(
            user=user,
            round_state=round_state,
            learning_session=learning_session,
        )

    progress_row = progress_repository.get_item(user["id"], round_state.word_id)
    review_row = review_repository.get_item(user["id"], round_state.word_id)

    assert progress_row is not None
    assert review_row is not None
    assert progress_row["familiarity_status"] == "strong"
    assert float(progress_row["mastery_score"]) >= 75.0
    assert float(progress_row["priority_score"]) <= 0.25
    assert int(review_row["is_active"]) == 0

    review_gap = datetime.fromisoformat(str(review_row["review_due_at"])) - datetime.fromisoformat(
        str(review_row["last_reviewed_at"])
    )
    assert review_gap >= timedelta(days=14)


def test_report_builds_guided_plan_streaks_and_daily_activity(tmp_path) -> None:
    db_path = tmp_path / "step6_report.db"
    init_db(db_path=db_path, seed_words=True)

    auth_service = AuthService(db_path=db_path)
    report_service = ReportService(db_path=db_path)
    review_repository = ReviewQueueRepository(db_path=db_path)
    progress_repository = WordProgressRepository(db_path=db_path)
    session_repository = GameSessionRepository(db_path=db_path)
    word_service = WordService(db_path=db_path)
    user = auth_service.register_user(
        username="historyuser",
        password="secret123",
        target_language="english",
        level="intermediate",
        preferred_categories=["verb", "noun"],
    )

    noun_word = word_service.get_words("english", category="noun")[0]
    verb_word = word_service.get_words("english", category="verb")[0]
    now = datetime.now(timezone.utc).replace(microsecond=0)
    yesterday = now - timedelta(days=1)

    session_repository.create_session(
        user_id=user["id"],
        word_id=noun_word["id"],
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
        started_at=yesterday.isoformat(),
        completed_at=(yesterday + timedelta(seconds=8)).isoformat(),
        played_at=(yesterday + timedelta(seconds=8)).isoformat(),
        practice_mode="standard",
    )
    session_repository.create_session(
        user_id=user["id"],
        word_id=verb_word["id"],
        language="english",
        level="intermediate",
        category="verb",
        result="lost",
        attempts_used=6,
        max_attempts=6,
        letters_correct=1,
        letters_wrong=5,
        guessed_letters="a,b,c,d,e,f",
        time_taken_seconds=15.0,
        started_at=now.isoformat(),
        completed_at=(now + timedelta(seconds=15)).isoformat(),
        played_at=(now + timedelta(seconds=15)).isoformat(),
        practice_mode="weak_area",
    )
    review_repository.upsert_review_item(
        user_id=user["id"],
        word_id=verb_word["id"],
        language="english",
        category="verb",
        priority_score=1.0,
        review_due_at=(now - timedelta(hours=1)).isoformat(),
        last_reviewed_at=(now - timedelta(hours=2)).isoformat(),
        last_result="lost",
        last_accuracy=0.2,
        is_active=True,
    )
    progress_repository.upsert_progress(
        user_id=user["id"],
        word_id=noun_word["id"],
        language="english",
        familiarity_status="familiar",
        mastery_score=62.0,
        wins_delta=1,
        losses_delta=0,
        successful_streak=1,
        correct_letters_delta=4,
        wrong_letters_delta=0,
        last_accuracy=1.0,
        last_result="won",
        priority_score=0.22,
        last_played_at=(yesterday + timedelta(seconds=8)).isoformat(),
    )
    progress_repository.upsert_progress(
        user_id=user["id"],
        word_id=verb_word["id"],
        language="english",
        familiarity_status="learning",
        mastery_score=28.0,
        wins_delta=0,
        losses_delta=1,
        successful_streak=0,
        correct_letters_delta=1,
        wrong_letters_delta=5,
        last_accuracy=0.17,
        last_result="lost",
        priority_score=0.94,
        last_played_at=(now + timedelta(seconds=15)).isoformat(),
    )

    report_service.refresh_user_performance(user["id"])
    report = report_service.build_summary_report(user["id"], language="english")

    assert report["streaks"]["current_streak"] >= 2
    assert len(report["daily_activity"]) >= 2
    assert report["guided_study_plan"]
    assert report["category_progress"]
    assert "milestone_label" in report["category_progress"][0]

    joined_summaries = " ".join(plan["summary"] for plan in report["guided_study_plan"]).lower()
    assert "review-only session" in joined_summaries
    assert "custom 5-round session" in joined_summaries
    assert "builder_settings" in report["guided_study_plan"][0]
