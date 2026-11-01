"""The word lists: languages, levels, clues, plain-letter guessing and endless sessions."""

import json
import sqlite3
import unicodedata
from dataclasses import asdict

import pytest

from src.db.database import init_db
from src.models.game_round import GameRound, base_letter
from src.services.auth_service import AuthService
from src.services.curated_content import LEVEL_WORD_COUNT, CuratedWordService, seed_curated
from src.services.desktop_storage import progress_report
from src.services.game_service import GameService, NoReviewWordsError
from src.services.hint_service import get_revealed_hints, sync_auto_revealed_hints
from src.services.practice_service import PracticeService
from src.utils.config import LEVEL_WORDS_DIR
from src.utils.constants import (
    BOARD_LETTERS,
    ENDLESS_ROUNDS,
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
        "english": 400,
        "spanish": 389,
        "italian": 390,
        "german": 365,
    }
    for items in rows.values():
        assert {row["difficulty"] for row in items} == set(WORD_LEVELS)


def test_the_six_words_kept_off_the_lists_for_the_travel_cards_are_back():
    words = {row["word"] for row in level_rows("english")}
    assert {"clean", "early", "quiet", "room", "slowly", "water"} <= words


def test_the_travel_cards_are_gone(tmp_path):
    assert not (LEVEL_WORDS_DIR.parent / "english.json").exists()
    path = tmp_path / "app.db"
    init_db(path, seed_words=False)
    seed_curated(path)
    with sqlite3.connect(path) as connection:
        sources = {row[0] for row in connection.execute("SELECT DISTINCT source FROM words")}
    assert sources == {"desktop-levels"}


def test_seeding_never_offers_legacy_banks_or_old_travel_cards(tmp_path):
    path = tmp_path / "app.db"
    init_db(path, seed_words=True)  # an upgrade or a restore: the old banks are in the table
    seed_curated(path)
    with sqlite3.connect(path) as connection:  # a card left in a database from rc5
        connection.execute(
            "INSERT INTO words (word, language, category, difficulty, hint, translation, "
            "example_sentence, situations, source) VALUES "
            "('towel', 'english', 'noun', 'beginner', 'x', 'x', 'x', '[\"hotel\"]', 'desktop-core')"
        )
    service = CuratedWordService(path)
    assert "towel" not in {word["word"] for word in service.get_words("english")}
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


def test_a_plain_letter_reveals_its_accented_forms():
    state = round_with("niño", "spanish")
    game = GameService()
    game.record_guess(state, "n")
    assert state.masked_letters == ["n", "_", "ñ", "_"]


def test_an_accented_guess_counts_as_the_plain_letter_and_costs_no_second_try():
    state = round_with("árbol", "spanish")
    game = GameService()
    assert game.record_guess(state, "á")["accepted"]
    assert state.masked_letters[0] == "á"
    assert not game.record_guess(state, "a")["accepted"]  # the same letter again
    assert state.wrong_letters == [] and state.guessed_letters == ["a"]


def test_a_word_is_won_with_plain_letters_alone():
    state = round_with("días", "spanish")
    game = GameService()
    for letter in "dias":
        game.record_guess(state, letter)
    assert state.result == "won"
    assert state.masked_letters == ["d", "í", "a", "s"]


def test_s_reveals_sharp_s():
    state = round_with("heiß", "german")
    game = GameService()
    game.record_guess(state, "s")
    assert state.masked_letters == ["_", "_", "_", "ß"]
    assert base_letter("ß") == "s"
    assert game.record_guess(state, unicodedata.normalize("NFD", "é"))["accepted"]
    assert state.masked_letters == ["_", "e", "_", "ß"]


def test_german_nouns_keep_their_capital():
    state = round_with("Übung", "german")
    GameService().record_guess(state, "u")
    assert state.masked_letters[0] == "Ü" and state.masked_letters[2] == "u"


def test_a_round_paused_in_rc5_with_an_accented_guess_still_works():
    state = round_with("niño", "spanish")
    state.guessed_letters.append("ñ")  # how rc5 stored it
    assert state.masked_letters == ["n", "_", "ñ", "_"]
    assert state.correct_letters == ["ñ"]
    assert not GameService().record_guess(state, "n")["accepted"]


def test_phrases_show_their_spaces_and_hyphens_without_being_guessed():
    state = round_with("en voz-alta", "spanish")
    assert state.masked_letters[2] == " " and state.masked_letters[6] == "-"
    game = GameService()
    for letter in sorted(state.unique_letters):
        game.record_guess(state, letter)
    assert state.result == "won"


