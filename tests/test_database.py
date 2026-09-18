"""Tests for database initialization."""

import sqlite3

from src.db.database import init_db


def test_init_db_creates_expected_tables(tmp_path) -> None:
    db_path = tmp_path / "test_app.db"
    init_db(db_path=db_path, seed_words=False)

    connection = sqlite3.connect(db_path)
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table';"
        ).fetchall()
    }
    connection.close()

    assert {
        "users",
        "words",
        "game_sessions",
        "learning_sessions",
        "review_queue",
        "word_progress",
        "performance_summary",
    }.issubset(tables)


def test_init_db_adds_step_two_columns(tmp_path) -> None:
    db_path = tmp_path / "test_step_two.db"
    init_db(db_path=db_path, seed_words=False)

    connection = sqlite3.connect(db_path)
    user_columns = {row[1] for row in connection.execute("PRAGMA table_info(users);").fetchall()}
    session_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(game_sessions);").fetchall()
    }
    learning_session_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(learning_sessions);").fetchall()
    }
    review_queue_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(review_queue);").fetchall()
    }
    word_columns = {row[1] for row in connection.execute("PRAGMA table_info(words);").fetchall()}
    word_progress_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(word_progress);").fetchall()
    }
    summary_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(performance_summary);").fetchall()
    }
    connection.close()

    assert "preferred_categories" in user_columns
    assert {
        "calibrated_level",
        "assessment_completed",
        "last_builder_settings",
        "daily_goal_words",
        "daily_goal_sessions",
    }.issubset(user_columns)
    assert {
        "learning_session_id",
        "practice_mode",
        "attempts_used",
        "letters_correct",
        "letters_wrong",
        "played_at",
    }.issubset(session_columns)
    assert {
        "language",
        "practice_mode",
        "planned_rounds",
        "selected_categories",
        "difficulty_filter",
        "review_policy",
        "show_hint_immediately",
        "game_mode",
        "accuracy",
        "categories_practiced",
        "words_practiced",
    }.issubset(learning_session_columns)
    assert {
        "priority_score",
        "review_due_at",
        "review_count",
        "last_accuracy",
        "is_active",
    }.issubset(review_queue_columns)
    assert {
        "meaning_hint",
        "synonym_hint",
        "association_hint",
    }.issubset(word_columns)
    assert {
        "familiarity_status",
        "mastery_score",
        "times_seen",
        "successful_streak",
        "priority_score",
        "last_played_at",
    }.issubset(word_progress_columns)
    assert {"category", "avg_attempts", "mastery_score"}.issubset(summary_columns)


def test_init_db_seeds_words_table(tmp_path) -> None:
    db_path = tmp_path / "seeded_app.db"
    init_db(db_path=db_path, seed_words=True)

    connection = sqlite3.connect(db_path)
    word_count = connection.execute("SELECT COUNT(*) FROM words;").fetchone()[0]
    connection.close()

    assert word_count >= 8


def test_init_db_migrates_pre_mode_learning_sessions(tmp_path) -> None:
    db_path = tmp_path / "pre_mode_app.db"
    connection = sqlite3.connect(db_path)
    connection.executescript(
        """
        CREATE TABLE learning_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            language TEXT NOT NULL,
            practice_mode TEXT NOT NULL DEFAULT 'standard',
            planned_rounds INTEGER NOT NULL DEFAULT 3,
            selected_category TEXT,
            selected_categories TEXT NOT NULL DEFAULT '[]',
            difficulty_filter TEXT NOT NULL DEFAULT '[]',
            review_policy TEXT NOT NULL DEFAULT 'prefer_review',
            show_hint_immediately INTEGER NOT NULL DEFAULT 1,
            completed_rounds INTEGER NOT NULL DEFAULT 0,
            wins INTEGER NOT NULL DEFAULT 0,
            losses INTEGER NOT NULL DEFAULT 0,
            accuracy REAL NOT NULL DEFAULT 0,
            categories_practiced TEXT NOT NULL DEFAULT '[]',
            words_practiced TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'active',
            recommendation TEXT,
            started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        INSERT INTO learning_sessions (
            user_id,
            language,
            practice_mode,
            planned_rounds,
            show_hint_immediately
        ) VALUES
            (1, 'english', 'standard', 1, 1),
            (1, 'english', 'standard', 1, 0);
        """
    )
    connection.commit()
    connection.close()

    init_db(db_path=db_path, seed_words=False)

    connection = sqlite3.connect(db_path)
    rows = connection.execute(
        "SELECT show_hint_immediately, game_mode FROM learning_sessions ORDER BY id"
    ).fetchall()
    connection.close()

    assert rows == [(1, "easy"), (0, "hard")]
