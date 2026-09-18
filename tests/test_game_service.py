"""Tests for Hangman game state logic."""

from src.models.game_round import GameRound
from src.services.game_service import GameService


def build_round_state() -> GameRound:
    """Return a deterministic round state for unit tests."""
    return GameRound(
        word_id=1,
        word="apple",
        language="english",
        level="beginner",
        category="noun",
        difficulty="beginner",
        hint="A fruit",
        translation="apple",
        example_sentence="She ate an apple.",
    )


def test_record_guess_prevents_duplicate_letters(tmp_path) -> None:
    game_service = GameService(db_path=tmp_path / "game_logic.db")
    round_state = build_round_state()

    first_guess = game_service.record_guess(round_state, "a")
    duplicate_guess = game_service.record_guess(round_state, "a")

    assert first_guess["accepted"] is True
    assert duplicate_guess["accepted"] is False
    assert round_state.attempts_used == 1


def test_record_guess_marks_round_as_won(tmp_path) -> None:
    game_service = GameService(db_path=tmp_path / "game_win.db")
    round_state = build_round_state()

    for guess in ["a", "p", "l", "e"]:
        outcome = game_service.record_guess(round_state, guess)

    assert round_state.result == "won"
    assert outcome["round_finished"] is True
    assert round_state.masked_word == "a p p l e"
