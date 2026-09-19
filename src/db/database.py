"""SQLite database bootstrap and schema management."""

from __future__ import annotations

import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from src.utils.config import DATABASE_PATH, WORDS_DIR
from src.utils.constants import DEFAULT_DAILY_GOAL_SESSIONS, DEFAULT_DAILY_GOAL_WORDS
from src.utils.word_bank_loader import build_seed_rows

DEFAULT_CATEGORIES_JSON = '["noun", "verb", "adjective", "adverb"]'
DEFAULT_BUILDER_SETTINGS_JSON = "{}"

SCHEMA_SQL = f"""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    target_language TEXT NOT NULL,
    level TEXT NOT NULL,
    calibrated_level TEXT,
    assessment_completed INTEGER NOT NULL DEFAULT 0,
    preferred_categories TEXT NOT NULL DEFAULT '{DEFAULT_CATEGORIES_JSON}',
    last_builder_settings TEXT NOT NULL DEFAULT '{DEFAULT_BUILDER_SETTINGS_JSON}',
    daily_goal_words INTEGER NOT NULL DEFAULT {DEFAULT_DAILY_GOAL_WORDS},
    daily_goal_sessions INTEGER NOT NULL DEFAULT {DEFAULT_DAILY_GOAL_SESSIONS},
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word_bank_id TEXT,
    word TEXT NOT NULL,
    meaning TEXT NOT NULL DEFAULT '',
    language TEXT NOT NULL,
    situations TEXT NOT NULL DEFAULT '[]',
    category TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    hint TEXT NOT NULL,
    translation TEXT NOT NULL,
    example_sentence TEXT NOT NULL,
    sentence_translation TEXT NOT NULL DEFAULT '',
    pronunciation_text TEXT NOT NULL DEFAULT '',
    usage_note TEXT NOT NULL DEFAULT '',
    synonym TEXT NOT NULL DEFAULT '',
    association TEXT NOT NULL DEFAULT '',
    meaning_hint TEXT NOT NULL DEFAULT '',
    synonym_hint TEXT NOT NULL DEFAULT '',
    association_hint TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '[]',
    subcategory TEXT,
    source TEXT,
    notes TEXT,
    source_file TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(word, language, category, difficulty)
);

CREATE TABLE IF NOT EXISTS learning_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    language TEXT NOT NULL,
    practice_mode TEXT NOT NULL DEFAULT 'standard',
    planned_rounds INTEGER NOT NULL DEFAULT 3,
    selected_category TEXT,
    selected_categories TEXT NOT NULL DEFAULT '[]',
    difficulty_filter TEXT NOT NULL DEFAULT '[]',
    situation TEXT,
    review_policy TEXT NOT NULL DEFAULT 'prefer_review',
    show_hint_immediately INTEGER NOT NULL DEFAULT 1,
    game_mode TEXT NOT NULL DEFAULT 'easy',
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
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS game_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    learning_session_id INTEGER,
    word_id INTEGER NOT NULL,
    language TEXT NOT NULL,
    situation TEXT,
    level TEXT NOT NULL,
    category TEXT NOT NULL,
    practice_mode TEXT NOT NULL DEFAULT 'standard',
    result TEXT NOT NULL DEFAULT 'in_progress',
    attempts_used INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 6,
    letters_correct INTEGER NOT NULL DEFAULT 0,
    letters_wrong INTEGER NOT NULL DEFAULT 0,
    guessed_letters TEXT NOT NULL DEFAULT '',
    hints_used INTEGER NOT NULL DEFAULT 0,
    time_taken_seconds REAL,
    played_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    FOREIGN KEY (learning_session_id) REFERENCES learning_sessions(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS review_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    word_id INTEGER NOT NULL,
    language TEXT NOT NULL,
    category TEXT NOT NULL,
    priority_score REAL NOT NULL DEFAULT 0,
    review_due_at TEXT NOT NULL,
    review_count INTEGER NOT NULL DEFAULT 0,
    last_reviewed_at TEXT,
    last_result TEXT,
    last_accuracy REAL NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE,
    UNIQUE(user_id, word_id)
);

CREATE TABLE IF NOT EXISTS word_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    word_id INTEGER NOT NULL,
    language TEXT NOT NULL,
    familiarity_status TEXT NOT NULL DEFAULT 'new',
    mastery_status TEXT NOT NULL DEFAULT 'weak',
    mastery_score REAL NOT NULL DEFAULT 0,
    times_seen INTEGER NOT NULL DEFAULT 0,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    wins INTEGER NOT NULL DEFAULT 0,
    losses INTEGER NOT NULL DEFAULT 0,
    successful_streak INTEGER NOT NULL DEFAULT 0,
    total_correct_letters INTEGER NOT NULL DEFAULT 0,
    total_wrong_letters INTEGER NOT NULL DEFAULT 0,
    total_wrong_guesses INTEGER NOT NULL DEFAULT 0,
    total_hints_used INTEGER NOT NULL DEFAULT 0,
    last_accuracy REAL NOT NULL DEFAULT 0,
    last_result TEXT,
    priority_score REAL NOT NULL DEFAULT 0,
    last_played_at TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE,
    UNIQUE(user_id, word_id)
);

CREATE TABLE IF NOT EXISTS performance_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    language TEXT NOT NULL,
    category TEXT NOT NULL,
    total_games INTEGER NOT NULL DEFAULT 0,
    wins INTEGER NOT NULL DEFAULT 0,
    losses INTEGER NOT NULL DEFAULT 0,
    accuracy REAL NOT NULL DEFAULT 0,
    avg_attempts REAL NOT NULL DEFAULT 0,
    mastery_score REAL NOT NULL DEFAULT 0,
    last_played_at TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, language, category)
);
"""

