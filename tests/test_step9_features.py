"""Tests for Step 9 content scale, CLI, release checks, and backup workflows."""

from __future__ import annotations

import json

from src.cli import main
from src.db.database import create_connection, init_db
from src.db.repository import (
    GameSessionRepository,
    LearningSessionRepository,
    ReviewQueueRepository,
    WordProgressRepository,
)
from src.services.auth_service import AuthService
from src.services.maintenance_service import MaintenanceService
from src.services.word_service import WordService
from src.utils.config import PROJECT_ROOT
from src.utils.constants import (
    CONTENT_MIN_WORDS_PER_LANGUAGE,
    CONTENT_MIN_WORDS_PER_LANGUAGE_CATEGORY,
    CONTENT_MIN_WORDS_PER_LANGUAGE_DIFFICULTY,
    DIFFICULTY_ORDER,
    WORD_CATEGORIES,
)
from src.utils.helpers import serialize_string_list
from src.utils.word_bank_loader import validate_word_bank_directory


def _complete_word(
    *,
    word: str,
    category: str,
    difficulty: str = "beginner",
    hint: str = "Helpful clue.",
    translation: str = "meaning",
    example_sentence: str = "Example sentence.",
    synonym: str = "related",
    association: str = "Useful memory clue.",
    language: str = "english",
) -> dict[str, object]:
    """Return a complete situational word-bank row for validation tests."""
    return {
        "word_id": f"{language}_{word.lower()}",
        "word": word,
        "meaning": translation,
        "language": language,
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
    }


def test_content_coverage_meets_step9_minimums() -> None:
    summary = validate_word_bank_directory(PROJECT_ROOT / "data" / "words")
    coverage = summary["coverage"]

    assert summary["has_errors"] is False
    assert set(coverage["total_words_by_language"]) == {"english", "french", "spanish"}
    assert coverage["weak_coverage_areas"] == []
    assert coverage["meets_minimum_coverage"] is True

    for language, count in coverage["total_words_by_language"].items():
        assert count >= CONTENT_MIN_WORDS_PER_LANGUAGE
        for category in WORD_CATEGORIES:
            assert (
                coverage["words_by_language_category"][f"{language}:{category}"]
                >= CONTENT_MIN_WORDS_PER_LANGUAGE_CATEGORY
            )
        for difficulty in DIFFICULTY_ORDER:
            assert (
                coverage["words_by_language_difficulty"][f"{language}:{difficulty}"]
                >= CONTENT_MIN_WORDS_PER_LANGUAGE_DIFFICULTY
            )


