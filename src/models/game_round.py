"""Game round model used during Streamlit gameplay."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.utils.constants import DEFAULT_MAX_ATTEMPTS
from src.utils.helpers import utc_now_iso


@dataclass(slots=True)
class GameRound:
    """Represents one active Hangman round stored in session state."""

    word_id: int
    word: str
    language: str
    level: str
    category: str
    difficulty: str
    hint: str
    translation: str
    example_sentence: str
    synonym: str | None = None
    association: str | None = None
    meaning: str | None = None
    situations: list[str] = field(default_factory=list)
    situation: str | None = None
    sentence_translation: str | None = None
    pronunciation_text: str | None = None
    usage_note: str | None = None
    meaning_hint: str | None = None
    synonym_hint: str | None = None
    association_hint: str | None = None
    round_type: str = "practice"
    practice_mode: str = "standard"
    game_mode: str = "easy"
    selection_reason: str | None = None
    selection_warning: str | None = None
    learning_session_id: int | None = None
    show_hint_immediately: bool = True
    hint_revealed: bool = False
    hint_mode: str = "normal"
    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    guessed_letters: list[str] = field(default_factory=list)
    wrong_letters: list[str] = field(default_factory=list)
    revealed_hint_keys: list[str] = field(default_factory=list)
    used_correct_feedback_lines: list[str] = field(default_factory=list)
    used_incorrect_feedback_lines: list[str] = field(default_factory=list)
    result: str = "in_progress"
    started_at: str = field(default_factory=utc_now_iso)
    completed_at: str | None = None
    saved: bool = False
    session_id: int | None = None

    @property
    def unique_letters(self) -> set[str]:
        """Return the distinct alphabetical letters that must be guessed."""
        return {character.lower() for character in self.word if character.isalpha()}

    @property
    def correct_letters(self) -> list[str]:
        """Return the correctly guessed letters in sorted order."""
        return sorted(letter for letter in self.guessed_letters if letter in self.unique_letters)

    @property
    def attempts_used(self) -> int:
        """Return the total number of accepted guesses."""
        return len(self.guessed_letters)

    @property
    def letters_correct(self) -> int:
        """Return the number of correct letter guesses."""
        return len(self.correct_letters)

    @property
    def letters_wrong(self) -> int:
        """Return the number of incorrect letter guesses."""
        return len(self.wrong_letters)

    @property
    def remaining_attempts(self) -> int:
        """Return the number of attempts left in the round."""
        return max(self.max_attempts - self.letters_wrong, 0)

    @property
    def masked_word(self) -> str:
        """Return the masked word shown to the player."""
        return " ".join(
            (
                character
                if not character.isalpha() or character.lower() in self.guessed_letters
                else "_"
            )
            for character in self.word
        )

    @property
    def guessed_letters_display(self) -> str:
        """Return a display-friendly string of guessed letters."""
        return ", ".join(self.guessed_letters) if self.guessed_letters else "None yet"

    @property
    def is_complete(self) -> bool:
        """Return whether the round is finished."""
        return self.result in {"won", "lost"}
