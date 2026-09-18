"""Multi-round Hangman gameplay UI."""

from __future__ import annotations

import streamlit as st

from src.models.game_round import GameRound
from src.models.learning_session import LearningSession
from src.services.auth_service import AuthService
from src.services.game_service import GameService
from src.services.hint_service import (
    HINT_LABELS,
    build_available_hints,
    get_revealed_hints,
    reveal_manual_hint,
    sync_auto_revealed_hints,
)
from src.services.report_service import ReportService
from src.services.word_service import WordService
from src.ui.design import render_callout, render_kpi_grid, render_page_header, render_section_intro
from src.ui.media import play_optional_sound, render_background_music
from src.utils.constants import (
    DIFFICULTY_ORDER,
    GAME_MODE_LABELS,
    GAME_MODE_SETTINGS,
    PRACTICE_MODE_LABELS,
    REVIEW_POLICY_LABELS,
    SESSION_LENGTH_OPTIONS,
    SITUATION_LABELS,
    SITUATIONS,
)
from src.utils.helpers import build_difficulty_range
from src.utils.language_display import format_language_label
from src.utils.visuals import get_hangman_stage


def render_game_page(
    current_user: dict[str, object],
    auth_service: AuthService,
    game_service: GameService,
    report_service: ReportService,
    word_service: WordService,
) -> None:
    """Render the multi-round Hangman learning experience."""
    _finalize_completed_round_if_needed(
        current_user=current_user,
        game_service=game_service,
        report_service=report_service,
    )
    _render_feedback()

    active_session = st.session_state.get("active_learning_session")
    active_game = st.session_state.get("active_game")
    _render_page_intro(current_user=current_user, active_session=active_session)

    if active_session is None:
        _render_start_session_controls(
            current_user=current_user,
            auth_service=auth_service,
            game_service=game_service,
            report_service=report_service,
            word_service=word_service,
        )
        return

    _render_session_progress(active_session=active_session, active_game=active_game)

    if active_game is None:
        _render_session_summary(
            current_user=current_user,
            game_service=game_service,
            session_summary=st.session_state.get("session_summary"),
        )
        return

    if active_game.is_complete and active_game.saved:
        _render_finished_round(
            current_user=current_user,
            round_state=active_game,
            learning_session=active_session,
            game_service=game_service,
            report_service=report_service,
        )
        return

    if not active_game.is_complete:
        render_background_music()
    _render_round_status(round_state=active_game)

    with st.form("guess_form", clear_on_submit=True):
        guess = st.text_input("Guess one letter")
        submitted = st.form_submit_button("Submit Guess", use_container_width=True)

    if submitted:
        outcome = game_service.record_guess(round_state=active_game, guess=guess)
        st.session_state.game_feedback = outcome["message"]
        st.session_state.game_feedback_type = outcome["status"]
        st.session_state.pending_sound = outcome.get("sound")
        st.rerun()


def _render_page_intro(
    current_user: dict[str, object],
    active_session: LearningSession | None,
) -> None:
    """Render beginner-friendly page context for setup or active play."""
    if active_session is None:
        render_page_header(
            "Practice Builder",
            "Choose a situation and difficulty for your session.",
            eyebrow="Practice setup",
            meta=[f"Effective level: {str(current_user['effective_level']).title()}"],
        )
    else:
        practice_label = PRACTICE_MODE_LABELS.get(
            active_session.practice_mode,
            active_session.practice_mode.title(),
        )
        game_label = GAME_MODE_LABELS.get(
            active_session.game_mode,
            active_session.game_mode.title(),
        )
        situation_label = SITUATION_LABELS.get(
            str(active_session.situation or ""),
            str(active_session.situation or "Situation").title(),
        )
        st.caption(
            f"{situation_label} | {practice_label} | {game_label} | "
            f"{str(current_user['effective_level']).title()}"
        )
        return

    if current_user.get("calibrated_level"):
        st.caption(
            "Calibrated from self-declared "
            f"{str(current_user['self_declared_level']).title()}."
        )


