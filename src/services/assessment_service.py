"""Assessment helpers for first-time learner calibration."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from src.models.game_round import GameRound
from src.services.word_service import WordService
from src.utils.constants import ASSESSMENT_DIFFICULTY_SEQUENCE, DEFAULT_PREFERRED_CATEGORIES


class AssessmentService:
    """Builds and scores a lightweight three-round assessment."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.word_service = WordService(db_path=db_path)

    def create_assessment_state(
        self,
        user: dict[str, Any],
        rng: random.Random | None = None,
    ) -> dict[str, Any]:
        """Create a fresh assessment state with three increasing-difficulty rounds."""
        random_generator = rng or random.Random()
        selected_rounds: list[GameRound] = []
        used_word_ids: list[int] = []

        for difficulty in ASSESSMENT_DIFFICULTY_SEQUENCE:
            selected_word = self.word_service.select_word(
                language=str(user["target_language"]),
                level=str(user["self_declared_level"]),
                preferred_categories=list(
                    user.get("preferred_categories") or list(DEFAULT_PREFERRED_CATEGORIES)
                ),
                category_order=list(
                    user.get("preferred_categories") or list(DEFAULT_PREFERRED_CATEGORIES)
                ),
                difficulty_override=[difficulty],
                excluded_word_ids=used_word_ids,
                rng=random_generator,
            )
            used_word_ids.append(int(selected_word["id"]))
            selected_rounds.append(
                GameRound(
                    word_id=int(selected_word["id"]),
                    word=str(selected_word["word"]),
                    language=str(selected_word["language"]),
                    level=difficulty,
                    category=str(selected_word["category"]),
                    difficulty=str(selected_word["difficulty"]),
                    hint=str(selected_word["hint"]),
                    translation=str(selected_word["translation"]),
                    example_sentence=str(selected_word["example_sentence"]),
                    synonym=selected_word.get("synonym"),
                    association=selected_word.get("association"),
                    round_type="assessment",
                    selection_reason=f"Assessment round for {difficulty.title()} difficulty.",
                )
            )

        return {
            "rounds": selected_rounds,
            "current_index": 0,
            "completed": False,
            "calibrated_level": None,
            "summary": None,
        }

    def get_current_round(self, assessment_state: dict[str, Any]) -> GameRound:
        """Return the current assessment round."""
        return assessment_state["rounds"][assessment_state["current_index"]]

    def advance_assessment(self, assessment_state: dict[str, Any]) -> dict[str, Any]:
        """Move the assessment to the next round or finalize the result."""
        current_index = int(assessment_state["current_index"])
        rounds = list(assessment_state["rounds"])

        if current_index < len(rounds) - 1:
            assessment_state["current_index"] = current_index + 1
            return assessment_state

        summary = self.score_assessment(rounds)
        assessment_state["completed"] = True
        assessment_state["calibrated_level"] = summary["calibrated_level"]
        assessment_state["summary"] = summary
        return assessment_state

    def score_assessment(self, rounds: list[GameRound]) -> dict[str, Any]:
        """Calculate a calibrated level from three assessment rounds."""
        round_results = [self._score_round(round_state) for round_state in rounds]
        pass_count = sum(1 for result in round_results if result["passed"])
        average_accuracy = (
            sum(result["guess_accuracy"] for result in round_results) / len(round_results)
            if round_results
            else 0.0
        )
        advanced_round_passed = bool(round_results and round_results[-1]["passed"])

        if pass_count == 3 and advanced_round_passed and average_accuracy >= 0.6:
            calibrated_level = "advanced"
        elif pass_count >= 2:
            calibrated_level = "intermediate"
        else:
            calibrated_level = "beginner"

        return {
            "calibrated_level": calibrated_level,
            "round_results": round_results,
            "average_accuracy": round(average_accuracy, 2),
            "passed_rounds": pass_count,
        }

    def _score_round(self, round_state: GameRound) -> dict[str, Any]:
        """Score one assessment round using simple, explainable rules."""
        guess_accuracy = (
            round_state.letters_correct / round_state.attempts_used
            if round_state.attempts_used
            else 0.0
        )
        passed = round_state.result == "won" or (
            guess_accuracy >= 0.6 and round_state.letters_correct >= 2
        )
        return {
            "word": round_state.word,
            "difficulty": round_state.difficulty,
            "category": round_state.category,
            "result": round_state.result,
            "attempts_used": round_state.attempts_used,
            "guess_accuracy": round(guess_accuracy, 2),
            "passed": passed,
        }