WORD_INSERT_SQL = """
INSERT INTO words (
    word_bank_id,
    word,
    meaning,
    language,
    situations,
    category,
    difficulty,
    hint,
    translation,
    example_sentence,
    sentence_translation,
    pronunciation_text,
    usage_note,
    synonym,
    association,
    meaning_hint,
    synonym_hint,
    association_hint,
    tags,
    subcategory,
    source,
    notes,
    source_file
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(word, language, category, difficulty) DO UPDATE SET
    word_bank_id = excluded.word_bank_id,
    meaning = excluded.meaning,
    situations = excluded.situations,
    hint = excluded.hint,
    translation = excluded.translation,
    example_sentence = excluded.example_sentence,
    sentence_translation = excluded.sentence_translation,
    pronunciation_text = excluded.pronunciation_text,
    usage_note = excluded.usage_note,
    synonym = excluded.synonym,
    association = excluded.association,
    meaning_hint = excluded.meaning_hint,
    synonym_hint = excluded.synonym_hint,
    association_hint = excluded.association_hint,
    tags = excluded.tags,
    subcategory = excluded.subcategory,
    source = excluded.source,
    notes = excluded.notes,
    source_file = excluded.source_file
"""


class ManagedConnection(sqlite3.Connection):
    """Commit or roll back a transaction, then release its file handle."""

    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()


def create_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Create a SQLite connection with foreign keys enabled."""
    resolved_path = Path(db_path or DATABASE_PATH)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(resolved_path, factory=ManagedConnection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


SCHEMA_VERSION = 1


def init_db(db_path: Path | None = None, seed_words: bool = True) -> Path:
    """Upgrade on a staging copy; preserve the source until upgrade succeeds."""
    target = Path(db_path or DATABASE_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    version = 0
    if target.exists():
        with create_connection(target) as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version > SCHEMA_VERSION:
            raise ValueError("This database needs a newer version of Language Hangman.")
        if version == SCHEMA_VERSION:
            if seed_words:
                with create_connection(target) as connection:
                    _seed_words_table(connection, words_dir=WORDS_DIR)
            return target
    descriptor, name = tempfile.mkstemp(prefix="upgrade-", suffix=".sqlite", dir=target.parent)
    os.close(descriptor)
    staging = Path(name)
    try:
        if target.exists():
            backup_dir = target.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
            with create_connection(target) as source:
                with create_connection(backup_dir / f"pre-upgrade-{stamp}.sqlite") as backup:
                    source.backup(backup)
                with create_connection(staging) as copy:
                    source.backup(copy)
        _initialize_db(staging, seed_words=seed_words)
        with create_connection(staging) as connection:
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Database upgrade integrity check failed.")
            if connection.execute("PRAGMA foreign_key_check").fetchone():
                raise ValueError("Database upgrade found broken relationships.")
        os.replace(staging, target)
    finally:
        staging.unlink(missing_ok=True)
    return target


def _initialize_db(db_path: Path | None = None, seed_words: bool = True) -> Path:
    """Create the database file, schema, and starter word data."""
    resolved_path = Path(db_path or DATABASE_PATH)

    with create_connection(resolved_path) as connection:
        connection.executescript(SCHEMA_SQL)
        _run_migrations(connection)
        _ensure_indexes(connection)
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS completion_receipts (
                round_key TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS active_practice (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                payload TEXT NOT NULL,
                revision INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            PRAGMA user_version = 1;
        """
        )

        if seed_words:
            _seed_words_table(connection, words_dir=WORDS_DIR)

    return resolved_path


