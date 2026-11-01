"""Core Hangman game logic."""

from __future__ import annotations

import copy
import json
import random
import unicodedata
from dataclasses import asdict, fields
from datetime import datetime
from pathlib import Path
from typing import Any

from src.db.repository import (
    GameSessionRepository,
    LearningSessionRepository,
    ReviewQueueRepository,
    WordProgressRepository,
)
from src.db.transaction import transaction
from src.models.game_round import GameRound, base_letter
from src.models.learning_session import LearningSession
from src.services.adaptation_service import AdaptationService
from src.services.smart_practice_service import SmartPracticeService
from src.services.word_service import WordService
from src.utils.constants import (
    DEFAULT_PREFERRED_CATEGORIES,
    DIFFICULT_REVIEW_ACCURACY_THRESHOLD,
    ENDLESS_ROUNDS,
    FAMILIARITY_STATES,
    GAME_MODE_SETTINGS,
    GAME_MODES,
    LOW_REVIEW_ACCURACY_THRESHOLD,
    PRACTICE_MODES,
    REVIEW_POLICIES,
    SESSION_LENGTH_OPTIONS,
    SITUATIONS,
)
from src.utils.feedback_lines import CORRECT_LINES, INCORRECT_LINES, get_random_line
from src.utils.helpers import serialize_string_list, shift_utc_iso, utc_now_iso


class NoReviewWordsError(ValueError):
    """Review was requested but the learner has no eligible review words."""


def _situation_label(situation: Any) -> str:
    return str(situation or "this situation").replace("_", " ").title()


