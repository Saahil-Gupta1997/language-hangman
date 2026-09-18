"""Tests for situation-based learning, mastery, and weak-word review."""

from __future__ import annotations

import json

from src.db.database import init_db
from src.db.repository import WordProgressRepository
from src.services.auth_service import AuthService
from src.services.game_service import GameService
from src.services.hint_service import get_revealed_hints, sync_auto_revealed_hints
from src.services.word_service import WordService
from src.utils.word_bank_loader import validate_word_bank_payload


def _win_round(game_service: GameService, round_state) -> None:
    """Solve a round by guessing each unique letter once."""
    for letter in sorted(round_state.unique_letters):
        if round_state.is_complete:
            break
        game_service.record_guess(round_state, letter)


def _lose_round(game_service: GameService, round_state) -> None:
    """Lose a round using letters that are not in the target word."""
    wrong_letters = [
        letter for letter in "bcdfghjklmnpqrstvwxyz" if letter not in round_state.unique_letters
    ]
    for letter in wrong_letters[: round_state.max_attempts]:
        if round_state.is_complete:
            break
        game_service.record_guess(round_state, letter)


def test_word_selection_filters_by_selected_situation(tmp_path) -> None:
    db_path = tmp_path / "situation_filter.db"
    init_db(db_path=db_path, seed_words=True)
    word_service = WordService(db_path=db_path)

    restaurant_words = word_service.get_words(
        "english",
        difficulties=["beginner"],
        situation="restaurant",
    )

    assert restaurant_words
    assert all("restaurant" in word["situations"] for word in restaurant_words)
    assert "restaurant" in word_service.get_available_situations("english")


def test_game_hints_do_not_reveal_learning_content_before_completion(tmp_path) -> None:
    db_path = tmp_path / "hidden_learning_content.db"
    init_db(db_path=db_path, seed_words=True)
    auth_service = AuthService(db_path=db_path)
    game_service = GameService(db_path=db_path)
    user = auth_service.register_user(
        username="situationalhints",
        password="secret123",
        target_language="english",
        level="beginner",
    )

    outcome = game_service.start_custom_learning_session(
        user=user,
        builder_settings={
            "language": "english",
            "situation": "airport",
            "practice_mode": "standard",
            "categories": ["noun", "verb", "adjective", "adverb"],
            "difficulties": ["beginner"],
            "rounds": 1,
            "review_policy": "prefer_review",
            "game_mode": "easy",
        },
    )
    round_state = outcome["first_round"]
    wrong_letter = next(
        letter for letter in "bcdfghjklmnpqrstvwxyz" if letter not in round_state.unique_letters
    )
    game_service.record_guess(round_state, wrong_letter)
    sync_auto_revealed_hints(round_state)
    revealed_hints = set(get_revealed_hints(round_state).values())

    assert round_state.situation == "airport"
    assert round_state.translation not in revealed_hints
    assert round_state.example_sentence not in revealed_hints
    assert round_state.usage_note not in revealed_hints


def test_post_round_learning_card_contains_situational_learning_fields(tmp_path) -> None:
    db_path = tmp_path / "learning_card.db"
    init_db(db_path=db_path, seed_words=True)
    auth_service = AuthService(db_path=db_path)
    game_service = GameService(db_path=db_path)
    user = auth_service.register_user(
        username="learningcard",
        password="secret123",
        target_language="english",
        level="beginner",
        preferred_categories=["noun"],
    )
    outcome = game_service.start_custom_learning_session(
        user=user,
        builder_settings={
            "language": "english",
            "situation": "restaurant",
            "practice_mode": "standard",
            "categories": ["noun"],
            "difficulties": ["beginner"],
            "rounds": 1,
            "review_policy": "prefer_review",
            "game_mode": "easy",
        },
    )
    learning_session = outcome["learning_session"]
    round_state = outcome["first_round"]
    _win_round(game_service, round_state)

    result = game_service.finalize_round(
        user=user,
        round_state=round_state,
        learning_session=learning_session,
    )
    review = result["learning_review"]

    assert review["word"]
    assert review["meaning"]
    assert review["situation"] == "restaurant"
    assert review["example_sentence"]
    assert review["sentence_translation"]
    assert review["pronunciation_text"]
    assert review["usage_note"]
    assert review["mastery_status"] in {"weak", "learning", "almost_mastered", "mastered"}


def test_weak_word_review_prioritizes_low_mastery_situation_words(tmp_path) -> None:
    db_path = tmp_path / "weak_words.db"
    init_db(db_path=db_path, seed_words=True)
    auth_service = AuthService(db_path=db_path)
    game_service = GameService(db_path=db_path)
    progress_repository = WordProgressRepository(db_path=db_path)
    user = auth_service.register_user(
        username="weakreviewer",
        password="secret123",
        target_language="english",
        level="beginner",
        preferred_categories=["noun"],
    )
    initial = game_service.start_custom_learning_session(
        user=user,
        builder_settings={
            "language": "english",
            "situation": "restaurant",
            "practice_mode": "standard",
            "categories": ["noun"],
            "difficulties": ["beginner"],
            "rounds": 1,
            "review_policy": "prefer_review",
            "game_mode": "easy",
        },
    )
    lost_round = initial["first_round"]
    _lose_round(game_service, lost_round)
    game_service.finalize_round(
        user=user,
        round_state=lost_round,
        learning_session=initial["learning_session"],
    )

    progress = progress_repository.get_item(user["id"], lost_round.word_id)
    weak_review = game_service.start_custom_learning_session(
        user=user,
        builder_settings={
            "language": "english",
            "situation": "restaurant",
            "practice_mode": "weak_words",
            "categories": ["noun"],
            "difficulties": ["beginner"],
            "rounds": 1,
            "review_policy": "review_only",
            "game_mode": "easy",
        },
    )

    assert progress is not None
    assert progress["mastery_status"] == "weak"
    assert weak_review["first_round"].word_id == lost_round.word_id


def test_validation_requires_situational_learning_fields() -> None:
    payload = {
        "language": "english",
        "words": [
            {
                "word_id": "english_bistro",
                "word": "bistro",
                "meaning": "small restaurant",
                "language": "english",
                "situations": [],
                "category": "noun",
                "difficulty": "beginner",
                "hint": "A place to eat.",
                "translation": "bistro",
                "example_sentence": "The bistro opens at noon.",
                "sentence_translation": "",
                "pronunciation_text": "",
                "usage_note": "",
                "synonym": "cafe",
                "association": "Small casual restaurant.",
                "synonym_hint": "cafe",
                "association_hint": "Small casual restaurant.",
            }
        ],
    }
    summary = validate_word_bank_payload(
        json.loads(json.dumps(payload)),
        source_name="missing_situational_fields.json",
    )
    errors = " ".join(summary["errors"])

    assert summary["valid_words"] == 0
    assert "Missing required field 'situations'" in errors
    assert "Missing required field 'sentence_translation'" in errors
    assert "Missing required field 'pronunciation_text'" in errors
    assert "Missing required field 'usage_note'" in errors
