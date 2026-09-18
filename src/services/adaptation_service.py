"""Rule-based adaptation helpers for next-word selection."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from src.db.repository import (
    GameSessionRepository,
    PerformanceSummaryRepository,
    ReviewQueueRepository,
    WordProgressRepository,
    WordRepository,
)
from src.utils.constants import (
    DEFAULT_PREFERRED_CATEGORIES,
    PRACTICE_MODE_LABELS,
    RECENT_ADAPTATION_LIMIT,
    RECENT_WORD_EXCLUSION_LIMIT,
    REVIEW_QUEUE_LIMIT,
    SUPPORTED_LEVELS,
)


class AdaptationService:
    """Chooses gentle, explainable practice adjustments without ML."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.game_session_repository = GameSessionRepository(db_path=db_path)
        self.performance_summary_repository = PerformanceSummaryRepository(db_path=db_path)
        self.review_queue_repository = ReviewQueueRepository(db_path=db_path)
        self.word_progress_repository = WordProgressRepository(db_path=db_path)
        self.word_repository = WordRepository(db_path=db_path)

    def build_recommendation(
        self,
        user: dict[str, Any],
        *,
        language: str | None = None,
        practice_mode: str = "standard",
        selected_categories: Sequence[str] | None = None,
        selected_category: str | None = None,
        difficulty_filter: Sequence[str] | None = None,
        review_policy: str = "prefer_review",
        excluded_word_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """Return the next-round recommendation for a user and session setup."""
        selected_language = str(language or user["target_language"]).lower()
        effective_level = str(user["effective_level"])
        preferred_categories = list(
            user.get("preferred_categories") or list(DEFAULT_PREFERRED_CATEGORIES)
        )
        available_categories = [
            row["category"] for row in self.word_repository.get_categories(selected_language)
        ] or preferred_categories
        filtered_categories = [
            str(category).strip().lower()
            for category in (selected_categories or [])
            if str(category).strip()
        ]
        if selected_category and selected_category.lower() not in filtered_categories:
            filtered_categories = [selected_category.lower(), *filtered_categories]
        if filtered_categories:
            available_categories = [
                category for category in available_categories if category in filtered_categories
            ] or filtered_categories

        category_scores = {category: 0.0 for category in available_categories}
        for index, category in enumerate(preferred_categories):
            if category in category_scores:
                category_scores[category] += max(1.0 - (index * 0.1), 0.4)

        summaries = self.performance_summary_repository.get_for_user(
            user_id=int(user["id"]),
            language=selected_language,
        )
        weak_categories: list[str] = []
        strong_categories: list[str] = []

        for summary in summaries:
            category = str(summary["category"])
            if category not in category_scores:
                continue

            total_games = int(summary["total_games"] or 0)
            wins = int(summary["wins"] or 0)
            losses = int(summary["losses"] or 0)
            mastery_score = float(summary["mastery_score"] or 0.0)

            if total_games >= 2:
                if mastery_score < 55 or losses > wins:
                    weak_categories.append(category)
                    category_scores[category] = category_scores.get(category, 0.0) + 2.0
                elif mastery_score > 80 and wins >= losses:
                    strong_categories.append(category)
                    category_scores[category] = category_scores.get(category, 0.0) - 0.75

        recent_sessions = self.game_session_repository.get_recent_sessions(
            user_id=int(user["id"]),
            limit=RECENT_ADAPTATION_LIMIT,
            language=selected_language,
        )
        recent_word_ids = self.game_session_repository.get_recent_word_ids(
            user_id=int(user["id"]),
            limit=RECENT_WORD_EXCLUSION_LIMIT,
            language=selected_language,
        )
        if recent_sessions:
            recent_wins = sum(1 for session in recent_sessions if session["result"] == "won")
            recent_win_rate = recent_wins / len(recent_sessions)
        else:
            recent_win_rate = 0.0

        for session in recent_sessions:
            category = str(session["category"])
            if category not in category_scores:
                continue
            if session["result"] == "lost":
                category_scores[category] = category_scores.get(category, 0.0) + 0.5
            elif session["result"] == "won":
                category_scores[category] = category_scores.get(category, 0.0) - 0.15

        review_candidates = self.review_queue_repository.get_due_items(
            user_id=int(user["id"]),
            language=selected_language,
            limit=REVIEW_QUEUE_LIMIT,
            category=selected_category.lower() if selected_category else None,
        )
        if not review_candidates and review_policy in {"prefer_review", "review_only"}:
            review_candidates = self.review_queue_repository.get_active_items(
                user_id=int(user["id"]),
                language=selected_language,
                limit=REVIEW_QUEUE_LIMIT,
                category=selected_category.lower() if selected_category else None,
            )
        if filtered_categories:
            review_candidates = [
                item for item in review_candidates if str(item["category"]) in filtered_categories
            ]

        if practice_mode == "weak_area":
            for category in weak_categories:
                if category in category_scores:
                    category_scores[category] = category_scores.get(category, 0.0) + 1.5

        if practice_mode == "review" or review_policy in {"prefer_review", "review_only"}:
            for index, item in enumerate(review_candidates):
                category = str(item["category"])
                if category not in category_scores:
                    continue
                category_scores[category] = category_scores.get(category, 0.0) + max(
                    2.5 - (index * 0.15),
                    1.0,
                )

        if selected_category:
            normalized_category = selected_category.lower()
            if normalized_category in category_scores:
                category_scores[normalized_category] = (
                    category_scores.get(normalized_category, 0.0) + 3.0
                )

        strong_word_ids = self.word_progress_repository.get_status_word_ids(
            user_id=int(user["id"]),
            language=selected_language,
            statuses=["strong"],
        )
        seen_word_ids = self.word_progress_repository.get_seen_word_ids(
            user_id=int(user["id"]),
            language=selected_language,
        )

        level_shift = 0
        if len(recent_sessions) >= 3 and recent_win_rate >= 0.8:
            level_shift = 1
        elif len(recent_sessions) >= 3 and recent_win_rate <= 0.34:
            level_shift = -1

        if practice_mode == "review":
            level_shift = min(level_shift, 0)
        if review_policy == "review_only":
            level_shift = min(level_shift, 0)
        if difficulty_filter:
            adapted_level = effective_level
        else:
            adapted_level = self._shift_level(effective_level, level_shift)

        category_order = sorted(
            available_categories,
            key=lambda category: (
                -category_scores.get(category, 0.0),
                (
                    preferred_categories.index(category)
                    if category in preferred_categories
                    else len(preferred_categories)
                ),
                category,
            ),
        )
        if selected_category:
            category_order = [
                selected_category.lower(),
                *[category for category in category_order if category != selected_category.lower()],
            ]

        excluded_ids = list(
            dict.fromkeys(
                [
                    *recent_word_ids,
                    *(int(word_id) for word_id in (excluded_word_ids or [])),
                ]
            )
        )

        return {
            "language": selected_language,
            "practice_mode": practice_mode,
            "base_level": effective_level,
            "adapted_level": adapted_level,
            "difficulty_filter": list(difficulty_filter or []),
            "category_order": category_order,
            "recent_word_ids": excluded_ids,
            "recent_win_rate": recent_win_rate,
            "weak_categories": weak_categories,
            "strong_categories": strong_categories,
            "candidate_word_ids": [int(item["word_id"]) for item in review_candidates],
            "deprioritized_word_ids": strong_word_ids,
            "seen_word_ids": seen_word_ids,
            "reason": self._build_reason(
                practice_mode=practice_mode,
                review_policy=review_policy,
                adapted_level=adapted_level,
                effective_level=effective_level,
                category_order=category_order,
                weak_categories=weak_categories,
                recent_word_ids=excluded_ids,
                candidate_word_ids=[int(item["word_id"]) for item in review_candidates],
                selected_category=selected_category,
            ),
        }

    def _shift_level(self, level: str, shift: int) -> str:
        """Shift a level up or down within the supported range."""
        level_order = list(SUPPORTED_LEVELS)
        if level not in level_order:
            return level_order[0]
        current_index = level_order.index(level)
        next_index = min(max(current_index + shift, 0), len(level_order) - 1)
        return level_order[next_index]

    def _build_reason(
        self,
        practice_mode: str,
        review_policy: str,
        adapted_level: str,
        effective_level: str,
        category_order: list[str],
        weak_categories: list[str],
        recent_word_ids: list[int],
        candidate_word_ids: list[int],
        selected_category: str | None,
    ) -> str:
        """Return a compact explanation for the next-round recommendation."""
        mode_label = PRACTICE_MODE_LABELS.get(practice_mode, practice_mode.title())
        focus_category = (
            selected_category.title()
            if selected_category
            else (category_order[0].title() if category_order else "Mixed practice")
        )

        reason_parts = [f"{mode_label}: focus on {focus_category}."]
        if practice_mode == "weak_area" and weak_categories:
            reason_parts.append(
                "Weak categories are being prioritized based on recent performance."
            )
        if review_policy in {"prefer_review", "review_only"} and candidate_word_ids:
            reason_parts.append("Review words are being brought back into practice first.")
        if adapted_level != effective_level:
            reason_parts.append(
                f"Difficulty adjusted from {effective_level.title()} "
                f"to {adapted_level.title()} based on recent results."
            )
        if recent_word_ids:
            reason_parts.append("Recently played words are being avoided when possible.")
        return " ".join(reason_parts)
