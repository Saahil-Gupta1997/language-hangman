"""Tests for progress summary rebuilding."""

from src.db.database import init_db
from src.db.repository import GameSessionRepository
from src.services.auth_service import AuthService
from src.services.report_service import ReportService
from src.services.word_service import WordService


def test_refresh_user_performance_updates_category_summary(tmp_path) -> None:
    db_path = tmp_path / "reporting.db"
    init_db(db_path=db_path, seed_words=True)

    auth_service = AuthService(db_path=db_path)
    user = auth_service.register_user(
        username="reportuser",
        password="secret123",
        target_language="english",
        level="beginner",
        preferred_categories=["noun"],
    )
    noun_word = WordService(db_path=db_path).get_words("english", category="noun")[0]
    session_repository = GameSessionRepository(db_path=db_path)

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
        time_taken_seconds=9.5,
        started_at="2026-04-23T00:00:00+00:00",
        completed_at="2026-04-23T00:00:09+00:00",
        played_at="2026-04-23T00:00:09+00:00",
    )
    session_repository.create_session(
        user_id=user["id"],
        word_id=noun_word["id"],
        language="english",
        level="beginner",
        category="noun",
        result="lost",
        attempts_used=6,
        max_attempts=6,
        letters_correct=1,
        letters_wrong=5,
        guessed_letters="a,b,c,d,e,f",
        time_taken_seconds=14.0,
        started_at="2026-04-23T01:00:00+00:00",
        completed_at="2026-04-23T01:00:14+00:00",
        played_at="2026-04-23T01:00:14+00:00",
    )

    report_service = ReportService(db_path=db_path)
    report_service.refresh_user_performance(user["id"])
    report = report_service.build_summary_report(user["id"], language="english")

    assert report["overview"] == {"total_games": 2, "wins": 1, "losses": 1}
    assert len(report["summaries"]) == 1

    summary = report["summaries"][0]
    assert summary["category"] == "noun"
    assert summary["total_games"] == 2
    assert summary["wins"] == 1
    assert summary["losses"] == 1
    assert summary["avg_attempts"] == 5.0
    assert summary["accuracy"] == 50.0
    assert summary["mastery_score"] == 50.0
