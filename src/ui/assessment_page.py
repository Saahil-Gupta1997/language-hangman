"""Assessment UI for first-time learner calibration."""

from __future__ import annotations

import streamlit as st

from src.models.game_round import GameRound
from src.services.assessment_service import AssessmentService
from src.services.auth_service import AuthService
from src.services.game_service import GameService
from src.utils.visuals import get_hangman_stage


def render_assessment_page(
    current_user: dict[str, object],
    assessment_service: AssessmentService,
    game_service: GameService,
    auth_service: AuthService,
) -> None:
    """Render the mandatory first-time assessment flow."""
    st.header("Initial Skill Check")
    st.write(
        "Complete three short Hangman rounds with increasing difficulty so the app "
        "can calibrate your starting level."
    )
    with st.expander("How Assessment Scoring Works", expanded=False):
        st.write("You will see one easier word, one medium word, and one harder word.")
        st.write(
            "Clean, accurate wins push your calibrated level up more than "
            "slow or shaky wins."
        )
        st.write(
            "The calibrated level becomes your main gameplay level, while your "
            "self-declared level stays saved as a fallback."
        )

    assessment_state = st.session_state.get("assessment_state")
    if assessment_state is None:
        _render_assessment_intro(current_user=current_user, assessment_service=assessment_service)
        return

    if assessment_state.get("completed"):
        _render_assessment_completion(
            assessment_state=assessment_state,
            auth_service=auth_service,
            current_user=current_user,
        )
        return

    current_round = assessment_service.get_current_round(assessment_state)
    round_number = int(assessment_state["current_index"]) + 1
    st.caption(f"Assessment round {round_number} of {len(assessment_state['rounds'])}")
    _render_feedback()
    _render_round_status(current_round)

    if current_round.is_complete:
        _render_finished_round(
            current_round=current_round,
            assessment_service=assessment_service,
            assessment_state=assessment_state,
        )
        return

    with st.form("assessment_guess_form", clear_on_submit=True):
        guess = st.text_input("Guess one letter")
        submitted = st.form_submit_button("Submit Guess", use_container_width=True)

    if submitted:
        outcome = game_service.record_guess(round_state=current_round, guess=guess)
        st.session_state.assessment_feedback = outcome["message"]
        st.session_state.assessment_feedback_type = outcome["status"]
        st.rerun()


def _render_assessment_intro(
    current_user: dict[str, object],
    assessment_service: AssessmentService,
) -> None:
    """Render the assessment start state."""
    st.info(
        "The assessment uses one beginner, one intermediate, and one advanced word. "
        "Your self-declared level starts at "
        f"{str(current_user['self_declared_level']).title()}, and we refine from there."
    )
    if st.button("Start Assessment", use_container_width=True):
        st.session_state.assessment_state = assessment_service.create_assessment_state(
            user=current_user
        )
        st.session_state.assessment_feedback = ""
        st.session_state.assessment_feedback_type = "info"
        st.rerun()


def _render_round_status(round_state: GameRound) -> None:
    """Render the current assessment round."""
    metric_column_1, metric_column_2, metric_column_3 = st.columns(3)
    with metric_column_1:
        st.metric("Remaining attempts", round_state.remaining_attempts)
    with metric_column_2:
        st.metric("Guesses used", round_state.attempts_used)
    with metric_column_3:
        st.metric("Target difficulty", round_state.difficulty.title())

    st.markdown(f"### {round_state.masked_word}")
    st.code(
        get_hangman_stage(
            wrong_guesses=round_state.letters_wrong,
            max_attempts=round_state.max_attempts,
        ),
        language="text",
    )
    st.write(f"Category: {round_state.category.title()}")
    st.write(f"Guessed letters: {round_state.guessed_letters_display}")
    st.write(f"Hint: {round_state.hint}")


def _render_finished_round(
    current_round: GameRound,
    assessment_service: AssessmentService,
    assessment_state: dict[str, object],
) -> None:
    """Render completion controls for one assessment round."""
    if current_round.result == "won":
        st.success(f"Round complete. You solved '{current_round.word}'.")
    else:
        st.error(f"Round complete. The word was '{current_round.word}'.")

    if st.button("Continue Assessment", use_container_width=True):
        updated_state = assessment_service.advance_assessment(assessment_state)
        st.session_state.assessment_state = updated_state
        st.session_state.assessment_feedback = ""
        st.session_state.assessment_feedback_type = "info"
        st.rerun()


def _render_assessment_completion(
    assessment_state: dict[str, object],
    auth_service: AuthService,
    current_user: dict[str, object],
) -> None:
    """Render the final assessment summary and persistence action."""
    summary = assessment_state["summary"]
    st.success(
        "Assessment complete. Your calibrated level is "
        f"{str(summary['calibrated_level']).title()}."
    )
    st.write(
        f"Passed rounds: {summary['passed_rounds']} / {len(assessment_state['rounds'])} | "
        f"Average guess accuracy: {summary['average_accuracy']:.2f}"
    )
    st.caption(
        "This calibrated level will guide future difficulty selection until your "
        "local performance data suggests otherwise."
    )
    st.dataframe(summary["round_results"], use_container_width=True, hide_index=True)

    left_column, right_column = st.columns(2)
    with left_column:
        if st.button("Save Assessment and Continue", use_container_width=True):
            st.session_state.current_user = auth_service.save_assessment_result(
                user_id=int(current_user["id"]),
                calibrated_level=str(summary["calibrated_level"]),
            )
            st.session_state.assessment_state = None
            st.session_state.assessment_feedback = ""
            st.session_state.assessment_feedback_type = "info"
            st.session_state.navigation = "Home"
            st.rerun()
    with right_column:
        if st.button("Restart Assessment", use_container_width=True):
            st.session_state.assessment_state = None
            st.session_state.assessment_feedback = ""
            st.session_state.assessment_feedback_type = "info"
            st.rerun()


def _render_feedback() -> None:
    """Render the latest assessment feedback message."""
    feedback = st.session_state.get("assessment_feedback")
    if not feedback:
        return

    feedback_type = st.session_state.get("assessment_feedback_type", "info")
    feedback_renderer = {
        "success": st.success,
        "warning": st.warning,
        "error": st.error,
        "info": st.info,
    }.get(feedback_type, st.info)
    feedback_renderer(feedback)
