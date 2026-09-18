"""Tests for Step 10 feedback, hint reveal, and visual polish helpers."""

from __future__ import annotations

import json
import random

from src.db.database import init_db
from src.db.repository import GameSessionRepository, LearningSessionRepository
from src.models.game_round import GameRound
from src.services.auth_service import AuthService
from src.services.game_service import GameService
from src.services.hint_service import (
    build_available_hints,
    get_revealed_hints,
    reveal_manual_hint,
    sync_auto_revealed_hints,
)
from src.ui import media
from src.utils.constants import HANGMAN_STAGES
from src.utils.feedback_lines import CORRECT_LINES, get_random_line
from src.utils.visuals import get_hangman_stage
from src.utils.word_bank_loader import ensure_word_bank_hint_fields, validate_word_bank_directory


def _build_round(
    *,
    hint_mode: str = "normal",
    game_mode: str = "easy",
    max_attempts: int = 6,
) -> GameRound:
    return GameRound(
        word_id=1,
        word="apple",
        language="english",
        level="beginner",
        category="noun",
        difficulty="beginner",
        hint="A fruit.",
        translation="apple",
        example_sentence="I eat an apple.",
        meaning="apple",
        situations=["restaurant"],
        situation="restaurant",
        sentence_translation="I eat an apple.",
        pronunciation_text="apple",
        usage_note="Use apple when talking about fruit in a restaurant.",
        synonym="fruit",
        association="Red fruit linked with school lunches.",
        meaning_hint="A fruit.",
        synonym_hint="fruit",
        association_hint="Red fruit linked with school lunches.",
        game_mode=game_mode,
        hint_mode=hint_mode,
        max_attempts=max_attempts,
    )


def _build_word_payload() -> dict[str, object]:
    return {
        "id": 1,
        "word_id": "english_apple",
        "word": "apple",
        "meaning": "apple",
        "language": "english",
        "situations": ["restaurant"],
        "category": "noun",
        "difficulty": "beginner",
        "hint": "A fruit.",
        "translation": "apple",
        "example_sentence": "I eat an apple.",
        "sentence_translation": "I eat an apple.",
        "pronunciation_text": "apple",
        "usage_note": "Use apple when talking about fruit in a restaurant.",
        "synonym": "fruit",
        "association": "Red fruit linked with school lunches.",
        "meaning_hint": "A fruit.",
        "synonym_hint": "fruit",
        "association_hint": "Red fruit linked with school lunches.",
    }


def test_game_service_builds_easy_and_hard_modes(tmp_path) -> None:
    game_service = GameService(db_path=tmp_path / "modes.db")

    easy_round = game_service.build_round(
        chosen_word=_build_word_payload(),
        level="beginner",
        game_mode="easy",
    )
    hard_round = game_service.build_round(
        chosen_word=_build_word_payload(),
        level="beginner",
        game_mode="hard",
    )

    assert easy_round.game_mode == "easy"
    assert easy_round.hint_mode == "easy"
    assert easy_round.max_attempts == 7
    assert hard_round.game_mode == "hard"
    assert hard_round.hint_mode == "hard"
    assert hard_round.max_attempts == 5


def test_learning_session_preserves_selected_game_mode(tmp_path) -> None:
    db_path = tmp_path / "hard_session.db"
    init_db(db_path=db_path, seed_words=True)
    auth_service = AuthService(db_path=db_path)
    game_service = GameService(db_path=db_path)
    learning_repository = LearningSessionRepository(db_path=db_path)
    user = auth_service.register_user(
        username="hardmodeplayer",
        password="secret123",
        target_language="english",
        level="beginner",
        preferred_categories=["noun"],
    )

    outcome = game_service.start_custom_learning_session(
        user=user,
        builder_settings={
            "language": "english",
            "practice_mode": "standard",
            "categories": ["noun"],
            "difficulties": ["beginner"],
            "rounds": 1,
            "review_policy": "prefer_review",
            "game_mode": "hard",
        },
    )
    stored_session = learning_repository.get_by_id(int(outcome["learning_session"].session_id or 0))

    assert outcome["learning_session"].game_mode == "hard"
    assert outcome["first_round"].game_mode == "hard"
    assert outcome["first_round"].max_attempts == 5
    assert stored_session is not None
    assert stored_session["game_mode"] == "hard"


def test_feedback_line_selection_avoids_immediate_repetition() -> None:
    used_lines: list[str] = []
    rng = random.Random(4)
    previous_line = None

    for _ in range(len(CORRECT_LINES) + 8):
        line = get_random_line(CORRECT_LINES, used_lines, rng=rng)
        assert line != previous_line
        previous_line = line


def test_hint_reveal_stages_in_normal_mode() -> None:
    round_state = _build_round(hint_mode="normal")

    assert sync_auto_revealed_hints(round_state) == {}

    round_state.wrong_letters.append("z")
    assert list(sync_auto_revealed_hints(round_state)) == ["hint"]

    round_state.wrong_letters.extend(["q", "x"])
    assert list(sync_auto_revealed_hints(round_state)) == ["hint", "synonym"]

    round_state.wrong_letters.extend(["v", "b"])
    assert list(sync_auto_revealed_hints(round_state)) == [
        "hint",
        "synonym",
        "association",
    ]


