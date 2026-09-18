"""Validation and import helpers for JSON word-bank files."""

from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

from src.utils.constants import (
    CONTENT_MIN_WORDS_PER_LANGUAGE,
    CONTENT_MIN_WORDS_PER_LANGUAGE_CATEGORY,
    CONTENT_MIN_WORDS_PER_LANGUAGE_DIFFICULTY,
    DIFFICULTY_ORDER,
    SITUATIONS,
    WORD_CATEGORIES,
)
from src.utils.helpers import load_json_file, serialize_json

REQUIRED_WORD_FIELDS = (
    "word_id",
    "word",
    "meaning",
    "language",
    "situations",
    "category",
    "difficulty",
    "hint",
    "translation",
    "example_sentence",
    "sentence_translation",
    "pronunciation_text",
    "usage_note",
    "synonym",
    "association",
    "synonym_hint",
    "association_hint",
)
OPTIONAL_WORD_FIELDS = (
    "tags",
    "subcategory",
    "source",
    "notes",
    "meaning_hint",
    "synonym_hint",
    "association_hint",
)
GENERIC_EXAMPLE_PATTERNS = (
    "appears in today's reading practice",
    "aparece en la lectura de hoy",
    "apparait dans la lecture du jour",
    "example sentence",
    "use {word} in context",
)
WEAK_USAGE_PATTERNS = (
    "use this",
    "when talking about",
    "in a restaurant situation",
    "in a office situation",
)
OBVIOUS_ACCENT_WARNINGS = {
    "spanish": {
        "jardin": "jardín",
        "musica": "música",
        "rapido": "rápido",
        "telefono": "teléfono",
        "cafe": "café",
        "facil": "fácil",
        "dificil": "difícil",
        "tambien": "también",
    },
    "french": {
        "apparait": "apparaît",
        "ecole": "école",
        "cafe": "café",
        "hotel": "hôtel",
        "rapide": "rapide",
        "tres": "très",
        "deja": "déjà",
    },
}


def scan_word_bank_files(words_dir: Path) -> list[Path]:
    """Return JSON word-bank files in a deterministic order."""
    return sorted(Path(words_dir).glob("*.json"))


def validate_word_bank_file(file_path: Path, *, include_rows: bool = False) -> dict[str, Any]:
    """Validate one word-bank JSON file and return a compact summary."""
    summary = _validate_word_bank_file_internal(file_path)
    return _strip_internal_file_summary(summary, include_rows=include_rows)


def validate_word_bank_payload(
    payload: dict[str, Any],
    *,
    source_name: str = "uploaded.json",
    include_rows: bool = False,
) -> dict[str, Any]:
    """Validate one in-memory word-bank payload from a UI upload."""
    summary = _validate_word_bank_payload_internal(
        payload=payload,
        source_name=source_name,
        fallback_language=Path(source_name).stem.lower(),
    )
    _apply_directory_duplicate_detection([summary])
    return _strip_internal_file_summary(summary, include_rows=include_rows)


def validate_word_bank_directory(words_dir: Path, *, include_rows: bool = False) -> dict[str, Any]:
    """Validate all word-bank files and report coverage across the full corpus."""
    file_summaries = [
        _validate_word_bank_file_internal(file_path)
        for file_path in scan_word_bank_files(words_dir)
    ]
    _apply_directory_duplicate_detection(file_summaries)

    rows = [row for file_summary in file_summaries for row in file_summary["_rows"]]
    coverage = _build_content_coverage(rows)
    public_file_summaries = [
        _strip_internal_file_summary(file_summary, include_rows=include_rows)
        for file_summary in file_summaries
    ]

    return {
        "files": public_file_summaries,
        "files_processed": len(public_file_summaries),
        "valid_words": sum(
            int(file_summary["valid_words"]) for file_summary in public_file_summaries
        ),
        "invalid_words": sum(
            int(file_summary["invalid_words"]) for file_summary in public_file_summaries
        ),
        "duplicate_words": sum(
            int(file_summary["duplicate_words"]) for file_summary in public_file_summaries
        ),
        "quality_warning_count": sum(
            len(file_summary["warnings"]) for file_summary in public_file_summaries
        ),
        "has_errors": any(file_summary["errors"] for file_summary in public_file_summaries),
        "coverage": coverage,
    }