@pytest.mark.parametrize("language", PRACTICE_LANGUAGES)
def test_every_letter_in_the_lists_is_on_the_a_to_z_keys(language):
    letters = {
        base_letter(letter)
        for row in level_rows(language)
        for letter in row["word"]
        if letter.isalpha()
    }
    assert letters <= set(BOARD_LETTERS), sorted(letters - set(BOARD_LETTERS))


def test_ignoring_accents_never_makes_two_words_in_a_language_identical():
    for language in PRACTICE_LANGUAGES:
        plain = ["".join(map(base_letter, row["word"])) for row in level_rows(language)]
        assert len(set(plain)) == len(plain), language


def play_word(service, user, payload):
    state = payload["round"]
    for letter in sorted({base_letter(c) for c in state["word"] if c.isalpha()}):
        payload = service.guess(user, letter, state["round_key"])
    assert payload["round"]["saved"]
    return payload


def small_set(rounds=ENDLESS_ROUNDS):
    return dict(
        settings(language="english", level="beginner"), rounds=rounds, categories=["adverb"]
    )


def test_an_endless_session_uses_every_word_then_repeats_oldest_first(practice):
    _, user, service = practice
    pool = len(
        CuratedWordService(service.db_path).get_words(
            "english", categories=["adverb"], difficulties=["beginner"], situation=GENERAL_SITUATION
        )
    )
    assert 5 <= pool <= 30
    payload = service.start(user, small_set())
    order = []
    for _ in range(pool * 2 + 2):
        order.append(payload["round"]["word"])
        payload = play_word(service, user, payload)
        assert payload["next_round"], "an endless session always has another word"
        payload = service.next_round(user["id"])
    first_pass = order[:pool]
    assert len(set(first_pass)) == pool, "no repeats until every word has been played"
    assert order[pool : pool * 2] == first_pass, "repeats follow the oldest word first"
    assert order[pool * 2 :] == first_pass[:2]
    assert payload["notice"] is None
    service.end(user["id"])


def test_an_endless_session_keeps_the_saved_session_small(practice):
    _, user, service = practice
    payload = service.start(user, small_set())
    for _ in range(6):
        payload = service.next_round(user["id"]) if payload["round"]["saved"] else payload
        payload = play_word(service, user, payload)
    assert payload["session"]["round_reviews"] == []
    fixed = None
    service.end(user["id"])
    fixed = service.start(user, small_set(rounds=3))
    fixed = play_word(service, user, fixed)
    assert len(fixed["session"]["round_reviews"]) == 1, "fixed sessions still keep their summary"


def test_end_session_keeps_finished_words_and_drops_the_unfinished_one(practice):
    path, user, service = practice
    payload = service.start(user, small_set())
    payload = play_word(service, user, payload)
    payload = service.next_round(user["id"])
    service.guess(user, "z", payload["round"]["round_key"])
    service.end(user["id"])
    assert service.load(user["id"]) is None
    report = progress_report(path, user["id"])
    assert (report["rounds"], report["sessions"]) == (1, 1)


def test_ending_a_session_with_no_finished_word_is_not_counted(practice):
    path, user, service = practice
    payload = service.start(user, small_set())
    service.guess(user, "z", payload["round"]["round_key"])
    service.end(user["id"])
    report = progress_report(path, user["id"])
    assert (report["rounds"], report["sessions"]) == (0, 0)


def test_ending_twice_changes_nothing(practice):
    path, user, service = practice
    service.start(user, small_set())
    service.end(user["id"])
    service.end(user["id"])
    assert progress_report(path, user["id"])["sessions"] == 0


def test_a_paused_travel_session_finishes_its_word_then_says_it_has_ended(practice):
    """rc5 saves situation sessions; rc6 has no travel words to continue them with."""
    path, user, service = practice
    payload = service.start(user, settings(language="english", level="beginner", rounds=3))
    payload["session"]["situation"] = "hotel"
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE active_practice SET payload=? WHERE user_id=?",
            (json.dumps(payload), user["id"]),
        )
    assert service.load(user["id"])["session"]["situation"] == "hotel"
    final = play_word(service, user, payload)
    assert final["next_round"] is None
    assert "ended after 1 of 3 rounds" in final["notice"]
    assert progress_report(path, user["id"])["rounds"] == 1


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
