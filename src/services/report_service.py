"""Reporting helpers for learner progress summaries."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.db.repository import (
    GameSessionRepository,
    LearningSessionRepository,
    PerformanceSummaryRepository,
    ReviewQueueRepository,
    UserRepository,
    WordProgressRepository,
    WordRepository,
)
from src.utils.constants import (
    DAILY_ACTIVITY_LIMIT,
    DEFAULT_DAILY_GOAL_SESSIONS,
    DEFAULT_DAILY_GOAL_WORDS,
    GUIDED_STUDY_PLAN_LIMIT,
    LEVEL_TO_DIFFICULTIES,
    PRACTICE_MODE_LABELS,
    PROGRESS_BADGE_DEFINITIONS,
    RECENT_LEARNING_SESSION_LIMIT,
    RECENT_REPORT_LIMIT,
    RECENT_WORD_REPORT_LIMIT,
    REVIEW_QUEUE_LIMIT,
    SITUATIONS,
)
from src.utils.helpers import deserialize_string_list, shift_utc_iso


class ReportService:
    """Calculates and exposes learner progress, history, and study guidance."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.game_session_repository = GameSessionRepository(db_path=db_path)
        self.learning_session_repository = LearningSessionRepository(db_path=db_path)
        self.performance_summary_repository = PerformanceSummaryRepository(db_path=db_path)
        self.review_queue_repository = ReviewQueueRepository(db_path=db_path)
        self.user_repository = UserRepository(db_path=db_path)
        self.word_progress_repository = WordProgressRepository(db_path=db_path)
        self.word_repository = WordRepository(db_path=db_path)

    def refresh_user_performance(self, user_id: int) -> None:
        """Rebuild all stored performance summary rows for a user."""
        aggregate_rows = self.game_session_repository.get_category_aggregates(user_id=user_id)
        summary_rows: list[tuple[object, ...]] = []

        for row in aggregate_rows:
            total_games = int(row["total_games"] or 0)
            wins = int(row["wins"] or 0)
            losses = int(row["losses"] or 0)
            avg_attempts = round(float(row["avg_attempts"] or 0.0), 2)
            total_correct_letters = int(row["total_correct_letters"] or 0)
            total_wrong_letters = int(row["total_wrong_letters"] or 0)
            total_guesses = total_correct_letters + total_wrong_letters
            accuracy = round(
                (total_correct_letters / total_guesses) * 100 if total_guesses else 0.0,
                2,
            )
            win_rate = (wins / total_games) * 100 if total_games else 0.0
            mastery_score = round((win_rate * 0.7) + (accuracy * 0.3), 2)

            summary_rows.append(
                (
                    user_id,
                    row["language"],
                    row["category"],
                    total_games,
                    wins,
                    losses,
                    accuracy,
                    avg_attempts,
                    mastery_score,
                    row["last_played_at"],
                )
            )

        self.performance_summary_repository.replace_user_summaries(
            user_id=user_id,
            summary_rows=summary_rows,
        )

    def build_summary_report(
        self,
        user_id: int,
        language: str | None = None,
        timeframe_days: int | None = None,
    ) -> dict[str, Any]:
        """Return top-level metrics, history, milestones, and study guidance."""
        played_after = shift_utc_iso(days=-timeframe_days) if timeframe_days else None
        user_profile = self.user_repository.get_by_id(user_id)
        plan_language = self._resolve_plan_language(user_profile=user_profile, language=language)
        effective_level = self._resolve_effective_level(user_profile)
        preferred_categories = deserialize_string_list(
            user_profile["preferred_categories"] if user_profile else None,
            default=[],
        )

        aggregate_rows = self.game_session_repository.get_category_aggregates(
            user_id=user_id,
            language=language,
            played_after=played_after,
        )
        summaries = [self._build_summary_row(row) for row in aggregate_rows]

        overview_row = self.game_session_repository.get_overview(
            user_id=user_id,
            language=language,
            played_after=played_after,
        )
        overview = {
            "total_games": int((overview_row["total_games"] if overview_row else 0) or 0),
            "wins": int((overview_row["wins"] if overview_row else 0) or 0),
            "losses": int((overview_row["losses"] if overview_row else 0) or 0),
        }
        total_words_practiced = self.game_session_repository.get_distinct_word_count(
            user_id=user_id,
            language=language,
            played_after=played_after,
        )

        sorted_summaries = sorted(
            summaries,
            key=lambda summary: (
                float(summary["mastery_score"]),
                float(summary["accuracy"]),
                -int(summary["losses"]),
            ),
        )
        strengths = list(reversed(sorted_summaries[-2:]))
        weaknesses = sorted_summaries[:2]

        recent_round_rows = self.game_session_repository.get_recent_sessions(
            user_id=user_id,
            language=language,
            played_after=played_after,
            limit=RECENT_WORD_REPORT_LIMIT,
        )
        recent_sessions = [
            {
                "played_at": row["played_at"],
                "word": row["word"],
                "category": row["category"],
                "situation": row["situation"],
                "difficulty": row["difficulty"],
                "practice_mode": row["practice_mode"],
                "result": row["result"],
                "attempts_used": row["attempts_used"],
                "letters_wrong": row["letters_wrong"],
                "translation": row["translation"],
            }
            for row in recent_round_rows[:RECENT_REPORT_LIMIT]
        ]
        recent_words_practiced = self._build_recent_words_practiced(recent_round_rows)
        category_trends = self._build_category_trends(recent_round_rows)
        daily_activity = self._build_daily_activity(
            self.game_session_repository.get_daily_activity(
                user_id=user_id,
                language=language,
                played_after=played_after,
                limit=DAILY_ACTIVITY_LIMIT,
            )
        )
        today_start = self._today_start_iso()
        completed_sessions_today = (
            self.learning_session_repository.get_completed_session_count_since(
                user_id=user_id,
                language=language,
                started_after=today_start,
            )
        )
        daily_goal = self._build_daily_goal(
            user_profile=user_profile,
            daily_activity=daily_activity,
            completed_sessions_today=completed_sessions_today,
        )
        streaks = self._build_streaks(
            self.game_session_repository.get_play_dates(
                user_id=user_id,
                language=language,
                played_after=played_after,
            )
        )
        last_seven_days = self._build_last_seven_days(daily_activity)

        recent_learning_sessions = [
            {
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "language": row["language"],
                "practice_mode": row["practice_mode"],
                "planned_rounds": row["planned_rounds"],
                "completed_rounds": row["completed_rounds"],
                "wins": row["wins"],
                "losses": row["losses"],
                "accuracy": row["accuracy"],
                "status": row["status"],
                "situation": row["situation"],
                "selected_category": row["selected_category"],
                "selected_categories": deserialize_string_list(row["selected_categories"]),
                "difficulty_filter": deserialize_string_list(row["difficulty_filter"]),
                "review_policy": row["review_policy"],
                "recommendation": row["recommendation"],
            }
            for row in self.learning_session_repository.get_recent_sessions(
                user_id=user_id,
                language=language,
                started_after=played_after,
                limit=RECENT_LEARNING_SESSION_LIMIT,
            )
        ]
        session_history_row = self.learning_session_repository.get_session_history_summary(
            user_id=user_id,
            language=language,
            started_after=played_after,
        )
        session_history_summary = {
            "total_sessions": int(
                (session_history_row["total_sessions"] if session_history_row else 0) or 0
            ),
            "total_rounds": int(
                (session_history_row["total_rounds"] if session_history_row else 0) or 0
            ),
            "avg_accuracy": round(
                float((session_history_row["avg_accuracy"] if session_history_row else 0) or 0.0),
                2,
            ),
            "last_session_at": (
                session_history_row["last_session_at"] if session_history_row else None
            ),
        }

        practice_mode_summary = [
            {
                "practice_mode": row["practice_mode"],
                "total_games": int(row["total_games"] or 0),
                "wins": int(row["wins"] or 0),
                "losses": int(row["losses"] or 0),
                "win_rate": round(
                    ((int(row["wins"] or 0) / int(row["total_games"] or 1)) * 100),
                    2,
                ),
            }
            for row in self.game_session_repository.get_practice_mode_aggregates(
                user_id=user_id,
                language=language,
                played_after=played_after,
            )
        ]

        review_counts_row = self.review_queue_repository.get_summary_counts(
            user_id=user_id,
            language=language,
        )
        due_review_items = (
            self.review_queue_repository.get_due_items(
                user_id=user_id,
                language=plan_language,
                limit=REVIEW_QUEUE_LIMIT,
            )
            if plan_language
            else []
        )
        word_lookup = {
            int(row["id"]): dict(row)
            for row in self.word_repository.get_words_by_ids(
                [int(item["word_id"]) for item in due_review_items]
            )
        }
        review_queue_summary = {
            "active_count": int(
                (review_counts_row["active_count"] if review_counts_row else 0) or 0
            ),
            "due_count": int((review_counts_row["due_count"] if review_counts_row else 0) or 0),
            "due_items": [
                {
                    "word": word_lookup.get(int(item["word_id"]), {}).get(
                        "word", f"Word {item['word_id']}"
                    ),
                    "category": item["category"],
                    "priority_score": item["priority_score"],
                    "review_due_at": item["review_due_at"],
                    "review_count": item["review_count"],
                    "last_result": item["last_result"],
                    "why_reviewed": self._describe_review_item(item),
                }
                for item in due_review_items[:RECENT_REPORT_LIMIT]
            ],
        }

        progress_counts_row = self.word_progress_repository.get_summary_counts(
            user_id=user_id,
            language=language,
        )
        word_status = {
            "new_words": int((progress_counts_row["new_count"] if progress_counts_row else 0) or 0),
            "learning_words": int(
                (progress_counts_row["learning_count"] if progress_counts_row else 0) or 0
            ),
            "familiar_words": int(
                (progress_counts_row["familiar_count"] if progress_counts_row else 0) or 0
            ),
            "strong_words": int(
                (progress_counts_row["strong_count"] if progress_counts_row else 0) or 0
            ),
            "avg_mastery_score": round(
                float(
                    (progress_counts_row["avg_mastery_score"] if progress_counts_row else 0) or 0.0
                ),
                2,
            ),
        }
        word_status["mastered_words"] = int(
            (progress_counts_row["mastered_count"] if progress_counts_row else 0) or 0
        ) or word_status["strong_words"]
        word_status["weak_words"] = int(
            (progress_counts_row["weak_mastery_count"] if progress_counts_row else 0) or 0
        ) or word_status["learning_words"]
        word_status["total_words_practiced"] = max(
            total_words_practiced,
            word_status["new_words"]
            + word_status["learning_words"]
            + word_status["familiar_words"]
            + word_status["strong_words"],
        )

        category_progress = [
            self._build_category_progress_row(row)
            for row in self.word_progress_repository.get_category_progress_summary(
                user_id=user_id,
                language=language,
            )
        ]
        insights = self._build_category_insights(
            strengths=strengths,
            weaknesses=weaknesses,
            category_trends=category_trends,
            category_progress=category_progress,
        )
        situation_progress = self._build_situation_progress(
            self.game_session_repository.get_situation_aggregates(
                user_id=user_id,
                language=language,
                played_after=played_after,
            )
        )
        insights.update(self._build_situation_insights(situation_progress))
        category_status = {
            "strong_categories": len(
                [
                    summary
                    for summary in category_progress
                    if float(summary["avg_mastery_score"]) >= 70
                ]
            ),
            "weak_categories": len(
                [
                    summary
                    for summary in category_progress
                    if float(summary["avg_mastery_score"]) < 50
                ]
            ),
        }
        milestones = self._build_milestones(
            overview=overview,
            session_history_summary=session_history_summary,
            word_status=word_status,
            streaks=streaks,
            category_progress=category_progress,
        )
        badges = self._build_badges(
            session_history_summary=session_history_summary,
            word_status=word_status,
            streaks=streaks,
            category_progress=category_progress,
        )
        guided_study_plan = self._build_guided_study_plan(
            language=plan_language,
            effective_level=effective_level,
            preferred_categories=preferred_categories,
            overview=overview,
            review_queue_summary=review_queue_summary,
            insights=insights,
            session_history_summary=session_history_summary,
            word_status=word_status,
        )
        recommendations = [plan["summary"] for plan in guided_study_plan[:GUIDED_STUDY_PLAN_LIMIT]]
        if not recommendations:
            recommendations = ["Start with a short standard session to build fresh momentum."]
        dashboard = self._build_dashboard_summary(
            user_profile=user_profile,
            overview=overview,
            word_status=word_status,
            review_queue_summary=review_queue_summary,
            streaks=streaks,
            daily_goal=daily_goal,
            insights=insights,
        )

        return {
            "dashboard": dashboard,
            "overview": overview,
            "summaries": summaries,
            "recent_sessions": recent_sessions,
            "recent_learning_sessions": recent_learning_sessions,
            "recent_words_practiced": recent_words_practiced,
            "session_history_summary": session_history_summary,
            "practice_mode_summary": practice_mode_summary,
            "review_queue_summary": review_queue_summary,
            "category_trends": category_trends,
            "daily_activity": daily_activity,
            "last_seven_days": last_seven_days,
            "daily_goal": daily_goal,
            "streaks": streaks,
            "milestones": milestones,
            "badges": badges,
            "category_progress": category_progress,
            "situation_progress": situation_progress,
            "word_status": word_status,
            "category_status": category_status,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "insights": insights,
            "recommendations": recommendations,
            "guided_study_plan": guided_study_plan,
        }

    def _build_summary_row(self, row: Any) -> dict[str, Any]:
        """Return a formatted category summary row."""
        total_games = int(row["total_games"] or 0)
        wins = int(row["wins"] or 0)
        losses = int(row["losses"] or 0)
        avg_attempts = round(float(row["avg_attempts"] or 0.0), 2)
        total_correct_letters = int(row["total_correct_letters"] or 0)
        total_wrong_letters = int(row["total_wrong_letters"] or 0)
        total_guesses = total_correct_letters + total_wrong_letters
        accuracy = round(
            (total_correct_letters / total_guesses) * 100 if total_guesses else 0.0,
            2,
        )
        win_rate = (wins / total_games) * 100 if total_games else 0.0
        mastery_score = round((win_rate * 0.7) + (accuracy * 0.3), 2)

        return {
            "language": row["language"],
            "category": row["category"],
            "total_games": total_games,
            "wins": wins,
            "losses": losses,
            "avg_attempts": avg_attempts,
            "accuracy": accuracy,
            "mastery_score": mastery_score,
            "last_played_at": row["last_played_at"],
        }

    def _build_category_progress_row(self, row: Any) -> dict[str, Any]:
        """Return category-level mastery and milestone details."""
        tracked_words = int(row["tracked_words"] or 0)
        strong_words = int(row["strong_words"] or 0)
        avg_mastery_score = round(float(row["avg_mastery_score"] or 0.0), 2)

        if tracked_words >= 3 and avg_mastery_score >= 85 and strong_words >= 2:
            milestone_label = "Category mastered"
        elif tracked_words >= 2 and avg_mastery_score >= 70 and strong_words >= 1:
            milestone_label = "Growing confidence"
        elif tracked_words >= 2 and avg_mastery_score >= 50:
            milestone_label = "Building foundation"
        else:
            milestone_label = "Starting out"

        return {
            "language": row["language"],
            "category": row["category"],
            "tracked_words": tracked_words,
            "avg_mastery_score": avg_mastery_score,
            "learning_words": int(row["learning_words"] or 0),
            "familiar_words": int(row["familiar_words"] or 0),
            "strong_words": strong_words,
            "last_played_at": row["last_played_at"],
            "milestone_label": milestone_label,
        }

    def _build_situation_progress(self, rows: list[Any]) -> list[dict[str, Any]]:
        """Return situation-level performance snapshots for dashboard insights."""
        progress: list[dict[str, Any]] = []
        for row in rows:
            total_games = int(row["total_games"] or 0)
            wins = int(row["wins"] or 0)
            losses = int(row["losses"] or 0)
            total_correct_letters = int(row["total_correct_letters"] or 0)
            total_wrong_letters = int(row["total_wrong_letters"] or 0)
            total_guesses = total_correct_letters + total_wrong_letters
            accuracy = round(
                (total_correct_letters / total_guesses) * 100 if total_guesses else 0.0,
                2,
            )
            win_rate = round((wins / total_games) * 100 if total_games else 0.0, 2)
            progress.append(
                {
                    "language": row["language"],
                    "situation": row["situation"],
                    "total_games": total_games,
                    "wins": wins,
                    "losses": losses,
                    "win_rate": win_rate,
                    "accuracy": accuracy,
                    "avg_attempts": round(float(row["avg_attempts"] or 0.0), 2),
                    "avg_hints_used": round(float(row["avg_hints_used"] or 0.0), 2),
                    "last_played_at": row["last_played_at"],
                }
            )
        return sorted(progress, key=lambda item: (-item["total_games"], item["situation"]))

    def _build_situation_insights(
        self,
        situation_progress: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Return strongest/weakest situation and a next-situation suggestion."""
        eligible = [row for row in situation_progress if int(row["total_games"]) > 0]
        if not eligible:
            return {
                "strongest_situation": None,
                "weakest_situation": None,
                "recommended_next_situation": SITUATIONS[0],
            }

        strongest = sorted(
            eligible,
            key=lambda row: (-float(row["win_rate"]), -float(row["accuracy"]), row["situation"]),
        )[0]
        weakest = sorted(
            eligible,
            key=lambda row: (float(row["win_rate"]), float(row["accuracy"]), row["situation"]),
        )[0]
        played_situations = {str(row["situation"]) for row in eligible}
        unplayed = [situation for situation in SITUATIONS if situation not in played_situations]
        recommended = unplayed[0] if unplayed else str(weakest["situation"])
        return {
            "strongest_situation": strongest["situation"],
            "weakest_situation": weakest["situation"],
            "recommended_next_situation": recommended,
        }

    def _build_recent_words_practiced(
        self,
        recent_round_rows: list[Any],
    ) -> list[dict[str, Any]]:
        """Return a unique recent-word list for the report screen."""
        words: list[dict[str, Any]] = []
        seen_words: set[int] = set()

        for row in recent_round_rows:
            word_id = int(row["word_id"])
            if word_id in seen_words:
                continue
            seen_words.add(word_id)
            words.append(
                {
                    "played_at": row["played_at"],
                    "word": row["word"],
                    "translation": row["translation"],
                    "situation": row["situation"],
                    "category": row["category"],
                    "difficulty": row["difficulty"],
                    "practice_mode": row["practice_mode"],
                    "result": row["result"],
                }
            )

        return words[:RECENT_WORD_REPORT_LIMIT]

    def _build_category_trends(
        self,
        recent_round_rows: list[Any],
    ) -> list[dict[str, Any]]:
        """Build a small trend snapshot from recent rounds."""
        trend_map: dict[str, dict[str, float]] = {}

        for row in recent_round_rows:
            category = str(row["category"])
            trend_map.setdefault(category, {"plays": 0.0, "wins": 0.0})
            trend_map[category]["plays"] += 1
            if row["result"] == "won":
                trend_map[category]["wins"] += 1

        trends: list[dict[str, Any]] = []
        for category, values in trend_map.items():
            plays = int(values["plays"])
            wins = int(values["wins"])
            recent_win_rate = round((wins / plays) * 100 if plays else 0.0, 2)
            if recent_win_rate >= 75:
                trend = "improving"
            elif recent_win_rate <= 40:
                trend = "needs support"
            else:
                trend = "steady"

            trends.append(
                {
                    "category": category,
                    "recent_plays": plays,
                    "recent_win_rate": recent_win_rate,
                    "trend": trend,
                }
            )

        return sorted(trends, key=lambda item: (-item["recent_plays"], item["category"]))

    def _build_daily_activity(self, rows: list[Any]) -> list[dict[str, Any]]:
        """Return a compact daily activity snapshot."""
        activity: list[dict[str, Any]] = []
        for row in rows:
            total_correct_letters = int(row["total_correct_letters"] or 0)
            total_wrong_letters = int(row["total_wrong_letters"] or 0)
            total_guesses = total_correct_letters + total_wrong_letters
            accuracy = round(
                (total_correct_letters / total_guesses) * 100 if total_guesses else 0.0,
                2,
            )
            activity.append(
                {
                    "played_day": row["played_day"],
                    "total_rounds": int(row["total_rounds"] or 0),
                    "wins": int(row["wins"] or 0),
                    "losses": int(row["losses"] or 0),
                    "accuracy": accuracy,
                }
            )
        return activity

    def _build_streaks(self, play_dates: list[str]) -> dict[str, Any]:
        """Return current and best streak counts from distinct play dates."""
        return self.build_streak_summary(play_dates)

    @staticmethod
    def build_streak_summary(
        play_dates: list[str],
        *,
        today: date | None = None,
    ) -> dict[str, Any]:
        """Return current and best streak counts from distinct play dates."""
        parsed_dates = sorted({date.fromisoformat(value) for value in play_dates if value})
        if not parsed_dates:
            return {
                "current_streak": 0,
                "best_streak": 0,
                "days_played": 0,
                "last_played_day": None,
                "today_practiced": False,
            }

        best_streak = 1
        rolling_streak = 1
        for previous_day, current_day in zip(parsed_dates, parsed_dates[1:]):
            if current_day == previous_day + timedelta(days=1):
                rolling_streak += 1
            else:
                rolling_streak = 1
            best_streak = max(best_streak, rolling_streak)

        last_played_day = parsed_dates[-1]
        current_streak = 0
        resolved_today = today or datetime.now(timezone.utc).date()
        today_practiced = last_played_day == resolved_today
        if (resolved_today - last_played_day).days <= 1:
            current_streak = 1
            current_day = last_played_day
            for previous_day in reversed(parsed_dates[:-1]):
                if current_day - previous_day == timedelta(days=1):
                    current_streak += 1
                    current_day = previous_day
                else:
                    break

        return {
            "current_streak": current_streak,
            "best_streak": best_streak,
            "days_played": len(parsed_dates),
            "last_played_day": last_played_day.isoformat(),
            "today_practiced": today_practiced,
        }

    def _build_daily_goal(
        self,
        *,
        user_profile: Any,
        daily_activity: list[dict[str, Any]],
        completed_sessions_today: int,
    ) -> dict[str, Any]:
        """Return today's progress against the user's simple daily goal."""
        word_goal = int(
            (user_profile["daily_goal_words"] if user_profile else DEFAULT_DAILY_GOAL_WORDS)
            or DEFAULT_DAILY_GOAL_WORDS
        )
        session_goal = int(
            (user_profile["daily_goal_sessions"] if user_profile else DEFAULT_DAILY_GOAL_SESSIONS)
            or DEFAULT_DAILY_GOAL_SESSIONS
        )
        today_key = datetime.now(timezone.utc).date().isoformat()
        today_activity = next(
            (activity for activity in daily_activity if activity["played_day"] == today_key),
            None,
        )
        words_today = int((today_activity or {}).get("total_rounds", 0))
        word_progress = words_today / max(word_goal, 1)
        session_progress = completed_sessions_today / max(session_goal, 1)
        progress_percent = round(min(max(word_progress, session_progress), 1.0) * 100, 2)

        return {
            "word_goal": word_goal,
            "session_goal": session_goal,
            "words_today": words_today,
            "sessions_today": completed_sessions_today,
            "progress_percent": progress_percent,
            "goal_met": progress_percent >= 100,
            "today_practiced": words_today > 0 or completed_sessions_today > 0,
            "status_message": (
                "Daily goal complete. Nice consistency."
                if progress_percent >= 100
                else "A short practice session will move today's goal forward."
            ),
        }

    def _build_last_seven_days(
        self,
        daily_activity: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Return a stable last-seven-days activity strip for dashboards."""
        activity_by_day = {str(activity["played_day"]): activity for activity in daily_activity}
        today = datetime.now(timezone.utc).date()
        days: list[dict[str, Any]] = []
        for days_ago in range(6, -1, -1):
            current_day = today - timedelta(days=days_ago)
            key = current_day.isoformat()
            activity = activity_by_day.get(key, {})
            rounds = int(activity.get("total_rounds", 0))
            days.append(
                {
                    "day": key,
                    "rounds": rounds,
                    "wins": int(activity.get("wins", 0)),
                    "practiced": rounds > 0,
                }
            )
        return days

    def _build_dashboard_summary(
        self,
        *,
        user_profile: Any,
        overview: dict[str, int],
        word_status: dict[str, Any],
        review_queue_summary: dict[str, Any],
        streaks: dict[str, Any],
        daily_goal: dict[str, Any],
        insights: dict[str, Any],
    ) -> dict[str, Any]:
        """Return beta dashboard data with friendly empty-state messages."""
        target_language = user_profile["target_language"] if user_profile else None
        effective_level = self._resolve_effective_level(user_profile)
        suggested_mode_key = self._suggest_practice_mode(
            overview=overview,
            review_queue_summary=review_queue_summary,
            insights=insights,
            daily_goal=daily_goal,
        )
        return {
            "current_language": target_language,
            "current_level": effective_level,
            "assessment_completed": (
                bool(user_profile["assessment_completed"]) if user_profile else False
            ),
            "total_words_practiced": word_status["total_words_practiced"],
            "current_streak": streaks["current_streak"],
            "best_streak": streaks["best_streak"],
            "review_items_due": review_queue_summary["due_count"],
            "strongest_situation": insights.get("strongest_situation"),
            "weakest_situation": insights.get("weakest_situation"),
            "recommended_next_situation": insights.get("recommended_next_situation"),
            "words_mastered": word_status["mastered_words"],
            "words_needing_practice": word_status["weak_words"],
            "suggested_practice_mode": PRACTICE_MODE_LABELS.get(
                suggested_mode_key, "Standard Practice"
            ),
            "suggested_practice_mode_key": suggested_mode_key,
            "empty_states": {
                "sessions": (
                    "No sessions yet. Start with a 3-round Standard Practice session."
                    if overview["total_games"] == 0
                    else ""
                ),
                "reviews": (
                    "No review words yet. They appear after missed or difficult words."
                    if review_queue_summary["active_count"] == 0
                    else ""
                ),
                "streak": (
                    "No streak yet. Practice today to start one."
                    if streaks["current_streak"] == 0
                    else ""
                ),
                "assessment": (
                    "Complete the short assessment to calibrate your level."
                    if user_profile and not bool(user_profile["assessment_completed"])
                    else ""
                ),
            },
        }

    def _suggest_practice_mode(
        self,
        *,
        overview: dict[str, int],
        review_queue_summary: dict[str, Any],
        insights: dict[str, Any],
        daily_goal: dict[str, Any],
    ) -> str:
        """Return a simple, explainable next practice mode."""
        if review_queue_summary["due_count"] > 0:
            return "review"
        if overview["total_games"] == 0 or not daily_goal["today_practiced"]:
            return "standard"
        if insights["needs_more_practice"]:
            return "weak_area"
        return "standard"

    def _today_start_iso(self) -> str:
        """Return the start of today in UTC for simple daily-goal queries."""
        return f"{datetime.now(timezone.utc).date().isoformat()}T00:00:00+00:00"

    def _build_category_insights(
        self,
        strengths: list[dict[str, Any]],
        weaknesses: list[dict[str, Any]],
        category_trends: list[dict[str, Any]],
        category_progress: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Return lightweight category insight labels for the report screen."""
        recent_improvement_area = next(
            (trend["category"] for trend in category_trends if trend["trend"] == "improving"),
            None,
        )
        next_milestone_category = next(
            (
                row["category"]
                for row in sorted(
                    category_progress,
                    key=lambda item: (-float(item["avg_mastery_score"]), item["category"]),
                )
                if row["milestone_label"] == "Building foundation"
            ),
            None,
        )

        return {
            "strongest_category": strengths[0]["category"] if strengths else None,
            "weakest_category": weaknesses[0]["category"] if weaknesses else None,
            "needs_more_practice": weaknesses[0]["category"] if weaknesses else None,
            "recent_improvement_area": recent_improvement_area,
            "next_milestone_category": next_milestone_category,
        }

    def _describe_review_item(self, item: Any) -> str:
        """Return a learner-friendly reason for one review queue item."""
        if item["last_result"] == "lost":
            return "Recently missed"
        if float(item["last_accuracy"] or 0) < 0.75:
            return "Needed extra guesses"
        if float(item["priority_score"] or 0) >= 0.7:
            return "High review priority"
        return "Scheduled spaced review"

    def _build_milestones(
        self,
        overview: dict[str, int],
        session_history_summary: dict[str, Any],
        word_status: dict[str, Any],
        streaks: dict[str, Any],
        category_progress: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        """Return compact milestone cards for the dashboard and reports."""
        milestones: list[dict[str, str]] = []

        if streaks["current_streak"] >= 2:
            milestones.append(
                {
                    "title": "Active streak",
                    "detail": f"{streaks['current_streak']}-day streak is still alive.",
                }
            )
        elif streaks["best_streak"] >= 3:
            milestones.append(
                {
                    "title": "Best streak",
                    "detail": (
                        "You have already reached a "
                        f"{streaks['best_streak']}-day study streak."
                    ),
                }
            )

        if session_history_summary["total_sessions"] >= 5:
            milestones.append(
                {
                    "title": "Session momentum",
                    "detail": (
                        f"{session_history_summary['total_sessions']} completed "
                        "learning sessions recorded."
                    ),
                }
            )

        if word_status["strong_words"] >= 3:
            milestones.append(
                {
                    "title": "Word mastery",
                    "detail": f"{word_status['strong_words']} words have reached the strong stage.",
                }
            )

        for row in category_progress:
            if row["milestone_label"] == "Category mastered":
                milestones.append(
                    {
                        "title": f"{str(row['category']).title()} milestone",
                        "detail": "This category is showing confident, repeatable mastery.",
                    }
                )
                break

        if not milestones and overview["total_games"] > 0:
            milestones.append(
                {
                    "title": "Practice history",
                    "detail": f"{overview['total_games']} saved rounds are available for review.",
                }
            )

        return milestones[:4]

    def _build_badges(
        self,
        *,
        session_history_summary: dict[str, Any],
        word_status: dict[str, Any],
        streaks: dict[str, Any],
        category_progress: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Return stable progress badge states for simple UI display."""
        unlocked_by_id = {
            "first_session": session_history_summary["total_sessions"] >= 1,
            "three_day_streak": streaks["best_streak"] >= 3,
            "first_strong_word": word_status["strong_words"] >= 1,
            "category_milestone": any(
                row["milestone_label"] != "Starting out" for row in category_progress
            ),
        }
        return [
            {
                "id": badge_id,
                "title": title,
                "detail": detail,
                "unlocked": bool(unlocked_by_id.get(badge_id, False)),
            }
            for badge_id, title, detail in PROGRESS_BADGE_DEFINITIONS
        ]

    def _build_guided_study_plan(
        self,
        *,
        language: str | None,
        effective_level: str,
        preferred_categories: list[str],
        overview: dict[str, int],
        review_queue_summary: dict[str, Any],
        insights: dict[str, Any],
        session_history_summary: dict[str, Any],
        word_status: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Return a short, explainable study plan that the UI can launch."""
        selected_language = language or "english"
        default_categories = preferred_categories or [insights["needs_more_practice"] or "noun"]
        difficulties = list(self._get_difficulties_for_level(effective_level))
        recommended_situation = str(insights.get("recommended_next_situation") or SITUATIONS[0])
        plans: list[dict[str, Any]] = []

        if review_queue_summary["due_count"] > 0:
            review_focus = (
                review_queue_summary["due_items"][0]["category"]
                if review_queue_summary["due_items"]
                else insights["needs_more_practice"]
            )
            review_categories = [review_focus] if review_focus else list(default_categories)
            rounds = 3 if review_queue_summary["due_count"] <= 3 else 5
            plans.append(
                self._build_plan_item(
                    title="Clear Due Reviews",
                    summary=(
                        "Do a review-only session to revisit "
                        f"{review_queue_summary['due_count']} due word(s)."
                    ),
                    reason="Missed or shaky words should come back before they fade.",
                    language=selected_language,
                    situation=recommended_situation,
                    practice_mode="review",
                    categories=review_categories,
                    difficulties=difficulties,
                    rounds=rounds,
                    review_policy="review_only",
                )
            )

        if insights["needs_more_practice"]:
            weak_category = str(insights["needs_more_practice"])
            rounds = 5
            plans.append(
                self._build_plan_item(
                    title=f"Repair {weak_category.title()} Accuracy",
                    summary=(
                        f"Try a custom {rounds}-round session focused on "
                        f"{weak_category.title()}."
                    ),
                    reason=(
                        "This category has the weakest recent results and should "
                        "be reinforced gently."
                    ),
                    language=selected_language,
                    situation=recommended_situation,
                    practice_mode="weak_area",
                    categories=[weak_category],
                    difficulties=difficulties,
                    rounds=rounds,
                    review_policy="prefer_review",
                )
            )

        if (
            overview["total_games"] >= 5
            and overview["wins"] >= overview["losses"]
            and review_queue_summary["due_count"] == 0
        ):
            stretch_category = insights["strongest_category"] or default_categories[0]
            stretch_difficulties = list(self._get_stretch_difficulties(effective_level))
            plans.append(
                self._build_plan_item(
                    title="Stretch to Harder Words",
                    summary=(
                        "You may be ready to move up difficulty in "
                        f"{str(stretch_category).title()}."
                    ),
                    reason=(
                        "Strong recent results and a light review queue make this "
                        "a safe stretch step."
                    ),
                    language=selected_language,
                    situation=recommended_situation,
                    practice_mode="category",
                    categories=[str(stretch_category)],
                    difficulties=stretch_difficulties,
                    rounds=5,
                    review_policy="new_only",
                )
            )

        if not plans:
            plans.append(
                self._build_plan_item(
                    title="Build Fresh Momentum",
                    summary="Continue adaptive standard practice with a short session.",
                    reason=(
                        "A small mixed session is the safest next step when "
                        "history is still limited."
                    ),
                    language=selected_language,
                    situation=recommended_situation,
                    practice_mode="standard",
                    categories=list(default_categories),
                    difficulties=difficulties,
                    rounds=3,
                    review_policy="prefer_review",
                )
            )

        if (
            word_status["learning_words"] > word_status["strong_words"] + 2
            and len(plans) < GUIDED_STUDY_PLAN_LIMIT
        ):
            focus_category = insights["needs_more_practice"] or default_categories[0]
            plans.append(
                self._build_plan_item(
                    title="Stabilize Learning Words",
                    summary=f"Focus on one category for 5 rounds in {str(focus_category).title()}.",
                    reason=(
                        "You have more fragile words than strong ones, so tighter "
                        "category repetition should help."
                    ),
                    language=selected_language,
                    situation=recommended_situation,
                    practice_mode="category",
                    categories=[str(focus_category)],
                    difficulties=difficulties,
                    rounds=5,
                    review_policy="prefer_review",
                )
            )

        return plans[:GUIDED_STUDY_PLAN_LIMIT]

    def _build_plan_item(
        self,
        *,
        title: str,
        summary: str,
        reason: str,
        language: str,
        situation: str,
        practice_mode: str,
        categories: list[str],
        difficulties: list[str],
        rounds: int,
        review_policy: str,
    ) -> dict[str, Any]:
        """Return a launchable guided-study plan item."""
        return {
            "title": title,
            "summary": summary,
            "reason": reason,
            "builder_settings": {
                "language": language,
                "situation": situation,
                "practice_mode": practice_mode,
                "categories": categories,
                "difficulties": difficulties,
                "rounds": rounds,
                "review_policy": review_policy,
                "game_mode": "easy",
                "show_hint_immediately": True,
            },
        }

    def _resolve_plan_language(
        self,
        user_profile: Any,
        language: str | None,
    ) -> str | None:
        """Return the language used for guided plans and due-review lookups."""
        if language:
            return str(language).lower()
        if user_profile and user_profile["target_language"]:
            return str(user_profile["target_language"]).lower()
        return None

    def _resolve_effective_level(self, user_profile: Any) -> str:
        """Return calibrated level when present, otherwise the self-declared level."""
        if user_profile and user_profile["calibrated_level"]:
            return str(user_profile["calibrated_level"]).lower()
        if user_profile and user_profile["level"]:
            return str(user_profile["level"]).lower()
        return "beginner"

    def _get_difficulties_for_level(self, level: str) -> tuple[str, ...]:
        """Return the default difficulty band for a learner level."""
        return LEVEL_TO_DIFFICULTIES.get(level, LEVEL_TO_DIFFICULTIES["beginner"])

    def _get_stretch_difficulties(self, level: str) -> tuple[str, ...]:
        """Return a slightly harder difficulty band for stretch recommendations."""
        if level == "beginner":
            return LEVEL_TO_DIFFICULTIES["intermediate"]
        if level == "intermediate":
            return LEVEL_TO_DIFFICULTIES["advanced"]
        return LEVEL_TO_DIFFICULTIES["advanced"]
