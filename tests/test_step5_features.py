"""Tests for Step 5 builder, import, recommendation, and mastery behavior."""

from __future__ import annotations

import json

from src.db.database import init_db
from src.db.repository import ReviewQueueRepository, WordProgressRepository
from src.models.learning_session import LearningSession
from src.services.auth_service import AuthService
from src.services.game_service import GameService
from src.services.report_service import ReportService
from src.services.word_service import WordService


def _complete_word(
    *,
    word: str,
    category: str,
    hint: str,
    translation: str,
    example_sentence: str,
    synonym: str,
    association: str,
    difficulty: str = "beginner",
    notes: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, object]:
    """Return a complete situational word-bank row for import tests."""
    row: dict[str, object] = {
        "word_id": f"english_{word.lower()}",
        "word": word,
        "meaning": translation,
        "language": "english",
        "situations": ["restaurant"],
        "category": category,
        "difficulty": difficulty,
        "hint": hint,
        "translation": translation,
        "example_sentence": example_sentence,
        "sentence_translation": example_sentence,
        "pronunciation_text": word,
        "usage_note": f"Use {word} in a restaurant situation.",
        "synonym": synonym,
        "association": association,
        "synonym_hint": synonym,
        "association_hint": association,
        "tags": tags or [],
    }
    if notes:
        row["notes"] = notes
    return row


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


def test_custom_builder_shortens_session_when_pool_is_small(tmp_path) -> None:
    db_path = tmp_path / "custom_builder.db"
    init_db(db_path=db_path, seed_words=True)

    auth_service = AuthService(db_path=db_path)
    game_service = GameService(db_path=db_path)
    user = auth_service.register_user(
        username="builderuser",
        password="secret123",
        target_language="english",
        level="advanced",
        preferred_categories=["noun", "verb"],
    )

    preparation = game_service.prepare_custom_session(
        user=user,
        builder_settings={
            "language": "english",
            "categories": ["adverb"],
            "practice_mode": "category",
            "difficulties": ["beginner"],
            "rounds": 12,
            "review_policy": "new_only",
            "show_hint_immediately": False,
        },
    )

    assert preparation["can_start"] is True
    assert preparation["settings"]["categories"] == ["adverb"]
    assert preparation["settings"]["difficulties"] == ["beginner"]
    assert preparation["settings"]["rounds"] == preparation["matched_word_count"]
    assert preparation["matched_word_count"] >= 1
    assert "shortened" in " ".join(preparation["warnings"])


def test_word_bank_reload_skips_invalid_rows_and_updates_duplicates(tmp_path) -> None:
    db_path = tmp_path / "word_import.db"
    words_dir = tmp_path / "words"
    words_dir.mkdir()
    init_db(db_path=db_path, seed_words=False)

    (words_dir / "english.json").write_text(
        json.dumps(
            {
                "language": "english",
                "words": [
                    _complete_word(
                        word="apple",
                        category="noun",
                        hint="Fruit hint",
                        translation="apple",
                        example_sentence="An apple a day.",
                        synonym="fruit",
                        association="A red fruit linked with lunch.",
                        tags=["food"],
                    ),
                    _complete_word(
                        word="run",
                        category="verb",
                        hint="Move fast",
                        translation="run",
                        example_sentence="They run daily.",
                        synonym="sprint",
                        association="Movement with legs.",
                    ),
                ],
            }
        ),
        encoding="utf-8",
    )
    (words_dir / "updates.json").write_text(
        json.dumps(
            {
                "language": "english",
                "words": [
                    _complete_word(
                        word="apple",
                        category="noun",
                        hint="Updated fruit hint",
                        translation="apple",
                        example_sentence="Updated example sentence.",
                        synonym="fruit",
                        association="A duplicate fruit row.",
                        notes="duplicate update",
                    ),
                    {
                        **_complete_word(
                            word="broken",
                            category="adjective",
                            hint="Missing hint should fail.",
                            translation="broken",
                            example_sentence="Missing hint should fail.",
                            synonym="damaged",
                            association="Something that needs repair.",
                        ),
                        "word": "broken",
                        "hint": "",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    service = WordService(words_dir=words_dir, db_path=db_path)
    first_import = service.reload_word_banks()
    second_import = service.reload_word_banks()
    apple_word = service.get_words("english", category="noun", difficulty="beginner")[0]

    assert first_import["valid_words"] == 2
    assert first_import["invalid_words"] == 2
    assert first_import["duplicate_words"] == 1
    assert first_import["inserted_count"] == 2
    assert second_import["inserted_count"] == 0
    assert second_import["reloaded_count"] == 2
    assert apple_word["hint"] == "Fruit hint"


def test_word_progress_reaches_strong_after_repeated_clean_wins(tmp_path) -> None:
    db_path = tmp_path / "word_progress.db"
    init_db(db_path=db_path, seed_words=True)

    auth_service = AuthService(db_path=db_path)
    game_service = GameService(db_path=db_path)
    progress_repository = WordProgressRepository(db_path=db_path)
    word_service = WordService(db_path=db_path)
    user = auth_service.register_user(
        username="masteryuser",
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

    assert progress_row is not None
    assert progress_row["familiarity_status"] == "strong"
    assert progress_row["times_seen"] == 3
    assert float(progress_row["priority_score"]) <= 0.25


def test_report_recommendations_reflect_review_and_weakness_signals(tmp_path) -> None:
    db_path = tmp_path / "recommendations.db"
    init_db(db_path=db_path, seed_words=True)

    auth_service = AuthService(db_path=db_path)
    game_service = GameService(db_path=db_path)
    report_service = ReportService(db_path=db_path)
    review_repository = ReviewQueueRepository(db_path=db_path)
    user = auth_service.register_user(
        username="recommenduser",
        password="secret123",
        target_language="english",
        level="intermediate",
        preferred_categories=["verb", "noun"],
    )

    learning_session, round_state = game_service.start_learning_session(
        user=user,
        practice_mode="weak_area",
        planned_rounds=1,
        selected_category="verb",
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
        category="verb",
        priority_score=1.0,
        review_due_at="2026-04-20T00:00:00+00:00",
        last_reviewed_at="2026-04-19T00:00:00+00:00",
        last_result="lost",
        last_accuracy=0.2,
        is_active=True,
    )
    report_service.refresh_user_performance(user["id"])
    report = report_service.build_summary_report(user["id"], language="english")

    joined_recommendations = " ".join(report["recommendations"]).lower()
    assert "review-only session" in joined_recommendations
    assert "custom 5-round session" in joined_recommendations
