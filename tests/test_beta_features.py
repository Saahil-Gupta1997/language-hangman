"""Tests for v1.0.0-beta onboarding, dashboard, goals, and imports."""

from __future__ import annotations

import json
import random
from datetime import date, datetime, timezone

from src import __release_name__, __version__, version
from src.db.database import init_db
from src.db.repository import GameSessionRepository, LearningSessionRepository
from src.services.auth_service import AuthService
from src.services.game_service import GameService
from src.services.onboarding_service import build_onboarding_state
from src.services.report_service import ReportService
from src.services.word_service import WordService
from src.utils.config import APP_VERSION_DISPLAY, PROJECT_ROOT
from src.utils.helpers import serialize_string_list
from src.utils.language_display import format_language_label


def _complete_word(
    *,
    word: str,
    category: str = "noun",
    difficulty: str = "beginner",
    hint: str = "Helpful clue.",
    translation: str | None = None,
    example_sentence: str | None = None,
    synonym: str = "related",
    association: str = "Useful memory clue.",
) -> dict[str, object]:
    """Return a complete situational upload row for import tests."""
    resolved_translation = translation or word
    resolved_example = example_sentence or f"Use {word} in context."
    return {
        "word_id": f"english_{word.lower()}",
        "word": word,
        "meaning": resolved_translation,
        "language": "english",
        "situations": ["restaurant"],
        "category": category,
        "difficulty": difficulty,
        "hint": hint,
        "translation": resolved_translation,
        "example_sentence": resolved_example,
        "sentence_translation": resolved_example,
        "pronunciation_text": word,
        "usage_note": f"Use {word} in a restaurant situation.",
        "synonym": synonym,
        "association": association,
        "synonym_hint": synonym,
        "association_hint": association,
    }