def _finalize_completed_round_if_needed(
    current_user: dict[str, object],
    game_service: GameService,
    report_service: ReportService,
) -> None:
    """Persist a finished round and prepare either the next round or session summary."""
    active_session = st.session_state.get("active_learning_session")
    active_game = st.session_state.get("active_game")
    if active_session is None or active_game is None:
        return
    if not active_game.is_complete or active_game.saved:
        return

    outcome = game_service.finalize_round(
        user=current_user,
        round_state=active_game,
        learning_session=active_session,
    )
    report_service.refresh_user_performance(user_id=int(current_user["id"]))

    st.session_state.active_learning_session = outcome["learning_session"]
    st.session_state.pending_next_round = outcome["next_round"]
    st.session_state.last_round_review = outcome["learning_review"]
    st.session_state.session_summary = outcome["session_summary"]
    st.session_state.game_feedback = outcome["message"]
    st.session_state.game_feedback_type = outcome["status"]
    st.rerun()


def _render_start_session_controls(
    current_user: dict[str, object],
    auth_service: AuthService,
    game_service: GameService,
    report_service: ReportService,
    word_service: WordService,
) -> None:
    """Render the controls used to begin a new learning session."""
    report_context = report_service.build_summary_report(
        user_id=int(current_user["id"]),
        language=str(current_user["target_language"]),
    )
    builder_defaults = game_service.get_default_builder_settings(current_user)
    builder_override = st.session_state.get("builder_override")
    if builder_override:
        builder_defaults = game_service.normalize_builder_settings(
            current_user,
            {**builder_defaults, **builder_override},
        )
        render_callout(
            "Guided plan loaded",
            "A guided study plan has been loaded into the builder. Review it or start right away.",
            tone="neutral",
        )
    available_languages = word_service.get_available_languages()

    setup_column, summary_column = st.columns([1.25, 0.75])
    start_session = False
    with setup_column:
        selected_language = st.selectbox(
            "Language",
            options=available_languages,
            index=_safe_index(available_languages, str(builder_defaults["language"])),
            format_func=format_language_label,
        )
        available_situations = word_service.get_available_situations(selected_language)
        if not available_situations:
            st.warning(
                "No situational words are available for this language yet. "
                "Reload or expand the word bank before starting a session."
            )
            return
        selected_situation = st.selectbox(
            "Where are you going today?",
            options=available_situations or list(SITUATIONS),
            index=_safe_index(
                available_situations,
                str(builder_defaults.get("situation")),
            ),
            format_func=lambda situation: SITUATION_LABELS.get(situation, situation.title()),
        )
        available_categories = word_service.get_categories(selected_language)
        default_categories = [
            category
            for category in builder_defaults["categories"]
            if category in available_categories
        ] or available_categories
        difficulty_defaults = list(builder_defaults["difficulties"]) or list(DIFFICULTY_ORDER)
        min_difficulty, max_difficulty = difficulty_defaults[0], difficulty_defaults[-1]

        selected_game_mode = st.selectbox(
            "Game mode",
            options=list(GAME_MODE_LABELS.keys()),
            index=_safe_index(
                list(GAME_MODE_LABELS.keys()),
                str(builder_defaults.get("game_mode", "easy")),
            ),
            format_func=lambda mode: GAME_MODE_LABELS[mode],
        )
        st.caption(GAME_MODE_SETTINGS[selected_game_mode]["description"])
        start_session = st.button("Start Session", type="primary", use_container_width=True)

        selected_categories = list(default_categories)
        selected_mode = str(builder_defaults["practice_mode"])
        selected_minimum_difficulty = min_difficulty
        selected_maximum_difficulty = max_difficulty
        planned_rounds = int(builder_defaults["rounds"])
        selected_review_policy = str(builder_defaults["review_policy"])

        with st.expander("Advanced settings", expanded=bool(builder_override)):
            st.caption(
                "Optional tuning for focused review, category practice, session length, "
                "and difficulty range. Most learners can leave these as-is."
            )
            selected_mode = st.selectbox(
                "Practice mode",
                options=list(PRACTICE_MODE_LABELS.keys()),
                index=_safe_index(
                    list(PRACTICE_MODE_LABELS.keys()),
                    selected_mode,
                ),
                format_func=lambda mode: PRACTICE_MODE_LABELS[mode],
            )
            if selected_mode == "review":
                st.info(
                    "Revisit words that were difficult or recently missed."
                )
            if selected_mode == "weak_words":
                st.info(
                    "Review Weak Words focuses on low-mastery words for the situation you selected."
                )

            selected_categories = st.multiselect(
                "Categories",
                options=available_categories,
                default=default_categories,
                format_func=lambda category: str(category).title(),
            )

            rounds_column, review_column = st.columns(2)
            with rounds_column:
                planned_rounds = st.selectbox(
                    "Number of rounds",
                    options=list(SESSION_LENGTH_OPTIONS),
                    index=_safe_index(list(SESSION_LENGTH_OPTIONS), planned_rounds),
                )
            with review_column:
                selected_review_policy = st.selectbox(
                    "Word selection policy",
                    options=list(REVIEW_POLICY_LABELS.keys()),
                    index=_safe_index(
                        list(REVIEW_POLICY_LABELS.keys()),
                        selected_review_policy,
                    ),
                    format_func=lambda policy: REVIEW_POLICY_LABELS[policy],
                )

            difficulty_left, difficulty_right = st.columns(2)
            with difficulty_left:
                selected_minimum_difficulty = st.selectbox(
                    "Minimum difficulty",
                    options=list(DIFFICULTY_ORDER),
                    index=_safe_index(list(DIFFICULTY_ORDER), selected_minimum_difficulty),
                )
            with difficulty_right:
                selected_maximum_difficulty = st.selectbox(
                    "Maximum difficulty",
                    options=list(DIFFICULTY_ORDER),
                    index=_safe_index(list(DIFFICULTY_ORDER), selected_maximum_difficulty),
                )

            if selected_review_policy in {"prefer_review", "review_only"}:
                due_count = report_context["review_queue_summary"]["due_count"]
                if due_count:
                    st.caption(f"{due_count} review word(s) are currently due.")
                elif selected_review_policy == "review_only" or selected_mode == "review":
                    st.info(
                        "No review words are due yet. Try Standard Practice or Weak Area Practice."
                    )
                else:
                    st.caption("No due review words yet. The app can fall back when possible.")

    with summary_column:
        render_section_intro(
            "Session Snapshot",
            "Review the current setup before starting.",
        )
        render_kpi_grid(
            [
                {
                    "label": "Situation",
                    "value": SITUATION_LABELS.get(selected_situation, selected_situation.title()),
                },
                {
                    "label": "Game mode",
                    "value": GAME_MODE_LABELS[selected_game_mode],
                },
                {
                    "label": "Rounds",
                    "value": planned_rounds,
                    "caption": PRACTICE_MODE_LABELS.get(selected_mode, selected_mode.title()),
                },
                {
                    "label": "Review due",
                    "value": report_context["review_queue_summary"]["due_count"],
                    "caption": REVIEW_POLICY_LABELS.get(
                        selected_review_policy,
                        selected_review_policy,
                    ),
                },
            ]
        )
        if report_context["recommendations"]:
            render_callout(
                "Suggested next step",
                " ".join(report_context["recommendations"][:2]),
                tone="neutral",
            )

    if start_session:
        builder_settings = {
            "language": selected_language,
            "situation": selected_situation,
            "categories": selected_categories,
            "practice_mode": selected_mode,
            "difficulties": build_difficulty_range(
                selected_minimum_difficulty,
                selected_maximum_difficulty,
            ),
            "rounds": int(planned_rounds),
            "review_policy": selected_review_policy,
            "game_mode": selected_game_mode,
        }

        try:
            outcome = game_service.start_custom_learning_session(
                user=current_user,
                builder_settings=builder_settings,
            )
        except ValueError as error:
            st.error(str(error))
            return

        updated_user = auth_service.save_last_builder_settings(
            user_id=int(current_user["id"]),
            builder_settings=outcome["settings"],
        )
        st.session_state.current_user = updated_user
        st.session_state.builder_override = None
        # A new mode-backed session replaces any stale active round safely.
        st.session_state.active_learning_session = outcome["learning_session"]
        st.session_state.active_game = outcome["first_round"]
        st.session_state.pending_next_round = None
        st.session_state.session_summary = None
        st.session_state.last_round_review = None
        st.session_state.pending_sound = None
        if outcome["warnings"]:
            st.session_state.game_feedback = " ".join(outcome["warnings"])
            st.session_state.game_feedback_type = "warning"
        else:
            st.session_state.game_feedback = "Session started."
            st.session_state.game_feedback_type = "success"
        st.rerun()