class GameService:
    """Owns Hangman gameplay rules, builder validation, and persistence."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.word_service = WordService(db_path=db_path)
        self.game_session_repository = GameSessionRepository(db_path=db_path)
        self.learning_session_repository = LearningSessionRepository(db_path=db_path)
        self.review_queue_repository = ReviewQueueRepository(db_path=db_path)
        self.word_progress_repository = WordProgressRepository(db_path=db_path)
        self.adaptation_service = AdaptationService(db_path=db_path)
        self.smart_practice_service = SmartPracticeService(db_path=db_path)

    def review_eligibility(
        self,
        user_id: int,
        language: str,
        situation: str | None,
        categories: list[str] | None = None,
        difficulties: list[str] | None = None,
    ) -> dict[str, list[int]]:
        """Return Review-eligible word ids split into due and not-yet-due, oldest due first.

        A word is eligible when the learner has an active review-queue item for it (created
        when a round with that word is completed) and the word is playable under the
        word service's corpus, situation, category and difficulty filters.
        """
        playable = {
            int(word["id"])
            for word in self.word_service.get_words(
                language=language,
                categories=categories,
                difficulties=difficulties,
                situation=situation,
            )
        }
        now = utc_now_iso()
        eligibility: dict[str, list[int]] = {"due": [], "upcoming": []}
        for row in self.review_queue_repository.get_active_items_by_due_date(
            user_id=user_id, language=language
        ):
            word_id = int(row["word_id"])
            if word_id in playable:
                bucket = "due" if str(row["review_due_at"] or "") <= now else "upcoming"
                eligibility[bucket].append(word_id)
        return eligibility

    def get_default_builder_settings(self, user: dict[str, Any]) -> dict[str, Any]:
        """Return the starting builder settings for a user."""
        saved_settings = dict(user.get("last_builder_settings") or {})
        default_settings = {
            "language": str(user["target_language"]).lower(),
            "practice_mode": "standard",
            "categories": list(
                user.get("preferred_categories") or list(DEFAULT_PREFERRED_CATEGORIES)
            ),
            "difficulties": list(
                self.word_service.get_difficulties_for_level(str(user["effective_level"]))
            ),
            "rounds": SESSION_LENGTH_OPTIONS[0],
            "review_policy": "prefer_review",
            "game_mode": "easy",
            "situation": SITUATIONS[0],
            "show_hint_immediately": True,
        }
        default_settings.update(saved_settings)
        return self._normalize_builder_settings(user=user, builder_settings=default_settings)

    def normalize_builder_settings(
        self,
        user: dict[str, Any],
        builder_settings: dict[str, Any],
    ) -> dict[str, Any]:
        """Expose builder normalization for guided-plan and UI reuse."""
        return self._normalize_builder_settings(user=user, builder_settings=builder_settings)

    def start_session(
        self,
        user: dict[str, Any],
        selected_category: str | None = None,
        rng: random.Random | None = None,
    ) -> GameRound:
        """Backward-compatible single-round wrapper around the session flow."""
        outcome = self.start_custom_learning_session(
            user=user,
            builder_settings={
                "language": user["target_language"],
                "practice_mode": "standard",
                "categories": (
                    [selected_category]
                    if selected_category
                    else list(
                        user.get("preferred_categories") or list(DEFAULT_PREFERRED_CATEGORIES)
                    )
                ),
                "difficulties": list(
                    self.word_service.get_difficulties_for_level(str(user["effective_level"]))
                ),
                "rounds": 1,
                "review_policy": "prefer_review",
                "game_mode": "easy",
                "situation": SITUATIONS[0],
                "show_hint_immediately": True,
            },
            rng=rng,
        )
        return outcome["first_round"]

    def start_learning_session(
        self,
        user: dict[str, Any],
        practice_mode: str = "standard",
        planned_rounds: int = 3,
        selected_category: str | None = None,
        rng: random.Random | None = None,
    ) -> tuple[LearningSession, GameRound]:
        """Backward-compatible helper for the earlier multi-round API."""
        outcome = self.start_custom_learning_session(
            user=user,
            builder_settings={
                "language": user["target_language"],
                "practice_mode": practice_mode,
                "categories": (
                    [selected_category]
                    if selected_category
                    else list(
                        user.get("preferred_categories") or list(DEFAULT_PREFERRED_CATEGORIES)
                    )
                ),
                "difficulties": list(
                    self.word_service.get_difficulties_for_level(str(user["effective_level"]))
                ),
                "rounds": planned_rounds,
                "review_policy": "prefer_review" if practice_mode != "review" else "review_only",
                "game_mode": "easy",
                "situation": SITUATIONS[0],
                "show_hint_immediately": True,
            },
            rng=rng,
        )
        return outcome["learning_session"], outcome["first_round"]

    def prepare_custom_session(
        self,
        user: dict[str, Any],
        builder_settings: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate custom builder settings and compute a safe session plan."""
        normalized_settings = self._normalize_builder_settings(
            user=user,
            builder_settings=builder_settings,
        )
        warnings: list[str] = []
        errors: list[str] = []

        available_languages = self.word_service.get_available_languages()
        if normalized_settings["language"] not in available_languages:
            errors.append(f"No word bank is available for '{normalized_settings['language']}'.")
            return {
                "can_start": False,
                "errors": errors,
                "warnings": warnings,
                "settings": normalized_settings,
                "matched_word_count": 0,
            }

        available_categories = self.word_service.get_categories(normalized_settings["language"])
        normalized_settings["categories"] = [
            category
            for category in normalized_settings["categories"]
            if category in available_categories
        ]
        if not normalized_settings["categories"]:
            errors.append("Choose at least one available category for this language.")
            return {
                "can_start": False,
                "errors": errors,
                "warnings": warnings,
                "settings": normalized_settings,
                "matched_word_count": 0,
            }

        available_difficulties = self.word_service.get_difficulties(normalized_settings["language"])
        normalized_settings["difficulties"] = [
            difficulty
            for difficulty in normalized_settings["difficulties"]
            if difficulty in available_difficulties
        ]
        if not normalized_settings["difficulties"]:
            errors.append("No words match the selected difficulty range for this language.")
            return {
                "can_start": False,
                "errors": errors,
                "warnings": warnings,
                "settings": normalized_settings,
                "matched_word_count": 0,
            }

        available_situations = self.word_service.get_available_situations(
            normalized_settings["language"]
        )
        if normalized_settings["situation"] not in available_situations:
            errors.append(
                "No words are available for that situation in this language yet. "
                "Try another situation or reload the word banks."
            )
            return {
                "can_start": False,
                "errors": errors,
                "warnings": warnings,
                "settings": normalized_settings,
                "matched_word_count": 0,
            }

        if (
            normalized_settings["practice_mode"] in {"review", "weak_words"}
            and normalized_settings["review_policy"] == "new_only"
        ):
            errors.append("Review modes cannot be combined with New Words Only.")
            return {
                "can_start": False,
                "errors": errors,
                "warnings": warnings,
                "settings": normalized_settings,
                "matched_word_count": 0,
            }

        recommendation = self.adaptation_service.build_recommendation(
            user=user,
            language=normalized_settings["language"],
            practice_mode=normalized_settings["practice_mode"],
            selected_categories=normalized_settings["categories"],
            selected_category=normalized_settings["selected_category"],
            difficulty_filter=normalized_settings["difficulties"],
            review_policy=normalized_settings["review_policy"],
        )

        weak_word_ids = [
            int(row["word_id"])
            for row in self.word_progress_repository.get_low_mastery_items(
                user_id=int(user["id"]),
                language=normalized_settings["language"],
                situation=normalized_settings["situation"],
                limit=100,
            )
        ]

        general_pool_count = self.word_service.count_candidate_words(
            language=normalized_settings["language"],
            categories=normalized_settings["categories"],
            difficulties=normalized_settings["difficulties"],
            situation=normalized_settings["situation"],
        )
        review_eligibility = self.review_eligibility(
            user_id=int(user["id"]),
            language=normalized_settings["language"],
            situation=normalized_settings["situation"],
            categories=normalized_settings["categories"],
            difficulties=normalized_settings["difficulties"],
        )
        review_pool_count = len(review_eligibility["due"]) + len(review_eligibility["upcoming"])
        situation_label = _situation_label(normalized_settings["situation"])
        new_word_pool_count = self.word_service.count_candidate_words(
            language=normalized_settings["language"],
            categories=normalized_settings["categories"],
            difficulties=normalized_settings["difficulties"],
            situation=normalized_settings["situation"],
            excluded_word_ids=recommendation["seen_word_ids"],
        )
        weak_word_pool_count = self.word_service.count_candidate_words(
            language=normalized_settings["language"],
            categories=normalized_settings["categories"],
            difficulties=normalized_settings["difficulties"],
            situation=normalized_settings["situation"],
            candidate_word_ids=weak_word_ids,
        )

        if normalized_settings["practice_mode"] == "weak_words":
            if weak_word_pool_count == 0:
                errors.append(
                    "No weak words match this situation yet. "
                    "Play a regular situation session first, then come back for review."
                )
                return {
                    "can_start": False,
                    "errors": errors,
                    "warnings": warnings,
                    "settings": normalized_settings,
                    "matched_word_count": 0,
                }
            matched_word_count = weak_word_pool_count
        elif normalized_settings["review_policy"] == "review_only":
            if review_pool_count == 0:
                errors.append(
                    f"There are no review words for {situation_label} yet. Review only uses "
                    "words you have already practised in this situation. "
                    "Play a Standard session first."
                )
                return {
                    "can_start": False,
                    "errors": errors,
                    "warnings": warnings,
                    "settings": normalized_settings,
                    "matched_word_count": 0,
                    "reason": "no_review_words",
                }
            matched_word_count = review_pool_count
        elif normalized_settings["review_policy"] == "new_only":
            if new_word_pool_count == 0:
                if general_pool_count == 0:
                    errors.append("No words match this practice setup.")
                    return {
                        "can_start": False,
                        "errors": errors,
                        "warnings": warnings,
                        "settings": normalized_settings,
                        "matched_word_count": 0,
                    }
                warnings.append(
                    "No completely new words matched the filters, "
                    "so this session will fall back to your regular pool."
                )
                normalized_settings["review_policy"] = "prefer_review"
                matched_word_count = general_pool_count
            else:
                matched_word_count = new_word_pool_count
        else:
            if general_pool_count == 0:
                errors.append("No words match this practice setup.")
                return {
                    "can_start": False,
                    "errors": errors,
                    "warnings": warnings,
                    "settings": normalized_settings,
                    "matched_word_count": 0,
                }
            matched_word_count = general_pool_count

        endless = normalized_settings["rounds"] >= ENDLESS_ROUNDS
        if endless and normalized_settings["review_policy"] == "review_only":
            # Review plays each eligible word once, so its length is simply that count.
            normalized_settings["rounds"] = matched_word_count
        elif matched_word_count < normalized_settings["rounds"] and not endless:
            if normalized_settings["review_policy"] == "review_only":
                warnings.append(
                    f"Only {matched_word_count} review word(s) are available for "
                    f"{situation_label}, so this session has {matched_word_count} round(s) "
                    f"instead of {normalized_settings['rounds']}."
                )
            else:
                warnings.append(
                    f"Only {matched_word_count} matching word(s) were available, "
                    "so the session was shortened from "
                    f"{normalized_settings['rounds']} rounds."
                )
            normalized_settings["rounds"] = matched_word_count

        if matched_word_count <= 0:
            errors.append("No playable words were available after validation.")

        return {
            "can_start": not errors,
            "errors": errors,
            "warnings": warnings,
            "settings": normalized_settings,
            "matched_word_count": matched_word_count,
        }

    def start_custom_learning_session(
        self,
        user: dict[str, Any],
        builder_settings: dict[str, Any],
        rng: random.Random | None = None,
    ) -> dict[str, Any]:
        """Create a validated multi-round learning session from custom builder settings."""
        preparation = self.prepare_custom_session(user=user, builder_settings=builder_settings)
        if not preparation["can_start"]:
            error_type = (
                NoReviewWordsError if preparation.get("reason") == "no_review_words" else ValueError
            )
            raise error_type(" ".join(preparation["errors"]))

        settings = preparation["settings"]
        started_at = utc_now_iso()
        session_id = self.learning_session_repository.create_learning_session(
            user_id=int(user["id"]),
            language=settings["language"],
            practice_mode=settings["practice_mode"],
            planned_rounds=settings["rounds"],
            selected_category=settings["selected_category"],
            selected_categories=serialize_string_list(settings["categories"]),
            difficulty_filter=serialize_string_list(settings["difficulties"]),
            review_policy=settings["review_policy"],
            show_hint_immediately=settings["show_hint_immediately"],
            game_mode=settings["game_mode"],
            situation=settings["situation"],
            started_at=started_at,
        )
        learning_session = LearningSession(
            user_id=int(user["id"]),
            language=settings["language"],
            practice_mode=settings["practice_mode"],
            planned_rounds=settings["rounds"],
            selected_categories=list(settings["categories"]),
            difficulty_filter=list(settings["difficulties"]),
            review_policy=settings["review_policy"],
            show_hint_immediately=bool(settings["show_hint_immediately"]),
            game_mode=settings["game_mode"],
            situation=settings["situation"],
            selected_category=settings["selected_category"],
            session_id=session_id,
            started_at=started_at,
        )
        first_round = self.build_next_round(user=user, learning_session=learning_session, rng=rng)
        warnings = list(preparation["warnings"])
        if first_round.selection_warning:
            warnings.append(first_round.selection_warning)
        return {
            "learning_session": learning_session,
            "first_round": first_round,
            "warnings": warnings,
            "settings": settings,
            "matched_word_count": preparation["matched_word_count"],
        }

    def build_next_round(
        self,
        user: dict[str, Any],
        learning_session: LearningSession,
        rng: random.Random | None = None,
    ) -> GameRound:
        """Create the next round for an active learning session."""
        recommendation = self.adaptation_service.build_recommendation(
            user=user,
            language=learning_session.language,
            practice_mode=learning_session.practice_mode,
            selected_categories=learning_session.selected_categories,
            selected_category=learning_session.selected_category,
            difficulty_filter=learning_session.difficulty_filter,
            review_policy=learning_session.review_policy,
            excluded_word_ids=learning_session.practiced_word_ids,
        )
        excluded_word_ids = list(recommendation["recent_word_ids"])
        if learning_session.practice_mode == "weak_words":
            excluded_word_ids = list(learning_session.practiced_word_ids)
        if learning_session.review_policy == "new_only":
            excluded_word_ids = list(
                dict.fromkeys(
                    [
                        *excluded_word_ids,
                        *recommendation["seen_word_ids"],
                    ]
                )
            )

        candidate_word_ids = None
        if learning_session.review_policy == "review_only":
            # Review: only eligible review words, due ones first, each once per session.
            # An empty list stays empty so selection cannot widen to unseen words.
            eligibility = self.review_eligibility(
                user_id=int(user["id"]),
                language=learning_session.language,
                situation=learning_session.situation,
                categories=learning_session.selected_categories,
                difficulties=learning_session.difficulty_filter,
            )
            practiced = set(learning_session.practiced_word_ids)
            due = [word_id for word_id in eligibility["due"] if word_id not in practiced]
            upcoming = [word_id for word_id in eligibility["upcoming"] if word_id not in practiced]
            candidate_word_ids = due or upcoming
            excluded_word_ids = list(learning_session.practiced_word_ids)
        elif learning_session.review_policy == "prefer_review":
            # Standard: review words are only a preference, never a restriction.
            candidate_word_ids = recommendation["candidate_word_ids"] or None
        if learning_session.practice_mode == "weak_words":
            candidate_word_ids = [
                int(row["word_id"])
                for row in self.word_progress_repository.get_low_mastery_items(
                    user_id=int(user["id"]),
                    language=learning_session.language,
                    situation=learning_session.situation,
                    limit=100,
                )
            ]

        selection_warning: str | None = None
        strict_mode = learning_session.review_policy in {"review_only", "new_only"}
        if learning_session.practice_mode == "weak_words":
            strict_mode = True
        selection_kwargs = {
            "language": learning_session.language,
            "level": str(recommendation["adapted_level"]),
            "preferred_categories": user.get("preferred_categories"),
            "selected_category": learning_session.selected_category,
            "selected_categories": learning_session.selected_categories,
            "category_order": recommendation["category_order"],
            "excluded_word_ids": excluded_word_ids,
            "candidate_word_ids": candidate_word_ids,
            "difficulty_override": learning_session.difficulty_filter,
            "deprioritized_word_ids": recommendation["deprioritized_word_ids"],
            "situation": learning_session.situation,
            "rng": rng,
        }

        smart_reason = ""
        repeated_word = self._least_recent_word(learning_session)
        candidate_pool = (
            []
            if repeated_word
            else self._build_smart_candidate_pool(
                learning_session=learning_session,
                recommendation=recommendation,
                candidate_word_ids=candidate_word_ids,
                excluded_word_ids=excluded_word_ids,
                strict_mode=strict_mode,
            )
        )
        if repeated_word:
            chosen_word = repeated_word
        elif candidate_pool:
            chosen_word, smart_reason = self.smart_practice_service.choose_word(
                user_id=int(user["id"]),
                candidate_words=candidate_pool,
                situation=str(learning_session.situation),
                difficulties=learning_session.difficulty_filter,
                review_candidate_ids=candidate_word_ids,
                recent_word_ids=excluded_word_ids,
                deprioritized_word_ids=recommendation["deprioritized_word_ids"],
                practice_mode=learning_session.practice_mode,
            )
        elif strict_mode:
            try:
                chosen_word = self.word_service.select_word(
                    strict_mode=True,
                    **selection_kwargs,
                )
            except ValueError as error:
                if learning_session.review_policy == "review_only":
                    raise ValueError(
                        "No review words remain for this session under "
                        "the strict review-only rules."
                    ) from error
                if learning_session.practice_mode == "weak_words":
                    raise ValueError(
                        "No weak words remain for this situation under the review rules."
                    ) from error

                chosen_word = self.word_service.select_word(
                    strict_mode=False,
                    **{
                        **selection_kwargs,
                        "excluded_word_ids": list(recommendation["recent_word_ids"]),
                    },
                )
                selection_warning = (
                    "No completely new words remained, so the session fell "
                    "back to your broader matching pool."
                )
        else:
            chosen_word = self.word_service.select_word(
                strict_mode=False,
                **selection_kwargs,
            )
        selection_reason = recommendation["reason"]
        if smart_reason:
            selection_reason = f"{selection_reason} {smart_reason}"
        return self.build_round(
            chosen_word=chosen_word,
            level=str(recommendation["adapted_level"]),
            round_type="practice",
            practice_mode=learning_session.practice_mode,
            selection_reason=selection_reason,
            selection_warning=selection_warning,
            learning_session_id=learning_session.session_id,
            show_hint_immediately=learning_session.show_hint_immediately,
            game_mode=learning_session.game_mode,
            situation=learning_session.situation,
        )

    def _least_recent_word(self, learning_session: LearningSession) -> dict[str, Any] | None:
        """Once an endless session has used its whole set, return the oldest word played.

        The scoring below would keep returning the same few high scorers, so a repeat
        follows the order words were last played in: the session's list, oldest first.
        """
        if learning_session.planned_rounds < ENDLESS_ROUNDS:
            return None
        words = {
            int(word["id"]): word
            for word in self.word_service.get_words(
                language=learning_session.language,
                categories=learning_session.selected_categories,
                difficulties=learning_session.difficulty_filter,
                situation=learning_session.situation,
            )
        }
        played = learning_session.practiced_word_ids
        if set(words) - set(played):
            return None
        return next((words[word_id] for word_id in played if word_id in words), None)

    def build_round(
        self,
        chosen_word: dict[str, Any],
        level: str,
        round_type: str = "practice",
        practice_mode: str = "standard",
        selection_reason: str | None = None,
        selection_warning: str | None = None,
        learning_session_id: int | None = None,
        show_hint_immediately: bool = True,
        game_mode: str = "easy",
        situation: str | None = None,
    ) -> GameRound:
        """Build a GameRound from a selected word payload."""
        mode_settings = GAME_MODE_SETTINGS.get(game_mode, GAME_MODE_SETTINGS["easy"])
        situations = list(chosen_word.get("situations") or [])
        selected_situation = situation or (situations[0] if situations else None)
        return GameRound(
            word_id=chosen_word["id"],
            word=chosen_word["word"],
            language=chosen_word["language"],
            level=level,
            category=chosen_word["category"],
            difficulty=chosen_word["difficulty"],
            hint=chosen_word["hint"],
            translation=chosen_word["translation"],
            example_sentence=chosen_word["example_sentence"],
            synonym=chosen_word.get("synonym"),
            association=chosen_word.get("association"),
            meaning=chosen_word.get("meaning") or chosen_word.get("translation"),
            situations=situations,
            situation=selected_situation,
            sentence_translation=(
                chosen_word.get("sentence_translation") or chosen_word.get("translation")
            ),
            pronunciation_text=chosen_word.get("pronunciation_text") or chosen_word.get("word"),
            usage_note=chosen_word.get("usage_note") or chosen_word.get("hint"),
            meaning_hint=chosen_word.get("meaning_hint") or chosen_word.get("hint"),
            synonym_hint=chosen_word.get("synonym_hint") or chosen_word.get("synonym"),
            association_hint=chosen_word.get("association_hint") or chosen_word.get("association"),
            round_type=round_type,
            practice_mode=practice_mode,
            game_mode=game_mode if game_mode in GAME_MODES else "easy",
            selection_reason=selection_reason,
            selection_warning=selection_warning,
            learning_session_id=learning_session_id,
            show_hint_immediately=show_hint_immediately,
            hint_mode=str(mode_settings["hint_mode"]),
            max_attempts=int(mode_settings["max_attempts"]),
        )

    def _build_smart_candidate_pool(
        self,
        *,
        learning_session: LearningSession,
        recommendation: dict[str, Any],
        candidate_word_ids: list[int] | None,
        excluded_word_ids: list[int],
        strict_mode: bool,
    ) -> list[dict[str, Any]]:
        """Build a candidate pool while keeping all words inside the situation."""
        words = self.word_service.get_words(
            language=learning_session.language,
            categories=learning_session.selected_categories,
            difficulties=learning_session.difficulty_filter,
            situation=learning_session.situation,
        )
        candidate_id_set = {int(word_id) for word_id in (candidate_word_ids or [])}
        if candidate_word_ids is not None and (
            strict_mode
            or learning_session.practice_mode == "weak_words"
            or learning_session.review_policy == "review_only"
        ):
            words = [word for word in words if int(word["id"]) in candidate_id_set]

        excluded_id_set = {int(word_id) for word_id in excluded_word_ids}
        if excluded_id_set:
            filtered_words = [word for word in words if int(word["id"]) not in excluded_id_set]
            if filtered_words or strict_mode:
                words = filtered_words

        deprioritized_ids = {
            int(word_id) for word_id in recommendation.get("deprioritized_word_ids", [])
        }
        prioritized_words = [word for word in words if int(word["id"]) not in deprioritized_ids]
        if prioritized_words:
            return prioritized_words
        return words

    def record_guess(self, round_state: GameRound, guess: str) -> dict[str, Any]:
        """Apply a single-letter guess and update the round state."""
        typed = unicodedata.normalize("NFC", guess.strip().lower())

        if round_state.is_complete:
            return {
                "accepted": False,
                "status": "info",
                "message": "This round is already finished.",
                "round_finished": True,
            }

        if len(typed) != 1 or not typed.isalpha():
            return {
                "accepted": False,
                "status": "warning",
                "message": "Enter one alphabetical letter at a time.",
                "round_finished": False,
            }

        letter = base_letter(typed)  # an accented letter counts as the plain one
        if letter in round_state.known_letters:
            return {
                "accepted": False,
                "status": "warning",
                "message": f"You already guessed '{letter}'. Try a different letter.",
                "round_finished": False,
            }

        round_state.guessed_letters.append(letter)

        if letter in round_state.unique_letters:
            feedback_line = get_random_line(
                CORRECT_LINES,
                round_state.used_correct_feedback_lines,
            )
            if round_state.unique_letters.issubset(round_state.known_letters):
                round_state.result = "won"
                round_state.completed_at = utc_now_iso()
                return {
                    "accepted": True,
                    "status": "success",
                    "message": f"{feedback_line} '{letter}' completes the word.",
                    "sound": "win",
                    "round_finished": True,
                }

            return {
                "accepted": True,
                "status": "success",
                "message": feedback_line,
                "sound": "correct",
                "round_finished": False,
            }

        round_state.wrong_letters.append(letter)
        feedback_line = get_random_line(
            INCORRECT_LINES,
            round_state.used_incorrect_feedback_lines,
        )
        if round_state.remaining_attempts == 0:
            round_state.result = "lost"
            round_state.completed_at = utc_now_iso()
            return {
                "accepted": True,
                "status": "error",
                "message": f"{feedback_line} No attempts left. The word was '{round_state.word}'.",
                "sound": "loss",
                "round_finished": True,
            }

        return {
            "accepted": True,
            "status": "warning",
            "message": feedback_line,
            "sound": "wrong",
            "round_finished": False,
        }

    def complete_session(self, user_id: int, round_state: GameRound) -> int:
        """Persist a finished round to SQLite and return the session id."""
        if round_state.saved and round_state.session_id is not None:
            return round_state.session_id

        if not round_state.is_complete:
            raise ValueError("Cannot save a session until the round is finished.")

        completed_at = round_state.completed_at or utc_now_iso()
        time_taken_seconds = self._calculate_time_taken(
            started_at=round_state.started_at,
            completed_at=completed_at,
        )
        if round_state.active_seconds is not None:
            time_taken_seconds = round_state.active_seconds
        session_id = self.game_session_repository.create_session(
            user_id=user_id,
            word_id=round_state.word_id,
            language=round_state.language,
            situation=round_state.situation,
            level=round_state.level,
            category=round_state.category,
            practice_mode=round_state.practice_mode,
            learning_session_id=round_state.learning_session_id,
            result=round_state.result,
            attempts_used=round_state.attempts_used,
            max_attempts=round_state.max_attempts,
            letters_correct=round_state.letters_correct,
            letters_wrong=round_state.letters_wrong,
            guessed_letters=",".join(round_state.guessed_letters),
            hints_used=len(round_state.revealed_hint_keys),
            time_taken_seconds=time_taken_seconds,
            started_at=round_state.started_at,
            completed_at=completed_at,
            played_at=completed_at,
        )
        round_state.saved = True
        round_state.session_id = session_id
        round_state.completed_at = completed_at
        return session_id

    def finalize_round(self, user, round_state, learning_session, rng=None):
        """Commit completion exactly once; failed saves never mutate caller state."""
        if int(user["id"]) != learning_session.user_id:
            raise ValueError("The session belongs to another profile.")
        if round_state.learning_session_id != learning_session.session_id:
            raise ValueError("The round does not belong to this session.")
        path = self.game_session_repository.db_path
        with transaction(path) as connection:
            receipt = connection.execute(
                "SELECT user_id, payload FROM completion_receipts WHERE round_key = ?",
                (round_state.round_key,),
            ).fetchone()
            if receipt:
                if receipt["user_id"] != int(user["id"]):
                    raise ValueError("The round belongs to another profile.")
                data = json.loads(receipt["payload"])
                result = data["outcome"]
                saved_round = GameRound(**data["round"])
                saved_session = LearningSession(**result["learning_session"])
                result["learning_session"] = saved_session
                result["next_round"] = (
                    GameRound(**result["next_round"]) if result["next_round"] else None
                )
            else:
                saved_round = copy.deepcopy(round_state)
                saved_session = copy.deepcopy(learning_session)
                result = self._finalize_round(user, saved_round, saved_session, rng)
                serialized = dict(result)
                serialized["learning_session"] = asdict(saved_session)
                serialized["next_round"] = (
                    asdict(result["next_round"]) if result["next_round"] else None
                )
                connection.execute(
                    "INSERT INTO completion_receipts(round_key,user_id,payload) VALUES(?,?,?)",
                    (
                        round_state.round_key,
                        int(user["id"]),
                        json.dumps({"round": asdict(saved_round), "outcome": serialized}),
                    ),
                )
        for field in fields(round_state):
            setattr(round_state, field.name, copy.deepcopy(getattr(saved_round, field.name)))
        # An old retry must not rewind a session that has already progressed further.
        if learning_session.completed_rounds <= saved_session.completed_rounds:
            for field in fields(learning_session):
                setattr(
                    learning_session, field.name, copy.deepcopy(getattr(saved_session, field.name))
                )
        result["learning_session"] = learning_session
        return result

    def _finalize_round(
        self,
        user: dict[str, Any],
        round_state: GameRound,
        learning_session: LearningSession,
        rng: random.Random | None = None,
    ) -> dict[str, Any]:
        """Persist a completed round, update mastery/review tracking, and advance the session."""
        session_id = self.complete_session(user_id=int(user["id"]), round_state=round_state)
        progress_snapshot = self._update_word_progress_for_round(
            user_id=int(user["id"]),
            round_state=round_state,
        )
        review_plan = self._schedule_review_for_round(
            user_id=int(user["id"]),
            round_state=round_state,
            progress_snapshot=progress_snapshot,
        )
        learning_review = self.build_learning_review(
            round_state=round_state,
            review_plan=review_plan,
            progress_snapshot=progress_snapshot,
        )

        learning_session.completed_rounds += 1
        if round_state.result == "won":
            learning_session.wins += 1
        else:
            learning_session.losses += 1
        learning_session.total_correct_letters += round_state.letters_correct
        learning_session.total_wrong_letters += round_state.letters_wrong
        learning_session.round_ids.append(session_id)
        endless = learning_session.planned_rounds >= ENDLESS_ROUNDS
        if endless and round_state.word_id in learning_session.practiced_word_ids:
            learning_session.practiced_word_ids.remove(round_state.word_id)  # now the newest
        if round_state.word_id not in learning_session.practiced_word_ids:
            learning_session.practiced_word_ids.append(round_state.word_id)
        if round_state.word not in learning_session.words_practiced:
            learning_session.words_practiced.append(round_state.word)
        if round_state.category not in learning_session.categories_practiced:
            learning_session.categories_practiced.append(round_state.category)
        if not endless:  # only a session summary reads these, and they grow with every word
            learning_session.round_reviews.append(learning_review)

        next_round = None
        session_summary = None
        status = "success" if round_state.result == "won" else "warning"
        message = "Round saved. Review the learning details and continue when you're ready."

        if learning_session.completed_rounds >= learning_session.planned_rounds:
            learning_session.status = "completed"
            learning_session.completed_at = round_state.completed_at
            session_summary = self.build_session_summary(learning_session)
            learning_session.recommendation = str(session_summary["recommendation"])
            message = "Session complete. Review your session summary below."
            status = "success"
        else:
            try:
                next_round = self.build_next_round(
                    user=user,
                    learning_session=learning_session,
                    rng=rng,
                )
            except ValueError as error:
                learning_session.status = "completed"
                learning_session.completed_at = round_state.completed_at
                session_summary = self.build_session_summary(learning_session)
                learning_session.recommendation = str(session_summary["recommendation"])
                message = (
                    "Session ended early because the remaining words no longer "
                    "matched the strict selection rules. "
                    f"{error}"
                )
                status = "warning"
            else:
                if next_round.selection_warning:
                    message = f"{message} {next_round.selection_warning}"
                    status = "warning"

        self.learning_session_repository.update_learning_session(
            session_id=int(learning_session.session_id or 0),
            completed_rounds=learning_session.completed_rounds,
            wins=learning_session.wins,
            losses=learning_session.losses,
            accuracy=learning_session.session_accuracy,
            categories_practiced=serialize_string_list(learning_session.categories_practiced),
            words_practiced=serialize_string_list(learning_session.words_practiced),
            status=learning_session.status,
            recommendation=learning_session.recommendation,
            completed_at=learning_session.completed_at,
        )

        return {
            "session_complete": learning_session.is_complete,
            "next_round": next_round,
            "learning_review": learning_review,
            "learning_session": learning_session,
            "session_summary": session_summary,
            "message": message,
            "status": status,
        }

    def build_learning_review(
        self,
        round_state: GameRound,
        review_plan: dict[str, Any] | None = None,
        progress_snapshot: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return compact post-round learning details for the UI."""
        return {
            "result": round_state.result,
            "word": round_state.word,
            "meaning": round_state.meaning or round_state.translation,
            "situation": round_state.situation,
            "situations": list(round_state.situations),
            "translation": round_state.translation,
            "example_sentence": round_state.example_sentence,
            "sentence_translation": round_state.sentence_translation or round_state.translation,
            "pronunciation_text": round_state.pronunciation_text or round_state.word,
            "usage_note": round_state.usage_note or round_state.hint,
            "synonym": round_state.synonym,
            "association": round_state.association,
            "category": round_state.category,
            "difficulty": round_state.difficulty,
            "practice_mode": round_state.practice_mode,
            "attempts_used": round_state.attempts_used,
            "letters_wrong": round_state.letters_wrong,
            "letters_correct": round_state.letters_correct,
            "wrong_letters": list(round_state.wrong_letters),
            "selection_reason": round_state.selection_reason,
            "selection_warning": round_state.selection_warning,
            "marked_for_review": bool(review_plan and review_plan["is_active"]),
            "review_due_at": review_plan["review_due_at"] if review_plan else None,
            "next_review_in_days": review_plan["next_review_in_days"] if review_plan else None,
            "review_reason": review_plan["reason"] if review_plan else None,
            "familiarity_status": (
                progress_snapshot["familiarity_status"] if progress_snapshot else None
            ),
            "mastery_status": (progress_snapshot["mastery_status"] if progress_snapshot else None),
            "mastery_score": progress_snapshot["mastery_score"] if progress_snapshot else None,
            "word_priority_score": (
                progress_snapshot["priority_score"] if progress_snapshot else None
            ),
        }

    def build_session_summary(self, learning_session: LearningSession) -> dict[str, Any]:
        """Return a compact session summary and recommendation payload."""
        total_rounds = max(learning_session.completed_rounds, 1)
        win_rate = learning_session.wins / total_rounds
        review_items = [
            review for review in learning_session.round_reviews if review["marked_for_review"]
        ]
        mastered_reviews = [
            review
            for review in learning_session.round_reviews
            if review.get("mastery_status") == "mastered"
        ]
        learning_reviews = [
            review
            for review in learning_session.round_reviews
            if review.get("mastery_status") in {"weak", "learning"}
        ]
        weak_words = [
            review["word"]
            for review in learning_session.round_reviews
            if review.get("mastery_status") == "weak" or review.get("result") == "lost"
        ]
        weak_category = self._get_most_difficult_category(learning_session)
        recommended_mode = (
            "weak_words" if weak_words else ("review" if review_items else "weak_area")
        )
        recommended_category = weak_category
        recommended_length = (
            5 if learning_session.planned_rounds < 5 else learning_session.planned_rounds
        )

        if not review_items and win_rate >= 0.8:
            recommended_mode = "standard"
            recommended_length = (
                5
                if learning_session.planned_rounds < 5
                else min(
                    learning_session.planned_rounds + 2,
                    10,
                )
            )

        encouragement = self._build_encouragement_message(win_rate)
        recommendation = self._build_recommendation_message(
            recommended_mode=recommended_mode,
            recommended_category=recommended_category,
            win_rate=win_rate,
            review_items=review_items,
        )

        return {
            "language": learning_session.language,
            "situation": learning_session.situation,
            "practice_mode": learning_session.practice_mode,
            "rounds_played": learning_session.completed_rounds,
            "wins": learning_session.wins,
            "losses": learning_session.losses,
            "session_accuracy": learning_session.session_accuracy,
            "categories_practiced": list(learning_session.categories_practiced),
            "words_practiced": list(learning_session.words_practiced),
            "review_words": [review["word"] for review in review_items],
            "words_mastered": [review["word"] for review in mastered_reviews],
            "words_still_learning": [review["word"] for review in learning_reviews],
            "weak_words": list(dict.fromkeys(weak_words)),
            "encouragement": encouragement,
            "recommendation": recommendation,
            "recommended_mode": recommended_mode,
            "recommended_category": recommended_category,
            "recommended_length": recommended_length,
        }

    def _normalize_builder_settings(
        self,
        user: dict[str, Any],
        builder_settings: dict[str, Any],
    ) -> dict[str, Any]:
        """Normalize raw builder settings into a predictable session payload."""
        language = str(builder_settings.get("language") or user["target_language"]).strip().lower()
        practice_mode = str(builder_settings.get("practice_mode") or "standard").strip().lower()
        if practice_mode not in PRACTICE_MODES:
            practice_mode = "standard"

        raw_categories = builder_settings.get("categories")
        if not raw_categories:
            raw_categories = list(
                user.get("preferred_categories") or list(DEFAULT_PREFERRED_CATEGORIES)
            )
        categories = list(
            dict.fromkeys(
                str(category).strip().lower()
                for category in raw_categories
                if str(category).strip()
            )
        )

        raw_difficulties = builder_settings.get("difficulties")
        if not raw_difficulties:
            raw_difficulties = list(
                self.word_service.get_difficulties_for_level(str(user["effective_level"]))
            )
        difficulties = list(
            dict.fromkeys(
                str(difficulty).strip().lower()
                for difficulty in raw_difficulties
                if str(difficulty).strip()
            )
        )

        rounds = int(builder_settings.get("rounds") or SESSION_LENGTH_OPTIONS[0])
        if rounds < 1:
            rounds = SESSION_LENGTH_OPTIONS[0]

        review_policy = (
            str(builder_settings.get("review_policy") or "prefer_review").strip().lower()
        )
        if review_policy not in REVIEW_POLICIES:
            review_policy = "prefer_review"
        if practice_mode == "weak_words" and review_policy == "prefer_review":
            review_policy = "review_only"

        raw_game_mode = builder_settings.get("game_mode")
        if raw_game_mode:
            game_mode = str(raw_game_mode).strip().lower()
        else:
            game_mode = (
                "easy" if bool(builder_settings.get("show_hint_immediately", True)) else "hard"
            )
        if game_mode not in GAME_MODES:
            game_mode = "easy"

        situation = self._normalize_situation(builder_settings.get("situation"))

        selected_category = categories[0] if len(categories) == 1 else None
        return {
            "language": language,
            "practice_mode": practice_mode,
            "categories": categories,
            "selected_category": selected_category,
            "difficulties": difficulties,
            "rounds": rounds,
            "review_policy": review_policy,
            "game_mode": game_mode,
            "situation": situation,
            "show_hint_immediately": game_mode == "easy",
        }

    def _normalize_situation(self, raw_situation: Any) -> str:
        """Return a supported situation key for situation-based practice."""
        normalized = str(raw_situation or "").strip().lower().replace(" ", "_").replace("/", "_")
        aliases = {
            "metro": "metro_train_station",
            "train_station": "metro_train_station",
            "metro_train": "metro_train_station",
            "school": "school_college",
            "college": "school_college",
        }
        normalized = aliases.get(normalized, normalized)
        return normalized if normalized in SITUATIONS else SITUATIONS[0]

    def _update_word_progress_for_round(
        self,
        user_id: int,
        round_state: GameRound,
    ) -> dict[str, Any]:
        """Update lightweight word-level mastery tracking after a round."""
        existing_progress = self.word_progress_repository.get_item(user_id, round_state.word_id)
        previous_wins = int(existing_progress["wins"] or 0) if existing_progress else 0
        previous_losses = int(existing_progress["losses"] or 0) if existing_progress else 0
        previous_streak = (
            int(existing_progress["successful_streak"] or 0) if existing_progress else 0
        )
        previous_correct = (
            int(existing_progress["total_correct_letters"] or 0) if existing_progress else 0
        )
        previous_wrong = (
            int(existing_progress["total_wrong_letters"] or 0) if existing_progress else 0
        )
        previous_times_seen = int(existing_progress["times_seen"] or 0) if existing_progress else 0
        previous_mastery_score = (
            float(existing_progress["mastery_score"] or 0.0) if existing_progress else 0.0
        )
        previous_attempt_count = (
            int(existing_progress["attempt_count"] or 0) if existing_progress else 0
        )
        previous_total_hints = (
            int(existing_progress["total_hints_used"] or 0) if existing_progress else 0
        )

        guess_accuracy = (
            round_state.letters_correct / round_state.attempts_used
            if round_state.attempts_used
            else 0.0
        )
        hints_used = len(round_state.revealed_hint_keys)
        completed_at = round_state.completed_at or utc_now_iso()
        time_taken_seconds = self._calculate_time_taken(
            started_at=round_state.started_at,
            completed_at=completed_at,
        )
        if round_state.active_seconds is not None:
            time_taken_seconds = round_state.active_seconds
        times_seen = previous_times_seen + 1
        attempt_count = previous_attempt_count + 1
        wins = previous_wins + (1 if round_state.result == "won" else 0)
        losses = previous_losses + (1 if round_state.result == "lost" else 0)
        successful_streak = (
            previous_streak + 1 if round_state.result == "won" and guess_accuracy >= 0.75 else 0
        )
        total_correct_letters = previous_correct + round_state.letters_correct
        total_wrong_letters = previous_wrong + round_state.letters_wrong
        total_guesses = total_correct_letters + total_wrong_letters
        average_accuracy = total_correct_letters / total_guesses if total_guesses else 0.0
        mastery_score = self._calculate_mastery_score(
            previous_mastery_score=previous_mastery_score,
            result=round_state.result,
            guess_accuracy=guess_accuracy,
            remaining_attempts=round_state.remaining_attempts,
            times_seen=times_seen,
            successful_streak=successful_streak,
            hints_used=hints_used,
            time_taken_seconds=time_taken_seconds,
        )
        mastery_status = self._determine_mastery_status(mastery_score)
        familiarity_status = self._determine_familiarity_status(
            mastery_score=mastery_score,
            wins=wins,
            losses=losses,
            times_seen=times_seen,
            successful_streak=successful_streak,
            round_result=round_state.result,
        )

        priority_score = self._calculate_word_priority(
            familiarity_status=familiarity_status,
            mastery_score=mastery_score,
            losses=losses,
            wins=wins,
            average_accuracy=average_accuracy,
            successful_streak=successful_streak,
            last_result=round_state.result,
        )

        self.word_progress_repository.upsert_progress(
            user_id=user_id,
            word_id=round_state.word_id,
            language=round_state.language,
            familiarity_status=familiarity_status,
            mastery_status=mastery_status,
            mastery_score=mastery_score,
            wins_delta=1 if round_state.result == "won" else 0,
            losses_delta=1 if round_state.result == "lost" else 0,
            successful_streak=successful_streak,
            correct_letters_delta=round_state.letters_correct,
            wrong_letters_delta=round_state.letters_wrong,
            wrong_guesses_delta=round_state.letters_wrong,
            hints_used_delta=hints_used,
            last_accuracy=round(guess_accuracy, 2),
            last_result=round_state.result,
            priority_score=priority_score,
            last_played_at=completed_at,
        )

        return {
            "familiarity_status": familiarity_status,
            "mastery_status": mastery_status,
            "mastery_score": mastery_score,
            "priority_score": priority_score,
            "times_seen": times_seen,
            "attempt_count": attempt_count,
            "total_hints_used": previous_total_hints + hints_used,
            "average_accuracy": round(average_accuracy, 2),
        }

    def _schedule_review_for_round(
        self,
        user_id: int,
        round_state: GameRound,
        progress_snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        """Update the review queue after a completed round."""
        completed_at = round_state.completed_at or utc_now_iso()
        guess_accuracy = (
            round_state.letters_correct / round_state.attempts_used
            if round_state.attempts_used
            else 0.0
        )
        existing_review_item = self.review_queue_repository.get_item(
            user_id=user_id,
            word_id=round_state.word_id,
        )
        review_count = int(existing_review_item["review_count"] or 0) if existing_review_item else 0

        plan = self._build_review_plan(
            round_state=round_state,
            progress_snapshot=progress_snapshot,
            guess_accuracy=guess_accuracy,
            completed_at=completed_at,
            review_count=review_count,
        )

        self.review_queue_repository.upsert_review_item(
            user_id=user_id,
            word_id=round_state.word_id,
            language=round_state.language,
            category=round_state.category,
            priority_score=plan["priority_score"],
            review_due_at=plan["review_due_at"],
            last_reviewed_at=completed_at,
            last_result=round_state.result,
            last_accuracy=round(guess_accuracy, 2),
            is_active=bool(plan["is_active"]),
        )

        return {
            **plan,
            "guess_accuracy": round(guess_accuracy, 2),
        }

    def _calculate_word_priority(
        self,
        familiarity_status: str,
        mastery_score: float,
        losses: int,
        wins: int,
        average_accuracy: float,
        successful_streak: int,
        last_result: str,
    ) -> float:
        """Return a simple rule-based priority score for future practice."""
        status_defaults = {
            "new": 0.45,
            "learning": 0.8,
            "familiar": 0.3,
            "strong": 0.1,
        }
        priority_score = status_defaults.get(
            familiarity_status if familiarity_status in FAMILIARITY_STATES else "learning",
            0.5,
        )
        total_results = max(wins + losses, 1)
        loss_rate = losses / total_results
        priority_score += loss_rate * 0.2
        priority_score += max(0.75 - average_accuracy, 0.0) * 0.2
        priority_score += max(0.65 - (mastery_score / 100), 0.0) * 0.25
        if last_result == "lost":
            priority_score += 0.15
        if successful_streak >= 2:
            priority_score -= 0.08
        return round(min(max(priority_score, 0.05), 1.0), 2)

    def _calculate_mastery_score(
        self,
        previous_mastery_score: float,
        result: str,
        guess_accuracy: float,
        remaining_attempts: int,
        times_seen: int,
        successful_streak: int,
        hints_used: int = 0,
        time_taken_seconds: float | None = None,
    ) -> float:
        """Return a lightweight 0-100 word mastery score."""
        starting_score = previous_mastery_score if previous_mastery_score > 0 else 10.0

        if result == "lost":
            score_delta = -20.0 + (guess_accuracy * 5.0)
        elif guess_accuracy >= 0.99 and remaining_attempts >= 3:
            score_delta = 18.0
        elif guess_accuracy >= 0.75 and remaining_attempts >= 2:
            score_delta = 12.0
        elif guess_accuracy >= LOW_REVIEW_ACCURACY_THRESHOLD:
            score_delta = 8.0
        else:
            score_delta = 4.0

        if result == "won" and successful_streak >= 2:
            score_delta += 4.0
        if result == "won" and times_seen == 1:
            score_delta += 3.0
        if hints_used:
            score_delta -= min(hints_used * 2.5, 8.0)
        if time_taken_seconds and time_taken_seconds > 90:
            score_delta -= min((time_taken_seconds - 90) / 60, 5.0)

        mastery_score = starting_score + score_delta
        return round(min(max(mastery_score, 0.0), 100.0), 2)

    def _determine_mastery_status(self, mastery_score: float) -> str:
        """Map a numeric mastery score to the beta mastery labels."""
        return self.smart_practice_service.mastery_status_for_score(mastery_score)

    def _determine_familiarity_status(
        self,
        mastery_score: float,
        wins: int,
        losses: int,
        times_seen: int,
        successful_streak: int,
        round_result: str,
    ) -> str:
        """Map the mastery score into a learner-friendly familiarity label."""
        if (
            mastery_score >= 75
            and wins >= 3
            and successful_streak >= 2
            and losses <= max(1, wins // 2)
        ):
            return "strong"
        if mastery_score >= 50 and wins >= 2 and losses <= wins:
            return "familiar"
        if times_seen == 1 and round_result != "lost" and mastery_score < 35:
            return "new"
        return "learning"

    def _build_review_plan(
        self,
        round_state: GameRound,
        progress_snapshot: dict[str, Any],
        guess_accuracy: float,
        completed_at: str,
        review_count: int,
    ) -> dict[str, Any]:
        """Return the next spaced-review step for the completed word."""
        if round_state.result == "lost":
            next_review_in_days = 1 if progress_snapshot["mastery_score"] < 60 else 2
            return {
                "priority_score": max(progress_snapshot["priority_score"], 0.9),
                "review_due_at": shift_utc_iso(completed_at, days=next_review_in_days),
                "next_review_in_days": next_review_in_days,
                "is_active": True,
                "reason": "Missed words come back quickly while the feedback is still fresh.",
            }

        if guess_accuracy < LOW_REVIEW_ACCURACY_THRESHOLD or round_state.remaining_attempts <= 1:
            next_review_in_days = 2 if review_count < 2 else 3
            return {
                "priority_score": max(progress_snapshot["priority_score"], 0.78),
                "review_due_at": shift_utc_iso(completed_at, days=next_review_in_days),
                "next_review_in_days": next_review_in_days,
                "is_active": True,
                "reason": "Hard-won words return soon so the pattern settles in.",
            }

        if (
            guess_accuracy < DIFFICULT_REVIEW_ACCURACY_THRESHOLD
            or round_state.letters_wrong >= 2
            or progress_snapshot["familiarity_status"] == "learning"
        ):
            next_review_in_days = 4 + min(review_count, 2)
            return {
                "priority_score": max(progress_snapshot["priority_score"], 0.5),
                "review_due_at": shift_utc_iso(completed_at, days=next_review_in_days),
                "next_review_in_days": next_review_in_days,
                "is_active": True,
                "reason": (
                    "This word is still settling, so it is scheduled for a "
                    "medium follow-up review."
                ),
            }

        if progress_snapshot["familiarity_status"] == "new":
            next_review_in_days = 5
            return {
                "priority_score": max(min(progress_snapshot["priority_score"], 0.4), 0.25),
                "review_due_at": shift_utc_iso(completed_at, days=next_review_in_days),
                "next_review_in_days": next_review_in_days,
                "is_active": True,
                "reason": (
                    "New words get one calmer follow-up before they are " "spaced further apart."
                ),
            }

        if progress_snapshot["familiarity_status"] == "familiar":
            next_review_in_days = 7 + (min(review_count, 2) * 3)
            return {
                "priority_score": max(min(progress_snapshot["priority_score"], 0.3), 0.2),
                "review_due_at": shift_utc_iso(completed_at, days=next_review_in_days),
                "next_review_in_days": next_review_in_days,
                "is_active": True,
                "reason": (
                    "Familiar words can wait longer, but they still deserve " "a later check-in."
                ),
            }

        next_review_in_days = 14 + (min(review_count, 2) * 7)
        return {
            "priority_score": min(progress_snapshot["priority_score"], 0.15),
            "review_due_at": shift_utc_iso(completed_at, days=next_review_in_days),
            "next_review_in_days": next_review_in_days,
            "is_active": False,
            "reason": (
                "Strong words are spaced farther apart and dropped from the "
                "active review queue for now."
            ),
        }

    def _build_encouragement_message(self, win_rate: float) -> str:
        """Return a lightweight motivational note for the session summary."""
        if win_rate >= 0.8:
            return "Strong session. You are handling these words with growing confidence."
        if win_rate >= 0.5:
            return "Solid progress. A little focused review will help the words stick."
        return (
            "This was a challenging session, which is still useful practice. "
            "A targeted review will help."
        )

    def _build_recommendation_message(
        self,
        recommended_mode: str,
        recommended_category: str | None,
        win_rate: float,
        review_items: list[dict[str, Any]],
    ) -> str:
        """Return a deterministic next-step recommendation for the learner."""
        if recommended_mode == "weak_words":
            return "Review weak words from this situation before starting something harder."

        if recommended_mode == "review" and review_items:
            if recommended_category:
                return f"Review difficult {recommended_category} words next."
            return "Try a short review practice session next."

        if recommended_mode == "weak_area" and recommended_category:
            return f"Practice {recommended_category} next in a weak-area session."

        if win_rate >= 0.8:
            return "You are doing well enough to try a longer standard session."

        return "Try another short standard session to reinforce today's words."

    def _get_most_difficult_category(self, learning_session: LearningSession) -> str | None:
        """Return the category that caused the most trouble during this session."""
        category_scores: dict[str, float] = {}
        for review in learning_session.round_reviews:
            category = str(review["category"])
            category_scores.setdefault(category, 0.0)
            if review["result"] == "lost":
                category_scores[category] += 2.0
            elif review["marked_for_review"]:
                category_scores[category] += 1.0
            else:
                category_scores[category] -= 0.2

        if not category_scores:
            return None

        return sorted(category_scores.items(), key=lambda item: (-item[1], item[0]))[0][0]

    def _calculate_time_taken(self, started_at: str, completed_at: str) -> float:
        """Return the time taken for the round in seconds."""
        start_time = datetime.fromisoformat(started_at)
        end_time = datetime.fromisoformat(completed_at)
        return max((end_time - start_time).total_seconds(), 0.0)
