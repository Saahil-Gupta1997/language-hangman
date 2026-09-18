"""Profile and preference management UI."""

from __future__ import annotations

import streamlit as st

from src.services.auth_service import AuthService
from src.services.word_service import WordService
from src.ui.design import render_callout, render_kpi_grid, render_page_header
from src.utils.constants import DEFAULT_PREFERRED_CATEGORIES, SUPPORTED_LEVELS
from src.utils.language_display import format_language_label


def render_profile_page(
    current_user: dict[str, object],
    auth_service: AuthService,
    word_service: WordService,
) -> None:
    """Render the preferences page for the logged-in user."""
    available_languages = word_service.get_available_languages()
    available_categories = word_service.get_categories(str(current_user["target_language"]))
    category_options = available_categories or list(DEFAULT_PREFERRED_CATEGORIES)

    render_page_header(
        "Preferences",
        "Tune the defaults used by the practice builder and daily goal tracking.",
        eyebrow="Profile setup",
        meta=[
            f"Effective level: {str(current_user['effective_level']).title()}",
            f"Language: {format_language_label(str(current_user['target_language']))}",
        ],
    )

    form_column, summary_column = st.columns([1.25, 0.75])
    with form_column:
        with st.form("preferences_form"):
            selected_language = st.selectbox(
                "Language",
                options=available_languages,
                index=available_languages.index(str(current_user["target_language"])),
                format_func=format_language_label,
            )
            selected_level = st.selectbox(
                "Self-declared level",
                options=SUPPORTED_LEVELS,
                index=SUPPORTED_LEVELS.index(str(current_user["self_declared_level"])),
            )
            selected_categories = st.multiselect(
                "Preferred categories",
                options=category_options,
                default=list(current_user["preferred_categories"]),
            )
            goal_left, goal_right = st.columns(2)
            with goal_left:
                daily_goal_words = st.number_input(
                    "Daily word goal",
                    min_value=1,
                    max_value=50,
                    value=int(current_user.get("daily_goal_words", 5)),
                )
            with goal_right:
                daily_goal_sessions = st.number_input(
                    "Daily session goal",
                    min_value=1,
                    max_value=10,
                    value=int(current_user.get("daily_goal_sessions", 1)),
                )
            submitted = st.form_submit_button(
                "Save Preferences",
                type="primary",
                use_container_width=True,
            )

    if submitted:
        if not selected_categories:
            st.error("Choose at least one preferred category.")
            return

        updated_user = auth_service.update_preferences(
            user_id=int(current_user["id"]),
            target_language=selected_language,
            level=selected_level,
            preferred_categories=selected_categories,
        )
        updated_user = auth_service.update_daily_goals(
            user_id=int(current_user["id"]),
            daily_goal_words=int(daily_goal_words),
            daily_goal_sessions=int(daily_goal_sessions),
        )
        st.session_state.current_user = updated_user
        st.success("Preferences saved.")

    display_user = st.session_state.current_user or current_user
    with summary_column:
        render_kpi_grid(
            [
                {
                    "label": "Calibrated level",
                    "value": str(display_user["calibrated_level"]).title()
                    if display_user["calibrated_level"]
                    else "Not available yet",
                },
                {
                    "label": "Gameplay level",
                    "value": str(display_user["effective_level"]).title(),
                },
                {
                    "label": "Daily goal",
                    "value": (
                        f"{display_user.get('daily_goal_words', 5)} words / "
                        f"{display_user.get('daily_goal_sessions', 1)} session"
                    ),
                },
            ]
        )
        render_callout(
            "Local-first storage",
            "Authentication and progress are stored locally for this app.",
            tone="neutral",
        )
