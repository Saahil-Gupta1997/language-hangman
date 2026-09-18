"""Tests for Step 4 practice modes, sessions, and review flow."""

from src.db.database import init_db
from src.db.repository import LearningSessionRepository, ReviewQueueRepository
from src.services.adaptation_service import AdaptationService
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


def _lose_round(game_service: GameService, round_state) -> None:
    """Lose a round by submitting incorrect letters until attempts run out."""
    wrong_letters = [
        letter for letter in "bcdfghjklmnpqrstvwxyz" if letter not in round_state.unique_letters
    ]
    for letter in wrong_letters[: round_state.max_attempts]:
        if round_state.is_complete:
            break
        game_service.record_guess(round_state, letter)


def test_adaptation_review_mode_prioritizes_due_review_words(tmp_path) -> None:
    db_path = tmp_path / "review_mode_adaptation.db"
    init_db(db_path=db_path, seed_words=True)

    auth_service = AuthService(db_path=db_path)
    word_service = WordService(db_path=db_path)
    review_repository = ReviewQueueRepository(db_path=db_path)
    user = auth_service.register_user(
        username="reviewfocus",
        password="secret123",
        target_language="english",
        level="beginner",
        preferred_categories=["noun", "verb"],
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

    recommendation = AdaptationService(db_path=db_path).build_recommendation(
        user,
        practice_mode="review",
    )

    assert recommendation["candidate_word_ids"] == [review_word["id"]]
    assert recommendation["category_order"][0] == "verb"


def test_game_service_advances_multi_round_session_and_persists_progress(tmp_path) -> None:
    db_path = tmp_path / "session_progress.db"
    init_db(db_path=db_path, seed_words=True)

    auth_service = AuthService(db_path=db_path)
    game_service = GameService(db_path=db_path)
    learning_session_repository = LearningSessionRepository(db_path=db_path)
    user = auth_service.register_user(
        username="sessionplayer",
        password="secret123",
        target_language="english",
        level="beginner",
        preferred_categories=["noun", "verb"],
    )

    learning_session, round_state = game_service.start_learning_session(
        user=user,
        practice_mode="standard",
        planned_rounds=3,
    )
    _win_round(game_service, round_state)

    outcome = game_service.finalize_round(
        user=user,
        round_state=round_state,
        learning_session=learning_session,
    )
    stored_session = learning_session_repository.get_by_id(int(learning_session.session_id or 0))

    assert outcome["session_complete"] is False
    assert outcome["next_round"] is not None
    assert outcome["learning_session"].completed_rounds == 1
    assert stored_session is not None
    assert stored_session["completed_rounds"] == 1
    assert stored_session["wins"] == 1
    assert stored_session["status"] == "active"


def test_failed_round_is_added_to_active_review_queue(tmp_path) -> None:
    db_path = tmp_path / "review_queue_failed.db"
    init_db(db_path=db_path, seed_words=True)

    auth_service = AuthService(db_path=db_path)
    game_service = GameService(db_path=db_path)
    review_repository = ReviewQueueRepository(db_path=db_path)
    user = auth_service.register_user(
        username="reviewloss",
        password="secret123",
        target_language="english",
        level="beginner",
        preferred_categories=["noun"],
    )

    learning_session, round_state = game_service.start_learning_session(
        user=user,
        practice_mode="standard",
        planned_rounds=1,
        selected_category="noun",
    )
    _lose_round(game_service, round_state)
    outcome = game_service.finalize_round(
        user=user,
        round_state=round_state,
        learning_session=learning_session,
    )
    review_item = review_repository.get_item(user["id"], round_state.word_id)

    assert outcome["session_complete"] is True
    assert review_item is not None
    assert review_item["is_active"] == 1
    assert float(review_item["priority_score"]) == 1.0
    assert review_item["last_result"] == "lost"


def test_easy_win_is_deprioritized_in_review_queue(tmp_path) -> None:
    db_path = tmp_path / "review_queue_easy_win.db"
    init_db(db_path=db_path, seed_words=True)

    auth_service = AuthService(db_path=db_path)
    game_service = GameService(db_path=db_path)
    review_repository = ReviewQueueRepository(db_path=db_path)
    user = auth_service.register_user(
        username="easywinner",
        password="secret123",
        target_language="english",
        level="beginner",
        preferred_categories=["noun"],
    )

    learning_session, round_state = game_service.start_learning_session(
        user=user,
        practice_mode="standard",
        planned_rounds=1,
        selected_category="noun",
    )
    _win_round(game_service, round_state)
    game_service.finalize_round(
        user=user,
        round_state=round_state,
        learning_session=learning_session,
    )
    review_item = review_repository.get_item(user["id"], round_state.word_id)

    assert review_item is not None
    assert review_item["is_active"] == 1
    assert 0.25 <= float(review_item["priority_score"]) <= 0.4


def test_review_mode_session_uses_due_review_word_first(tmp_path) -> None:
    db_path = tmp_path / "review_session_mode.db"
    init_db(db_path=db_path, seed_words=True)

    auth_service = AuthService(db_path=db_path)
    word_service = WordService(db_path=db_path)
    review_repository = ReviewQueueRepository(db_path=db_path)
    game_service = GameService(db_path=db_path)
    user = auth_service.register_user(
        username="reviewsession",
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
        last_accuracy=0.1,
        is_active=True,
    )

    _, first_round = game_service.start_learning_session(
        user=user,
        practice_mode="review",
        planned_rounds=3,
    )

    assert first_round.word_id == review_word["id"]
    assert first_round.practice_mode == "review"


def test_report_summary_includes_learning_sessions_review_queue_and_history(tmp_path) -> None:
    db_path = tmp_path / "step4_report.db"
    init_db(db_path=db_path, seed_words=True)

    auth_service = AuthService(db_path=db_path)
    game_service = GameService(db_path=db_path)
    report_service = ReportService(db_path=db_path)
    review_repository = ReviewQueueRepository(db_path=db_path)
    user = auth_service.register_user(
        username="historyplayer",
        password="secret123",
        target_language="english",
        level="beginner",
        preferred_categories=["noun", "verb"],
    )

    learning_session, round_state = game_service.start_learning_session(
        user=user,
        practice_mode="weak_area",
        planned_rounds=1,
    )
    _lose_round(game_service, round_state)
    game_service.finalize_round(
        user=user,
        round_state=round_state,
        learning_session=learning_session,
    )
    review_repository.upsert_review_item(
        user_id=user["id"],
        word_id=round_state.word_id,
        language="english",
        category=round_state.category,
        priority_score=1.0,
        review_due_at="2026-04-20T00:00:00+00:00",
        last_reviewed_at="2026-04-19T00:00:00+00:00",
        last_result="lost",
        last_accuracy=0.2,
        is_active=True,
    )
    report_service.refresh_user_performance(user["id"])
    report = report_service.build_summary_report(user["id"], language="english")

    assert report["recent_learning_sessions"]
    assert report["recent_words_practiced"]
    assert report["review_queue_summary"]["active_count"] >= 1
    assert report["review_queue_summary"]["due_count"] >= 1
    assert report["category_trends"]
    assert report["recommendations"]
