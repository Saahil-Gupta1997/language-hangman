"""Repository helpers for data access."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Sequence

from src.db.database import WORD_INSERT_SQL, create_connection
from src.utils.config import DATABASE_PATH
from src.utils.constants import DEFAULT_DAILY_GOAL_SESSIONS, DEFAULT_DAILY_GOAL_WORDS
from src.utils.helpers import utc_now_iso


class BaseRepository:
    """Minimal repository wrapper around SQLite connections."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = Path(db_path or DATABASE_PATH)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Yield a database connection that auto-closes after use."""
        connection = create_connection(self.db_path)
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def fetchall(self, query: str, params: Sequence[object] = ()) -> list[sqlite3.Row]:
        """Return all rows for a query."""
        with self.connection() as connection:
            return list(connection.execute(query, params).fetchall())

    def fetchone(self, query: str, params: Sequence[object] = ()) -> sqlite3.Row | None:
        """Return the first row for a query or None."""
        with self.connection() as connection:
            return connection.execute(query, params).fetchone()

    def execute(self, query: str, params: Sequence[object] = ()) -> None:
        """Execute a write query."""
        with self.connection() as connection:
            connection.execute(query, params)

    def execute_returning_id(self, query: str, params: Sequence[object] = ()) -> int:
        """Execute a write query and return the inserted row id."""
        with self.connection() as connection:
            cursor = connection.execute(query, params)
            return int(cursor.lastrowid)

    def executemany(self, query: str, params: Sequence[Sequence[object]]) -> None:
        """Execute a query for multiple parameter sets."""
        with self.connection() as connection:
            connection.executemany(query, params)


