"""Situation-aware, rule-based word recommendation engine.

The scoring shape is intentionally explicit and ML-ready: future model output can
replace or augment these feature weights without changing the gameplay service.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from src.db.repository import WordProgressRepository
from src.utils.constants import DIFFICULTY_ORDER


class SmartPracticeService:
    """Rank candidate words using situation, mastery, and review signals."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.word_progress_repository = WordProgressRepository(db_path=db_path)

    def choose_word(
        self,
        *,
        user_id: int,
        candidate_words: Sequence[dict[str, Any]],
        situation: str,
        difficulties: Sequence[str],
        review_candidate_ids: Sequence[int] | None = None,
        recent_word_ids: Sequence[int] | None = None,
        deprioritized_word_ids: Sequence[int] | None = None,
        practice_mode: str = "standard",
    ) -> tuple[dict[str, Any], str]:
        """Return the highest-scored word and a short explanation."""
        if not candidate_words:
            raise ValueError("No words are available for this situation and setup.")

        review_ids = {int(word_id) for word_id in (review_candidate_ids or [])}
        recent_ids = {int(word_id) for word_id in (recent_word_ids or [])}
        deprioritized_ids = {int(word_id) for word_id in (deprioritized_word_ids or [])}
        difficulty_set = {str(difficulty).lower() for difficulty in difficulties}

        scored_words = [
            (
                self.score_word(
                    user_id=user_id,
                    word=word,
                    situation=situation,
                    difficulties=difficulty_set,
                    review_candidate_ids=review_ids,
                    recent_word_ids=recent_ids,
                    deprioritized_word_ids=deprioritized_ids,
                    practice_mode=practice_mode,
                ),
                word,
            )
            for word in candidate_words
        ]
        scored_words.sort(
            key=lambda item: (
                -item[0]["score"],
                str(item[1].get("difficulty", "")),
                str(item[1].get("category", "")),
                str(item[1].get("word", "")),
            )
        )
        best_features, best_word = scored_words[0]
        return best_word, self._build_reason(best_features)

    def score_word(
        self,
        *,
        user_id: int,
        word: dict[str, Any],
        situation: str,
        difficulties: set[str],
        review_candidate_ids: set[int],
        recent_word_ids: set[int],
        deprioritized_word_ids: set[int],
        practice_mode: str,
    ) -> dict[str, Any]:
        """Return explainable scoring features for one candidate word."""
        word_id = int(word["id"])
        word_situations = {str(item).lower() for item in word.get("situations", [])}
        situation_match = situation in word_situations
        score = 60.0 if situation_match else -500.0

        difficulty = str(word.get("difficulty", "")).lower()
        score += 12.0 if difficulty in difficulties else -10.0
        if difficulty in DIFFICULTY_ORDER:
            score += (
                max(0, len(DIFFICULTY_ORDER) - DIFFICULTY_ORDER.index(difficulty)) * 0.2
            )

        progress = self.word_progress_repository.get_item(user_id=user_id, word_id=word_id)
        mastery_score = float(progress["mastery_score"] or 0.0) if progress else 0.0
        mastery_status = str(progress["mastery_status"] or "weak") if progress else "new"
        last_result = str(progress["last_result"] or "") if progress else ""
        total_wrong_guesses = int(progress["total_wrong_guesses"] or 0) if progress else 0
        total_hints_used = int(progress["total_hints_used"] or 0) if progress else 0
        attempt_count = int(progress["attempt_count"] or 0) if progress else 0
        last_seen_date = str(progress["last_seen_date"] or "") if progress else ""

        if not progress:
            score += 18.0
        else:
            score += (100.0 - mastery_score) * 0.28
            score += min(total_wrong_guesses * 1.5, 12.0)
            score += min(total_hints_used * 1.25, 8.0)
            score += min(attempt_count, 8) * 0.35
            score += self._last_seen_bonus(last_seen_date)
            if last_result == "lost":
                score += 14.0
            if mastery_status == "mastered":
                score -= 32.0
            elif mastery_status == "almost_mastered":
                score -= 14.0

        if word_id in review_candidate_ids:
            score += 25.0
        if practice_mode == "weak_words":
            is_weak_candidate = mastery_status in {"weak", "learning"} or last_result == "lost"
            score += 30.0 if is_weak_candidate else -30.0
        if word_id in recent_word_ids:
            score -= 35.0
        if word_id in deprioritized_word_ids:
            score -= 18.0

        return {
            "score": round(score, 2),
            "situation_match": situation_match,
            "mastery_score": mastery_score,
            "mastery_status": mastery_status,
            "last_result": last_result,
            "is_review": word_id in review_candidate_ids,
            "is_recent": word_id in recent_word_ids,
            "practice_mode": practice_mode,
        }

    def mastery_status_for_score(self, score: float) -> str:
        """Map a 0-100 mastery score to the beta product labels."""
        if score <= 30:
            return "weak"
        if score <= 70:
            return "learning"
        if score <= 90:
            return "almost_mastered"
        return "mastered"

    def _last_seen_bonus(self, last_seen_date: str) -> float:
        """Gently favor words that have not appeared recently."""
        if not last_seen_date:
            return 6.0
        try:
            last_seen = datetime.fromisoformat(last_seen_date)
        except ValueError:
            return 3.0
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        age_days = max((datetime.now(timezone.utc) - last_seen).days, 0)
        return min(age_days * 0.7, 14.0)

    def _build_reason(self, features: dict[str, Any]) -> str:
        """Build a compact user-safe recommendation explanation."""
        if features["practice_mode"] == "weak_words":
            return "Smart Practice selected a weak or review-needed word for this situation."
        if features["is_review"]:
            return "Smart Practice selected a review word that still matches this situation."
        if features["mastery_status"] in {"weak", "learning"}:
            return "Smart Practice prioritized a word that still needs practice."
        return "Smart Practice selected a relevant word for this situation."