def _run_migrations(connection: sqlite3.Connection) -> None:
    """Apply lightweight schema migrations for older local databases."""
    _ensure_column(
        connection,
        table_name="users",
        column_name="calibrated_level",
        definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="users",
        column_name="assessment_completed",
        definition="INTEGER NOT NULL DEFAULT 0",
    )
    _ensure_column(
        connection,
        table_name="users",
        column_name="preferred_categories",
        definition=f"TEXT NOT NULL DEFAULT '{DEFAULT_CATEGORIES_JSON}'",
    )
    _ensure_column(
        connection,
        table_name="users",
        column_name="last_builder_settings",
        definition=f"TEXT NOT NULL DEFAULT '{DEFAULT_BUILDER_SETTINGS_JSON}'",
    )
    _ensure_column(
        connection,
        table_name="users",
        column_name="daily_goal_words",
        definition=f"INTEGER NOT NULL DEFAULT {DEFAULT_DAILY_GOAL_WORDS}",
    )
    _ensure_column(
        connection,
        table_name="users",
        column_name="daily_goal_sessions",
        definition=f"INTEGER NOT NULL DEFAULT {DEFAULT_DAILY_GOAL_SESSIONS}",
    )
    connection.execute(
        """
        UPDATE users
        SET preferred_categories = ?
        WHERE preferred_categories IS NULL OR preferred_categories = ''
        """,
        (DEFAULT_CATEGORIES_JSON,),
    )
    connection.execute(
        """
        UPDATE users
        SET last_builder_settings = ?
        WHERE last_builder_settings IS NULL OR last_builder_settings = ''
        """,
        (DEFAULT_BUILDER_SETTINGS_JSON,),
    )
    connection.execute(
        """
        UPDATE users
        SET daily_goal_words = ?
        WHERE daily_goal_words IS NULL OR daily_goal_words <= 0
        """,
        (DEFAULT_DAILY_GOAL_WORDS,),
    )
    connection.execute(
        """
        UPDATE users
        SET daily_goal_sessions = ?
        WHERE daily_goal_sessions IS NULL OR daily_goal_sessions <= 0
        """,
        (DEFAULT_DAILY_GOAL_SESSIONS,),
    )
    connection.execute(
        """
        UPDATE users
        SET assessment_completed = CASE
            WHEN calibrated_level IS NOT NULL AND calibrated_level != '' THEN 1
            ELSE assessment_completed
        END
        """
    )

    _ensure_column(
        connection,
        table_name="game_sessions",
        column_name="learning_session_id",
        definition="INTEGER",
    )
    _ensure_column(
        connection,
        table_name="game_sessions",
        column_name="practice_mode",
        definition="TEXT NOT NULL DEFAULT 'standard'",
    )
    _ensure_column(
        connection,
        table_name="game_sessions",
        column_name="situation",
        definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="game_sessions",
        column_name="attempts_used",
        definition="INTEGER NOT NULL DEFAULT 0",
    )
    _ensure_column(
        connection,
        table_name="game_sessions",
        column_name="letters_correct",
        definition="INTEGER NOT NULL DEFAULT 0",
    )
    _ensure_column(
        connection,
        table_name="game_sessions",
        column_name="letters_wrong",
        definition="INTEGER NOT NULL DEFAULT 0",
    )
    _ensure_column(
        connection,
        table_name="game_sessions",
        column_name="guessed_letters",
        definition="TEXT NOT NULL DEFAULT ''",
    )
    _ensure_column(
        connection,
        table_name="game_sessions",
        column_name="hints_used",
        definition="INTEGER NOT NULL DEFAULT 0",
    )
    _ensure_column(
        connection,
        table_name="game_sessions",
        column_name="time_taken_seconds",
        definition="REAL",
    )
    _ensure_column(
        connection,
        table_name="game_sessions",
        column_name="played_at",
        definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="words",
        column_name="word_bank_id",
        definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="words",
        column_name="meaning",
        definition="TEXT NOT NULL DEFAULT ''",
    )
    _ensure_column(
        connection,
        table_name="words",
        column_name="situations",
        definition="TEXT NOT NULL DEFAULT '[]'",
    )
    _ensure_column(
        connection,
        table_name="words",
        column_name="sentence_translation",
        definition="TEXT NOT NULL DEFAULT ''",
    )
    _ensure_column(
        connection,
        table_name="words",
        column_name="pronunciation_text",
        definition="TEXT NOT NULL DEFAULT ''",
    )
    _ensure_column(
        connection,
        table_name="words",
        column_name="usage_note",
        definition="TEXT NOT NULL DEFAULT ''",
    )
    _ensure_column(
        connection,
        table_name="words",
        column_name="synonym",
        definition="TEXT NOT NULL DEFAULT ''",
    )
    _ensure_column(
        connection,
        table_name="words",
        column_name="association",
        definition="TEXT NOT NULL DEFAULT ''",
    )
    _ensure_column(
        connection,
        table_name="words",
        column_name="tags",
        definition="TEXT NOT NULL DEFAULT '[]'",
    )
    _ensure_column(
        connection,
        table_name="words",
        column_name="meaning_hint",
        definition="TEXT NOT NULL DEFAULT ''",
    )
    _ensure_column(
        connection,
        table_name="words",
        column_name="synonym_hint",
        definition="TEXT NOT NULL DEFAULT ''",
    )
    _ensure_column(
        connection,
        table_name="words",
        column_name="association_hint",
        definition="TEXT NOT NULL DEFAULT ''",
    )
    _ensure_column(
        connection,
        table_name="words",
        column_name="subcategory",
        definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="words",
        column_name="source",
        definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="words",
        column_name="notes",
        definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="words",
        column_name="source_file",
        definition="TEXT",
    )
    connection.execute(
        """
        UPDATE words
        SET tags = COALESCE(NULLIF(tags, ''), '[]')
        """
    )
    connection.execute(
        """
        UPDATE words
        SET
            word_bank_id = COALESCE(NULLIF(word_bank_id, ''), language || ':' || word),
            meaning = COALESCE(NULLIF(meaning, ''), translation),
            situations = COALESCE(NULLIF(situations, ''), '[]'),
            sentence_translation = COALESCE(NULLIF(sentence_translation, ''), translation),
            pronunciation_text = COALESCE(NULLIF(pronunciation_text, ''), word),
            usage_note = COALESCE(NULLIF(usage_note, ''), hint)
        """
    )
    connection.execute(
        """
        UPDATE words
        SET
            meaning_hint = COALESCE(NULLIF(meaning_hint, ''), hint),
            synonym_hint = COALESCE(NULLIF(synonym_hint, ''), synonym),
            association_hint = COALESCE(NULLIF(association_hint, ''), association)
        """
    )

    existing_learning_session_columns = _get_table_columns(connection, "learning_sessions")
    had_game_mode_column = "game_mode" in existing_learning_session_columns

    _ensure_column(
        connection,
        table_name="learning_sessions",
        column_name="language",
        definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="learning_sessions",
        column_name="selected_categories",
        definition="TEXT NOT NULL DEFAULT '[]'",
    )
    _ensure_column(
        connection,
        table_name="learning_sessions",
        column_name="difficulty_filter",
        definition="TEXT NOT NULL DEFAULT '[]'",
    )
    _ensure_column(
        connection,
        table_name="learning_sessions",
        column_name="situation",
        definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="learning_sessions",
        column_name="review_policy",
        definition="TEXT NOT NULL DEFAULT 'prefer_review'",
    )
    _ensure_column(
        connection,
        table_name="learning_sessions",
        column_name="show_hint_immediately",
        definition="INTEGER NOT NULL DEFAULT 1",
    )
    _ensure_column(
        connection,
        table_name="learning_sessions",
        column_name="game_mode",
        definition="TEXT NOT NULL DEFAULT 'easy'",
    )
    existing_game_mode_case = (
        "WHEN game_mode IN ('easy', 'hard') THEN game_mode" if had_game_mode_column else ""
    )
    connection.execute(
        f"""
        UPDATE learning_sessions
        SET
            language = COALESCE(NULLIF(language, ''), 'english'),
            selected_categories = COALESCE(NULLIF(selected_categories, ''), '[]'),
            difficulty_filter = COALESCE(NULLIF(difficulty_filter, ''), '[]'),
            review_policy = COALESCE(NULLIF(review_policy, ''), 'prefer_review'),
            show_hint_immediately = COALESCE(show_hint_immediately, 1),
            game_mode = CASE
                {existing_game_mode_case}
                WHEN COALESCE(show_hint_immediately, 1) = 0 THEN 'hard'
                ELSE 'easy'
            END
        """
    )
    existing_game_session_columns = _get_table_columns(connection, "game_sessions")
    update_fragments = []

    if "guesses_used" in existing_game_session_columns:
        update_fragments.append(
            """
            attempts_used = CASE
                WHEN attempts_used = 0 THEN COALESCE(guesses_used, 0)
                ELSE attempts_used
            END
            """
        )
    if "incorrect_guesses" in existing_game_session_columns:
        update_fragments.append(
            """
            letters_wrong = CASE
                WHEN letters_wrong = 0 THEN COALESCE(incorrect_guesses, 0)
                ELSE letters_wrong
            END
            """
        )

    update_fragments.append("guessed_letters = COALESCE(guessed_letters, '')")

    if (
        "completed_at" in existing_game_session_columns
        and "started_at" in existing_game_session_columns
    ):
        update_fragments.append(
            "played_at = COALESCE(played_at, completed_at, started_at, CURRENT_TIMESTAMP)"
        )
    else:
        update_fragments.append("played_at = COALESCE(played_at, CURRENT_TIMESTAMP)")

    update_fragments.append("practice_mode = COALESCE(NULLIF(practice_mode, ''), 'standard')")

    connection.execute(
        f"""
        UPDATE game_sessions
        SET {", ".join(update_fragments)}
        """
    )

    _ensure_column(
        connection,
        table_name="word_progress",
        column_name="mastery_status",
        definition="TEXT NOT NULL DEFAULT 'weak'",
    )
    _ensure_column(
        connection,
        table_name="word_progress",
        column_name="mastery_score",
        definition="REAL NOT NULL DEFAULT 0",
    )
    _ensure_column(
        connection,
        table_name="word_progress",
        column_name="attempt_count",
        definition="INTEGER NOT NULL DEFAULT 0",
    )
    _ensure_column(
        connection,
        table_name="word_progress",
        column_name="last_seen_date",
        definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="word_progress",
        column_name="total_wrong_guesses",
        definition="INTEGER NOT NULL DEFAULT 0",
    )
    _ensure_column(
        connection,
        table_name="word_progress",
        column_name="total_hints_used",
        definition="INTEGER NOT NULL DEFAULT 0",
    )
    connection.execute(
        """
        UPDATE word_progress
        SET mastery_score = CASE
            WHEN COALESCE(mastery_score, 0) > 0 THEN mastery_score
            WHEN familiarity_status = 'strong' THEN 85
            WHEN familiarity_status = 'familiar' THEN 65
            WHEN familiarity_status = 'learning' THEN 35
            ELSE 15
        END
        """
    )
    connection.execute(
        """
        UPDATE word_progress
        SET
            mastery_status = CASE
                WHEN mastery_score <= 30 THEN 'weak'
                WHEN mastery_score <= 70 THEN 'learning'
                WHEN mastery_score <= 90 THEN 'almost_mastered'
                ELSE 'mastered'
            END,
            attempt_count = CASE
                WHEN attempt_count <= 0 THEN COALESCE(times_seen, 0)
                ELSE attempt_count
            END,
            last_seen_date = COALESCE(NULLIF(last_seen_date, ''), last_played_at),
            total_wrong_guesses = CASE
                WHEN total_wrong_guesses <= 0 THEN COALESCE(total_wrong_letters, 0)
                ELSE total_wrong_guesses
            END
        """
    )

    if _performance_summary_needs_rebuild(connection):
        _rebuild_performance_summary_table(connection)


