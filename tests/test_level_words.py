"""The level lists: four languages, five levels, three clues and the restored feedback lines."""

import json
import unicodedata
from dataclasses import asdict

import pytest

from src.db.database import init_db
from src.models.game_round import GameRound
from src.services.auth_service import AuthService
from src.services.curated_content import LEVEL_WORD_COUNT, CuratedWordService, seed_curated
from src.services.game_service import GameService, NoReviewWordsError
from src.services.hint_service import get_revealed_hints, sync_auto_revealed_hints
from src.services.practice_service import PracticeService
from src.utils.config import LEVEL_WORDS_DIR
from src.utils.constants import (
    BOARD_LETTERS,
    EXTRA_LETTERS,
    GENERAL_SITUATION,
    PRACTICE_LANGUAGES,
    WORD_LEVELS,
)
from src.utils.feedback_lines import CORRECT_LINES, INCORRECT_LINES


def level_rows(language):
    path = LEVEL_WORDS_DIR / f"{language}.json"
    return json.loads(path.read_text(encoding="utf-8"))["words"]


def settings(language="spanish", level="novice", rounds=3, mode="easy", review=False):
    return {
        "language": language,
        "categories": ["noun", "verb", "adjective", "adverb"],
        "difficulties": [level],
        "rounds": rounds,
        "game_mode": mode,
        "situation": GENERAL_SITUATION,
        "practice_mode": "review" if review else "standard",
        "review_policy": "review_only" if review else "prefer_review",
        "show_hint_immediately": False,
    }


@pytest.fixture
def practice(tmp_path):
    path = tmp_path / "app.db"
    init_db(path, seed_words=False)
    seed_curated(path)
    AuthService(path).register_user("level-learner", "level-pass-2026", target_language="english")
    user = AuthService(path).authenticate_user("level-learner", "level-pass-2026")
    return path, user, PracticeService(path, curated=True)


def round_with(word, language, mode="easy"):
    return GameService().build_round(
        chosen_word={
            "id": 1,
            "word": word,
            "language": language,
            "category": "noun",
            "difficulty": "beginner",
            "hint": "The meaning.",
            "translation": "The meaning.",
            "example_sentence": "",
            "meaning_hint": "The meaning.",
            "synonym": "A synonym",
            "association": "An association.",
        },
        level="beginner",
        game_mode=mode,
    )


def test_every_language_has_all_five_levels_and_the_counts_add_up():
    rows = {language: level_rows(language) for language in PRACTICE_LANGUAGES}
    assert sum(len(items) for items in rows.values()) == LEVEL_WORD_COUNT
    assert {language: len(items) for language, items in rows.items()} == {
        "english": 394,
        "spanish": 389,
        "italian": 390,
        "german": 365,
    }
    for items in rows.values():
        assert {row["difficulty"] for row in items} == set(WORD_LEVELS)


def test_seeding_keeps_the_travel_cards_and_never_offers_legacy_banks(tmp_path):
    path = tmp_path / "app.db"
    init_db(path, seed_words=True)  # an upgrade or a restore: the old banks are in the table
    seed_curated(path)
    service = CuratedWordService(path)
    cards = service.travel_cards()
    assert len(cards) == 30 and all(card["example_sentence"] for card in cards)
    assert {word["source"] for word in service.get_words("spanish")} == {"desktop-levels"}
    assert service.get_words("french") == []
    assert service.get_available_languages() == list(PRACTICE_LANGUAGES)


def test_seeding_twice_changes_nothing(practice):
    path, _, _ = practice
    before = len(CuratedWordService(path).get_words("german"))
    seed_curated(path)
    assert len(CuratedWordService(path).get_words("german")) == before


def test_a_level_session_stays_in_its_language_and_level(practice):
    _, user, service = practice
    payload = service.start(user, settings(rounds=10))
    seen = set()
    while True:
        state = payload["round"]
        assert (state["language"], state["difficulty"]) == ("spanish", "novice")
        seen.add(state["word"])
        for letter in sorted({c.lower() for c in state["word"] if c.isalpha()}):
            payload = service.guess(user, letter, state["round_key"])
        if not payload["next_round"]:
            break
        payload = service.next_round(user["id"])
    assert len(seen) == 10
    service.discard(user["id"])