def _render_session_progress(
    active_session: LearningSession,
    active_game: GameRound | None,
) -> None:
    """Render the current multi-round session progress."""
    round_number = active_session.completed_rounds
    if active_game is not None and not active_game.is_complete:
        round_number = active_session.current_round_number

    progress = (
        active_session.completed_rounds / active_session.planned_rounds
        if active_session.planned_rounds
        else 0.0
    )
    st.progress(progress)

    st.caption(
        f"Round {round_number}/{active_session.planned_rounds} | "
        f"Wins: {active_session.wins} | Losses: {active_session.losses} | "
        f"Accuracy: {active_session.session_accuracy}%"
    )


def _render_round_status(round_state: GameRound) -> None:
    """Keep the puzzle, lives, and hints together during play."""
    st.caption(
        f"{round_state.remaining_attempts} lives remaining | "
        f"{round_state.attempts_used} guesses | {round_state.category.title()}"
    )
    st.markdown(f"### {round_state.masked_word}")
    drawing, hints = st.columns([1, 2])
    with drawing:
        st.code(
            get_hangman_stage(
                wrong_guesses=round_state.letters_wrong,
                max_attempts=round_state.max_attempts,
            ),
            language="text",
        )
    with hints:
        sync_auto_revealed_hints(round_state)
        _render_hint_panel(round_state)
    st.caption(f"Guessed letters: {round_state.guessed_letters_display}")


