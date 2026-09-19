"""Encouraging gameplay feedback lines for English learners."""

from __future__ import annotations

import random
from typing import Sequence

# Short, plain English for learners: no sarcasm, idioms or comments about the learner.
# Each line must still read well before the game's own suffix, e.g. "'e' completes the
# word." after a correct guess or "No attempts left. The word was ..." after the last miss.
CORRECT_LINES = [
    "Correct!",
    "Yes, good guess!",
    "Well done!",
    "Nice work!",
    "Great guess!",
    "That's right!",
    "Good thinking!",
    "Yes, that letter is in the word.",
]

INCORRECT_LINES = [
    "That letter is not in the word.",
    "Not this time.",
    "No, that letter is not here.",
    "Not in this word.",
    "No match for that letter.",
    "That guess is not in the word.",
]


def get_random_line(
    lines: Sequence[str],
    used_lines: list[str],
    rng: random.Random | None = None,
) -> str:
    """Return a random line while avoiding immediate repetition where possible."""
    random_generator = rng or random
    last_line = used_lines[-1] if used_lines else None
    available_lines = [line for line in lines if line not in used_lines]
    if not available_lines:
        used_lines.clear()
        available_lines = list(lines)

    if len(available_lines) > 1 and last_line:
        available_lines = [line for line in available_lines if line != last_line] or available_lines

    comment = random_generator.choice(list(available_lines))
    used_lines.append(comment)
    return comment
