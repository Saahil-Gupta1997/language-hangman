"""Tests for assessment scoring and calibration."""

from src.models.game_round import GameRound
from src.services.assessment_service import AssessmentService


def build_round(
    word: str,
    difficulty: str,
    result: str,
    attempts_used: int,
    letters_correct: int,
) -> GameRound:
    """Build an assessment round with the requested result shape."""
    round_state = GameRound(
        word_id=1,
        word=word,
        language="english",
        level=difficulty,
        category="noun",
        difficulty=difficulty,
        hint="hint",
        translation=word,
        example_sentence=f"{word} example.",
        round_type="assessment",
    )
    round_state.result = result
    round_state.guessed_letters = [chr(97 + index) for index in range(attempts_used)]
    round_state.wrong_letters = [
        chr(120 + index) for index in range(max(attempts_used - letters_correct, 0))
    ]
    if letters_correct > 0:
        round_state.guessed_letters = [character.lower() for character in word[:letters_correct]]
        round_state.guessed_letters.extend(
            chr(120 + index) for index in range(max(attempts_used - letters_correct, 0))
        )
    return round_state


def test_score_assessment_returns_advanced_for_strong_performance(tmp_path) -> None:
    service = AssessmentService(db_path=tmp_path / "assessment_advanced.db")
    rounds = [
        build_round("apple", "beginner", "won", 4, 4),
        build_round("library", "intermediate", "won", 6, 6),
        build_round("astronomy", "advanced", "won", 8, 8),
    ]

    summary = service.score_assessment(rounds)

    assert summary["calibrated_level"] == "advanced"
    assert summary["passed_rounds"] == 3


def test_score_assessment_returns_intermediate_for_two_passes(tmp_path) -> None:
    service = AssessmentService(db_path=tmp_path / "assessment_intermediate.db")
    rounds = [
        build_round("apple", "beginner", "won", 4, 4),
        build_round("library", "intermediate", "won", 6, 5),
        build_round("astronomy", "advanced", "lost", 6, 2),
    ]

    summary = service.score_assessment(rounds)

    assert summary["calibrated_level"] == "intermediate"
    assert summary["passed_rounds"] == 2