def _render_hint_panel(round_state: GameRound) -> None:
    """Render progressive and clicked hints without showing blank fallbacks."""
    available_hints = build_available_hints(round_state)
    revealed_hints = get_revealed_hints(round_state)

    with st.container(border=True):
        st.markdown("#### Hints")
        st.caption(
            "Easy unlocks hints after wrong guesses 1, 3, and 5. "
            "Hard reveals all hints at 2 lives or fewer."
        )
        if revealed_hints:
            for hint_key, hint_value in revealed_hints.items():
                st.write(f"{HINT_LABELS.get(hint_key, hint_key.title())}: {hint_value}")
        else:
            st.write("No hints revealed yet.")

        if round_state.hint_mode not in {"easy", "hard"}:
            button_columns = st.columns(2)
            for index, hint_key in enumerate(("synonym", "association")):
                if hint_key not in available_hints or hint_key in round_state.revealed_hint_keys:
                    continue
                with button_columns[index]:
                    if st.button(
                        f"Reveal {HINT_LABELS[hint_key]}",
                        key=f"reveal_{hint_key}_{round_state.word_id}_{round_state.attempts_used}",
                        use_container_width=True,
                    ):
                        if reveal_manual_hint(round_state, hint_key):
                            st.session_state.pending_sound = "hint"
                        st.rerun()


def _render_finished_round(
    current_user: dict[str, object],
    round_state: GameRound,
    learning_session: LearningSession,
    game_service: GameService,
    report_service: ReportService,
) -> None:
    """Render the end-of-round review and next actions."""
    learning_review = st.session_state.get(
        "last_round_review"
    ) or game_service.build_learning_review(round_state=round_state)
    report_context = report_service.build_summary_report(
        user_id=int(current_user["id"]),
        language=round_state.language,
    )

    if round_state.result == "won":
        st.success(_build_round_result_message(round_state))
    else:
        st.error(_build_round_result_message(round_state))

    st.write(
        f"Correct guesses: {round_state.letters_correct} | "
        f"Wrong guesses: {round_state.letters_wrong}"
    )
    _render_round_review_card(learning_review)
    _render_badges(report_context["badges"])

    left_column, middle_column, right_column = st.columns(3)
    with left_column:
        next_round = st.session_state.get("pending_next_round")
        if next_round is not None:
            if st.button(
                f"Continue to Round {learning_session.completed_rounds + 1}",
                use_container_width=True,
            ):
                st.session_state.active_game = next_round
                st.session_state.pending_next_round = None
                st.session_state.game_feedback = ""
                st.session_state.game_feedback_type = "info"
                st.rerun()
        elif st.button("Start New Session", use_container_width=True):
            _reset_session_flow()
            st.rerun()
    with middle_column:
        if st.button("Return to Reports", use_container_width=True):
            st.session_state.navigation = "Reports"
            st.session_state.navigation_control = "Reports"
            st.session_state.navigation_control_last_sync = "Reports"
            st.rerun()
    with right_column:
        if learning_session.is_complete and st.button(
            "View Session Summary", use_container_width=True
        ):
            st.session_state.active_game = None
            st.rerun()

    if learning_session.is_complete and st.session_state.get("session_summary"):
        _render_session_summary(
            current_user=current_user,
            game_service=game_service,
            session_summary=st.session_state["session_summary"],
        )


