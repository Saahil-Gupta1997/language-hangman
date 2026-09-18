"""Progress reporting UI."""

from __future__ import annotations

import streamlit as st

from src.services.report_service import ReportService
from src.services.word_service import WordService
from src.ui.design import render_callout, render_kpi_grid, render_page_header, render_section_intro
from src.utils.constants import REPORT_TIMEFRAME_OPTIONS, SITUATION_LABELS
from src.utils.language_display import format_language_label


def render_report_page(
    current_user: dict[str, object],
    report_service: ReportService,
    word_service: WordService,
) -> None:
    """Render the user's progress summary."""
    render_page_header(
        "Progress Report",
        "Review learning momentum, weak spots, and the next guided practice setup.",
        eyebrow="Insights",
    )

    available_languages = ["All Languages", *word_service.get_available_languages()]
    filter_left, filter_right = st.columns(2)
    with filter_left:
        selected_language = st.selectbox(
            "Language filter",
            options=available_languages,
            index=_safe_index(
                available_languages,
                str(current_user["target_language"]),
            ),
            format_func=lambda language: (
                str(language)
                if language == "All Languages"
                else format_language_label(str(language))
            ),
        )
    with filter_right:
        timeframe_label = st.selectbox(
            "Timeframe",
            options=list(REPORT_TIMEFRAME_OPTIONS.keys()),
            index=0,
        )
    report_context = report_service.build_summary_report(
        user_id=int(current_user["id"]),
        language=None if selected_language == "All Languages" else selected_language,
        timeframe_days=REPORT_TIMEFRAME_OPTIONS[timeframe_label],
    )
    overview = report_context["overview"]
    streaks = report_context["streaks"]

    render_kpi_grid(
        [
            {"label": "Total games", "value": overview["total_games"]},
            {"label": "Wins", "value": overview["wins"]},
            {"label": "Losses", "value": overview["losses"]},
            {
                "label": "Current streak",
                "value": streaks["current_streak"],
                "caption": f"Best streak: {streaks['best_streak']}",
            },
        ]
    )

    daily_goal = report_context["daily_goal"]
    render_section_intro("Today")
    render_kpi_grid(
        [
            {
                "label": "Daily goal",
                "value": f"{daily_goal['word_goal']} words",
                "caption": f"{daily_goal['session_goal']} session",
            },
            {"label": "Progress", "value": f"{daily_goal['progress_percent']}%"},
            {
                "label": "Practiced today",
                "value": "Yes" if daily_goal["today_practiced"] else "Not yet",
            },
        ]
    )
    render_callout("Daily status", daily_goal["status_message"], tone="neutral")

    render_section_intro("Level Snapshot")
    render_kpi_grid(
        [
            {
                "label": "Self-declared",
                "value": str(current_user["self_declared_level"]).title(),
            },
            {
                "label": "Calibrated",
                "value": str(current_user["calibrated_level"]).title()
                if current_user["calibrated_level"]
                else "Not available yet",
            },
            {
                "label": "Gameplay level",
                "value": str(current_user["effective_level"]).title(),
            },
        ]
    )

    session_history = report_context["session_history_summary"]
    render_section_intro("Learning Health")
    render_kpi_grid(
        [
            {"label": "Learning sessions", "value": session_history["total_sessions"]},
            {"label": "Total rounds", "value": session_history["total_rounds"]},
            {
                "label": "Session accuracy",
                "value": f"{session_history['avg_accuracy']}%",
            },
            {"label": "Study days logged", "value": streaks["days_played"]},
            {
                "label": "Average mastery",
                "value": f"{report_context['word_status']['avg_mastery_score']}%",
            },
            {
                "label": "Words mastered",
                "value": report_context["word_status"]["mastered_words"],
            },
            {
                "label": "Words still weak",
                "value": report_context["word_status"]["weak_words"],
            },
            {
                "label": "Review due",
                "value": report_context["review_queue_summary"]["due_count"],
            },
        ]
    )

    insights = report_context["insights"]
    render_section_intro("Category Insights")
    insight_column_1, insight_column_2 = st.columns(2)
    with insight_column_1:
        st.write(
            "Strongest category: "
            + (
                str(insights["strongest_category"]).title()
                if insights["strongest_category"]
                else "Not enough data yet"
            )
        )
        st.write(
            "Recent improvement area: "
            + (
                str(insights["recent_improvement_area"]).title()
                if insights["recent_improvement_area"]
                else "Not enough data yet"
            )
        )
    with insight_column_2:
        st.write(
            "Weakest category: "
            + (
                str(insights["weakest_category"]).title()
                if insights["weakest_category"]
                else "Not enough data yet"
            )
        )

    render_section_intro("Situation Insights")
    situation_left, situation_middle, situation_right = st.columns(3)
    with situation_left:
        strongest = insights.get("strongest_situation")
        strongest_label = (
            SITUATION_LABELS.get(str(strongest), str(strongest))
            if strongest
            else "Not enough data yet"
        )
        st.write(
            "Strongest situation: "
            + strongest_label
        )
    with situation_middle:
        weakest = insights.get("weakest_situation")
        weakest_label = (
            SITUATION_LABELS.get(str(weakest), str(weakest))
            if weakest
            else "Not enough data yet"
        )
        st.write(
            "Weakest situation: "
            + weakest_label
        )
    with situation_right:
        recommended = insights.get("recommended_next_situation")
        recommended_label = (
            SITUATION_LABELS.get(str(recommended), str(recommended))
            if recommended
            else "Restaurant"
        )
        st.write(
            "Recommended next situation: "
            + recommended_label
        )
        st.write(
            "Next milestone category: "
            + (
                str(insights["next_milestone_category"]).title()
                if insights["next_milestone_category"]
                else "Not enough data yet"
            )
        )

    if report_context["milestones"]:
        render_section_intro("Milestones")
        for milestone in report_context["milestones"]:
            st.write(f"{milestone['title']}: {milestone['detail']}")

    render_section_intro("Progress Badges")
    for badge in report_context["badges"]:
        status = "[Unlocked]" if badge["unlocked"] else "[Locked]"
        st.write(f"{status} {badge['title']}: {badge['detail']}")

    if report_context["guided_study_plan"]:
        render_section_intro(
            "Guided Study Plan",
            "Use the strongest recommendation as the next practice setup.",
        )
        active_session_exists = st.session_state.get("active_learning_session") is not None
        for index, plan in enumerate(report_context["guided_study_plan"], start=1):
            render_callout(plan["title"], f"{plan['summary']} {plan['reason']}", tone="neutral")
            if st.button(
                "Open This Plan In Practice Builder",
                key=f"report_plan_{index}",
                type="primary" if index == 1 else "secondary",
                use_container_width=True,
                disabled=active_session_exists,
            ):
                st.session_state.builder_override = plan["builder_settings"]
                st.session_state.navigation = "Play"
                st.session_state.navigation_control = "Play"
                st.session_state.navigation_control_last_sync = "Play"
                st.rerun()
        if active_session_exists:
            st.caption("Finish or resume your active session before launching another guided plan.")

    if not report_context["summaries"]:
        render_callout(
            "No saved rounds yet",
            "Play a session to build category, situation, and mastery insights for this filter.",
            tone="neutral",
        )
        if st.button("Start a Practice Session", type="primary", use_container_width=True):
            st.session_state.navigation = "Play"
            st.session_state.navigation_control = "Play"
            st.session_state.navigation_control_last_sync = "Play"
            st.rerun()
        return

    render_section_intro("Category-wise Performance")
    st.dataframe(report_context["summaries"], use_container_width=True, hide_index=True)

    summary_left, summary_right = st.columns(2)
    with summary_left:
        render_section_intro("Practice Mode Summary")
        if report_context["practice_mode_summary"]:
            st.dataframe(
                report_context["practice_mode_summary"],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.write("No practice-mode summary is available yet.")
    with summary_right:
        render_section_intro("Word Status")
        st.write(
            f"New: {report_context['word_status']['new_words']} | "
            f"Learning: {report_context['word_status']['learning_words']} | "
            f"Familiar: {report_context['word_status']['familiar_words']} | "
            f"Strong: {report_context['word_status']['strong_words']}"
        )
        st.write(f"Strong categories: {report_context['category_status']['strong_categories']}")
        st.write(f"Weak categories: {report_context['category_status']['weak_categories']}")

    if report_context["daily_activity"]:
        render_section_intro("Recent Daily Activity")
        st.dataframe(report_context["daily_activity"], use_container_width=True, hide_index=True)

    if report_context["last_seven_days"]:
        render_section_intro("Last 7 Days")
        st.dataframe(report_context["last_seven_days"], use_container_width=True, hide_index=True)

    if report_context["category_progress"]:
        render_section_intro("Category Milestones")
        st.dataframe(
            report_context["category_progress"],
            use_container_width=True,
            hide_index=True,
        )

    if report_context["category_trends"]:
        st.subheader("Category Trend Snapshot")
        st.dataframe(report_context["category_trends"], use_container_width=True, hide_index=True)

    if report_context["situation_progress"]:
        st.subheader("Situation Progress")
        st.dataframe(
            report_context["situation_progress"],
            use_container_width=True,
            hide_index=True,
        )

    strengths_column, weaknesses_column = st.columns(2)
    with strengths_column:
        st.subheader("Strengths")
        if report_context["strengths"]:
            for item in report_context["strengths"]:
                st.write(
                    f"{str(item['category']).title()} "
                    f"(mastery {item['mastery_score']}, accuracy {item['accuracy']})"
                )
        else:
            st.write("Not enough data yet.")
    with weaknesses_column:
        st.subheader("Weaknesses")
        if report_context["weaknesses"]:
            for item in report_context["weaknesses"]:
                st.write(
                    f"{str(item['category']).title()} "
                    f"(mastery {item['mastery_score']}, accuracy {item['accuracy']})"
                )
        else:
            st.write("Not enough data yet.")

    st.subheader("Recent Learning Sessions")
    if report_context["recent_learning_sessions"]:
        st.dataframe(
            report_context["recent_learning_sessions"],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.write("No learning sessions saved yet.")

    st.subheader("Recent Words Practiced")
    if report_context["recent_words_practiced"]:
        st.dataframe(
            report_context["recent_words_practiced"],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.write("No recent words to show yet.")

    st.subheader("Recent Rounds")
    if report_context["recent_sessions"]:
        st.dataframe(
            report_context["recent_sessions"],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.write("No recent rounds to show yet.")

    st.subheader("Review Queue")
    st.write("Review practice helps you revisit words that were difficult or recently missed.")
    if report_context["review_queue_summary"]["due_items"]:
        st.dataframe(
            report_context["review_queue_summary"]["due_items"],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(
            "No review words are due right now. Try Standard Practice or "
            "Weak Area Practice to keep learning."
        )


def _safe_index(options: list[object], value: object) -> int:
    """Return a safe index for Streamlit select widgets."""
    try:
        return options.index(value)
    except ValueError:
        return 0