def test_release_version_display_is_current() -> None:
    assert __version__ == "1.0.0rc7"
    assert version == __version__
    assert __release_name__ == "Desktop Release Candidate 6"
    assert APP_VERSION_DISPLAY == "v1.0.0rc7"
    version_file = (PROJECT_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert version_file == __version__


def test_installer_default_version_matches_the_application() -> None:
    script = (PROJECT_ROOT / "packaging" / "hangman.iss").read_text(encoding="utf-8")
    assert f'#define MyAppVersion "{__version__}"' in script


def test_onboarding_state_guides_unassessed_users() -> None:
    new_user = {
        "assessment_completed": False,
    }
    assessed_user = {
        "assessment_completed": True,
    }

    new_state = build_onboarding_state(new_user)
    assessed_state = build_onboarding_state(assessed_user)

    assert new_state["should_prompt"] is True
    assert new_state["next_action"] == "Start assessment"
    assert len(new_state["steps"]) == 5
    assert assessed_state["should_prompt"] is False


def test_dashboard_daily_goal_and_streak_summary(tmp_path) -> None:
    db_path = tmp_path / "beta_dashboard.db"
    init_db(db_path=db_path, seed_words=True)
    auth_service = AuthService(db_path=db_path)
    word_service = WordService(db_path=db_path)
    game_repository = GameSessionRepository(db_path=db_path)
    learning_repository = LearningSessionRepository(db_path=db_path)
    user = auth_service.register_user(
        username="betadashboard",
        password="secret123",
        target_language="english",
        level="beginner",
        preferred_categories=["noun"],
    )
    user = auth_service.update_daily_goals(
        user_id=user["id"],
        daily_goal_words=2,
        daily_goal_sessions=1,
    )
    today = datetime.now(timezone.utc).replace(hour=10, minute=0, second=0, microsecond=0)
    today_iso = today.isoformat()
    words = word_service.get_words("english", category="noun", difficulty="beginner")[:2]

    learning_session_id = learning_repository.create_learning_session(
        user_id=user["id"],
        language="english",
        practice_mode="standard",
        planned_rounds=2,
        selected_category="noun",
        selected_categories=serialize_string_list(["noun"]),
        difficulty_filter=serialize_string_list(["beginner"]),
        review_policy="prefer_review",
        show_hint_immediately=True,
        started_at=today_iso,
    )
    learning_repository.update_learning_session(
        session_id=learning_session_id,
        completed_rounds=2,
        wins=2,
        losses=0,
        accuracy=100.0,
        categories_practiced=serialize_string_list(["noun"]),
        words_practiced=serialize_string_list([word["word"] for word in words]),
        status="completed",
        recommendation="Keep going.",
        completed_at=today_iso,
    )
    for index, word in enumerate(words):
        game_repository.create_session(
            user_id=user["id"],
            learning_session_id=learning_session_id,
            word_id=word["id"],
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
            started_at=today_iso,
            completed_at=today_iso,
            played_at=today.replace(minute=index).isoformat(),
            practice_mode="standard",
        )

    report = ReportService(db_path=db_path).build_summary_report(
        user_id=user["id"],
        language="english",
    )

    assert report["daily_goal"]["goal_met"] is True
    assert report["daily_goal"]["words_today"] == 2
    assert report["daily_goal"]["sessions_today"] == 1
    assert report["dashboard"]["total_words_practiced"] == 2
    assert report["dashboard"]["current_streak"] >= 1
    assert report["dashboard"]["suggested_practice_mode"] in {
        "Standard Practice",
        "Weak Area Practice",
        "Review Practice",
        "Review Weak Words",
    }


def test_streak_calculation_tracks_current_and_best_streaks() -> None:
    streaks = ReportService.build_streak_summary(
        ["2026-05-01", "2026-05-02", "2026-05-03"],
        today=date(2026, 5, 3),
    )
    broken_streaks = ReportService.build_streak_summary(
        ["2026-05-01", "2026-05-02", "2026-05-04"],
        today=date(2026, 5, 4),
    )

    assert streaks["current_streak"] == 3
    assert streaks["best_streak"] == 3
    assert streaks["today_practiced"] is True
    assert broken_streaks["current_streak"] == 1
    assert broken_streaks["best_streak"] == 2


def test_review_empty_state_and_recommendation_are_friendly(tmp_path) -> None:
    db_path = tmp_path / "beta_empty_review.db"
    init_db(db_path=db_path, seed_words=True)
    user = AuthService(db_path=db_path).register_user(
        username="emptyreview",
        password="secret123",
        target_language="english",
        level="beginner",
    )

    report = ReportService(db_path=db_path).build_summary_report(
        user_id=user["id"],
        language="english",
    )

    assert report["review_queue_summary"]["due_count"] == 0
    assert "No review words yet" in report["dashboard"]["empty_states"]["reviews"]
    assert report["dashboard"]["suggested_practice_mode"] == "Standard Practice"


def test_custom_json_word_import_validates_and_skips_existing_rows(tmp_path) -> None:
    db_path = tmp_path / "beta_import.db"
    init_db(db_path=db_path, seed_words=False)
    service = WordService(db_path=db_path)
    payload = {
        "language": "english",
        "words": [
            _complete_word(
                word="glimmer",
                hint="A small light.",
                translation="glimmer",
                example_sentence="A glimmer appeared in the window.",
                synonym="spark",
                association="Tiny shine in darkness.",
            ),
            _complete_word(
                word="glimmer",
                hint="Duplicate.",
                translation="glimmer",
                example_sentence="Duplicate row.",
                synonym="spark",
                association="Duplicate shine.",
            ),
            {
                **_complete_word(
                    word="broken",
                    hint="Missing required content.",
                ),
                "word": "broken",
                "translation": "",
            },
        ],
    }
    content = json.dumps(payload).encode("utf-8")

    first_import = service.import_uploaded_word_bank(
        filename="custom.json",
        content=content,
    )
    second_import = service.import_uploaded_word_bank(
        filename="custom.json",
        content=content,
    )

    assert first_import["valid_words"] == 1
    assert first_import["invalid_words"] == 2
    assert first_import["duplicate_words"] == 1
    assert first_import["inserted_count"] == 1
    assert second_import["inserted_count"] == 0
    assert second_import["skipped_existing_count"] == 1


def test_completed_gameplay_review_contains_learning_details(tmp_path) -> None:
    db_path = tmp_path / "beta_gameplay_review.db"
    init_db(db_path=db_path, seed_words=True)
    auth_service = AuthService(db_path=db_path)
    game_service = GameService(db_path=db_path)
    user = auth_service.register_user(
        username="reviewdetails",
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
        rng=random.Random(3),
    )
    for letter in sorted(round_state.unique_letters):
        game_service.record_guess(round_state, letter)

    game_service.finalize_round(
        user=user,
        round_state=round_state,
        learning_session=learning_session,
    )
    review = game_service.build_learning_review(round_state)

    assert review["word"]
    assert review["translation"]
    assert review["example_sentence"]
    assert review["meaning"]
    assert review["situation"]
    assert review["sentence_translation"]
    assert review["pronunciation_text"]
    assert review["usage_note"]
    assert review["synonym"]
    assert review["association"]
    assert review["category"]
    assert review["difficulty"]


def test_language_labels_are_consistent() -> None:
    assert format_language_label("english").endswith("English")
    assert format_language_label("spanish").endswith("Spanish")
    assert format_language_label("french").endswith("French")