def _render_round_review_card(learning_review: dict[str, object]) -> None:
    """Render a learner-friendly post-round card with the useful study details."""
    with st.container(border=True):
        st.subheader("Learning Card")
        result_label = str(learning_review["result"]).title()
        review_status = (
            "Added to review queue"
            if learning_review["marked_for_review"]
            else "No urgent review needed"
        )
        if learning_review["result"] == "lost":
            st.error(f"Correct answer: {learning_review['word']}")
            st.caption("Missed words become useful review material for later practice.")
        else:
            st.success(f"You found: {learning_review['word']}")

        st.markdown(f"**Target word:** {learning_review['word']}")
        st.markdown(
            f"**Meaning:** {learning_review.get('meaning') or learning_review['translation']}"
        )
        if learning_review.get("situation"):
            situation = str(learning_review["situation"])
            st.caption(f"Situation: {SITUATION_LABELS.get(situation, situation.title())}")

        st.markdown("**Example sentence**")
        st.write(str(learning_review["example_sentence"]))
        st.markdown("**Sentence translation**")
        st.write(str(learning_review.get("sentence_translation") or learning_review["translation"]))

        detail_left, detail_right = st.columns(2)
        with detail_left:
            st.markdown(
                "**Pronunciation:** "
                f"{learning_review.get('pronunciation_text') or learning_review['word']}"
            )
            if learning_review.get("synonym"):
                st.markdown(f"**Synonym:** {learning_review['synonym']}")
        with detail_right:
            st.markdown(f"**Result:** {result_label}")
            st.markdown(f"**Review status:** {review_status}")

        st.markdown(
            f"**Usage note:** {learning_review.get('usage_note') or 'Use it in context.'}"
        )
        if learning_review.get("association"):
            st.markdown(f"**Association:** {learning_review['association']}")

        st.write(
            f"Category: {str(learning_review['category']).title()} | "
            f"Difficulty: {str(learning_review['difficulty']).title()} | "
            f"Attempts used: {learning_review['attempts_used']}"
        )
        wrong_letters = ", ".join(learning_review["wrong_letters"]) or "None"
        st.write(f"Wrong letters guessed: {wrong_letters}")
        if learning_review.get("mastery_status"):
            mastery_label = str(learning_review["mastery_status"]).replace("_", " ").title()
            st.write(f"Mastery status: {mastery_label}")
        elif learning_review["familiarity_status"]:
            st.write(f"Word mastery state: {str(learning_review['familiarity_status']).title()}")
        if learning_review["mastery_score"] is not None:
            st.write(f"Mastery score: {learning_review['mastery_score']} / 100")
        if learning_review["next_review_in_days"] is not None:
            st.caption(
                "Next review target: about "
                f"{learning_review['next_review_in_days']} day(s) from now."
            )
        elif learning_review["review_reason"]:
            st.caption(str(learning_review["review_reason"]))
        if learning_review["selection_reason"]:
            st.caption(str(learning_review["selection_reason"]))


def _render_badges(badges: list[dict[str, object]]) -> None:
    """Render unlocked progress badges after a round."""
    unlocked_badges = [badge for badge in badges if badge["unlocked"]]
    if not unlocked_badges:
        return

    st.subheader("Progress Badges")
    st.write(" | ".join(str(badge["title"]) for badge in unlocked_badges))


def _build_round_result_message(round_state: GameRound) -> str:
    """Return stronger round-completion feedback."""
    if round_state.result == "won":
        if round_state.remaining_attempts >= 3:
            return f"Clean win. You solved '{round_state.word}' with room to spare."
        return f"Nice recovery. You solved '{round_state.word}' under pressure."
    return (
        f"Good data for review. The word was '{round_state.word}', "
        "and it will help shape future practice."
    )