def _ensure_indexes(connection: sqlite3.Connection) -> None:
    """Create indexes after migrations have ensured the necessary columns exist."""
    connection.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_words_lookup
        ON words(language, category, difficulty);

        CREATE INDEX IF NOT EXISTS idx_words_situations
        ON words(language, situations);

        CREATE INDEX IF NOT EXISTS idx_game_sessions_user
        ON game_sessions(user_id, played_at);

        CREATE INDEX IF NOT EXISTS idx_game_sessions_learning_session
        ON game_sessions(learning_session_id, played_at);

        CREATE INDEX IF NOT EXISTS idx_learning_sessions_user
        ON learning_sessions(user_id, started_at);

        CREATE INDEX IF NOT EXISTS idx_review_queue_user_due
        ON review_queue(user_id, language, is_active, review_due_at);

        CREATE INDEX IF NOT EXISTS idx_word_progress_user
        ON word_progress(user_id, language, familiarity_status, priority_score);

        CREATE INDEX IF NOT EXISTS idx_performance_summary_user
        ON performance_summary(user_id, language, category);
        """
    )


def _ensure_column(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
    definition: str,
) -> None:
    """Add a missing column to an existing table."""
    existing_columns = _get_table_columns(connection, table_name)
    if column_name not in existing_columns:
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def _get_table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    """Return the set of column names for a table."""
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def _performance_summary_needs_rebuild(connection: sqlite3.Connection) -> bool:
    """Return whether the performance summary table still uses the older schema."""
    expected_columns = {
        "id",
        "user_id",
        "language",
        "category",
        "total_games",
        "wins",
        "losses",
        "accuracy",
        "avg_attempts",
        "mastery_score",
        "last_played_at",
        "updated_at",
    }
    current_columns = _get_table_columns(connection, "performance_summary")
    return current_columns != expected_columns


def _rebuild_performance_summary_table(connection: sqlite3.Connection) -> None:
    """Recreate the performance summary table with the current schema."""
    current_columns = _get_table_columns(connection, "performance_summary")
    if current_columns:
        connection.execute("ALTER TABLE performance_summary RENAME TO performance_summary_legacy")

    connection.execute(
        """
        CREATE TABLE performance_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            language TEXT NOT NULL,
            category TEXT NOT NULL,
            total_games INTEGER NOT NULL DEFAULT 0,
            wins INTEGER NOT NULL DEFAULT 0,
            losses INTEGER NOT NULL DEFAULT 0,
            accuracy REAL NOT NULL DEFAULT 0,
            avg_attempts REAL NOT NULL DEFAULT 0,
            mastery_score REAL NOT NULL DEFAULT 0,
            last_played_at TEXT,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, language, category)
        )
        """
    )

    legacy_columns = _get_table_columns(connection, "performance_summary_legacy")
    if legacy_columns:
        connection.execute("DROP TABLE performance_summary_legacy")


def _seed_words_table(connection: sqlite3.Connection, words_dir: Path) -> None:
    """Load words from JSON files into the database."""
    seed_payload = build_seed_rows(words_dir)
    rows = seed_payload["rows"]
    if rows:
        connection.executemany(WORD_INSERT_SQL, rows)