def build_seed_rows(words_dir: Path) -> dict[str, Any]:
    """Return normalized seed rows and validation summary for import."""
    directory_summary = validate_word_bank_directory(words_dir, include_rows=True)
    rows = [
        (
            row["word_id"],
            row["word"],
            row["meaning"],
            row["language"],
            row["situations"],
            row["category"],
            row["difficulty"],
            row["hint"],
            row["translation"],
            row["example_sentence"],
            row["sentence_translation"],
            row["pronunciation_text"],
            row["usage_note"],
            row["synonym"],
            row["association"],
            row["meaning_hint"],
            row["synonym_hint"],
            row["association_hint"],
            row["tags"],
            row["subcategory"],
            row["source"],
            row["notes"],
            row["source_file"],
        )
        for file_summary in directory_summary["files"]
        for row in file_summary.get("rows", [])
    ]
    return {
        **directory_summary,
        "rows": rows,
    }


def build_seed_rows_from_payload(
    payload: dict[str, Any],
    *,
    source_name: str = "uploaded.json",
) -> dict[str, Any]:
    """Return normalized seed rows for one uploaded word-bank payload."""
    file_summary = validate_word_bank_payload(
        payload,
        source_name=source_name,
        include_rows=True,
    )
    rows = [
        (
            row["word_id"],
            row["word"],
            row["meaning"],
            row["language"],
            row["situations"],
            row["category"],
            row["difficulty"],
            row["hint"],
            row["translation"],
            row["example_sentence"],
            row["sentence_translation"],
            row["pronunciation_text"],
            row["usage_note"],
            row["synonym"],
            row["association"],
            row["meaning_hint"],
            row["synonym_hint"],
            row["association_hint"],
            row["tags"],
            row["subcategory"],
            row["source"],
            row["notes"],
            source_name,
        )
        for row in file_summary.get("rows", [])
    ]
    return {
        "files": [file_summary],
        "files_processed": 1,
        "valid_words": int(file_summary["valid_words"]),
        "invalid_words": int(file_summary["invalid_words"]),
        "duplicate_words": int(file_summary["duplicate_words"]),
        "quality_warning_count": len(file_summary["warnings"]),
        "has_errors": bool(file_summary["errors"]),
        "coverage": _build_content_coverage(file_summary.get("rows", [])),
        "rows": rows,
    }


def ensure_word_bank_hint_fields(words_dir: Path) -> dict[str, Any]:
    """Fill missing hint alias fields in JSON word banks without overwriting content."""
    updated_files: list[str] = []
    filled_counts = {
        "meaning_hint": 0,
        "synonym_hint": 0,
        "association_hint": 0,
    }

    for file_path in scan_word_bank_files(words_dir):
        try:
            payload = load_json_file(file_path)
        except Exception:
            continue
        if not isinstance(payload, dict) or not isinstance(payload.get("words"), list):
            continue

        file_changed = False
        for raw_word in payload["words"]:
            if not isinstance(raw_word, dict):
                continue
            changed_fields = _fill_missing_hint_fields(
                raw_word, default_language=payload.get("language")
            )
            if changed_fields:
                file_changed = True
                for field_name in changed_fields:
                    filled_counts[field_name] += 1

        if file_changed:
            file_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            updated_files.append(file_path.name)

    xlsx_summary = _backup_words_xlsx_if_present(Path(words_dir).resolve().parents[1])

    return {
        "updated_files": updated_files,
        "filled_counts": filled_counts,
        "xlsx": xlsx_summary,
    }


def _validate_word_bank_file_internal(file_path: Path) -> dict[str, Any]:
    """Validate one file while retaining internal row keys for directory checks."""
    try:
        payload = load_json_file(file_path)
    except Exception as error:
        summary = _empty_file_summary(
            source_name=file_path.name, fallback_language=file_path.stem.lower()
        )
        summary["errors"].append(f"Unable to read JSON: {error}")
        return summary

    return _validate_word_bank_payload_internal(
        payload=payload,
        source_name=file_path.name,
        fallback_language=file_path.stem.lower(),
    )


