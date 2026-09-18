"""Language display helpers for small UI polish."""

from __future__ import annotations

LANGUAGE_FLAGS = {
    "english": "\U0001F1EC\U0001F1E7/\U0001F1FA\U0001F1F8",
    "spanish": "\U0001F1EA\U0001F1F8",
    "french": "\U0001F1EB\U0001F1F7",
}


def format_language_label(language: str) -> str:
    """Return a language label with a flag when one is available."""
    normalized_language = str(language).strip().lower()
    flag = LANGUAGE_FLAGS.get(normalized_language)
    title = normalized_language.title()
    return f"{flag} {title}" if flag else title
