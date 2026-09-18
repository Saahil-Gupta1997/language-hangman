"""Progressive hint reveal rules for Hangman rounds."""

from __future__ import annotations

from typing import Any

AUTO_HINT_ORDER = ("hint", "synonym", "association")
EASY_HINT_ORDER = ("meaning", "synonym", "association")
EXTENDED_HINT_ORDER = (
    "meaning",
    "hint",
    "synonym",
    "association",
)
MANUAL_REVEAL_HINTS = ("synonym", "association")


HINT_LABELS = {
    "hint": "Hint",
    "meaning": "Meaning Hint",
    "synonym": "Synonym",
    "association": "Association",
}


def sync_auto_revealed_hints(round_state: Any) -> dict[str, str]:
    """Reveal hints according to the old normal/hard-mode lives rules."""
    available_hints = build_available_hints(round_state)
    if not available_hints:
        return {}

    if round_state.hint_mode == "hard":
        if round_state.remaining_attempts <= 2:
            _append_new_hint_keys(round_state, available_hints.keys())
        return get_revealed_hints(round_state)

    if round_state.hint_mode == "easy":
        easy_unlocks = (
            (1, "meaning"),
            (3, "synonym"),
            (5, "association"),
        )
        for wrong_guess_count, hint_key in easy_unlocks:
            if round_state.letters_wrong >= wrong_guess_count and hint_key in available_hints:
                _append_new_hint_keys(round_state, [hint_key])
        return get_revealed_hints(round_state)

    # Keep the legacy lives cadence: max_lives - 1, -3, and -5.
    hint_intervals = [
        round_state.max_attempts - 1,
        round_state.max_attempts - 3,
        round_state.max_attempts - 5,
    ]
    auto_hint_keys = [key for key in AUTO_HINT_ORDER if key in available_hints]
    for index, lives_threshold in enumerate(hint_intervals):
        if index >= len(auto_hint_keys):
            continue
        if round_state.remaining_attempts <= lives_threshold:
            _append_new_hint_keys(round_state, [auto_hint_keys[index]])

    return get_revealed_hints(round_state)


def reveal_manual_hint(round_state: Any, hint_key: str) -> bool:
    """Reveal a clicked hint if it has useful text."""
    normalized_key = str(hint_key).strip().lower()
    if normalized_key not in MANUAL_REVEAL_HINTS:
        return False

    available_hints = build_available_hints(round_state)
    if normalized_key not in available_hints:
        return False

    _append_new_hint_keys(round_state, [normalized_key])
    return True


def get_revealed_hints(round_state: Any) -> dict[str, str]:
    """Return only revealed, non-blank hints in display order."""
    available_hints = build_available_hints(round_state)
    return {
        key: available_hints[key]
        for key in EXTENDED_HINT_ORDER
        if key in round_state.revealed_hint_keys and key in available_hints
    }


def build_available_hints(round_state: Any) -> dict[str, str]:
    """Return clue text with safe fallbacks so revealed panels are never blank.

    During active play we intentionally avoid translation/example/usage content.
    Full learning details are reserved for the post-round learning card.
    """
    category_fallback = _build_category_fallback(round_state)
    meaning_fallback = _build_meaning_fallback(round_state)
    association = (
        _clean_hint_value(getattr(round_state, "association_hint", None))
        or _clean_hint_value(getattr(round_state, "association", None))
        or category_fallback
    )
    synonym = (
        _clean_hint_value(getattr(round_state, "synonym_hint", None))
        or _clean_hint_value(getattr(round_state, "synonym", None))
        or association
        or category_fallback
    )
    hint = _clean_hint_value(getattr(round_state, "hint", None)) or category_fallback
    meaning = (
        _clean_hint_value(getattr(round_state, "meaning_hint", None))
        or hint
        or meaning_fallback
    )

    resolved_hints = {
        "meaning": meaning,
        "hint": hint,
        "synonym": synonym,
        "association": association,
    }
    return resolved_hints


def _append_new_hint_keys(round_state: Any, hint_keys: Any) -> None:
    """Add hint keys without duplicates while preserving reveal order."""
    for hint_key in hint_keys:
        if hint_key not in round_state.revealed_hint_keys:
            round_state.revealed_hint_keys.append(hint_key)


def _clean_hint_value(value: Any) -> str | None:
    """Return stripped text or None for empty/placeholder hint values."""
    if value is None:
        return None
    cleaned_value = str(value).strip()
    if not cleaned_value or cleaned_value.upper() == "N/A":
        return None
    return cleaned_value


def _build_category_fallback(round_state: Any) -> str:
    """Return the final safe hint text when content fields are missing."""
    category = _clean_hint_value(getattr(round_state, "category", None)) or "language"
    return f"Think of a common {category} word."


def _build_meaning_fallback(round_state: Any) -> str:
    """Return a meaning-style fallback for Easy Mode hint unlocks."""
    category = _clean_hint_value(getattr(round_state, "category", None)) or "language"
    return f"Related meaning: common {category} word."