class UserRepository(BaseRepository):
    """Data access methods for local user profiles."""

    def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        target_language: str,
        level: str,
        preferred_categories: str,
        last_builder_settings: str,
        daily_goal_words: int = DEFAULT_DAILY_GOAL_WORDS,
        daily_goal_sessions: int = DEFAULT_DAILY_GOAL_SESSIONS,
    ) -> int:
        """Insert a new user and return its database id."""
        return self.execute_returning_id(
            """
            INSERT INTO users (
                username,
                email,
                password_hash,
                target_language,
                level,
                preferred_categories,
                last_builder_settings,
                daily_goal_words,
                daily_goal_sessions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                email,
                password_hash,
                target_language,
                level,
                preferred_categories,
                last_builder_settings,
                int(daily_goal_words),
                int(daily_goal_sessions),
            ),
        )

    def get_by_username(self, username: str) -> sqlite3.Row | None:
        """Return a user row for a given username."""
        return self.fetchone(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        )

    def get_by_id(self, user_id: int) -> sqlite3.Row | None:
        """Return a user row for a given id."""
        return self.fetchone(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        )

    def update_preferences(
        self,
        user_id: int,
        target_language: str,
        level: str,
        preferred_categories: str,
    ) -> None:
        """Update the language, level, and preferred categories for a user."""
        self.execute(
            """
            UPDATE users
            SET
                target_language = ?,
                level = ?,
                preferred_categories = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (target_language, level, preferred_categories, user_id),
        )

    def update_last_builder_settings(self, user_id: int, last_builder_settings: str) -> None:
        """Persist the user's most recent custom-practice builder settings."""
        self.execute(
            """
            UPDATE users
            SET
                last_builder_settings = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (last_builder_settings, user_id),
        )

    def update_daily_goals(
        self,
        user_id: int,
        daily_goal_words: int,
        daily_goal_sessions: int,
    ) -> None:
        """Persist simple daily learning goals for a user."""
        self.execute(
            """
            UPDATE users
            SET
                daily_goal_words = ?,
                daily_goal_sessions = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (int(daily_goal_words), int(daily_goal_sessions), user_id),
        )

    def update_assessment_result(
        self,
        user_id: int,
        calibrated_level: str,
        assessment_completed: bool = True,
    ) -> None:
        """Persist the calibrated level after assessment."""
        self.execute(
            """
            UPDATE users
            SET
                calibrated_level = ?,
                assessment_completed = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (calibrated_level, int(assessment_completed), user_id),
        )


class WordRepository(BaseRepository):
    """Data access methods for seeded Hangman words."""

    def upsert_words(self, rows: Sequence[Sequence[object]]) -> None:
        """Insert or update normalized word rows."""
        if not rows:
            return
        self.executemany(WORD_INSERT_SQL, rows)

    def get_available_languages(self) -> list[sqlite3.Row]:
        """Return the languages available in the words table."""
        return self.fetchall("SELECT DISTINCT language FROM words ORDER BY language")

    def get_categories(self, language: str) -> list[sqlite3.Row]:
        """Return distinct categories for a language."""
        return self.fetchall(
            """
            SELECT DISTINCT category
            FROM words
            WHERE language = ?
            ORDER BY category
            """,
            (language,),
        )

    def get_difficulties(self, language: str) -> list[sqlite3.Row]:
        """Return distinct difficulty labels for a language."""
        return self.fetchall(
            """
            SELECT DISTINCT difficulty
            FROM words
            WHERE language = ?
            ORDER BY difficulty
            """,
            (language,),
        )

    def get_words(
        self,
        language: str,
        categories: Sequence[str] | None = None,
        difficulties: Sequence[str] | None = None,
        limit: int | None = None,
    ) -> list[sqlite3.Row]:
        """Return words filtered by language, categories, and difficulties."""
        query = [
            """
            SELECT
                id,
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
            FROM words
            WHERE language = ?
            """
        ]
        params: list[object] = [language]

        if categories:
            placeholders = ", ".join("?" for _ in categories)
            query.append(f"AND category IN ({placeholders})")
            params.extend(categories)

        if difficulties:
            placeholders = ", ".join("?" for _ in difficulties)
            query.append(f"AND difficulty IN ({placeholders})")
            params.extend(difficulties)

        query.append("ORDER BY word")
        if limit is not None:
            query.append("LIMIT ?")
            params.append(limit)
        return self.fetchall(" ".join(query), params)

    def get_words_by_ids(self, word_ids: Sequence[int]) -> list[sqlite3.Row]:
        """Return word rows for the provided ids while preserving input order."""
        normalized_ids = [int(word_id) for word_id in word_ids]
        if not normalized_ids:
            return []

        placeholders = ", ".join("?" for _ in normalized_ids)
        rows = self.fetchall(
            f"""
            SELECT
                id,
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
            FROM words
            WHERE id IN ({placeholders})
            """,
            normalized_ids,
        )
        rows_by_id = {int(row["id"]): row for row in rows}
        return [rows_by_id[word_id] for word_id in normalized_ids if word_id in rows_by_id]

    def get_word_by_id(self, word_id: int) -> sqlite3.Row | None:
        """Return one word row by id."""
        return self.fetchone(
            """
            SELECT
                id,
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
            FROM words
            WHERE id = ?
            """,
            (word_id,),
        )

    def get_counts_by_language(self) -> list[sqlite3.Row]:
        """Return total words grouped by language."""
        return self.fetchall(
            """
            SELECT language, COUNT(*) AS word_count
            FROM words
            GROUP BY language
            ORDER BY language
            """
        )

    def get_counts_by_category(self, language: str | None = None) -> list[sqlite3.Row]:
        """Return total words grouped by category."""
        query = [
            """
            SELECT category, COUNT(*) AS word_count
            FROM words
            WHERE 1 = 1
            """
        ]
        params: list[object] = []
        if language:
            query.append("AND language = ?")
            params.append(language)
        query.append("GROUP BY category ORDER BY category")
        return self.fetchall(" ".join(query), params)

    def get_counts_by_difficulty(self, language: str | None = None) -> list[sqlite3.Row]:
        """Return total words grouped by difficulty."""
        query = [
            """
            SELECT difficulty, COUNT(*) AS word_count
            FROM words
            WHERE 1 = 1
            """
        ]
        params: list[object] = []
        if language:
            query.append("AND language = ?")
            params.append(language)
        query.append("GROUP BY difficulty ORDER BY difficulty")
        return self.fetchall(" ".join(query), params)


class LearningSessionRepository(BaseRepository):
    """Data access methods for multi-round learning sessions."""

    def create_learning_session(
        self,
        user_id: int,
        language: str,
        practice_mode: str,
        planned_rounds: int,
        selected_category: str | None,
        selected_categories: str,
        difficulty_filter: str,
        review_policy: str,
        show_hint_immediately: bool,
        started_at: str,
        game_mode: str = "easy",
        situation: str | None = None,
    ) -> int:
        """Insert a new learning session and return its id."""
        return self.execute_returning_id(
            """
            INSERT INTO learning_sessions (
                user_id,
                language,
                practice_mode,
                planned_rounds,
                selected_category,
                selected_categories,
                difficulty_filter,
                situation,
                review_policy,
                show_hint_immediately,
                game_mode,
                started_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                language,
                practice_mode,
                planned_rounds,
                selected_category,
                selected_categories,
                difficulty_filter,
                situation,
                review_policy,
                int(show_hint_immediately),
                game_mode,
                started_at,
            ),
        )

    def update_learning_session(
        self,
        session_id: int,
        completed_rounds: int,
        wins: int,
        losses: int,
        accuracy: float,
        categories_practiced: str,
        words_practiced: str,
        status: str,
        recommendation: str | None,
        completed_at: str | None,
    ) -> None:
        """Persist the latest progress for a learning session."""
        self.execute(
            """
            UPDATE learning_sessions
            SET
                completed_rounds = ?,
                wins = ?,
                losses = ?,
                accuracy = ?,
                categories_practiced = ?,
                words_practiced = ?,
                status = ?,
                recommendation = ?,
                completed_at = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                completed_rounds,
                wins,
                losses,
                accuracy,
                categories_practiced,
                words_practiced,
                status,
                recommendation,
                completed_at,
                session_id,
            ),
        )

    def get_by_id(self, session_id: int) -> sqlite3.Row | None:
        """Return a learning session by id."""
        return self.fetchone(
            "SELECT * FROM learning_sessions WHERE id = ?",
            (session_id,),
        )

    def get_recent_sessions(
        self,
        user_id: int,
        limit: int = 5,
        language: str | None = None,
        started_after: str | None = None,
    ) -> list[sqlite3.Row]:
        """Return recent multi-round learning sessions for a user."""
        query = [
            """
            SELECT
                id,
                language,
                practice_mode,
                planned_rounds,
                selected_category,
                selected_categories,
                difficulty_filter,
                situation,
                review_policy,
                show_hint_immediately,
                game_mode,
                completed_rounds,
                wins,
                losses,
                accuracy,
                categories_practiced,
                words_practiced,
                status,
                recommendation,
                started_at,
                completed_at
            FROM learning_sessions
            WHERE user_id = ?
            """
        ]
        params: list[object] = [user_id]
        if language:
            query.append("AND language = ?")
            params.append(language)
        if started_after:
            query.append("AND COALESCE(completed_at, started_at) >= ?")
            params.append(started_after)
        query.append("ORDER BY COALESCE(completed_at, started_at) DESC LIMIT ?")
        params.append(limit)
        return self.fetchall(" ".join(query), params)

    def get_session_history_summary(
        self,
        user_id: int,
        language: str | None = None,
        started_after: str | None = None,
    ) -> sqlite3.Row | None:
        """Return summary stats for a user's learning sessions."""
        query = [
            """
            SELECT
                COUNT(*) AS total_sessions,
                SUM(completed_rounds) AS total_rounds,
                AVG(accuracy) AS avg_accuracy,
                MAX(COALESCE(completed_at, started_at)) AS last_session_at
            FROM learning_sessions
            WHERE user_id = ?
            """
        ]
        params: list[object] = [user_id]
        if language:
            query.append("AND language = ?")
            params.append(language)
        if started_after:
            query.append("AND COALESCE(completed_at, started_at) >= ?")
            params.append(started_after)
        return self.fetchone(" ".join(query), params)

    def get_completed_session_count_since(
        self,
        user_id: int,
        language: str | None = None,
        started_after: str | None = None,
    ) -> int:
        """Return completed learning sessions since a timestamp."""
        query = [
            """
            SELECT COUNT(*) AS completed_sessions
            FROM learning_sessions
            WHERE user_id = ?
              AND status = 'completed'
            """
        ]
        params: list[object] = [user_id]
        if language:
            query.append("AND language = ?")
            params.append(language)
        if started_after:
            query.append("AND COALESCE(completed_at, started_at) >= ?")
            params.append(started_after)
        row = self.fetchone(" ".join(query), params)
        return int((row["completed_sessions"] if row else 0) or 0)


class GameSessionRepository(BaseRepository):
    """Data access methods for played Hangman rounds."""

    def create_session(
        self,
        user_id: int,
        word_id: int,
        language: str,
        level: str,
        category: str,
        result: str,
        attempts_used: int,
        max_attempts: int,
        letters_correct: int,
        letters_wrong: int,
        guessed_letters: str,
        time_taken_seconds: float | None,
        started_at: str,
        completed_at: str | None,
        played_at: str,
        practice_mode: str = "standard",
        learning_session_id: int | None = None,
        situation: str | None = None,
        hints_used: int = 0,
    ) -> int:
        """Insert a finished game session and return its id."""
        return self.execute_returning_id(
            """
            INSERT INTO game_sessions (
                user_id,
                learning_session_id,
                word_id,
                language,
                situation,
                level,
                category,
                practice_mode,
                result,
                attempts_used,
                max_attempts,
                letters_correct,
                letters_wrong,
                guessed_letters,
                hints_used,
                time_taken_seconds,
                started_at,
                completed_at,
                played_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                learning_session_id,
                word_id,
                language,
                situation,
                level,
                category,
                practice_mode,
                result,
                attempts_used,
                max_attempts,
                letters_correct,
                letters_wrong,
                guessed_letters,
                hints_used,
                time_taken_seconds,
                started_at,
                completed_at,
                played_at,
            ),
        )

    def get_overview(
        self,
        user_id: int,
        language: str | None = None,
        played_after: str | None = None,
    ) -> sqlite3.Row | None:
        """Return total games, wins, and losses for a user."""
        query = [
            """
            SELECT
                COUNT(*) AS total_games,
                SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN result = 'lost' THEN 1 ELSE 0 END) AS losses
            FROM game_sessions
            WHERE user_id = ?
            """
        ]
        params: list[object] = [user_id]

        if language:
            query.append("AND language = ?")
            params.append(language)
        if played_after:
            query.append("AND played_at >= ?")
            params.append(played_after)

        return self.fetchone(" ".join(query), params)

    def get_distinct_word_count(
        self,
        user_id: int,
        language: str | None = None,
        played_after: str | None = None,
    ) -> int:
        """Return the number of unique words a learner has practiced."""
        query = [
            """
            SELECT COUNT(DISTINCT word_id) AS distinct_words
            FROM game_sessions
            WHERE user_id = ?
            """
        ]
        params: list[object] = [user_id]
        if language:
            query.append("AND language = ?")
            params.append(language)
        if played_after:
            query.append("AND played_at >= ?")
            params.append(played_after)
        row = self.fetchone(" ".join(query), params)
        return int((row["distinct_words"] if row else 0) or 0)

    def get_category_aggregates(
        self,
        user_id: int,
        language: str | None = None,
        played_after: str | None = None,
    ) -> list[sqlite3.Row]:
        """Return aggregate session metrics grouped by language and category."""
        query = [
            """
            SELECT
                language,
                category,
                COUNT(*) AS total_games,
                SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN result = 'lost' THEN 1 ELSE 0 END) AS losses,
                AVG(attempts_used) AS avg_attempts,
                SUM(letters_correct) AS total_correct_letters,
                SUM(letters_wrong) AS total_wrong_letters,
                MAX(played_at) AS last_played_at
            FROM game_sessions
            WHERE user_id = ?
            """
        ]
        params: list[object] = [user_id]

        if language:
            query.append("AND language = ?")
            params.append(language)
        if played_after:
            query.append("AND played_at >= ?")
            params.append(played_after)

        query.append("GROUP BY language, category ORDER BY category")
        return self.fetchall(" ".join(query), params)

    def get_practice_mode_aggregates(
        self,
        user_id: int,
        language: str | None = None,
        played_after: str | None = None,
    ) -> list[sqlite3.Row]:
        """Return aggregate stats grouped by practice mode."""
        query = [
            """
            SELECT
                practice_mode,
                COUNT(*) AS total_games,
                SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN result = 'lost' THEN 1 ELSE 0 END) AS losses
            FROM game_sessions
            WHERE user_id = ?
            """
        ]
        params: list[object] = [user_id]
        if language:
            query.append("AND language = ?")
            params.append(language)
        if played_after:
            query.append("AND played_at >= ?")
            params.append(played_after)
        query.append("GROUP BY practice_mode ORDER BY practice_mode")
        return self.fetchall(" ".join(query), params)

    def get_situation_aggregates(
        self,
        user_id: int,
        language: str | None = None,
        played_after: str | None = None,
    ) -> list[sqlite3.Row]:
        """Return aggregate round metrics grouped by real-world situation."""
        query = [
            """
            SELECT
                language,
                COALESCE(NULLIF(situation, ''), 'unspecified') AS situation,
                COUNT(*) AS total_games,
                SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN result = 'lost' THEN 1 ELSE 0 END) AS losses,
                AVG(attempts_used) AS avg_attempts,
                SUM(letters_correct) AS total_correct_letters,
                SUM(letters_wrong) AS total_wrong_letters,
                AVG(hints_used) AS avg_hints_used,
                MAX(played_at) AS last_played_at
            FROM game_sessions
            WHERE user_id = ?
            """
        ]
        params: list[object] = [user_id]

        if language:
            query.append("AND language = ?")
            params.append(language)
        if played_after:
            query.append("AND played_at >= ?")
            params.append(played_after)

        query.append("GROUP BY language, situation ORDER BY situation")
        return self.fetchall(" ".join(query), params)

    def get_recent_word_ids(
        self,
        user_id: int,
        limit: int = 10,
        language: str | None = None,
    ) -> list[int]:
        """Return recently used word ids for a user."""
        query = [
            """
            SELECT word_id
            FROM game_sessions
            WHERE user_id = ?
            """
        ]
        params: list[object] = [user_id]

        if language:
            query.append("AND language = ?")
            params.append(language)

        query.append("ORDER BY played_at DESC LIMIT ?")
        params.append(limit)
        rows = self.fetchall(" ".join(query), params)
        return [int(row["word_id"]) for row in rows]

    def get_seen_word_ids(self, user_id: int, language: str | None = None) -> list[int]:
        """Return distinct word ids the learner has already seen."""
        query = [
            """
            SELECT DISTINCT word_id
            FROM game_sessions
            WHERE user_id = ?
            """
        ]
        params: list[object] = [user_id]
        if language:
            query.append("AND language = ?")
            params.append(language)
        rows = self.fetchall(" ".join(query), params)
        return [int(row["word_id"]) for row in rows]

    def get_recent_sessions(
        self,
        user_id: int,
        limit: int = 5,
        language: str | None = None,
        played_after: str | None = None,
    ) -> list[sqlite3.Row]:
        """Return recent rounds joined with word details."""
        query = [
            """
            SELECT
                game_sessions.id,
                game_sessions.learning_session_id,
                game_sessions.practice_mode,
                game_sessions.word_id,
                game_sessions.language,
                game_sessions.situation,
                game_sessions.level,
                game_sessions.category,
                game_sessions.result,
                game_sessions.attempts_used,
                game_sessions.max_attempts,
                game_sessions.letters_correct,
                game_sessions.letters_wrong,
                game_sessions.hints_used,
                game_sessions.guessed_letters,
                game_sessions.played_at,
                words.word,
                words.meaning,
                words.situations,
                words.translation,
                words.example_sentence,
                words.sentence_translation,
                words.pronunciation_text,
                words.usage_note,
                words.synonym,
                words.association,
                words.difficulty,
                words.hint,
                words.tags,
                words.subcategory,
                words.source
            FROM game_sessions
            INNER JOIN words ON words.id = game_sessions.word_id
            WHERE game_sessions.user_id = ?
            """
        ]
        params: list[object] = [user_id]

        if language:
            query.append("AND game_sessions.language = ?")
            params.append(language)
        if played_after:
            query.append("AND game_sessions.played_at >= ?")
            params.append(played_after)

        query.append("ORDER BY game_sessions.played_at DESC LIMIT ?")
        params.append(limit)
        return self.fetchall(" ".join(query), params)

    def get_distinct_won_word_ids(
        self,
        user_id: int,
        language: str | None = None,
        played_after: str | None = None,
    ) -> list[int]:
        """Return distinct word ids the learner has successfully completed."""
        query = [
            """
            SELECT DISTINCT word_id
            FROM game_sessions
            WHERE user_id = ? AND result = 'won'
            """
        ]
        params: list[object] = [user_id]

        if language:
            query.append("AND language = ?")
            params.append(language)
        if played_after:
            query.append("AND played_at >= ?")
            params.append(played_after)

        rows = self.fetchall(" ".join(query), params)
        return [int(row["word_id"]) for row in rows]

    def get_daily_activity(
        self,
        user_id: int,
        language: str | None = None,
        played_after: str | None = None,
        limit: int = 14,
    ) -> list[sqlite3.Row]:
        """Return recent day-by-day activity aggregates for a user."""
        query = [
            """
            SELECT
                substr(played_at, 1, 10) AS played_day,
                COUNT(*) AS total_rounds,
                SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN result = 'lost' THEN 1 ELSE 0 END) AS losses,
                SUM(letters_correct) AS total_correct_letters,
                SUM(letters_wrong) AS total_wrong_letters
            FROM game_sessions
            WHERE user_id = ?
            """
        ]
        params: list[object] = [user_id]

        if language:
            query.append("AND language = ?")
            params.append(language)
        if played_after:
            query.append("AND played_at >= ?")
            params.append(played_after)

        query.append(
            """
            GROUP BY substr(played_at, 1, 10)
            ORDER BY played_day DESC
            LIMIT ?
            """
        )
        params.append(limit)
        return self.fetchall(" ".join(query), params)

    def get_play_dates(
        self,
        user_id: int,
        language: str | None = None,
        played_after: str | None = None,
    ) -> list[str]:
        """Return distinct play dates for streak calculations."""
        query = [
            """
            SELECT DISTINCT substr(played_at, 1, 10) AS played_day
            FROM game_sessions
            WHERE user_id = ?
            """
        ]
        params: list[object] = [user_id]

        if language:
            query.append("AND language = ?")
            params.append(language)
        if played_after:
            query.append("AND played_at >= ?")
            params.append(played_after)

        query.append("ORDER BY played_day ASC")
        rows = self.fetchall(" ".join(query), params)
        return [str(row["played_day"]) for row in rows if row["played_day"]]


class ReviewQueueRepository(BaseRepository):
    """Data access helpers for spaced review items."""

    def upsert_review_item(
        self,
        user_id: int,
        word_id: int,
        language: str,
        category: str,
        priority_score: float,
        review_due_at: str,
        last_reviewed_at: str,
        last_result: str,
        last_accuracy: float,
        is_active: bool,
    ) -> None:
        """Insert or update one review queue item."""
        self.execute(
            """
            INSERT INTO review_queue (
                user_id,
                word_id,
                language,
                category,
                priority_score,
                review_due_at,
                review_count,
                last_reviewed_at,
                last_result,
                last_accuracy,
                is_active
            ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
            ON CONFLICT(user_id, word_id) DO UPDATE SET
                language = excluded.language,
                category = excluded.category,
                priority_score = excluded.priority_score,
                review_due_at = excluded.review_due_at,
                review_count = review_queue.review_count + 1,
                last_reviewed_at = excluded.last_reviewed_at,
                last_result = excluded.last_result,
                last_accuracy = excluded.last_accuracy,
                is_active = excluded.is_active,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                word_id,
                language,
                category,
                priority_score,
                review_due_at,
                last_reviewed_at,
                last_result,
                last_accuracy,
                int(is_active),
            ),
        )

    def get_item(self, user_id: int, word_id: int) -> sqlite3.Row | None:
        """Return one review item for a user and word id."""
        return self.fetchone(
            """
            SELECT *
            FROM review_queue
            WHERE user_id = ? AND word_id = ?
            """,
            (user_id, word_id),
        )

    def get_due_items(
        self,
        user_id: int,
        language: str,
        limit: int = 10,
        category: str | None = None,
        due_at: str | None = None,
    ) -> list[sqlite3.Row]:
        """Return active review items that are due now."""
        query = [
            """
            SELECT *
            FROM review_queue
            WHERE user_id = ?
              AND language = ?
              AND is_active = 1
              AND review_due_at <= ?
            """
        ]
        params: list[object] = [user_id, language, due_at or utc_now_iso()]

        if category:
            query.append("AND category = ?")
            params.append(category)

        query.append("ORDER BY priority_score DESC, review_due_at ASC LIMIT ?")
        params.append(limit)
        return self.fetchall(" ".join(query), params)

    def get_active_items(
        self,
        user_id: int,
        language: str | None = None,
        limit: int = 10,
        category: str | None = None,
    ) -> list[sqlite3.Row]:
        """Return active review items ordered by priority."""
        query = [
            """
            SELECT *
            FROM review_queue
            WHERE user_id = ?
              AND is_active = 1
            """
        ]
        params: list[object] = [user_id]

        if language:
            query.append("AND language = ?")
            params.append(language)

        if category:
            query.append("AND category = ?")
            params.append(category)

        query.append("ORDER BY priority_score DESC, review_due_at ASC LIMIT ?")
        params.append(limit)
        return self.fetchall(" ".join(query), params)

    def get_active_word_ids(self, user_id: int, language: str | None = None) -> list[int]:
        """Return active review word ids for a user."""
        query = [
            """
            SELECT word_id
            FROM review_queue
            WHERE user_id = ? AND is_active = 1
            """
        ]
        params: list[object] = [user_id]

        if language:
            query.append("AND language = ?")
            params.append(language)

        rows = self.fetchall(" ".join(query), params)
        return [int(row["word_id"]) for row in rows]

    def get_summary_counts(
        self,
        user_id: int,
        language: str | None = None,
        due_at: str | None = None,
    ) -> sqlite3.Row | None:
        """Return active and due review counts for a user."""
        query = [
            """
            SELECT
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS active_count,
                SUM(
                    CASE
                        WHEN is_active = 1 AND review_due_at <= ? THEN 1
                        ELSE 0
                    END
                ) AS due_count
            FROM review_queue
            WHERE user_id = ?
            """
        ]
        params: list[object] = [due_at or utc_now_iso(), user_id]

        if language:
            query.append("AND language = ?")
            params.append(language)

        return self.fetchone(" ".join(query), params)