def test_hint_reveal_behavior_in_hard_mode() -> None:
    round_state = _build_round(hint_mode="hard", game_mode="hard", max_attempts=5)
    round_state.wrong_letters.extend(["z", "q"])

    assert sync_auto_revealed_hints(round_state) == {}

    round_state.wrong_letters.append("x")
    revealed = sync_auto_revealed_hints(round_state)

    assert set(revealed) == {
        "meaning",
        "hint",
        "synonym",
        "association",
    }


def test_easy_mode_unlocks_hints_after_wrong_guesses_one_three_and_five() -> None:
    round_state = _build_round(hint_mode="easy", game_mode="easy", max_attempts=7)

    assert sync_auto_revealed_hints(round_state) == {}

    round_state.wrong_letters.append("z")
    assert list(sync_auto_revealed_hints(round_state)) == ["meaning"]

    round_state.wrong_letters.extend(["q", "x"])
    assert list(sync_auto_revealed_hints(round_state)) == ["meaning", "synonym"]

    round_state.wrong_letters.extend(["v", "b"])
    assert list(sync_auto_revealed_hints(round_state)) == [
        "meaning",
        "synonym",
        "association",
    ]


def test_revealed_hints_stay_visible_for_the_round() -> None:
    round_state = _build_round(hint_mode="easy", game_mode="easy", max_attempts=7)

    round_state.wrong_letters.append("z")
    first_reveal = sync_auto_revealed_hints(round_state)
    round_state.wrong_letters.append("q")
    second_reveal = sync_auto_revealed_hints(round_state)

    assert first_reveal["meaning"] == "A fruit."
    assert second_reveal["meaning"] == "A fruit."
    assert round_state.revealed_hint_keys.count("meaning") == 1


def test_synonym_and_association_reveal_only_use_real_text() -> None:
    round_state = _build_round()

    assert reveal_manual_hint(round_state, "synonym") is True
    assert get_revealed_hints(round_state)["synonym"] == "fruit"
    assert reveal_manual_hint(round_state, "association") is True
    assert "school lunches" in get_revealed_hints(round_state)["association"]

    blank_round = _build_round()
    blank_round.synonym = ""
    blank_round.association = ""
    blank_round.synonym_hint = ""
    blank_round.association_hint = ""
    assert reveal_manual_hint(blank_round, "synonym") is True
    assert reveal_manual_hint(blank_round, "association") is True
    assert get_revealed_hints(blank_round)["synonym"] == "Think of a common noun word."
    assert get_revealed_hints(blank_round)["association"] == "Think of a common noun word."


def test_hint_reveal_never_returns_blank_hints() -> None:
    round_state = _build_round()
    round_state.hint = ""
    round_state.translation = ""
    round_state.example_sentence = ""
    round_state.synonym = ""
    round_state.association = ""
    round_state.revealed_hint_keys = [
        "hint",
        "synonym",
        "association",
    ]

    revealed_hints = get_revealed_hints(round_state)

    assert revealed_hints
    assert all(value.strip() for value in revealed_hints.values())
    assert "Think of a common noun word." in set(revealed_hints.values())


def test_missing_synonym_and_association_fallbacks_do_not_use_learning_content() -> None:
    round_state = _build_round()
    round_state.synonym = ""
    round_state.association = ""
    round_state.synonym_hint = ""
    round_state.association_hint = ""

    available_hints = build_available_hints(round_state)

    assert available_hints["synonym"] == "Think of a common noun word."
    assert available_hints["association"] == "Think of a common noun word."


