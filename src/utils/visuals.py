"""Small visual helpers for Streamlit gameplay."""

from __future__ import annotations

from src.utils.constants import HANGMAN_STAGES


def get_hangman_stage(wrong_guesses: int, max_attempts: int) -> str:
    """Return the Hangman stage mapped to wrong guesses and max attempts."""
    if max_attempts <= 0:
        return HANGMAN_STAGES[-1]

    clamped_wrong_guesses = min(max(int(wrong_guesses), 0), int(max_attempts))
    stage_index = round((clamped_wrong_guesses / max_attempts) * (len(HANGMAN_STAGES) - 1))
    return HANGMAN_STAGES[min(stage_index, len(HANGMAN_STAGES) - 1)]
