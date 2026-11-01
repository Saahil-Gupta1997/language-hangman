"""The game's sarcastic feedback lines, restored from the original app by the owner."""

from __future__ import annotations

import random
from typing import Sequence

# The owner's original humorous_lines.py, word for word (DEC-07, 2026-11-01): the tone is
# deliberate and replaces the plain lines from D-17. Each line is followed by the game's
# own suffix, e.g. "'e' completes the word." or "No attempts left. The word was ...".
CORRECT_LINES = [
    "Yeah, that’s right! Even a broken clock is right twice a day!",
    "Boom! Nailed it! You must be cheating, huh?",
    "Look at you, getting it right! Don’t let it go to your head!",
    "Wow, you actually got one! A miracle just happened!",
    "Holy smokes, you’re on a roll! What, did you have Wheaties for breakfast?",
    "Correct! Don’t get too excited, it’s just a game!",
    "You got it! Maybe you’re not as clueless as you look.",
    "Right again! See? Even you can do something right!",
    "Nice job! You might actually be good at this... for once!",
    "Congrats, you got it! Let’s see if you can keep this streak going.",
    "Well, well, look at you! You got it right. Who would’ve thought?",
    "Hey, nice job! Even a blind squirrel finds a nut once in a while.",
    "You got it! I guess miracles do happen.",
    "Correct! Just like that, you’re a regular Einstein.",
    "Well, what do you know? You actually got one.",
    "Right on the money! Maybe you’re not as dumb as you look.",
    "Wow, you got it! The sun shines on a dog’s tail every now and then.",
    "Correct! Looks like your brain decided to show up today.",
    "You got it right! What, did you read the answers beforehand?",
    "Nice job! Now don’t go getting a big head over it.",
]

INCORRECT_LINES = [
    "Nope! Guess again, genius!",
    "Wrong! What, did you just pick a letter at random?",
    "Nice try, but that’s a swing and a miss. You play baseball much?",
    "Wrong answer! Were you even trying?",
    "Nope, not even close. Do you know the alphabet?",
    "Uh-oh, another one wrong! You’re really testing the rope here!",
    "Wrong! Let’s see if you can get the next one or if this is just a fluke.",
    "Strike! You’re making this too easy for me!",
    "Incorrect! It’s like watching a train wreck in slow motion.",
    "Nope, wrong again! Are you sure you’re awake?",
    "Nope, that’s wrong. But hey, it’s only hangman, not brain surgery.",
    "Wrong! I’d say try again, but, you know, maybe not.",
    "Incorrect! Did you even go to school?",
    "Nope, not even close. It’s almost impressive how wrong that was.",
    "Wrong answer! But don’t worry, it’s not like anyone was expecting much.",
    "Nope! That’s about as wrong as you can get without being right.",
    "Well, that’s wrong. But hey, you’re keeping it interesting.",
    "Incorrect! Maybe next time try a little harder, or, you know, at all.",
    "Wrong again! At this rate, you’re gonna need a miracle.",
    "Nope, that’s wrong. But you gave it a good shot... if by ‘good shot’ you mean ‘terrible guess’.",  # noqa: E501
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
