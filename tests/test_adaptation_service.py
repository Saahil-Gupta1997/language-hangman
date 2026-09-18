"""Tests for rule-based adaptation behavior."""

from src.db.database import init_db
from src.db.repository import GameSessionRepository
from src.services.adaptation_service import AdaptationService
from src.services.auth_service import AuthService
from src.services.report_service import ReportService
from src.services.word_service import WordService


def create_session(
    session_repository: GameSessionRepository,
    user_id: int,
    word_id: int,
    category: str,
    result: str,
    attempts_used: int,
    letters_correct: int,
    letters_wrong: int,
    played_at: str,
) -> None:
    """Insert one synthetic game session for adaptation tests."""
    session_repository.create_session(
        user_id=user_id,
        word_id=word_id,
        language="english",
        level="beginner",
        category=category,
        result=result,
        attempts_used=attempts_used,
        max_attempts=6,
        letters_correct=letters_correct,
        letters_wrong=letters_wrong,
        guessed_letters="a,b,c",
        time_taken_seconds=8.0,
        started_at=played_at,
        completed_at=played_at,
        played_at=played_at,
    )


def test_adaptation_prioritizes_weaker_categories(tmp_path) -> None:
    db_path = tmp_path / "adaptation_weak.db"
    init_db(db_path=db_path, seed_words=True)

    auth_service = AuthService(db_path=db_path)
    word_service = WordService(db_path=db_path)
    report_service = ReportService(db_path=db_path)
    session_repository = GameSessionRepository(db_path=db_path)
    user = auth_service.register_user(
        username="adaptive",
        password="secret123",
        target_language="english",
        level="intermediate",
        preferred_categories=["noun", "verb"],
    )

    noun_word = word_service.get_words("english", category="noun")[0]
    verb_word = word_service.get_words("english", category="verb")[0]

    create_session(
        session_repository,
        user_id=user["id"],
        word_id=noun_word["id"],
        category="noun",
        result="won",
        attempts_used=4,
        letters_correct=4,
        letters_wrong=0,
        played_at="2026-04-23T00:00:00+00:00",
    )
    create_session(
        session_repository,
        user_id=user["id"],
        word_id=verb_word["id"],
        category="verb",
        result="lost",
        attempts_used=6,
        letters_correct=1,
        letters_wrong=5,
        played_at="2026-04-23T01:00:00+00:00",
    )
    create_session(
        session_repository,
        user_id=user["id"],
        word_id=verb_word["id"],
        category="verb",
        result="lost",
        attempts_used=6,
        letters_correct=2,
        letters_wrong=4,
        played_at="2026-04-23T02:00:00+00:00",
    )
    report_service.refresh_user_performance(user["id"])

    recommendation = AdaptationService(db_path=db_path).build_recommendation(
        auth_service.get_user_by_id(user["id"])
    )

    assert recommendation["category_order"][0] == "verb"
    assert verb_word["id"] in recommendation["recent_word_ids"]


def test_adaptation_gently_increases_level_after_recent_wins(tmp_path) -> None:
    db_path = tmp_path / "adaptation_level.db"
    init_db(db_path=db_path, seed_words=True)

    auth_service = AuthService(db_path=db_path)
    word_service = WordService(db_path=db_path)
    session_repository = GameSessionRepository(db_path=db_path)
    user = auth_service.register_user(
        username="streak",
        password="secret123",
        target_language="english",
        level="beginner",
        preferred_categories=["noun"],
    )

    noun_word = word_service.get_words("english", category="noun")[0]
    for offset in range(3):
        create_session(
            session_repository,
            user_id=user["id"],
            word_id=noun_word["id"],
            category="noun",
            result="won",
            attempts_used=4,
            letters_correct=4,
            letters_wrong=0,
            played_at=f"2026-04-23T0{offset}:00:00+00:00",
        )

    recommendation = AdaptationService(db_path=db_path).build_recommendation(
        auth_service.get_user_by_id(user["id"])
    )

    assert recommendation["base_level"] == "beginner"
    assert recommendation["adapted_level"] == "intermediate"
