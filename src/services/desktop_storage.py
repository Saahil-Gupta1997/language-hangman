"""Validated SQLite backups, profile controls and privacy-safe diagnostics."""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from src import __version__
from src.db.database import SCHEMA_SQL, SCHEMA_VERSION, _run_migrations, create_connection, init_db
from src.db.transaction import transaction


def _stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")


def validate_backup(path):
    path = Path(path).resolve()
    if not path.is_file() or path.stat().st_size > 512 * 1024 * 1024:
        raise ValueError("Choose a Hangman SQLite backup smaller than 512 MB.")
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    try:
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("The selected backup is damaged.")
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version > SCHEMA_VERSION:
            raise ValueError("This backup needs a newer version of the application.")
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if not {"users", "words", "game_sessions", "learning_sessions"} <= tables:
            raise ValueError("This file is not a supported Hangman database.")
        if connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('trigger','view')"
        ).fetchone():
            raise ValueError("Backups with custom triggers or views are not supported.")
        if connection.execute("PRAGMA foreign_key_check").fetchone():
            raise ValueError("The backup has inconsistent profile or progress records.")
        # Validate fields used by the application, not merely table names.
        for table, columns in {
            "users": "id,username,password_hash,target_language,level",
            "words": "id,word,language,category,difficulty",
            "game_sessions": "id,user_id,word_id,result",
            "learning_sessions": "id,user_id,status",
        }.items():
            connection.execute(f"SELECT {columns} FROM {table} LIMIT 0")
        if version == SCHEMA_VERSION:
            expected = sqlite3.connect(":memory:")
            expected.row_factory = sqlite3.Row
            try:
                expected.executescript(SCHEMA_SQL)
                _run_migrations(expected)
                required = {
                    row[0]
                    for row in expected.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' "
                        "AND name != 'sqlite_sequence'"
                    )
                }
                for table in required:
                    columns = {row[1] for row in expected.execute(f"PRAGMA table_info({table})")}
                    actual = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
                    if not columns <= actual:
                        raise ValueError("The backup is missing required data structures.")
                connection.execute(
                    "SELECT round_key,user_id,payload FROM completion_receipts LIMIT 0"
                )
                connection.execute(
                    "SELECT user_id,payload,revision,updated_at FROM active_practice LIMIT 0"
                )
            finally:
                expected.close()
        if "active_practice" in tables:
            for row in connection.execute("SELECT user_id,payload FROM active_practice"):
                from src.models.game_round import GameRound
                from src.models.learning_session import LearningSession

                data = json.loads(row[1])
                if data["schema"] != 1 or data["session"]["user_id"] != row[0]:
                    raise ValueError("The backup contains an incompatible saved session.")
                GameRound(**data["round"])
                LearningSession(**data["session"])
    except (sqlite3.Error, KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("This backup is damaged or incompatible.") from error
    finally:
        connection.close()


def backup_database(db_path, destination):
    destination = Path(destination)
    if destination.resolve() == Path(db_path).resolve():
        raise ValueError("Choose a location different from the active database.")
    if destination.exists():
        raise ValueError("Choose a new backup filename; existing files are preserved.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(suffix=".sqlite", dir=destination.parent)
    os.close(descriptor)
    temporary = Path(name)
    try:
        with create_connection(db_path) as source, create_connection(temporary) as target:
            source.backup(target)
        validate_backup(temporary)
        # Exclusive create avoids overwriting a file created after the initial check.
        with destination.open("xb") as output, temporary.open("rb") as source:
            import shutil

            shutil.copyfileobj(source, output)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


SIDECAR_SUFFIXES = ("-journal", "-wal", "-shm")


class DatabaseUnavailableError(RuntimeError):
    """The live database cannot be opened, upgraded or validated at start-up."""


def open_live_database(db_path):
    """Open, upgrade and quick-check the live database for the desktop app.

    Raises DatabaseUnavailableError (with a message safe to show and log) so the launcher
    can offer recovery instead of failing to start.
    """
    try:
        path = init_db(db_path, seed_words=False)
    except ValueError as error:  # newer schema or a failed upgrade check
        raise DatabaseUnavailableError(str(error)) from error
    except (sqlite3.Error, OSError) as error:
        raise DatabaseUnavailableError(
            f"The data file could not be opened ({type(error).__name__})."
        ) from error
    if not database_is_healthy(path):
        raise DatabaseUnavailableError("The data file failed its integrity check.")
    return path


class RestoreError(ValueError):
    """A restore stopped before the live database was replaced; ``stage`` says where."""

    def __init__(self, stage, message):
        super().__init__(message)
        self.stage = stage


def database_is_healthy(path):
    """Return True when the file opens read-only and passes SQLite's quick check."""
    try:
        connection = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
        try:
            return connection.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        finally:
            connection.close()
    except sqlite3.Error:
        return False


def quarantine_database(db_path, backups_dir):
    """Copy a damaged database's bytes, and any side files, into a labelled folder."""
    db_path = Path(db_path)
    folder = Path(backups_dir) / f"quarantine-{_stamp()}"
    folder.mkdir(parents=True)
    import shutil

    for suffix in ("", *SIDECAR_SUFFIXES):
        original = Path(f"{db_path}{suffix}")
        if original.exists():
            shutil.copy2(original, folder / f"damaged-{original.name}")
    (folder / "README.txt").write_text(
        "These files are an exact copy of a Language Hangman database that could not be\n"
        "opened or validated, saved before a backup was restored over it. They are kept\n"
        "only for investigation or data recovery and are never used by the application.\n",
        encoding="utf-8",
    )
    return folder


def _protect_current_database(db_path, backups_dir):
    """Keep the current file before replacement: a safety backup, else a quarantine copy."""
    if database_is_healthy(db_path):
        try:
            return backup_database(db_path, backups_dir / f"before-restore-{_stamp()}.sqlite")
        except ValueError:
            pass  # Readable but not a valid Hangman database (e.g. newer schema): keep bytes.
    return quarantine_database(db_path, backups_dir)


def _set_aside_sidecars(db_path, backups_dir):
    """Move journal side files away so SQLite cannot replay them into the restored file."""
    moved = []
    for suffix in SIDECAR_SUFFIXES:
        sidecar = Path(f"{db_path}{suffix}")
        if sidecar.exists():
            destination = backups_dir / f"set-aside-{_stamp()}-{sidecar.name}"
            os.replace(sidecar, destination)
            moved.append((destination, sidecar))
    return moved


def restore_database(db_path, source):
    """Replace the live database with a validated backup, even when the live file is damaged.

    Steps: validate the backup; stage, upgrade and re-validate a copy; keep the current file
    (a validated safety backup when readable, otherwise a byte-for-byte quarantine copy);
    move journal side files aside; switch with one atomic rename. A failure before the
    rename leaves the live file exactly as it was. Returns the safety backup or quarantine
    folder, or None when there was no live file.
    """
    db_path, source = Path(db_path), Path(source)
    validate_backup(source)
    backups_dir = db_path.parent / "backups"
    try:
        backups_dir.mkdir(parents=True, exist_ok=True)
        descriptor, name = tempfile.mkstemp(prefix="restore-", suffix=".sqlite", dir=db_path.parent)
        os.close(descriptor)
    except OSError as error:
        raise RestoreError(
            "stage",
            "The backup was not restored because the data folder is not writable "
            f"({type(error).__name__}). Check free disk space and folder permissions, then "
            "try again. Your current data is unchanged.",
        ) from error
    staging = Path(name)
    try:
        try:
            origin = sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)
            try:
                with create_connection(staging) as target:
                    origin.backup(target)
            finally:
                origin.close()
            init_db(staging, seed_words=False)
            validate_backup(staging)
        except (OSError, sqlite3.Error) as error:
            raise RestoreError(
                "stage",
                "The backup could not be prepared for use "
                f"({type(error).__name__}). Check free disk space, then try again. "
                "Your current data is unchanged.",
            ) from error

        preserved = None
        if db_path.exists():
            try:
                preserved = _protect_current_database(db_path, backups_dir)
            except (OSError, sqlite3.Error) as error:
                raise RestoreError(
                    "protect",
                    "The backup was not restored because a copy of your current data could "
                    f"not be saved first ({type(error).__name__}). Free some disk space or "
                    "check folder permissions, then try again. Your current data is unchanged.",
                ) from error

        moved = []
        try:
            moved = _set_aside_sidecars(db_path, backups_dir)
            os.replace(staging, db_path)
        except OSError as error:
            for destination, original in reversed(moved):
                os.replace(destination, original)
            raise RestoreError(
                "replace",
                "The backup was not restored because the current data file could not be "
                f"replaced ({type(error).__name__}). Close any program that may be using it, "
                "such as a sync or antivirus tool, then try again. Your current data is "
                "unchanged.",
            ) from error
    finally:
        staging.unlink(missing_ok=True)
    return preserved


def delete_profile(db_path, user_id):
    with transaction(db_path) as connection:
        connection.execute("DELETE FROM users WHERE id=?", (user_id,))


def export_profile(db_path, user_id, destination):
    """Human-readable export; excludes credentials and other profiles."""
    payload = {"format": 1, "application_version": __version__}
    with transaction(db_path) as connection:
        user = connection.execute(
            "SELECT username,target_language,level,created_at FROM users WHERE id=?", (user_id,)
        ).fetchone()
        if not user:
            raise ValueError("Profile no longer exists.")
        payload["profile"] = dict(user)
        for table in ("game_sessions", "learning_sessions", "word_progress", "review_queue"):
            payload[table] = [
                dict(row)
                for row in connection.execute(f"SELECT * FROM {table} WHERE user_id=?", (user_id,))
            ]
    with Path(destination).open("x", encoding="utf-8") as output:
        json.dump(payload, output, ensure_ascii=False, indent=2)


def progress_report(db_path, user_id):
    """Derive all displayed metrics directly from completed game rows."""
    with transaction(db_path) as connection:
        rounds = [
            dict(row)
            for row in connection.execute(
                "SELECT g.*, w.word FROM game_sessions g JOIN words w ON w.id=g.word_id "
                "WHERE user_id=? AND result IN ('won','lost') ORDER BY played_at DESC,id DESC",
                (user_id,),
            )
        ]
        count = len(rounds)
        wins = sum(row["result"] == "won" for row in rounds)
        guesses = sum(row["attempts_used"] for row in rounds)
        correct = sum(row["letters_correct"] for row in rounds)
        sessions = connection.execute(
            "SELECT count(*) FROM learning_sessions WHERE user_id=? AND status='completed'",
            (user_id,),
        ).fetchone()[0]
    return {
        "rounds": count,
        "wins": wins,
        "losses": count - wins,
        "win_rate": 100 * wins / count if count else 0,
        "guess_accuracy": 100 * correct / guesses if guesses else 0,
        "guesses": guesses,
        "correct_guesses": correct,
        "sessions": sessions,
        "words": len({row["word_id"] for row in rounds}),
        "history": rounds,
    }


def export_diagnostics(db_path, destination, events=()):
    """Write build details, database health and recent coded failure events.

    ``events`` must already be filtered to the fixed ``op=… stage=… error=… version=…``
    format. Local paths, names, passwords, words and saved-session payloads are never
    included.
    """
    import platform
    import sys

    payload = {
        "application_version": __version__,
        "build": "installed" if getattr(sys, "frozen", False) else "source",
        "python_version": platform.python_version(),
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
    }
    try:
        connection = sqlite3.connect(Path(db_path).resolve().as_uri() + "?mode=ro", uri=True)
        try:
            payload["schema_version"] = connection.execute("PRAGMA user_version").fetchone()[0]
            payload["integrity_ok"] = (
                connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            )
            payload["foreign_keys_ok"] = not connection.execute(
                "PRAGMA foreign_key_check"
            ).fetchone()
        finally:
            connection.close()
    except sqlite3.Error as error:
        payload["database"] = f"unavailable ({type(error).__name__})"
    payload["recent_events"] = list(events)
    with zipfile.ZipFile(destination, "x", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("diagnostics.json", json.dumps(payload, indent=2))