def _validate_word_bank_payload_internal(
    *,
    payload: dict[str, Any],
    source_name: str,
    fallback_language: str,
) -> dict[str, Any]:
    """Validate one payload while retaining internal row keys for duplicate checks."""
    summary = _empty_file_summary(source_name=source_name, fallback_language=fallback_language)

    if not isinstance(payload, dict):
        summary["errors"].append("The uploaded JSON must be an object.")
        return summary

    default_language = _normalize_string(payload.get("language"))
    summary["language"] = default_language or fallback_language
    words = payload.get("words", [])
    if not isinstance(words, list):
        summary["errors"].append("The top-level 'words' field must be a list.")
        return summary

    for index, raw_word in enumerate(words, start=1):
        normalized_word, issues = _normalize_word_entry(
            raw_word=raw_word,
            default_language=summary["language"],
        )
        if issues:
            summary["invalid_words"] += 1
            summary["errors"].append(f"Row {index}: {'; '.join(issues)}")
            continue

        normalized_word["source_file"] = source_name
        normalized_word["_source_index"] = index
        normalized_word["_normalized_key"] = _build_normalized_word_key(
            word=normalized_word["word"],
            language=normalized_word["language"],
        )
        for warning in _build_quality_warnings(normalized_word):
            summary["warnings"].append(
                f"Row {index} ({normalized_word['word']}): {warning}"
            )
        summary["_rows"].append(normalized_word)
        summary["valid_words"] += 1

    if not summary["_rows"]:
        summary["warnings"].append("No valid words were found in this file.")

    return summary


def _empty_file_summary(source_name: str, fallback_language: str) -> dict[str, Any]:
    """Return a blank internal file summary."""
    summary: dict[str, Any] = {
        "file": source_name,
        "language": fallback_language,
        "valid_words": 0,
        "invalid_words": 0,
        "duplicate_words": 0,
        "errors": [],
        "warnings": [],
        "_rows": [],
    }
    return summary


def _apply_directory_duplicate_detection(file_summaries: list[dict[str, Any]]) -> None:
    """Mark duplicate normalized word/language pairs as invalid after the first row."""
    seen_keys: dict[str, dict[str, Any]] = {}

    for file_summary in file_summaries:
        unique_rows: list[dict[str, Any]] = []
        for row in file_summary["_rows"]:
            normalized_key = str(row["_normalized_key"])
            if normalized_key in seen_keys:
                first_seen = seen_keys[normalized_key]
                file_summary["valid_words"] -= 1
                file_summary["invalid_words"] += 1
                file_summary["duplicate_words"] += 1
                file_summary["errors"].append(
                    "Row "
                    f"{row['_source_index']}: Duplicate word/language pair "
                    f"'{row['word']}' / '{row['language']}' already appears in "
                    f"{first_seen['source_file']} row {first_seen['_source_index']}."
                )
                continue

            seen_keys[normalized_key] = row
            unique_rows.append(row)

        file_summary["_rows"] = unique_rows