def _render_session_summary(
    current_user: dict[str, object],
    game_service: GameService,
    session_summary: dict[str, object] | None,
) -> None:
    """Render the end-of-session summary and recommendation actions."""
    if not session_summary:
        st.info("No session summary is available yet.")
        return

    st.subheader("Session Summary")
    left_column, middle_column, right_column, fourth_column = st.columns(4)
    with left_column:
        st.metric("Rounds played", session_summary["rounds_played"])
    with middle_column:
        st.metric("Wins", session_summary["wins"])
    with right_column:
        st.metric("Losses", session_summary["losses"])
    with fourth_column:
        st.metric("Accuracy", f"{session_summary['session_accuracy']}%")

    categories = (
        ", ".join(str(category).title() for category in session_summary["categories_practiced"])
        or "Mixed"
    )
    words = ", ".join(session_summary["words_practiced"]) or "None recorded"

    st.write(f"Language practiced: {format_language_label(str(session_summary['language']))}")
    if session_summary.get("situation"):
        situation = str(session_summary["situation"])
        st.write(f"Situation practiced: {SITUATION_LABELS.get(situation, situation.title())}")
    st.write(f"Categories practiced: {categories}")
    st.write(f"Words learned or reviewed: {words}")
    st.write(
        "Mastered this session: "
        + (", ".join(session_summary.get("words_mastered", [])) or "None yet")
    )
    st.write(
        "Still learning: "
        + (", ".join(session_summary.get("words_still_learning", [])) or "None recorded")
    )
    st.write(
        "Weak words: " + (", ".join(session_summary.get("weak_words", [])) or "None recorded")
    )
    st.write(session_summary["encouragement"])
    st.info(session_summary["recommendation"])

    left_column, middle_column, right_column = st.columns(3)
    with left_column:
        if st.button("Start Recommended Session", use_container_width=True):
            builder_settings = {
                "language": session_summary["language"],
                "situation": session_summary.get("situation") or SITUATIONS[0],
                "practice_mode": str(session_summary["recommended_mode"]),
                "categories": (
                    [session_summary["recommended_category"]]
                    if session_summary["recommended_category"]
                    else list(current_user["preferred_categories"])
                ),
                "difficulties": list(
                    game_service.word_service.get_difficulties_for_level(
                        str(current_user["effective_level"])
                    )
                ),
                "rounds": int(session_summary["recommended_length"]),
                "review_policy": (
                    "review_only"
                    if session_summary["recommended_mode"] in {"review", "weak_words"}
                    else "prefer_review"
                ),
                "game_mode": str(
                    current_user.get("last_builder_settings", {}).get("game_mode", "easy")
                ),
                "show_hint_immediately": True,
            }
            try:
                outcome = game_service.start_custom_learning_session(
                    user=current_user,
                    builder_settings=builder_settings,
                )
            except ValueError as error:
                st.error(
                    "That recommended session is not available right now. "
                    f"{error}"
                )
                return
            st.session_state.active_learning_session = outcome["learning_session"]
            st.session_state.active_game = outcome["first_round"]
            st.session_state.builder_override = None
            st.session_state.pending_next_round = None
            st.session_state.session_summary = None
            st.session_state.last_round_review = None
            st.session_state.pending_sound = None
            st.session_state.game_feedback = ""
            st.session_state.game_feedback_type = "info"
            st.rerun()
    with middle_column:
        if st.button("Choose Another Session", use_container_width=True):
            _reset_session_flow()
            st.rerun()
    with right_column:
        if st.button("Go To Reports", use_container_width=True):
            _reset_session_flow()
            st.session_state.navigation = "Reports"
            st.session_state.navigation_control = "Reports"
            st.session_state.navigation_control_last_sync = "Reports"
            st.rerun()


def _render_feedback() -> None:
    """Render the latest gameplay feedback message."""
    pending_sound = st.session_state.get("pending_sound")
    if pending_sound:
        play_optional_sound(str(pending_sound))
        st.session_state.pending_sound = None

    feedback = st.session_state.get("game_feedback")
    if not feedback:
        return

    feedback_type = st.session_state.get("game_feedback_type", "info")
    feedback_renderer = {
        "success": st.success,
        "warning": st.warning,
        "error": st.error,
        "info": st.info,
    }.get(feedback_type, st.info)
    feedback_renderer(feedback)


def _reset_session_flow() -> None:
    """Clear the active session-related state."""
    st.session_state.builder_override = None
    st.session_state.active_learning_session = None
    st.session_state.active_game = None
    st.session_state.pending_next_round = None
    st.session_state.session_summary = None
    st.session_state.last_round_review = None
    st.session_state.pending_sound = None
    st.session_state.game_feedback = ""
    st.session_state.game_feedback_type = "info"


def _safe_index(options: list[object], value: object) -> int:
    """Return a safe index for Streamlit select widgets."""
    try:
        return options.index(value)
    except ValueError:
        return 0
