"""Word-bank loading, validation, import, and selection helpers."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Sequence

from src.db.repository import WordRepository
from src.utils.config import WORDS_DIR
from src.utils.constants import (
    DEFAULT_PREFERRED_CATEGORIES,
    LEVEL_TO_DIFFICULTIES,
    SITUATIONS,
)
from src.utils.helpers import deserialize_string_list
from src.utils.word_bank_loader import (
    build_seed_rows,
    build_seed_rows_from_payload,
    ensure_word_bank_hint_fields,
    validate_word_bank_directory,
    validate_word_bank_payload,
)

WordRecord = dict[str, Any]


class WordService:
    """Loads word banks, validates content, and selects playable words.

    Candidate id lists follow one rule everywhere: ``None`` means no restriction and an
    empty list means no eligible words.
    """

    # When set, listing, counting and selection only ever return words from these sources.
    sources: tuple[str, ...] | None = None

    def __init__(self, words_dir: Path | None = None, db_path: Path | None = None) -> None:
        self.words_dir = Path(words_dir or WORDS_DIR)
        self.word_repository = WordRepository(db_path=db_path)

    def _restrict_to_source(self, rows: Sequence[Any]) -> list[Any]:
        """Drop rows outside the supported corpus when a source restriction is set."""
        if not self.sources:
            return list(rows)
        return [row for row in rows if row["source"] in self.sources]

    def get_available_languages(self) -> list[str]:
        """Return each available language based on the database or JSON fallback."""
        database_languages = [
            row["language"] for row in self.word_repository.get_available_languages()
        ]
        if database_languages:
            return sorted(database_languages)

        validation_summary = self.inspect_word_banks(include_rows=True)
        languages = {
            file_summary["language"]
            for file_summary in validation_summary["files"]
            if file_summary["language"]
        }
        return sorted(languages)

    def inspect_word_banks(self, *, include_rows: bool = False) -> dict[str, Any]:
        """Validate all word-bank files and return a file-level summary."""
        return validate_word_bank_directory(self.words_dir, include_rows=include_rows)

    def reload_word_banks(self) -> dict[str, Any]:
        """Validate and import word banks into SQLite with an idempotent upsert flow."""
        hint_update_summary = ensure_word_bank_hint_fields(self.words_dir)
        seed_payload = build_seed_rows(self.words_dir)
        before_count = self.get_total_word_count()
        self.word_repository.upsert_words(seed_payload["rows"])
        after_count = self.get_total_word_count()

        inserted_count = max(after_count - before_count, 0)
        reloaded_count = max(seed_payload["valid_words"] - inserted_count, 0)
        return {
            **seed_payload,
            "inserted_count": inserted_count,
            "reloaded_count": reloaded_count,
            "total_words_after_import": after_count,
            "hint_update_summary": hint_update_summary,
        }

    def import_uploaded_word_bank(
        self,
        *,
        filename: str,
        content: bytes,
    ) -> dict[str, Any]:
        """Validate and import one uploaded JSON word-bank file into SQLite."""
        try:
            payload = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            return {
                "files": [
                    {
                        "file": filename,
                        "language": None,
                        "valid_words": 0,
                        "invalid_words": 0,
                        "duplicate_words": 0,
                        "errors": [f"Unable to read uploaded JSON: {error}"],
                        "warnings": [],
                    }
                ],
                "files_processed": 1,
                "valid_words": 0,
                "invalid_words": 0,
                "duplicate_words": 0,
                "has_errors": True,
                "inserted_count": 0,
                "reloaded_count": 0,
                "skipped_existing_count": 0,
                "total_words_after_import": self.get_total_word_count(),
            }

        import_payload = build_seed_rows_from_payload(payload, source_name=filename)
        existing_keys = self._get_existing_normalized_keys(import_payload["rows"])
        rows_to_import = [
            row
            for row in import_payload["rows"]
            if self._build_normalized_key(word=str(row[1]), language=str(row[3]))
            not in existing_keys
        ]
        skipped_existing_count = len(import_payload["rows"]) - len(rows_to_import)
        before_count = self.get_total_word_count()
        if rows_to_import:
            self.word_repository.upsert_words(rows_to_import)
        after_count = self.get_total_word_count()
        inserted_count = max(after_count - before_count, 0)
        return {
            **import_payload,
            "inserted_count": inserted_count,
            "reloaded_count": 0,
            "skipped_existing_count": skipped_existing_count,
            "total_words_after_import": after_count,
        }

    def validate_uploaded_word_bank(
        self,
        *,
        filename: str,
        content: bytes,
    ) -> dict[str, Any]:
        """Validate one uploaded JSON word-bank file without importing it."""
        try:
            payload = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            return {
                "file": filename,
                "language": None,
                "valid_words": 0,
                "invalid_words": 0,
                "duplicate_words": 0,
                "errors": [f"Unable to read uploaded JSON: {error}"],
                "warnings": [],
            }
        return validate_word_bank_payload(payload, source_name=filename)

    def load_word_bank(self, language: str) -> list[WordRecord]:
        """Load all validated words for a given language from the source files."""
        validation_summary = self.inspect_word_banks(include_rows=True)
        rows = [
            row
            for file_summary in validation_summary["files"]
            for row in file_summary["rows"]
            if row["language"] == language.lower()
        ]
        return [self._normalize_word_row(row) for row in rows]

    def get_words(
        self,
        language: str,
        category: str | None = None,
        difficulty: str | None = None,
        categories: Sequence[str] | None = None,
        difficulties: Sequence[str] | None = None,
        situation: str | None = None,
        limit: int | None = None,
    ) -> list[WordRecord]:
        """Return words with optional category and difficulty filtering."""
        normalized_categories = (
            [str(item).strip().lower() for item in categories]
            if categories is not None
            else ([category.lower()] if category else None)
        )
        normalized_difficulties = (
            [str(item).strip().lower() for item in difficulties]
            if difficulties is not None
            else ([difficulty.lower()] if difficulty else None)
        )

        database_words = self._restrict_to_source(
            self.word_repository.get_words(
                language=language.lower(),
                categories=normalized_categories,
                difficulties=normalized_difficulties,
                # With a source restriction the limit must apply after filtering.
                limit=None if self.sources else limit,
            )
        )
        if database_words:
            words = [self._normalize_word_row(row) for row in database_words]
            if situation:
                words = [word for word in words if self._word_matches_situation(word, situation)]
            return words[:limit] if limit is not None else words
        if self.sources:
            # Never fall back to file banks that sit outside the supported corpus.
            return []

        words = self.load_word_bank(language)
        if normalized_categories:
            words = [word for word in words if word["category"] in normalized_categories]
        if normalized_difficulties:
            words = [word for word in words if word["difficulty"] in normalized_difficulties]
        if situation:
            words = [word for word in words if self._word_matches_situation(word, situation)]
        return words[:limit] if limit is not None else words

    def get_categories(self, language: str) -> list[str]:
        """Return distinct categories for a language."""
        if self.sources:
            return sorted({word["category"] for word in self.get_words(language)})
        database_categories = [
            row["category"] for row in self.word_repository.get_categories(language.lower())
        ]
        if database_categories:
            return sorted(database_categories)
        return sorted({word["category"] for word in self.load_word_bank(language)})

    def get_difficulties(self, language: str) -> list[str]:
        """Return distinct difficulty levels for a language."""
        if self.sources:
            return sorted({word["difficulty"] for word in self.get_words(language)})
        database_difficulties = [
            row["difficulty"] for row in self.word_repository.get_difficulties(language.lower())
        ]
        if database_difficulties:
            return sorted(database_difficulties)
        return sorted({word["difficulty"] for word in self.load_word_bank(language)})

    def get_available_situations(self, language: str | None = None) -> list[str]:
        """Return situations that have at least one playable word."""
        languages = [language.lower()] if language else self.get_available_languages()
        situations: set[str] = set()
        for language_key in languages:
            for word in self.get_words(language=language_key):
                word_situations = word.get("situations", [])
                if isinstance(word_situations, str):
                    word_situations = deserialize_string_list(word_situations, default=[])
                situations.update(
                    situation
                    for situation in word_situations
                    if situation in SITUATIONS
                )
        return [situation for situation in SITUATIONS if situation in situations]

    def preview_words(
        self,
        language: str,
        limit: int = 5,
        categories: Sequence[str] | None = None,
        difficulties: Sequence[str] | None = None,
    ) -> list[WordRecord]:
        """Return a small preview of the word bank for UI display."""
        return self.get_words(
            language=language,
            categories=categories,
            difficulties=difficulties,
            limit=limit,
        )

    def get_words_by_ids(self, word_ids: Sequence[int]) -> list[WordRecord]:
        """Return words for specific ids while preserving input order."""
        return [
            self._normalize_word_row(row) for row in self.word_repository.get_words_by_ids(word_ids)
        ]

    def get_difficulties_for_level(self, level: str) -> tuple[str, ...]:
        """Map the learner level to the difficulties used for word selection."""
        return LEVEL_TO_DIFFICULTIES.get(
            level.lower(),
            tuple(
                sorted(
                    {
                        difficulty
                        for values in LEVEL_TO_DIFFICULTIES.values()
                        for difficulty in values
                    }
                )
            ),
        )

    def get_content_summary(self, language: str | None = None) -> dict[str, Any]:
        """Return summary counts used by the local content utility page."""
        return {
            "total_words": self.get_total_word_count(language=language),
            "by_language": [dict(row) for row in self.word_repository.get_counts_by_language()],
            "by_category": [
                dict(row) for row in self.word_repository.get_counts_by_category(language=language)
            ],
            "by_difficulty": [
                dict(row)
                for row in self.word_repository.get_counts_by_difficulty(language=language)
            ],
        }

    def get_total_word_count(self, language: str | None = None) -> int:
        """Return the total number of words stored in SQLite."""
        if language:
            return len(self.get_words(language=language))
        return sum(int(row["word_count"]) for row in self.word_repository.get_counts_by_language())

    def count_candidate_words(
        self,
        language: str,
        categories: Sequence[str] | None = None,
        difficulties: Sequence[str] | None = None,
        situation: str | None = None,
        candidate_word_ids: Sequence[int] | None = None,
        excluded_word_ids: Sequence[int] | None = None,
    ) -> int:
        """Return the number of candidate words matching the provided filters."""
        return len(
            self._find_candidate_words(
                language=language.lower(),
                categories=(
                    [str(category).lower() for category in categories] if categories else None
                ),
                difficulties=(
                    [str(difficulty).lower() for difficulty in difficulties]
                    if difficulties
                    else None
                ),
                situation=situation,
                excluded_word_ids={int(word_id) for word_id in (excluded_word_ids or [])},
                candidate_word_ids=candidate_word_ids,
                deprioritized_word_ids=None,
            )
        )

    def select_word(
        self,
        language: str,
        level: str,
        preferred_categories: list[str] | None = None,
        selected_category: str | None = None,
        selected_categories: Sequence[str] | None = None,
        category_order: Sequence[str] | None = None,
        excluded_word_ids: Sequence[int] | None = None,
        candidate_word_ids: Sequence[int] | None = None,
        difficulty_override: Sequence[str] | None = None,
        deprioritized_word_ids: Sequence[int] | None = None,
        situation: str | None = None,
        strict_mode: bool = False,
        rng: random.Random | None = None,
    ) -> WordRecord:
        """Select one word with either strict matching or fallback behavior."""
        random_generator = rng or random.Random()
        language_key = language.lower()
        allowed_categories = [
            str(category).strip().lower()
            for category in (selected_categories or [])
            if str(category).strip()
        ]
        if selected_category and selected_category.lower() not in allowed_categories:
            allowed_categories = [selected_category.lower(), *allowed_categories]

        prioritized_categories = (
            [selected_category.lower()]
            if selected_category
            else [
                category.lower()
                for category in (
                    category_order
                    or allowed_categories
                    or preferred_categories
                    or list(DEFAULT_PREFERRED_CATEGORIES)
                )
            ]
        )
        if allowed_categories:
            prioritized_categories = [
                category for category in prioritized_categories if category in allowed_categories
            ] or allowed_categories

        difficulty_pool = list(difficulty_override or self.get_difficulties_for_level(level))
        excluded_ids = {int(word_id) for word_id in (excluded_word_ids or [])}
        prioritized_word_ids = (
            None if candidate_word_ids is None else [int(word_id) for word_id in candidate_word_ids]
        )
        deprioritized_ids = {int(word_id) for word_id in (deprioritized_word_ids or [])}

        if strict_mode:
            selection_attempts = (
                (
                    prioritized_categories,
                    difficulty_pool,
                    excluded_ids,
                    prioritized_word_ids,
                    deprioritized_ids,
                ),
            )
        else:
            selection_attempts = (
                (
                    prioritized_categories,
                    difficulty_pool,
                    excluded_ids,
                    prioritized_word_ids,
                    deprioritized_ids,
                ),
                (
                    prioritized_categories,
                    difficulty_pool,
                    set(),
                    prioritized_word_ids,
                    deprioritized_ids,
                ),
                (None, difficulty_pool, excluded_ids, prioritized_word_ids, deprioritized_ids),
                (None, difficulty_pool, set(), prioritized_word_ids, deprioritized_ids),
                (
                    prioritized_categories,
                    None,
                    excluded_ids,
                    prioritized_word_ids,
                    deprioritized_ids,
                ),
                (prioritized_categories, None, set(), prioritized_word_ids, deprioritized_ids),
                (None, None, excluded_ids, prioritized_word_ids, deprioritized_ids),
                (None, None, set(), prioritized_word_ids, deprioritized_ids),
                (prioritized_categories, difficulty_pool, excluded_ids, None, deprioritized_ids),
                (prioritized_categories, difficulty_pool, set(), None, deprioritized_ids),
                (None, difficulty_pool, excluded_ids, None, deprioritized_ids),
                (None, difficulty_pool, set(), None, deprioritized_ids),
                (prioritized_categories, None, excluded_ids, None, deprioritized_ids),
                (prioritized_categories, None, set(), None, deprioritized_ids),
                (None, None, excluded_ids, None, deprioritized_ids),
                (None, None, set(), None, deprioritized_ids),
            )

        for (
            category_candidates,
            difficulty_candidates,
            excluded_candidates,
            candidate_ids,
            deprioritized_candidates,
        ) in selection_attempts:
            candidate_words = self._find_prioritized_candidates(
                language=language_key,
                category_order=category_candidates,
                difficulties=difficulty_candidates,
                excluded_word_ids=excluded_candidates,
                candidate_word_ids=candidate_ids,
                deprioritized_word_ids=deprioritized_candidates,
                situation=situation,
            )
            if candidate_words:
                return random_generator.choice(candidate_words)

        if strict_mode:
            raise ValueError("No words matched the strict selection rules for this practice setup.")

        raise ValueError("No words are available for the selected practice setup.")

    def _find_candidate_words(
        self,
        language: str,
        categories: list[str] | None,
        difficulties: list[str] | None,
        excluded_word_ids: set[int] | None = None,
        candidate_word_ids: Sequence[int] | None = None,
        deprioritized_word_ids: set[int] | None = None,
        situation: str | None = None,
    ) -> list[WordRecord]:
        """Return candidate words from the database with lightweight priority filters."""
        rows = self._restrict_to_source(
            self.word_repository.get_words(
                language=language,
                categories=categories,
                difficulties=difficulties,
            )
        )
        candidate_words = [self._normalize_word_row(row) for row in rows]
        if situation:
            candidate_words = [
                word for word in candidate_words if self._word_matches_situation(word, situation)
            ]
        if candidate_word_ids is not None:
            candidate_id_set = {int(word_id) for word_id in candidate_word_ids}
            candidate_words = [
                word for word in candidate_words if int(word["id"]) in candidate_id_set
            ]
        if excluded_word_ids:
            candidate_words = [
                word for word in candidate_words if int(word["id"]) not in excluded_word_ids
            ]
        if deprioritized_word_ids:
            prioritized_words = [
                word for word in candidate_words if int(word["id"]) not in deprioritized_word_ids
            ]
            if prioritized_words:
                candidate_words = prioritized_words
        return candidate_words

    def _find_prioritized_candidates(
        self,
        language: str,
        category_order: Sequence[str] | None,
        difficulties: Sequence[str] | None,
        excluded_word_ids: set[int] | None,
        candidate_word_ids: Sequence[int] | None,
        deprioritized_word_ids: set[int] | None,
        situation: str | None = None,
    ) -> list[WordRecord]:
        """Return candidates while preserving category priority order."""
        normalized_difficulties = list(difficulties) if difficulties else None

        if category_order:
            for category in category_order:
                category_candidates = self._find_candidate_words(
                    language=language,
                    categories=[category],
                    difficulties=normalized_difficulties,
                    excluded_word_ids=excluded_word_ids,
                    candidate_word_ids=candidate_word_ids,
                    deprioritized_word_ids=deprioritized_word_ids,
                    situation=situation,
                )
                if category_candidates:
                    return category_candidates
            return []

        return self._find_candidate_words(
            language=language,
            categories=None,
            difficulties=normalized_difficulties,
            excluded_word_ids=excluded_word_ids,
            candidate_word_ids=candidate_word_ids,
            deprioritized_word_ids=deprioritized_word_ids,
            situation=situation,
        )

    def _normalize_word_row(self, row: Any) -> WordRecord:
        """Convert a SQLite row into a UI-friendly word record."""
        record = dict(row)
        record["situations"] = deserialize_string_list(record.get("situations"), default=[])
        record["tags"] = deserialize_string_list(record.get("tags"), default=[])
        record["word_id"] = record.get("word_bank_id") or f"{record['language']}:{record['word']}"
        record["meaning"] = record.get("meaning") or record.get("translation")
        record["sentence_translation"] = (
            record.get("sentence_translation") or record.get("translation")
        )
        record["pronunciation_text"] = record.get("pronunciation_text") or record.get("word")
        record["usage_note"] = record.get("usage_note") or record.get("hint")
        record["meaning_hint"] = record.get("meaning_hint") or record.get("hint")
        record["synonym_hint"] = record.get("synonym_hint") or record.get("synonym")
        record["association_hint"] = record.get("association_hint") or record.get("association")
        return record

    def _word_matches_situation(self, word: WordRecord, situation: str | None) -> bool:
        """Return whether a normalized word belongs to the requested situation."""
        if not situation:
            return True
        normalized_situation = str(situation).strip().lower()
        situations = word.get("situations") or []
        if isinstance(situations, str):
            situations = deserialize_string_list(situations, default=[])
        return normalized_situation in {str(item).strip().lower() for item in situations}

    def _get_existing_normalized_keys(self, rows: Sequence[Sequence[object]]) -> set[str]:
        """Return normalized word/language keys that already exist in SQLite."""
        languages = sorted({str(row[3]).strip().lower() for row in rows if len(row) > 3})
        existing_keys: set[str] = set()
        for language in languages:
            for word in self.word_repository.get_words(language=language):
                existing_keys.add(
                    self._build_normalized_key(
                        word=str(word["word"]),
                        language=str(word["language"]),
                    )
                )
        return existing_keys

    def _build_normalized_key(self, *, word: str, language: str) -> str:
        """Return the duplicate-check key used for custom UI imports."""
        normalized_word = " ".join(word.strip().lower().split())
        normalized_language = language.strip().lower()
        return f"{normalized_language}:{normalized_word}"