def _build_content_coverage(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build corpus-level coverage counts and weak-area warnings."""
    total_by_language = Counter(row["language"] for row in rows)
    by_category = Counter(row["category"] for row in rows)
    by_difficulty = Counter(row["difficulty"] for row in rows)
    by_situation: Counter[str] = Counter()
    by_language_category = Counter((row["language"], row["category"]) for row in rows)
    by_language_difficulty = Counter((row["language"], row["difficulty"]) for row in rows)
    for row in rows:
        for situation in _deserialize_situations(row.get("situations")):
            by_situation[situation] += 1

    languages = sorted(total_by_language)
    weak_coverage_areas: list[str] = []

    for language in languages:
        if total_by_language[language] < CONTENT_MIN_WORDS_PER_LANGUAGE:
            weak_coverage_areas.append(
                f"{language}: only {total_by_language[language]} total words "
                f"(minimum {CONTENT_MIN_WORDS_PER_LANGUAGE})."
            )

        for category in WORD_CATEGORIES:
            count = by_language_category[(language, category)]
            if count < CONTENT_MIN_WORDS_PER_LANGUAGE_CATEGORY:
                weak_coverage_areas.append(
                    f"{language}/{category}: only {count} words "
                    f"(minimum {CONTENT_MIN_WORDS_PER_LANGUAGE_CATEGORY})."
                )

        for difficulty in DIFFICULTY_ORDER:
            count = by_language_difficulty[(language, difficulty)]
            if count < CONTENT_MIN_WORDS_PER_LANGUAGE_DIFFICULTY:
                weak_coverage_areas.append(
                    f"{language}/{difficulty}: only {count} words "
                    f"(minimum {CONTENT_MIN_WORDS_PER_LANGUAGE_DIFFICULTY})."
                )

    return {
        "total_words_by_language": dict(sorted(total_by_language.items())),
        "words_by_category": dict(sorted(by_category.items())),
        "words_by_difficulty": dict(sorted(by_difficulty.items())),
        "words_by_situation": dict(sorted(by_situation.items())),
        "words_by_language_category": {
            f"{language}:{category}": count
            for (language, category), count in sorted(by_language_category.items())
        },
        "words_by_language_difficulty": {
            f"{language}:{difficulty}": count
            for (language, difficulty), count in sorted(by_language_difficulty.items())
        },
        "weak_coverage_areas": weak_coverage_areas,
        "meets_minimum_coverage": not weak_coverage_areas,
    }


def _normalize_word_entry(
    raw_word: Any,
    default_language: str,
) -> tuple[dict[str, Any], list[str]]:
    """Return a normalized word entry plus any validation issues."""
    if not isinstance(raw_word, dict):
        return {}, ["Entry must be a JSON object."]

    issues: list[str] = []
    word_id = _normalize_text(raw_word.get("word_id"))
    word = _normalize_string(raw_word.get("word"))
    meaning = _normalize_text(raw_word.get("meaning"))
    language = _normalize_string(raw_word.get("language")) or default_language
    situations = _normalize_situations(raw_word.get("situations"))
    category = _normalize_string(raw_word.get("category"))
    difficulty = _normalize_string(raw_word.get("difficulty"))
    hint = _normalize_text(raw_word.get("hint"))
    meaning_hint = _normalize_text(raw_word.get("meaning_hint")) or hint
    translation = _normalize_text(raw_word.get("translation"))
    example_sentence = _normalize_text(raw_word.get("example_sentence"))
    sentence_translation = _normalize_text(raw_word.get("sentence_translation"))
    pronunciation_text = _normalize_text(raw_word.get("pronunciation_text"))
    usage_note = _normalize_text(raw_word.get("usage_note"))
    synonym = _normalize_text(raw_word.get("synonym"))
    association = _normalize_text(raw_word.get("association"))
    synonym_hint = _normalize_text(raw_word.get("synonym_hint")) or synonym
    association_hint = _normalize_text(raw_word.get("association_hint")) or association

    if not word_id:
        issues.append("Missing required field 'word_id'.")
    if not word:
        issues.append("Missing required field 'word'.")
    if not meaning:
        issues.append("Missing required field 'meaning'.")
    if not language:
        issues.append("Missing required field 'language'.")
    if not situations:
        issues.append("Missing required field 'situations'.")
    else:
        unsupported_situations = [
            situation for situation in situations if situation not in SITUATIONS
        ]
        if unsupported_situations:
            issues.append(
                "Unsupported situation(s): "
                + ", ".join(sorted(unsupported_situations))
                + "."
            )
    if not category:
        issues.append("Missing required field 'category'.")
    elif category not in WORD_CATEGORIES:
        issues.append(f"Unsupported category '{category}'.")
    if not difficulty:
        issues.append("Missing required field 'difficulty'.")
    elif difficulty not in DIFFICULTY_ORDER:
        issues.append(f"Unsupported difficulty '{difficulty}'.")
    if not hint:
        issues.append("Missing required field 'hint'.")
    if not translation:
        issues.append("Missing required field 'translation'.")
    if not example_sentence:
        issues.append("Missing required field 'example_sentence'.")
    if not sentence_translation:
        issues.append("Missing required field 'sentence_translation'.")
    if not pronunciation_text:
        issues.append("Missing required field 'pronunciation_text'.")
    if not usage_note:
        issues.append("Missing required field 'usage_note'.")
    if not synonym:
        issues.append("Missing required field 'synonym'.")
    if not association:
        issues.append("Missing required field 'association'.")
    if not synonym_hint:
        issues.append("Missing required field 'synonym_hint'.")
    if not association_hint:
        issues.append("Missing required field 'association_hint'.")

    if issues:
        return {}, issues

    return {
        "word_id": word_id,
        "word": word,
        "meaning": meaning,
        "language": language,
        "situations": serialize_json(situations),
        "category": category,
        "difficulty": difficulty,
        "hint": hint,
        "meaning_hint": meaning_hint,
        "translation": translation,
        "example_sentence": example_sentence,
        "sentence_translation": sentence_translation,
        "pronunciation_text": pronunciation_text,
        "usage_note": usage_note,
        "synonym": synonym,
        "association": association,
        "synonym_hint": synonym_hint,
        "association_hint": association_hint,
        "tags": _normalize_tags(raw_word.get("tags")),
        "subcategory": _normalize_text(raw_word.get("subcategory")),
        "source": _normalize_text(raw_word.get("source")),
        "notes": _normalize_text(raw_word.get("notes")),
    }, []


def _build_quality_warnings(row: dict[str, Any]) -> list[str]:
    """Return non-blocking content quality warnings for learner-facing copy."""
    warnings: list[str] = []
    word = str(row["word"])
    language = str(row["language"])
    example_sentence = str(row["example_sentence"])
    pronunciation_text = str(row["pronunciation_text"])
    usage_note = str(row["usage_note"])
    situations = _deserialize_situations(row.get("situations"))

    if _looks_generic_example(example_sentence, word):
        warnings.append(
            "Example sentence looks generic; replace it with a natural learner scenario."
        )

    if pronunciation_text.strip().lower() == word.strip().lower():
        warnings.append(
            "Pronunciation text matches the word exactly; add learner-friendly guidance."
        )

    accent_warning = _build_accent_warning(
        language=language,
        word=word,
        example_sentence=example_sentence,
    )
    if accent_warning:
        warnings.append(accent_warning)

    if _looks_weak_usage_note(usage_note):
        warnings.append(
            "Usage note looks templated; make it explain when a learner would say this word."
        )

    if situations and not _usage_note_mentions_any_situation(usage_note, situations):
        warnings.append(
            "Usage note may not match the assigned situation(s); mention a concrete context."
        )

    return warnings


def _looks_generic_example(example_sentence: str, word: str) -> bool:
    """Return whether an example sentence appears templated or low-value."""
    normalized = example_sentence.strip().lower()
    word_key = word.strip().lower()
    for pattern in GENERIC_EXAMPLE_PATTERNS:
        if pattern.format(word=word_key) in normalized:
            return True
    return normalized in {word_key, f"{word_key}."}


def _build_accent_warning(
    *,
    language: str,
    word: str,
    example_sentence: str,
) -> str | None:
    """Return a warning for obvious accent omissions in curated content."""
    replacements = OBVIOUS_ACCENT_WARNINGS.get(language, {})
    if not replacements:
        return None

    haystack = f" {word.lower()} {example_sentence.lower()} "
    missing = [
        f"{plain} -> {accented}"
        for plain, accented in replacements.items()
        if f" {plain} " in haystack
    ]
    if not missing:
        return None
    return "Possible missing accent(s): " + ", ".join(missing) + "."


def _looks_weak_usage_note(usage_note: str) -> bool:
    """Return whether the usage note is probably generated/template copy."""
    normalized = usage_note.strip().lower()
    return any(pattern in normalized for pattern in WEAK_USAGE_PATTERNS)


def _usage_note_mentions_any_situation(usage_note: str, situations: list[str]) -> bool:
    """Return whether a usage note names at least one assigned situation."""
    normalized_note = usage_note.lower().replace("/", "_").replace(" ", "_")
    for situation in situations:
        normalized_situation = str(situation).lower()
        if normalized_situation in normalized_note:
            return True
        if normalized_situation == "metro_train_station" and (
            "metro" in normalized_note or "train" in normalized_note
        ):
            return True
        if normalized_situation == "school_college" and (
            "school" in normalized_note or "college" in normalized_note
        ):
            return True
    return False


def _fill_missing_hint_fields(raw_word: dict[str, Any], default_language: Any = None) -> list[str]:
    """Fill missing hint aliases for one raw JSON word row."""
    changed_fields: list[str] = []
    category = _normalize_string(raw_word.get("category")) or "language"
    language = (
        _normalize_string(raw_word.get("language"))
        or _normalize_string(default_language)
        or "language"
    )
    meaning_source = _normalize_text(raw_word.get("hint")) or f"common {category} word"

    fallback_values = {
        "meaning_hint": meaning_source,
        "synonym_hint": (
            _normalize_text(raw_word.get("synonym")) or f"Related meaning: {meaning_source}"
        ),
        "association_hint": (
            _normalize_text(raw_word.get("association"))
            or f"Often connected with: {category} in {language} practice."
        ),
    }

    for field_name, fallback_value in fallback_values.items():
        if not _normalize_text(raw_word.get(field_name)):
            raw_word[field_name] = fallback_value
            changed_fields.append(field_name)
    return changed_fields


def _backup_words_xlsx_if_present(project_root: Path) -> dict[str, Any]:
    """Back up words.xlsx if present; JSON is the active word-bank format here."""
    words_xlsx_path = project_root / "words.xlsx"
    if not words_xlsx_path.exists():
        return {
            "found": False,
            "backup_path": None,
            "updated": False,
            "message": "No words.xlsx file found.",
        }

    backup_path = project_root / "words_backup_before_hint_update.xlsx"
    if not backup_path.exists():
        shutil.copy2(words_xlsx_path, backup_path)

    # openpyxl is intentionally not a project dependency. If it is installed locally,
    # we add the columns; otherwise the backup still preserves the file safely.
    try:
        from openpyxl import load_workbook  # type: ignore[import-not-found]
    except Exception:
        return {
            "found": True,
            "backup_path": str(backup_path),
            "updated": False,
            "message": "Backed up words.xlsx; install openpyxl to edit workbook hint columns.",
        }

    workbook = load_workbook(words_xlsx_path)
    sheet = workbook.active
    headers = [cell.value for cell in sheet[1]]
    required_headers = ["meaning_hint", "synonym_hint", "association_hint"]
    for header in required_headers:
        if header not in headers:
            sheet.cell(row=1, column=len(headers) + 1, value=header)
            headers.append(header)
    workbook.save(words_xlsx_path)
    return {
        "found": True,
        "backup_path": str(backup_path),
        "updated": True,
        "message": "Backed up and added missing workbook hint columns.",
    }


def _build_normalized_word_key(word: str, language: str) -> str:
    """Return the duplicate-detection key for one word."""
    normalized_word = " ".join(str(word).strip().lower().split())
    normalized_language = str(language).strip().lower()
    return f"{normalized_language}:{normalized_word}"


def _normalize_string(value: Any) -> str | None:
    """Normalize a short identifier-style string."""
    if value is None:
        return None
    normalized = str(value).strip().lower()
    return normalized or None


def _normalize_text(value: Any) -> str | None:
    """Normalize freeform display text."""
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _normalize_tags(value: Any) -> str:
    """Normalize tags into a JSON string for SQLite storage."""
    if value is None:
        return "[]"
    if isinstance(value, list):
        cleaned_values = [str(tag).strip().lower() for tag in value if str(tag).strip()]
        return serialize_json(cleaned_values)
    if isinstance(value, str):
        tags = [tag.strip().lower() for tag in value.split(",") if tag.strip()]
        return serialize_json(tags)
    return "[]"


def _normalize_situations(value: Any) -> list[str]:
    """Normalize one or more situation labels into stored keys."""
    if value is None:
        return []
    if isinstance(value, list):
        raw_values = value
    elif isinstance(value, str):
        raw_values = value.split(",")
    else:
        return []
    normalized_values = [
        str(item).strip().lower().replace("/", "_").replace(" ", "_").replace("-", "_")
        for item in raw_values
        if str(item).strip()
    ]
    aliases = {
        "train_station": "metro_train_station",
        "metro": "metro_train_station",
        "metro_station": "metro_train_station",
        "school": "school_college",
        "college": "school_college",
    }
    return list(
        dict.fromkeys(aliases.get(situation, situation) for situation in normalized_values)
    )


def _deserialize_situations(value: Any) -> list[str]:
    """Return situation keys from a stored JSON string or raw list."""
    if isinstance(value, list):
        return _normalize_situations(value)
    if isinstance(value, str):
        try:
            parsed_value = json.loads(value)
        except json.JSONDecodeError:
            return _normalize_situations(value)
        return _normalize_situations(parsed_value)
    return []


def _strip_internal_file_summary(
    file_summary: dict[str, Any],
    *,
    include_rows: bool,
) -> dict[str, Any]:
    """Return the public version of a file summary."""
    public_summary = {
        "file": file_summary["file"],
        "language": file_summary["language"],
        "valid_words": file_summary["valid_words"],
        "invalid_words": file_summary["invalid_words"],
        "duplicate_words": file_summary["duplicate_words"],
        "errors": list(file_summary["errors"]),
        "warnings": list(file_summary["warnings"]),
    }
    if include_rows:
        public_summary["rows"] = [_strip_internal_row_keys(row) for row in file_summary["_rows"]]
    return public_summary


def _strip_internal_row_keys(row: dict[str, Any]) -> dict[str, Any]:
    """Remove validation-only row metadata before returning rows to callers."""
    return {key: value for key, value in row.items() if not key.startswith("_")}
