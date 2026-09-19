"""Local maintenance helpers for setup, content workflows, and release checks."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.db.database import create_connection, init_db
from src.services.report_service import ReportService
from src.services.word_service import WordService
from src.utils.config import (
    APP_VERSION,
    APP_VERSION_DISPLAY,
    DATABASE_PATH,
    PROJECT_ROOT,
    WORDS_DIR,
)
from src.utils.constants import (
    BACKUP_SCHEMA_VERSION,
    DEFAULT_DAILY_GOAL_SESSIONS,
    DEFAULT_DAILY_GOAL_WORDS,
)
from src.utils.helpers import utc_now_iso

ARTIFACT_DIRECTORY_NAMES = (
    "node_modules",
    "backups",
    ".venv",
    "__pycache__",
    ".idea",
    ".pytest_cache",
    ".pytest_tmp",
    ".ruff_cache",
    ".mypy_cache",
    "htmlcov",
    "build",
    "dist",
    "release",
)
ARTIFACT_DIRECTORY_PATTERNS = (
    "pytest_tmp*",
    "pytest-cache-files-*",
    "codex_pytest_tmp*",
)
ARTIFACT_FILE_PATHS = (
    ".coverage",
    ".streamlit/secrets.toml",
    "data/.desktop_login_handoff.json",
    "data/.session_secret",
)
ARTIFACT_FILE_PATTERNS = (
    "*.pyc",
    "*.sqlite",
    "*.sqlite3",
    "*.db",
    "*.zip",
)
EXPORT_TABLES = (
    "users",
    "learning_sessions",
    "game_sessions",
    "review_queue",
    "word_progress",
)


def _is_relative_to(path: Path, possible_parent: Path) -> bool:
    """Return whether path is inside possible_parent without raising ValueError."""
    try:
        path.relative_to(possible_parent)
    except ValueError:
        return False
    return True


class MaintenanceService:
    """Provides local setup, content, backup, and release-readiness helpers."""

    def __init__(
        self,
        *,
        project_root: Path | None = None,
        db_path: Path | None = None,
        words_dir: Path | None = None,
    ) -> None:
        self.project_root = Path(project_root or PROJECT_ROOT)
        self.db_path = Path(db_path or DATABASE_PATH)
        self.words_dir = Path(words_dir or WORDS_DIR)
        self.data_dir = self.db_path.parent
        self.word_service = WordService(words_dir=self.words_dir, db_path=self.db_path)

    def get_runtime_summary(self) -> dict[str, Any]:
        """Return the current runtime paths and content coverage."""
        validation_summary = self.validate_word_banks()
        fallback_languages = sorted(validation_summary["coverage"]["total_words_by_language"])
        database_total_words = 0
        database_languages: list[str] = []
        database_exists = self.db_path.exists()
        database_ready = False

        if database_exists:
            try:
                content_summary = self.word_service.get_content_summary()
                database_total_words = int(content_summary["total_words"])
                database_languages = sorted(
                    {
                        str(row["language"])
                        for row in content_summary["by_language"]
                        if row["language"]
                    }
                )
                database_ready = True
            except sqlite3.OperationalError:
                # The maintenance CLI should still work before the schema exists.
                database_ready = False

        return {
            "app_version": APP_VERSION,
            "app_version_display": APP_VERSION_DISPLAY,
            "project_root": str(self.project_root),
            "data_dir": str(self.data_dir),
            "database_path": str(self.db_path),
            "words_dir": str(self.words_dir),
            "database_exists": database_exists,
            "database_ready": database_ready,
            "database_total_words": database_total_words,
            "database_languages": database_languages,
            "word_bank_files": int(validation_summary["files_processed"]),
            "word_bank_valid_words": int(validation_summary["valid_words"]),
            "word_bank_invalid_words": int(validation_summary["invalid_words"]),
            "word_bank_duplicate_words": int(validation_summary["duplicate_words"]),
            "weak_coverage_areas": validation_summary["coverage"]["weak_coverage_areas"],
            "meets_minimum_content_coverage": validation_summary["coverage"][
                "meets_minimum_coverage"
            ],
            "total_words": database_total_words or int(validation_summary["valid_words"]),
            "languages": database_languages or fallback_languages,
            "content_source": "database" if database_total_words else "word_bank_files",
        }

    def validate_word_banks(self, *, include_rows: bool = False) -> dict[str, Any]:
        """Validate all word-bank files and return a scalable content summary."""
        return self.word_service.inspect_word_banks(include_rows=include_rows)

    def seed_word_banks(self) -> dict[str, Any]:
        """Ensure the database exists, then reload word banks into SQLite."""
        init_db(db_path=self.db_path, seed_words=False)
        import_summary = self.word_service.reload_word_banks()
        return {
            **import_summary,
            "database_path": str(self.db_path),
            "words_dir": str(self.words_dir),
        }

    def find_local_artifacts(self) -> dict[str, Any]:
        """Return local/dev artifacts that should stay out of a clean repo snapshot."""
        artifact_paths: set[Path] = set()

        for directory_name in ARTIFACT_DIRECTORY_NAMES:
            artifact_paths.update(
                path for path in self.project_root.rglob(directory_name) if path.is_dir()
            )

        for directory_pattern in ARTIFACT_DIRECTORY_PATTERNS:
            artifact_paths.update(
                path for path in self.project_root.rglob(directory_pattern) if path.is_dir()
            )

        for relative_path in ARTIFACT_FILE_PATHS:
            candidate_path = self.project_root / relative_path
            if candidate_path.exists():
                artifact_paths.add(candidate_path)

        for pattern in ARTIFACT_FILE_PATTERNS:
            artifact_paths.update(
                path for path in self.project_root.rglob(pattern) if path.is_file()
            )

        # Git's own data is never distributed; its refs for a branch named release/... would
        # otherwise match the "release" directory name (D-29).
        artifact_paths = {path for path in artifact_paths if not self._inside_git(path)}
        artifact_paths = self._collapse_nested_artifact_paths(artifact_paths)
        sorted_artifacts = sorted(str(path) for path in artifact_paths)
        return {
            "is_clean": not sorted_artifacts,
            "artifact_count": len(sorted_artifacts),
            "artifacts": sorted_artifacts,
            "relative_artifacts": self._build_relative_artifact_paths(artifact_paths),
        }

    def _inside_git(self, path: Path) -> bool:
        try:
            return ".git" in path.relative_to(self.project_root).parts
        except ValueError:
            return False

    def _collapse_nested_artifact_paths(self, artifact_paths: set[Path]) -> set[Path]:
        """Avoid noisy reports for files already covered by an artifact directory."""
        normalized_paths = sorted(
            {Path(path) for path in artifact_paths}, key=lambda path: len(path.parts)
        )
        collapsed_paths: set[Path] = set()
        for artifact_path in normalized_paths:
            if any(
                artifact_path != existing_path and _is_relative_to(artifact_path, existing_path)
                for existing_path in collapsed_paths
            ):
                continue
            collapsed_paths.add(artifact_path)
        return collapsed_paths

    def _build_relative_artifact_paths(self, artifact_paths: set[Path]) -> list[str]:
        """Return project-relative artifact paths with stable POSIX separators."""
        relative_paths: list[str] = []
        for artifact_path in artifact_paths:
            try:
                relative_path = artifact_path.relative_to(self.project_root)
            except ValueError:
                relative_path = artifact_path
            relative_paths.append(relative_path.as_posix())
        return sorted(relative_paths)

    def export_progress(self, output_path: Path) -> dict[str, Any]:
        """Export learner progress tables to a local JSON backup file."""
        if not self.db_path.exists():
            raise ValueError("No local database exists to export.")

        resolved_output_path = Path(output_path)
        resolved_output_path.parent.mkdir(parents=True, exist_ok=True)

        payload = self._build_backup_payload()
        resolved_output_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return {
            "output_path": str(resolved_output_path),
            "schema_version": BACKUP_SCHEMA_VERSION,
            "exported_at": payload["exported_at"],
            "counts": payload["counts"],
        }

    def import_progress(self, input_path: Path) -> dict[str, Any]:
        """Restore learner progress from a local JSON backup file."""
        resolved_input_path = Path(input_path)
        if not resolved_input_path.exists():
            raise ValueError("Backup file does not exist.")

        try:
            payload = json.loads(resolved_input_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError("Backup file is not valid JSON.") from error

        self._validate_backup_payload(payload)
        init_db(db_path=self.db_path, seed_words=False)
        self.word_service.reload_word_banks()

        imported_counts = {table_name: 0 for table_name in EXPORT_TABLES}
        skipped_counts = {"missing_words": 0}
        user_id_map: dict[int, int] = {}
        learning_session_id_map: dict[int, int] = {}
        imported_user_ids: set[int] = set()

        with create_connection(self.db_path) as connection:
            connection.execute("BEGIN")
            try:
                for user_snapshot in payload["tables"]["users"]:
                    source_user_id = int(user_snapshot["id"])
                    target_user_id = self._upsert_user_snapshot(connection, user_snapshot)
                    user_id_map[source_user_id] = target_user_id
                    imported_user_ids.add(target_user_id)
                    imported_counts["users"] += 1

                for session_snapshot in payload["tables"]["learning_sessions"]:
                    source_user_id = int(session_snapshot["user_id"])
                    if source_user_id not in user_id_map:
                        continue
                    target_session_id = self._upsert_learning_session_snapshot(
                        connection=connection,
                        snapshot=session_snapshot,
                        target_user_id=user_id_map[source_user_id],
                    )
                    learning_session_id_map[int(session_snapshot["id"])] = target_session_id
                    imported_counts["learning_sessions"] += 1

                for game_snapshot in payload["tables"]["game_sessions"]:
                    source_user_id = int(game_snapshot["user_id"])
                    if source_user_id not in user_id_map:
                        continue
                    target_word_id = self._resolve_word_id(connection, game_snapshot)
                    if target_word_id is None:
                        skipped_counts["missing_words"] += 1
                        continue
                    self._upsert_game_session_snapshot(
                        connection=connection,
                        snapshot=game_snapshot,
                        target_user_id=user_id_map[source_user_id],
                        target_word_id=target_word_id,
                        learning_session_id_map=learning_session_id_map,
                    )
                    imported_counts["game_sessions"] += 1

                for review_snapshot in payload["tables"]["review_queue"]:
                    source_user_id = int(review_snapshot["user_id"])
                    if source_user_id not in user_id_map:
                        continue
                    target_word_id = self._resolve_word_id(connection, review_snapshot)
                    if target_word_id is None:
                        skipped_counts["missing_words"] += 1
                        continue
                    self._upsert_review_snapshot(
                        connection=connection,
                        snapshot=review_snapshot,
                        target_user_id=user_id_map[source_user_id],
                        target_word_id=target_word_id,
                    )
                    imported_counts["review_queue"] += 1

                for progress_snapshot in payload["tables"]["word_progress"]:
                    source_user_id = int(progress_snapshot["user_id"])
                    if source_user_id not in user_id_map:
                        continue
                    target_word_id = self._resolve_word_id(connection, progress_snapshot)
                    if target_word_id is None:
                        skipped_counts["missing_words"] += 1
                        continue
                    self._upsert_word_progress_snapshot(
                        connection=connection,
                        snapshot=progress_snapshot,
                        target_user_id=user_id_map[source_user_id],
                        target_word_id=target_word_id,
                    )
                    imported_counts["word_progress"] += 1

                connection.commit()
            except Exception:
                connection.rollback()
                raise

        report_service = ReportService(db_path=self.db_path)
        for user_id in imported_user_ids:
            report_service.refresh_user_performance(user_id=user_id)

        return {
            "input_path": str(resolved_input_path),
            "schema_version": int(payload["schema_version"]),
            "imported_counts": imported_counts,
            "skipped_counts": skipped_counts,
        }

    def _build_backup_payload(self) -> dict[str, Any]:
        """Return a JSON-serializable backup payload."""
        with create_connection(self.db_path) as connection:
            tables = {
                "users": self._fetch_table_rows(connection, "users"),
                "learning_sessions": self._fetch_table_rows(connection, "learning_sessions"),
                "game_sessions": self._fetch_table_rows_with_words(connection, "game_sessions"),
                "review_queue": self._fetch_table_rows_with_words(connection, "review_queue"),
                "word_progress": self._fetch_table_rows_with_words(connection, "word_progress"),
            }

        return {
            "schema_version": BACKUP_SCHEMA_VERSION,
            "app_version": APP_VERSION,
            "app_version_display": APP_VERSION_DISPLAY,
            "exported_at": utc_now_iso(),
            "tables": tables,
            "counts": {table_name: len(rows) for table_name, rows in tables.items()},
        }

    def _validate_backup_payload(self, payload: dict[str, Any]) -> None:
        """Validate the backup envelope before touching the database."""
        if not isinstance(payload, dict):
            raise ValueError("Backup payload must be a JSON object.")
        if int(payload.get("schema_version", 0)) != BACKUP_SCHEMA_VERSION:
            raise ValueError("Unsupported backup schema version.")
        tables = payload.get("tables")
        if not isinstance(tables, dict):
            raise ValueError("Backup payload is missing tables.")
        for table_name in EXPORT_TABLES:
            if not isinstance(tables.get(table_name), list):
                raise ValueError(f"Backup table '{table_name}' is missing or invalid.")

    def _fetch_table_rows(
        self,
        connection: sqlite3.Connection,
        table_name: str,
    ) -> list[dict[str, Any]]:
        """Return all rows from one table."""
        rows = connection.execute(f"SELECT * FROM {table_name} ORDER BY id").fetchall()
        return [dict(row) for row in rows]

    def _fetch_table_rows_with_words(
        self,
        connection: sqlite3.Connection,
        table_name: str,
    ) -> list[dict[str, Any]]:
        """Return table rows with a stable word snapshot for restore."""
        rows = connection.execute(
            f"""
            SELECT
                {table_name}.*,
                words.word AS snapshot_word,
                words.language AS snapshot_language,
                words.category AS snapshot_category,
                words.difficulty AS snapshot_difficulty
            FROM {table_name}
            INNER JOIN words ON words.id = {table_name}.word_id
            ORDER BY {table_name}.id
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def _upsert_user_snapshot(
        self,
        connection: sqlite3.Connection,
        snapshot: dict[str, Any],
    ) -> int:
        """Insert or update one user and return the target id."""
        existing = connection.execute(
            "SELECT id FROM users WHERE username = ?",
            (snapshot["username"],),
        ).fetchone()
        if existing:
            target_user_id = int(existing["id"])
            connection.execute(
                """
                UPDATE users
                SET
                    email = ?,
                    password_hash = ?,
                    target_language = ?,
                    level = ?,
                    calibrated_level = ?,
                    assessment_completed = ?,
                    preferred_categories = ?,
                    last_builder_settings = ?,
                    daily_goal_words = ?,
                    daily_goal_sessions = ?,
                    created_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    snapshot["email"],
                    snapshot["password_hash"],
                    snapshot["target_language"],
                    snapshot["level"],
                    snapshot.get("calibrated_level"),
                    int(snapshot.get("assessment_completed", 0)),
                    snapshot.get("preferred_categories", "[]"),
                    snapshot.get("last_builder_settings", "{}"),
                    int(snapshot.get("daily_goal_words", DEFAULT_DAILY_GOAL_WORDS)),
                    int(snapshot.get("daily_goal_sessions", DEFAULT_DAILY_GOAL_SESSIONS)),
                    snapshot.get("created_at"),
                    snapshot.get("updated_at"),
                    target_user_id,
                ),
            )
            return target_user_id

        connection.execute(
            """
            INSERT INTO users (
                id,
                username,
                email,
                password_hash,
                target_language,
                level,
                calibrated_level,
                assessment_completed,
                preferred_categories,
                last_builder_settings,
                daily_goal_words,
                daily_goal_sessions,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot["id"],
                snapshot["username"],
                snapshot["email"],
                snapshot["password_hash"],
                snapshot["target_language"],
                snapshot["level"],
                snapshot.get("calibrated_level"),
                int(snapshot.get("assessment_completed", 0)),
                snapshot.get("preferred_categories", "[]"),
                snapshot.get("last_builder_settings", "{}"),
                int(snapshot.get("daily_goal_words", DEFAULT_DAILY_GOAL_WORDS)),
                int(snapshot.get("daily_goal_sessions", DEFAULT_DAILY_GOAL_SESSIONS)),
                snapshot.get("created_at"),
                snapshot.get("updated_at"),
            ),
        )
        return int(snapshot["id"])

    def _upsert_learning_session_snapshot(
        self,
        *,
        connection: sqlite3.Connection,
        snapshot: dict[str, Any],
        target_user_id: int,
    ) -> int:
        """Insert or update one learning session snapshot."""
        values = (
            target_user_id,
            snapshot["language"],
            snapshot["practice_mode"],
            int(snapshot["planned_rounds"]),
            snapshot.get("selected_category"),
            snapshot.get("selected_categories", "[]"),
            snapshot.get("difficulty_filter", "[]"),
            snapshot.get("review_policy", "prefer_review"),
            int(snapshot.get("show_hint_immediately", 1)),
            snapshot.get("game_mode", "easy"),
            int(snapshot.get("completed_rounds", 0)),
            int(snapshot.get("wins", 0)),
            int(snapshot.get("losses", 0)),
            float(snapshot.get("accuracy", 0)),
            snapshot.get("categories_practiced", "[]"),
            snapshot.get("words_practiced", "[]"),
            snapshot.get("status", "active"),
            snapshot.get("recommendation"),
            snapshot.get("started_at"),
            snapshot.get("completed_at"),
            snapshot.get("created_at"),
            snapshot.get("updated_at"),
        )
        existing = connection.execute(
            "SELECT id FROM learning_sessions WHERE id = ?",
            (snapshot["id"],),
        ).fetchone()
        if existing:
            connection.execute(
                """
                UPDATE learning_sessions
                SET
                    user_id = ?,
                    language = ?,
                    practice_mode = ?,
                    planned_rounds = ?,
                    selected_category = ?,
                    selected_categories = ?,
                    difficulty_filter = ?,
                    review_policy = ?,
                    show_hint_immediately = ?,
                    game_mode = ?,
                    completed_rounds = ?,
                    wins = ?,
                    losses = ?,
                    accuracy = ?,
                    categories_practiced = ?,
                    words_practiced = ?,
                    status = ?,
                    recommendation = ?,
                    started_at = ?,
                    completed_at = ?,
                    created_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (*values, int(snapshot["id"])),
            )
            return int(existing["id"])

        connection.execute(
            """
            INSERT INTO learning_sessions (
                id,
                user_id,
                language,
                practice_mode,
                planned_rounds,
                selected_category,
                selected_categories,
                difficulty_filter,
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
                completed_at,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (int(snapshot["id"]), *values),
        )
        return int(snapshot["id"])

    def _upsert_game_session_snapshot(
        self,
        *,
        connection: sqlite3.Connection,
        snapshot: dict[str, Any],
        target_user_id: int,
        target_word_id: int,
        learning_session_id_map: dict[int, int],
    ) -> None:
        """Insert or update one game session snapshot."""
        target_learning_session_id = (
            learning_session_id_map.get(int(snapshot["learning_session_id"]))
            if snapshot.get("learning_session_id") is not None
            else None
        )
        values = (
            target_user_id,
            target_learning_session_id,
            target_word_id,
            snapshot["language"],
            snapshot["level"],
            snapshot["category"],
            snapshot.get("practice_mode", "standard"),
            snapshot["result"],
            int(snapshot.get("attempts_used", 0)),
            int(snapshot.get("max_attempts", 6)),
            int(snapshot.get("letters_correct", 0)),
            int(snapshot.get("letters_wrong", 0)),
            snapshot.get("guessed_letters", ""),
            snapshot.get("time_taken_seconds"),
            snapshot.get("played_at"),
            snapshot.get("started_at"),
            snapshot.get("completed_at"),
        )
        existing = connection.execute(
            "SELECT id FROM game_sessions WHERE id = ?",
            (snapshot["id"],),
        ).fetchone()
        if existing:
            connection.execute(
                """
                UPDATE game_sessions
                SET
                    user_id = ?,
                    learning_session_id = ?,
                    word_id = ?,
                    language = ?,
                    level = ?,
                    category = ?,
                    practice_mode = ?,
                    result = ?,
                    attempts_used = ?,
                    max_attempts = ?,
                    letters_correct = ?,
                    letters_wrong = ?,
                    guessed_letters = ?,
                    time_taken_seconds = ?,
                    played_at = ?,
                    started_at = ?,
                    completed_at = ?
                WHERE id = ?
                """,
                (*values, int(snapshot["id"])),
            )
            return

        connection.execute(
            """
            INSERT INTO game_sessions (
                id,
                user_id,
                learning_session_id,
                word_id,
                language,
                level,
                category,
                practice_mode,
                result,
                attempts_used,
                max_attempts,
                letters_correct,
                letters_wrong,
                guessed_letters,
                time_taken_seconds,
                played_at,
                started_at,
                completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (int(snapshot["id"]), *values),
        )

    def _upsert_review_snapshot(
        self,
        *,
        connection: sqlite3.Connection,
        snapshot: dict[str, Any],
        target_user_id: int,
        target_word_id: int,
    ) -> None:
        """Insert or update one review queue snapshot."""
        values = (
            target_user_id,
            target_word_id,
            snapshot["language"],
            snapshot["category"],
            float(snapshot.get("priority_score", 0)),
            snapshot["review_due_at"],
            int(snapshot.get("review_count", 0)),
            snapshot.get("last_reviewed_at"),
            snapshot.get("last_result"),
            float(snapshot.get("last_accuracy", 0)),
            int(snapshot.get("is_active", 1)),
            snapshot.get("created_at"),
            snapshot.get("updated_at"),
        )
        existing = connection.execute(
            """
            SELECT id FROM review_queue
            WHERE id = ? OR (user_id = ? AND word_id = ?)
            """,
            (snapshot["id"], target_user_id, target_word_id),
        ).fetchone()
        if existing:
            connection.execute(
                """
                UPDATE review_queue
                SET
                    user_id = ?,
                    word_id = ?,
                    language = ?,
                    category = ?,
                    priority_score = ?,
                    review_due_at = ?,
                    review_count = ?,
                    last_reviewed_at = ?,
                    last_result = ?,
                    last_accuracy = ?,
                    is_active = ?,
                    created_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (*values, int(existing["id"])),
            )
            return

        connection.execute(
            """
            INSERT INTO review_queue (
                id,
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
                is_active,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (int(snapshot["id"]), *values),
        )

    def _upsert_word_progress_snapshot(
        self,
        *,
        connection: sqlite3.Connection,
        snapshot: dict[str, Any],
        target_user_id: int,
        target_word_id: int,
    ) -> None:
        """Insert or update one word-progress snapshot."""
        values = (
            target_user_id,
            target_word_id,
            snapshot["language"],
            snapshot.get("familiarity_status", "new"),
            float(snapshot.get("mastery_score", 0)),
            int(snapshot.get("times_seen", 0)),
            int(snapshot.get("wins", 0)),
            int(snapshot.get("losses", 0)),
            int(snapshot.get("successful_streak", 0)),
            int(snapshot.get("total_correct_letters", 0)),
            int(snapshot.get("total_wrong_letters", 0)),
            float(snapshot.get("last_accuracy", 0)),
            snapshot.get("last_result"),
            float(snapshot.get("priority_score", 0)),
            snapshot.get("last_played_at"),
            snapshot.get("updated_at"),
        )
        existing = connection.execute(
            """
            SELECT id FROM word_progress
            WHERE id = ? OR (user_id = ? AND word_id = ?)
            """,
            (snapshot["id"], target_user_id, target_word_id),
        ).fetchone()
        if existing:
            connection.execute(
                """
                UPDATE word_progress
                SET
                    user_id = ?,
                    word_id = ?,
                    language = ?,
                    familiarity_status = ?,
                    mastery_score = ?,
                    times_seen = ?,
                    wins = ?,
                    losses = ?,
                    successful_streak = ?,
                    total_correct_letters = ?,
                    total_wrong_letters = ?,
                    last_accuracy = ?,
                    last_result = ?,
                    priority_score = ?,
                    last_played_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (*values, int(existing["id"])),
            )
            return

        connection.execute(
            """
            INSERT INTO word_progress (
                id,
                user_id,
                word_id,
                language,
                familiarity_status,
                mastery_score,
                times_seen,
                wins,
                losses,
                successful_streak,
                total_correct_letters,
                total_wrong_letters,
                last_accuracy,
                last_result,
                priority_score,
                last_played_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (int(snapshot["id"]), *values),
        )

    def _resolve_word_id(
        self,
        connection: sqlite3.Connection,
        snapshot: dict[str, Any],
    ) -> int | None:
        """Resolve a backed-up word against the current seeded word bank."""
        row = connection.execute(
            """
            SELECT id
            FROM words
            WHERE word = ?
              AND language = ?
              AND category = ?
              AND difficulty = ?
            """,
            (
                snapshot.get("snapshot_word"),
                snapshot.get("snapshot_language"),
                snapshot.get("snapshot_category"),
                snapshot.get("snapshot_difficulty"),
            ),
        ).fetchone()
        return int(row["id"]) if row else None