def test_validation_detects_duplicates_and_required_content_issues(tmp_path) -> None:
    words_dir = tmp_path / "words"
    words_dir.mkdir()
    (words_dir / "english.json").write_text(
        json.dumps(
            {
                "language": "english",
                "words": [
                    _complete_word(
                        word="apple",
                        category="noun",
                        hint="A fruit.",
                        translation="apple",
                        example_sentence="I eat an apple.",
                        synonym="fruit",
                        association="A red fruit linked with lunch.",
                    ),
                    _complete_word(
                        word="Apple",
                        category="noun",
                        hint="Duplicate fruit.",
                        translation="apple",
                        example_sentence="This duplicate should be skipped.",
                        synonym="fruit",
                        association="A duplicate fruit row.",
                    ),
                    {
                        **_complete_word(
                            word="missingtranslation",
                            category="noun",
                            hint="Missing translation.",
                            translation="missing translation",
                            example_sentence="This row is incomplete.",
                            synonym="missing",
                            association="A row missing translation.",
                        ),
                        "word": "missingtranslation",
                        "translation": "",
                    },
                    {
                        **_complete_word(
                            word="missingexample",
                            category="verb",
                            hint="Missing example.",
                            translation="missing example",
                            example_sentence="Missing example.",
                            synonym="missing",
                            association="A row missing example text.",
                        ),
                        "example_sentence": "",
                    },
                    {
                        **_complete_word(
                            word="oddcategory",
                            category="noun",
                            hint="Unsupported category.",
                            translation="odd",
                            example_sentence="Odd category.",
                            synonym="strange",
                            association="Unsupported category row.",
                        ),
                        "category": "interjection",
                    },
                    {
                        **_complete_word(
                            word="odddifficulty",
                            category="adverb",
                            hint="Unsupported difficulty.",
                            translation="odd",
                            example_sentence="Odd difficulty.",
                            synonym="strange",
                            association="Unsupported difficulty row.",
                        ),
                        "difficulty": "expert",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    summary = validate_word_bank_directory(words_dir)
    joined_errors = " ".join(
        error for file_summary in summary["files"] for error in file_summary["errors"]
    )

    assert summary["valid_words"] == 1
    assert summary["invalid_words"] == 5
    assert summary["duplicate_words"] == 1
    assert "Duplicate word/language pair" in joined_errors
    assert "Missing required field 'translation'" in joined_errors
    assert "Missing required field 'example_sentence'" in joined_errors
    assert "Unsupported category" in joined_errors
    assert "Unsupported difficulty" in joined_errors


def test_cli_validate_content_summary_and_coverage_output(capsys) -> None:
    exit_code = main(["validate-content", "--summary", "--coverage"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Files processed:" in captured.out
    assert "Quality warnings:" in captured.out
    assert "Coverage by language:" in captured.out
    assert "Coverage by difficulty:" in captured.out
    assert "Coverage by situation:" in captured.out
    assert "Weak coverage areas:" in captured.out


def test_validation_reports_content_quality_warnings(tmp_path) -> None:
    words_dir = tmp_path / "words"
    words_dir.mkdir()
    (words_dir / "spanish.json").write_text(
        json.dumps(
            {
                "language": "spanish",
                "words": [
                    _complete_word(
                        word="jardin",
                        category="noun",
                        translation="garden",
                        example_sentence="La palabra jardin aparece en la lectura de hoy.",
                        synonym="garden",
                        association="A green outdoor place.",
                        language="spanish",
                    )
                ],
            }
        ),
        encoding="utf-8",
    )

    summary = validate_word_bank_directory(words_dir)
    warnings = " ".join(
        warning for file_summary in summary["files"] for warning in file_summary["warnings"]
    )

    assert summary["has_errors"] is False
    assert summary["quality_warning_count"] >= 1
    assert "Example sentence looks generic" in warnings
    assert "Possible missing accent" in warnings
    assert "Pronunciation text matches the word exactly" in warnings


def test_release_check_detects_local_artifacts_but_allows_word_json(tmp_path) -> None:
    project_root = tmp_path / "project"
    artifact_directories = [
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".pytest_tmp",
        ".ruff_cache",
        ".mypy_cache",
        "htmlcov",
        "build",
        "dist",
        "release",
        "pytest_tmp_run_011",
        "pytest-cache-files-demo",
    ]
    for directory_name in artifact_directories:
        (project_root / directory_name).mkdir(parents=True)
    (project_root / ".venv" / "Lib" / "site-packages" / "__pycache__").mkdir(parents=True)
    (project_root / ".venv" / "Lib" / "site-packages" / "__pycache__" / "nested.pyc").write_text(
        "", encoding="utf-8"
    )
    (project_root / ".streamlit").mkdir(parents=True)
    (project_root / ".streamlit" / "secrets.toml").write_text("", encoding="utf-8")
    (project_root / ".coverage").write_text("", encoding="utf-8")
    (project_root / "module.pyc").write_text("", encoding="utf-8")
    (project_root / "data").mkdir(parents=True)
    (project_root / "data" / "app.db").write_text("", encoding="utf-8")
    (project_root / "extra.sqlite").write_text("", encoding="utf-8")
    (project_root / "extra.sqlite3").write_text("", encoding="utf-8")
    (project_root / "release.zip").write_text("", encoding="utf-8")
    (project_root / "data" / "words").mkdir(parents=True)
    (project_root / "data" / "words" / "english.json").write_text("{}", encoding="utf-8")

    service = MaintenanceService(
        project_root=project_root,
        db_path=project_root / "data" / "app.db",
        words_dir=project_root / "data" / "words",
    )
    release_check = service.find_local_artifacts()
    relative_artifacts = set(release_check["relative_artifacts"])

    assert release_check["is_clean"] is False
    assert ".streamlit/secrets.toml" in relative_artifacts
    assert ".venv" in relative_artifacts
    assert ".venv/Lib/site-packages/__pycache__/nested.pyc" not in relative_artifacts
    assert ".ruff_cache" in relative_artifacts
    assert ".mypy_cache" in relative_artifacts
    assert "htmlcov" in relative_artifacts
    assert "build" in relative_artifacts
    assert "dist" in relative_artifacts
    assert "release" in relative_artifacts
    assert "__pycache__" in relative_artifacts
    assert ".pytest_tmp" in relative_artifacts
    assert "pytest_tmp_run_011" in relative_artifacts
    assert "pytest-cache-files-demo" in relative_artifacts
    assert "module.pyc" in relative_artifacts
    assert ".coverage" in relative_artifacts
    assert "extra.sqlite" in relative_artifacts
    assert "extra.sqlite3" in relative_artifacts
    assert "release.zip" in relative_artifacts
    assert "data/app.db" in relative_artifacts
    assert "data/words/english.json" not in relative_artifacts


def test_export_import_progress_round_trip_is_idempotent(tmp_path) -> None:
    source_db = tmp_path / "source.db"
    target_db = tmp_path / "target.db"
    backup_path = tmp_path / "progress_backup.json"
    words_dir = PROJECT_ROOT / "data" / "words"
    init_db(db_path=source_db, seed_words=True)

    auth_service = AuthService(db_path=source_db)
    word_service = WordService(db_path=source_db)
    learning_repository = LearningSessionRepository(db_path=source_db)
    game_repository = GameSessionRepository(db_path=source_db)
    review_repository = ReviewQueueRepository(db_path=source_db)
    progress_repository = WordProgressRepository(db_path=source_db)

    user = auth_service.register_user(
        username="backupdemo",
        password="backup123",
        target_language="english",
        level="beginner",
        preferred_categories=["noun"],
    )
    word = word_service.get_words("english", category="noun", difficulty="beginner")[0]
    learning_session_id = learning_repository.create_learning_session(
        user_id=user["id"],
        language="english",
        practice_mode="standard",
        planned_rounds=1,
        selected_category="noun",
        selected_categories=serialize_string_list(["noun"]),
        difficulty_filter=serialize_string_list(["beginner"]),
        review_policy="prefer_review",
        show_hint_immediately=True,
        started_at="2026-04-29T00:00:00+00:00",
    )
    game_repository.create_session(
        user_id=user["id"],
        learning_session_id=learning_session_id,
        word_id=word["id"],
        language="english",
        level="beginner",
        category="noun",
        practice_mode="standard",
        result="won",
        attempts_used=4,
        max_attempts=6,
        letters_correct=4,
        letters_wrong=0,
        guessed_letters="a,p,l,e",
        time_taken_seconds=8.0,
        started_at="2026-04-29T00:00:00+00:00",
        completed_at="2026-04-29T00:00:08+00:00",
        played_at="2026-04-29T00:00:08+00:00",
    )
    review_repository.upsert_review_item(
        user_id=user["id"],
        word_id=word["id"],
        language="english",
        category="noun",
        priority_score=0.7,
        review_due_at="2026-04-30T00:00:00+00:00",
        last_reviewed_at="2026-04-29T00:00:08+00:00",
        last_result="won",
        last_accuracy=1.0,
        is_active=True,
    )
    progress_repository.upsert_progress(
        user_id=user["id"],
        word_id=word["id"],
        language="english",
        familiarity_status="strong",
        mastery_score=85.0,
        wins_delta=1,
        losses_delta=0,
        successful_streak=1,
        correct_letters_delta=4,
        wrong_letters_delta=0,
        last_accuracy=1.0,
        last_result="won",
        priority_score=0.2,
        last_played_at="2026-04-29T00:00:08+00:00",
    )

    source_service = MaintenanceService(db_path=source_db, words_dir=words_dir)
    export_summary = source_service.export_progress(backup_path)
    assert export_summary["counts"]["users"] == 1
    assert backup_path.exists()

    target_service = MaintenanceService(db_path=target_db, words_dir=words_dir)
    first_import = target_service.import_progress(backup_path)
    second_import = target_service.import_progress(backup_path)
    target_auth = AuthService(db_path=target_db)
    restored_user = target_auth.authenticate_user("backupdemo", "backup123")

    assert restored_user is not None
    assert first_import["imported_counts"]["game_sessions"] == 1
    assert second_import["imported_counts"]["game_sessions"] == 1

    with create_connection(target_db) as connection:
        counts = {
            table_name: connection.execute(
                f"SELECT COUNT(*) AS count FROM {table_name}"
            ).fetchone()["count"]
            for table_name in (
                "learning_sessions",
                "game_sessions",
                "review_queue",
                "word_progress",
            )
        }

    assert counts == {
        "learning_sessions": 1,
        "game_sessions": 1,
        "review_queue": 1,
        "word_progress": 1,
    }