def test_review_at_a_level_only_uses_words_practised_at_that_level(practice):
    _, user, service = practice
    with pytest.raises(NoReviewWordsError):
        service.start(user, settings(review=True))
    payload = service.start(user, settings(rounds=3))
    practised = set()
    while True:
        state = payload["round"]
        practised.add(state["word"])
        for letter in sorted({c.lower() for c in state["word"] if c.isalpha()}):
            payload = service.guess(user, letter, state["round_key"])
        if not payload["next_round"]:
            break
        payload = service.next_round(user["id"])
    service.discard(user["id"])
    with pytest.raises(NoReviewWordsError):
        service.start(user, settings(language="german", review=True))
    with pytest.raises(NoReviewWordsError):
        service.start(user, settings(level="expert", review=True))
    payload = service.start(user, settings(rounds=10, review=True))
    assert payload["session"]["planned_rounds"] == 3
    assert payload["round"]["word"] in practised


def test_level_words_show_three_different_clues_on_easy():
    state = round_with("libro", "spanish")
    shown = []
    for letter in "zqx" "wjk" "v":
        state.wrong_letters.append(letter)
        sync_auto_revealed_hints(state)
        shown.append(len(set(get_revealed_hints(state).values())))
    assert shown == [1, 1, 2, 2, 3, 3, 3]


def test_hard_mode_shows_all_three_clues_with_two_lives_left():
    state = round_with("libro", "spanish", mode="hard")
    for letter in "zq":
        state.wrong_letters.append(letter)
        sync_auto_revealed_hints(state)
        assert get_revealed_hints(state) == {}
    state.wrong_letters.append("x")
    sync_auto_revealed_hints(state)
    assert state.remaining_attempts == 2
    assert len(set(get_revealed_hints(state).values())) == 3


def test_an_accented_letter_is_its_own_letter():
    state = round_with("niño", "spanish")
    game = GameService()
    game.record_guess(state, "n")
    assert state.masked_letters == ["n", "_", "_", "_"]
    game.record_guess(state, "ñ")
    assert state.masked_letters == ["n", "_", "ñ", "_"]


def test_german_nouns_keep_their_capital_and_are_guessed_in_lower_case():
    state = round_with("Übung", "german")
    GameService().record_guess(state, "Ü")
    assert state.masked_letters[0] == "Ü"
    assert state.correct_letters == ["ü"]


def test_sharp_s_can_be_guessed_and_composed_input_is_accepted():
    state = round_with("heiß", "german")
    assert GameService().record_guess(state, "ß")["accepted"]
    assert GameService().record_guess(state, unicodedata.normalize("NFD", "e"))["accepted"]
    assert state.masked_letters == ["_", "e", "_", "ß"]


def test_phrases_show_their_spaces_and_hyphens_without_being_guessed():
    state = round_with("en voz-alta", "spanish")
    assert state.masked_letters[2] == " " and state.masked_letters[6] == "-"
    game = GameService()
    for letter in sorted(state.unique_letters):
        game.record_guess(state, letter)
    assert state.result == "won"


@pytest.mark.parametrize("language", PRACTICE_LANGUAGES)
def test_every_letter_in_the_lists_has_a_key(language):
    keys = set(BOARD_LETTERS + EXTRA_LETTERS.get(language, ""))
    letters = {
        letter.lower() for row in level_rows(language) for letter in row["word"] if letter.isalpha()
    }
    assert letters <= keys, sorted(letters - keys)


def test_the_extra_keys_are_only_letters_the_lists_use():
    for language, extras in EXTRA_LETTERS.items():
        letters = {c.lower() for row in level_rows(language) for c in row["word"]}
        assert set(extras) <= letters, language


def test_german_nouns_are_capitalised_and_other_words_are_not():
    rows = level_rows("german")
    assert all(row["word"][0].isupper() for row in rows if row["category"] == "noun")
    single = [row for row in rows if row["category"] == "verb" and " " not in row["word"]]
    assert all(row["word"][0].islower() for row in single)


def test_the_original_feedback_lines_are_back_word_for_word():
    assert len(CORRECT_LINES) == len(INCORRECT_LINES) == 20
    assert "Yeah, that’s right! Even a broken clock is right twice a day!" in CORRECT_LINES
    assert "Incorrect! Did you even go to school?" in INCORRECT_LINES
    assert len(set(CORRECT_LINES + INCORRECT_LINES)) == 40


def test_a_saved_round_from_rc4_still_loads():
    """No field was added to a round, so a paused rc3 or rc4 session resumes."""
    saved = asdict(round_with("menu", "english"))
    assert GameRound(**saved).masked_word == "_ _ _ _"