def test_missing_hint_aliases_are_filled_without_overwriting_existing_values(tmp_path) -> None:
    words_dir = tmp_path / "words"
    words_dir.mkdir()
    word_bank_path = words_dir / "english.json"
    word_bank_path.write_text(
        json.dumps(
            {
                "language": "english",
                "words": [
                    {
                        "word": "apple",
                        "language": "english",
                        "category": "noun",
                        "difficulty": "beginner",
                        "hint": "A fruit.",
                        "translation": "apple",
                        "example_sentence": "I eat an apple.",
                        "synonym": "fruit",
                        "association": "Red fruit.",
                    },
                    {
                        "word": "run",
                        "language": "english",
                        "category": "verb",
                        "difficulty": "beginner",
                        "hint": "Move quickly.",
                        "translation": "run",
                        "example_sentence": "I run daily.",
                        "synonym": "sprint",
                        "association": "Exercise.",
                        "synonym_hint": "Existing synonym hint",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    summary = ensure_word_bank_hint_fields(words_dir)
    updated_payload = json.loads(word_bank_path.read_text(encoding="utf-8"))
    apple = updated_payload["words"][0]
    run = updated_payload["words"][1]

    assert summary["filled_counts"]["meaning_hint"] == 2
    assert summary["filled_counts"]["synonym_hint"] == 1
    assert summary["filled_counts"]["association_hint"] == 2
    assert apple["meaning_hint"] == "A fruit."
    assert apple["synonym_hint"] == "fruit"
    assert apple["association_hint"] == "Red fruit."
    assert run["synonym_hint"] == "Existing synonym hint"


def test_visual_hangman_stage_mapping() -> None:
    assert get_hangman_stage(0, 6) == HANGMAN_STAGES[0]
    assert get_hangman_stage(6, 6) == HANGMAN_STAGES[-1]
    assert get_hangman_stage(99, 6) == HANGMAN_STAGES[-1]


def test_validation_detects_missing_synonym_and_association(tmp_path) -> None:
    words_dir = tmp_path / "words"
    words_dir.mkdir()
    (words_dir / "english.json").write_text(
        json.dumps(
            {
                "language": "english",
                "words": [
                    {
                        "word": "apple",
                        "language": "english",
                        "category": "noun",
                        "difficulty": "beginner",
                        "hint": "A fruit.",
                        "translation": "apple",
                        "example_sentence": "I eat an apple.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    summary = validate_word_bank_directory(words_dir)
    errors = " ".join(
        error for file_summary in summary["files"] for error in file_summary["errors"]
    )

    assert summary["valid_words"] == 0
    assert summary["invalid_words"] == 1
    assert "Missing required field 'synonym'" in errors
    assert "Missing required field 'association'" in errors


def test_audio_helpers_do_not_crash_when_assets_are_missing(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        media,
        "SOUND_FILES",
        {
            "correct": tmp_path / "missing-correct.mp3",
            "wrong": tmp_path / "missing-wrong.mp3",
        },
    )
    monkeypatch.setattr(media, "BACKGROUND_MUSIC_FILE", tmp_path / "missing-background.mp3")

    audio_status = media.get_audio_asset_status()

    assert audio_status["has_any_audio"] is False
    assert audio_status["sound_available"] is False
    assert audio_status["music_available"] is False
    media.play_optional_sound("correct")
    media.render_background_music()


def test_sound_playback_respects_enabled_flag_and_handles_errors(monkeypatch, tmp_path) -> None:
    sound_path = tmp_path / "correct_guess.wav"
    sound_path.write_bytes(b"placeholder wav")

    class FakeStreamlit:
        def __init__(self) -> None:
            self.session_state = {"sound_enabled": True, "music_enabled": True}
            self.calls: list[tuple[str, str, bool | None, bool | None]] = []

        def audio(
            self,
            path: str,
            *,
            format: str,
            autoplay: bool | None = None,
            loop: bool | None = None,
        ) -> None:
            self.calls.append((path, format, autoplay, loop))

    fake_st = FakeStreamlit()
    monkeypatch.setattr(media, "st", fake_st)
    monkeypatch.setattr(media, "SOUND_FILES", {"correct": sound_path})
    monkeypatch.setattr(media, "SOUND_ENABLED", True)

    assert media.play_optional_sound("correct") is True
    assert fake_st.calls[-1][0] == str(sound_path)

    monkeypatch.setattr(media, "SOUND_ENABLED", False)
    assert media.play_optional_sound("correct") is False
    assert len(fake_st.calls) == 1

    monkeypatch.setattr(media, "SOUND_ENABLED", True)

    def broken_audio(*_args, **_kwargs) -> None:
        raise RuntimeError("browser refused audio")

    monkeypatch.setattr(fake_st, "audio", broken_audio)
    assert media.play_optional_sound("correct") is False


def test_basic_full_gameplay_session_still_persists(tmp_path) -> None:
    db_path = tmp_path / "full_gameplay.db"
    init_db(db_path=db_path, seed_words=True)
    auth_service = AuthService(db_path=db_path)
    game_service = GameService(db_path=db_path)
    session_repository = GameSessionRepository(db_path=db_path)
    learning_repository = LearningSessionRepository(db_path=db_path)
    user = auth_service.register_user(
        username="stabilizedplayer",
        password="secret123",
        target_language="english",
        level="beginner",
        preferred_categories=["noun"],
    )

    learning_session, round_state = game_service.start_learning_session(
        user=user,
        practice_mode="standard",
        planned_rounds=1,
        selected_category="noun",
        rng=random.Random(3),
    )
    for letter in sorted(round_state.unique_letters):
        game_service.record_guess(round_state, letter)

    outcome = game_service.finalize_round(
        user=user,
        round_state=round_state,
        learning_session=learning_session,
    )
    stored_rounds = session_repository.get_recent_sessions(user_id=user["id"], limit=5)
    stored_learning_session = learning_repository.get_by_id(int(learning_session.session_id or 0))

    assert round_state.result == "won"
    assert outcome["session_complete"] is True
    assert stored_rounds
    assert stored_rounds[0]["result"] == "won"
    assert stored_learning_session is not None
    assert stored_learning_session["status"] == "completed"
