"""Tests for JSON and database-backed word loading."""

import json
import random

from src.db.database import init_db
from src.services.word_service import WordService
from src.utils.constants import WORD_CATEGORIES


def test_load_word_bank_returns_expected_fields() -> None:
    words = WordService().load_word_bank("english")

    assert words
    first_word = words[0]
    assert {
        "word",
        "word_id",
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
        "meaning_hint",
        "synonym_hint",
        "association_hint",
    }.issubset(first_word.keys())


def test_get_words_can_filter_by_category(tmp_path) -> None:
    db_path = tmp_path / "word_filtering.db"
    init_db(db_path=db_path, seed_words=True)

    service = WordService(db_path=db_path)
    verb_words = service.get_words(language="english", category="verb")

    assert verb_words
    assert all(word["category"] == "verb" for word in verb_words)
    assert set(service.get_categories("english")).issuperset(WORD_CATEGORIES)


def test_reload_word_banks_preserves_custom_hint_aliases(tmp_path) -> None:
    db_path = tmp_path / "hint_aliases.db"
    words_dir = tmp_path / "words"
    words_dir.mkdir()
    (words_dir / "english.json").write_text(
        json.dumps(
            {
                "language": "english",
                "words": [
                    {
                        "word": "lantern",
                        "word_id": "english_lantern",
                        "meaning": "lantern",
                        "language": "english",
                        "situations": ["hotel"],
                        "category": "noun",
                        "difficulty": "beginner",
                        "hint": "Base hint.",
                        "meaning_hint": "Custom meaning hint.",
                        "translation": "lantern",
                        "example_sentence": "The lantern glowed softly.",
                        "sentence_translation": "The lantern glowed softly.",
                        "pronunciation_text": "lantern",
                        "usage_note": "Use lantern when talking about light in a hotel.",
                        "synonym": "lamp",
                        "synonym_hint": "Custom synonym hint.",
                        "association": "Camping light.",
                        "association_hint": "Custom association hint.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    init_db(db_path=db_path, seed_words=False)

    service = WordService(words_dir=words_dir, db_path=db_path)
    service.reload_word_banks()
    [word] = service.get_words("english")

    assert word["hint"] == "Base hint."
    assert word["meaning_hint"] == "Custom meaning hint."
    assert word["synonym"] == "lamp"
    assert word["synonym_hint"] == "Custom synonym hint."
    assert word["association"] == "Camping light."
    assert word["association_hint"] == "Custom association hint."


def test_select_word_respects_category_and_level_preferences(tmp_path) -> None:
    db_path = tmp_path / "word_selection.db"
    init_db(db_path=db_path, seed_words=True)

    service = WordService(db_path=db_path)
    selected_word = service.select_word(
        language="english",
        level="advanced",
        preferred_categories=["adverb"],
        selected_category="adverb",
        rng=random.Random(7),
    )

    assert selected_word["category"] == "adverb"
    assert selected_word["difficulty"] in {"intermediate", "advanced"}


def test_select_word_avoids_recent_word_ids_when_possible(tmp_path) -> None:
    db_path = tmp_path / "recent_exclusion.db"
    init_db(db_path=db_path, seed_words=True)

    service = WordService(db_path=db_path)
    recent_word = service.get_words("english", category="noun", difficulty="advanced")[0]

    selected_word = service.select_word(
        language="english",
        level="advanced",
        preferred_categories=["noun"],
        selected_category="noun",
        excluded_word_ids=[recent_word["id"]],
        rng=random.Random(11),
    )

    assert selected_word["category"] == "noun"
    assert selected_word["id"] != recent_word["id"]