class WordProgressRepository(BaseRepository):
    """Data access helpers for word-level mastery tracking."""

    def upsert_progress(
        self,
        user_id: int,
        word_id: int,
        language: str,
        familiarity_status: str,
        mastery_score: float,
        wins_delta: int,
        losses_delta: int,
        successful_streak: int,
        correct_letters_delta: int,
        wrong_letters_delta: int,
        last_accuracy: float,
        last_result: str,
        priority_score: float,
        last_played_at: str,
        mastery_status: str = "weak",
        wrong_guesses_delta: int = 0,
        hints_used_delta: int = 0,
    ) -> None:
        """Insert or update word-level progress for a learner."""
        if mastery_status == "weak" and mastery_score > 30:
            if mastery_score <= 70:
                mastery_status = "learning"
            elif mastery_score <= 90:
                mastery_status = "almost_mastered"
            else:
                mastery_status = "mastered"
        self.execute(
            """
            INSERT INTO word_progress (
                user_id,
                word_id,
                language,
                familiarity_status,
                mastery_status,
                mastery_score,
                times_seen,
                attempt_count,
                wins,
                losses,
                successful_streak,
                total_correct_letters,
                total_wrong_letters,
                total_wrong_guesses,
                total_hints_used,
                last_accuracy,
                last_result,
                priority_score,
                last_played_at,
                last_seen_date
            ) VALUES (?, ?, ?, ?, ?, ?, 1, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, word_id) DO UPDATE SET
                language = excluded.language,
                familiarity_status = excluded.familiarity_status,
                mastery_status = excluded.mastery_status,
                mastery_score = excluded.mastery_score,
                times_seen = word_progress.times_seen + 1,
                attempt_count = word_progress.attempt_count + 1,
                wins = word_progress.wins + excluded.wins,
                losses = word_progress.losses + excluded.losses,
                successful_streak = excluded.successful_streak,
                total_correct_letters = (
                    word_progress.total_correct_letters
                    + excluded.total_correct_letters
                ),
                total_wrong_letters = (
                    word_progress.total_wrong_letters
                    + excluded.total_wrong_letters
                ),
                total_wrong_guesses = (
                    word_progress.total_wrong_guesses
                    + excluded.total_wrong_guesses
                ),
                total_hints_used = (
                    word_progress.total_hints_used
                    + excluded.total_hints_used
                ),
                last_accuracy = excluded.last_accuracy,
                last_result = excluded.last_result,
                priority_score = excluded.priority_score,
                last_played_at = excluded.last_played_at,
                last_seen_date = excluded.last_seen_date,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                word_id,
                language,
                familiarity_status,
                mastery_status,
                mastery_score,
                wins_delta,
                losses_delta,
                successful_streak,
                correct_letters_delta,
                wrong_letters_delta,
                wrong_guesses_delta,
                hints_used_delta,
                last_accuracy,
                last_result,
                priority_score,
                last_played_at,
                last_played_at,
            ),
        )

    def get_item(self, user_id: int, word_id: int) -> sqlite3.Row | None:
        """Return one word-progress record for a user and word."""
        return self.fetchone(
            """
            SELECT *
            FROM word_progress
            WHERE user_id = ? AND word_id = ?
            """,
            (user_id, word_id),
        )

    def get_items(
        self,
        user_id: int,
        language: str | None = None,
        statuses: Sequence[str] | None = None,
        limit: int | None = None,
    ) -> list[sqlite3.Row]:
        """Return progress rows for a learner, optionally filtered by status."""
        query = [
            """
            SELECT *
            FROM word_progress
            WHERE user_id = ?
            """
        ]
        params: list[object] = [user_id]
        if language:
            query.append("AND language = ?")
            params.append(language)
        if statuses:
            placeholders = ", ".join("?" for _ in statuses)
            query.append(
                f"AND (familiarity_status IN ({placeholders}) "
                f"OR mastery_status IN ({placeholders}))"
            )
            params.extend(statuses)
            params.extend(statuses)
        query.append("ORDER BY priority_score DESC, last_played_at DESC")
        if limit is not None:
            query.append("LIMIT ?")
            params.append(limit)
        return self.fetchall(" ".join(query), params)

    def get_seen_word_ids(self, user_id: int, language: str | None = None) -> list[int]:
        """Return word ids that already have progress history."""
        query = [
            """
            SELECT word_id
            FROM word_progress
            WHERE user_id = ?
            """
        ]
        params: list[object] = [user_id]
        if language:
            query.append("AND language = ?")
            params.append(language)
        rows = self.fetchall(" ".join(query), params)
        return [int(row["word_id"]) for row in rows]

    def get_status_word_ids(
        self,
        user_id: int,
        language: str | None = None,
        statuses: Sequence[str] | None = None,
    ) -> list[int]:
        """Return word ids for one or more familiarity states."""
        rows = self.get_items(user_id=user_id, language=language, statuses=statuses)
        return [int(row["word_id"]) for row in rows]

    def get_category_progress_summary(
        self,
        user_id: int,
        language: str | None = None,
    ) -> list[sqlite3.Row]:
        """Return category-level word mastery summaries."""
        query = [
            """
            SELECT
                words.language,
                words.category,
                COUNT(*) AS tracked_words,
                AVG(word_progress.mastery_score) AS avg_mastery_score,
                SUM(
                    CASE
                        WHEN word_progress.familiarity_status = 'learning'
                          OR word_progress.mastery_status IN ('weak', 'learning')
                        THEN 1 ELSE 0
                    END
                ) AS learning_words,
                SUM(
                    CASE
                        WHEN word_progress.familiarity_status = 'familiar'
                        THEN 1 ELSE 0
                    END
                ) AS familiar_words,
                SUM(
                    CASE
                        WHEN word_progress.familiarity_status = 'strong'
                          OR word_progress.mastery_status = 'mastered'
                        THEN 1 ELSE 0
                    END
                ) AS strong_words,
                MAX(word_progress.last_played_at) AS last_played_at
            FROM word_progress
            INNER JOIN words ON words.id = word_progress.word_id
            WHERE word_progress.user_id = ?
            """
        ]
        params: list[object] = [user_id]
        if language:
            query.append("AND word_progress.language = ?")
            params.append(language)
        query.append("GROUP BY words.language, words.category ORDER BY words.category")
        return self.fetchall(" ".join(query), params)

    def get_summary_counts(self, user_id: int, language: str | None = None) -> sqlite3.Row | None:
        """Return count totals per familiarity state."""
        query = [
            """
            SELECT
                SUM(CASE WHEN familiarity_status = 'new' THEN 1 ELSE 0 END) AS new_count,
                SUM(CASE WHEN familiarity_status = 'learning' THEN 1 ELSE 0 END) AS learning_count,
                SUM(CASE WHEN familiarity_status = 'familiar' THEN 1 ELSE 0 END) AS familiar_count,
                SUM(CASE WHEN familiarity_status = 'strong' THEN 1 ELSE 0 END) AS strong_count,
                SUM(CASE WHEN mastery_status = 'weak' THEN 1 ELSE 0 END) AS weak_mastery_count,
                SUM(CASE WHEN mastery_status = 'learning' THEN 1 ELSE 0 END)
                    AS learning_mastery_count,
                SUM(CASE WHEN mastery_status = 'almost_mastered' THEN 1 ELSE 0 END)
                    AS almost_mastered_count,
                SUM(CASE WHEN mastery_status = 'mastered' THEN 1 ELSE 0 END)
                    AS mastered_count,
                AVG(mastery_score) AS avg_mastery_score
            FROM word_progress
            WHERE user_id = ?
            """
        ]
        params: list[object] = [user_id]
        if language:
            query.append("AND language = ?")
            params.append(language)
        return self.fetchone(" ".join(query), params)

    def get_low_mastery_items(
        self,
        user_id: int,
        language: str | None = None,
        situation: str | None = None,
        limit: int = 50,
    ) -> list[sqlite3.Row]:
        """Return low-mastery words, optionally constrained to a situation."""
        query = [
            """
            SELECT
                word_progress.*,
                words.word,
                words.category,
                words.difficulty,
                words.situations
            FROM word_progress
            INNER JOIN words ON words.id = word_progress.word_id
            WHERE word_progress.user_id = ?
              AND (
                word_progress.mastery_score <= 70
                OR word_progress.mastery_status IN ('weak', 'learning')
                OR word_progress.losses > 0
                OR word_progress.total_wrong_guesses >= 3
                OR word_progress.total_hints_used >= 2
              )
            """
        ]
        params: list[object] = [user_id]
        if language:
            query.append("AND word_progress.language = ?")
            params.append(language)
        if situation:
            query.append("AND words.situations LIKE ?")
            params.append(f'%"{situation}"%')
        query.append(
            """
            ORDER BY
                word_progress.mastery_score ASC,
                word_progress.priority_score DESC,
                word_progress.last_seen_date ASC
            LIMIT ?
            """
        )
        params.append(limit)
        return self.fetchall(" ".join(query), params)


class PerformanceSummaryRepository(BaseRepository):
    """Data access methods for category-based learner summaries."""

    def replace_user_summaries(
        self,
        user_id: int,
        summary_rows: Sequence[Sequence[object]],
    ) -> None:
        """Replace all summaries for a user."""
        with self.connection() as connection:
            connection.execute(
                "DELETE FROM performance_summary WHERE user_id = ?",
                (user_id,),
            )
            if summary_rows:
                connection.executemany(
                    """
                    INSERT INTO performance_summary (
                        user_id,
                        language,
                        category,
                        total_games,
                        wins,
                        losses,
                        accuracy,
                        avg_attempts,
                        mastery_score,
                        last_played_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    summary_rows,
                )

    def get_for_user(self, user_id: int, language: str | None = None) -> list[sqlite3.Row]:
        """Return the stored performance summaries for a user."""
        query = [
            """
            SELECT
                user_id,
                language,
                category,
                total_games,
                wins,
                losses,
                accuracy,
                avg_attempts,
                mastery_score,
                last_played_at,
                updated_at
            FROM performance_summary
            WHERE user_id = ?
            """
        ]
        params: list[object] = [user_id]

        if language:
            query.append("AND language = ?")
            params.append(language)

        query.append("ORDER BY category")
        return self.fetchall(" ".join(query), params)
