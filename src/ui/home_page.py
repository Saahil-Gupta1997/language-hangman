"""Top-level Streamlit app flow."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import streamlit as st

from src.services.assessment_service import AssessmentService
from src.services.auth_service import AuthService
from src.services.desktop_login_handoff import consume_desktop_login_handoff
from src.services.game_service import GameService
from src.services.maintenance_service import MaintenanceService
from src.services.onboarding_service import build_onboarding_state
from src.services.report_service import ReportService
from src.services.session_token_service import (
    extract_session_token_from_cookie_header,
    verify_session_token,
)
from src.services.word_service import WordService
from src.ui.assessment_page import render_assessment_page
from src.ui.content_page import render_content_page
from src.ui.design import (
    render_callout,
    render_kpi_grid,
    render_page_header,
    render_section_intro,
)
from src.ui.game_page import render_game_page
from src.ui.media import get_audio_asset_status
from src.ui.profile_page import render_profile_page
from src.ui.report_page import render_report_page
from src.utils.config import AUTH_GATEWAY_ENABLED, AUTH_GATEWAY_LOGIN_URL, AUTH_GATEWAY_LOGOUT_URL
from src.utils.constants import (
    APP_NAME,
    DEFAULT_PREFERRED_CATEGORIES,
    NAVIGATION_ITEMS,
    SITUATION_LABELS,
    SUPPORTED_LEVELS,
)
from src.utils.language_display import format_language_label


def render_home_page(database_path: Path) -> None:
    """Render the app shell and route the user through the current flow."""
    assessment_service = AssessmentService(db_path=database_path)
    auth_service = AuthService(db_path=database_path)
    word_service = WordService(db_path=database_path)
    game_service = GameService(db_path=database_path)
    maintenance_service = MaintenanceService(db_path=database_path)
    report_service = ReportService(db_path=database_path)
    _initialize_session_state()
    _inject_polish_styles()
    _restore_desktop_login_handoff(auth_service=auth_service)
    _restore_gateway_login_cookie(auth_service=auth_service)

    current_user = st.session_state.current_user
    if current_user is None:
        if AUTH_GATEWAY_ENABLED:
            _redirect_to_gateway_login()
        _render_auth_landing(
            auth_service=auth_service,
            word_service=word_service,
        )
        return

    if (
        not current_user["assessment_completed"]
        and st.session_state.get("show_onboarding", False)
        and st.session_state.assessment_state is None
    ):
        _render_onboarding(current_user=current_user)
        return

    if not current_user["assessment_completed"] and st.session_state.navigation == "Preferences":
        st.title(APP_NAME)
        st.info("Review your preferences, then take the short assessment to unlock practice.")
        with st.sidebar:
            st.subheader(f"Hi, {current_user['username']}")
            if st.button("Start Assessment", use_container_width=True):
                st.session_state.navigation = "Home"
                st.rerun()
            if st.button("Logout", use_container_width=True):
                _logout()
        render_profile_page(
            current_user=current_user,
            auth_service=auth_service,
            word_service=word_service,
        )
        return

    if (not current_user["assessment_completed"]) or st.session_state.assessment_state is not None:
        st.title(APP_NAME)
        with st.sidebar:
            st.subheader(f"Hi, {current_user['username']}")
            st.caption("Complete the initial assessment to unlock full practice.")
            _render_media_toggles()
            if st.button("Logout", use_container_width=True):
                _logout()
        render_assessment_page(
            current_user=current_user,
            assessment_service=assessment_service,
            game_service=game_service,
            auth_service=auth_service,
        )
        return

    st.title(APP_NAME)

    with st.sidebar:
        st.subheader(f"Hi, {current_user['username']}")
        if st.session_state.get("guest_session") is not None:
            st.caption("Guest progress lasts for this browser session.")
        st.caption(
            f"Language: {format_language_label(str(current_user['target_language']))} | "
            f"Effective level: {current_user['effective_level'].title()}"
        )
        _render_media_toggles()
        st.caption("Use the section switcher at the top of the app to move between screens.")
        if st.button("Logout", use_container_width=True):
            _logout()

    _render_main_navigation()

    if st.session_state.navigation == "Home":
        _render_dashboard(current_user=current_user, report_service=report_service)
    elif st.session_state.navigation == "Preferences":
        render_profile_page(
            current_user=current_user,
            auth_service=auth_service,
            word_service=word_service,
        )
    elif st.session_state.navigation == "Play":
        render_game_page(
            current_user=current_user,
            auth_service=auth_service,
            game_service=game_service,
            report_service=report_service,
            word_service=word_service,
        )
    elif st.session_state.navigation == "Reports":
        render_report_page(
            current_user=current_user,
            report_service=report_service,
            word_service=word_service,
        )
    else:
        render_content_page(
            maintenance_service=maintenance_service,
            word_service=word_service,
        )


def _initialize_session_state() -> None:
    """Initialize the session keys used across the app."""
    st.session_state.setdefault("current_user", None)
    st.session_state.setdefault("navigation", "Home")
    st.session_state.setdefault("builder_override", None)
    st.session_state.setdefault("active_game", None)
    st.session_state.setdefault("active_learning_session", None)
    st.session_state.setdefault("pending_next_round", None)
    st.session_state.setdefault("session_summary", None)
    st.session_state.setdefault("last_round_review", None)
    st.session_state.setdefault("content_import_summary", None)
    st.session_state.setdefault("sound_enabled", False)
    st.session_state.setdefault("music_enabled", False)
    st.session_state.setdefault("pending_sound", None)
    st.session_state.setdefault("game_feedback", "")
    st.session_state.setdefault("game_feedback_type", "info")
    st.session_state.setdefault("assessment_state", None)
    st.session_state.setdefault("assessment_feedback", "")
    st.session_state.setdefault("assessment_feedback_type", "info")
    st.session_state.setdefault("show_onboarding", False)
    st.session_state.setdefault("auth_mode", "sign_in")


def _sync_navigation_from_control() -> None:
    """Keep the visible section switcher and route state in sync."""
    selected = st.session_state.get("navigation_control")
    if selected in NAVIGATION_ITEMS:
        st.session_state.navigation = selected
        st.session_state.navigation_control_last_sync = selected


def _render_main_navigation() -> None:
    """Render the primary app navigation in the main work area."""
    if st.session_state.get("navigation_control_last_sync") != st.session_state.navigation:
        st.session_state.navigation_control = st.session_state.navigation
        st.session_state.navigation_control_last_sync = st.session_state.navigation

    st.segmented_control(
        "App section",
        NAVIGATION_ITEMS,
        key="navigation_control",
        label_visibility="collapsed",
        on_change=_sync_navigation_from_control,
        width="stretch",
    )


def _restore_desktop_login_handoff(auth_service: AuthService) -> None:
    """Consume a local desktop-launcher login handoff if one exists."""
    if st.session_state.current_user is not None:
        return

    user_id = consume_desktop_login_handoff()
    if user_id is None:
        return

    try:
        st.session_state.current_user = auth_service.get_user_by_id(user_id)
    except ValueError:
        return

    st.session_state.navigation = "Home"
    st.session_state.builder_override = None
    st.session_state.active_game = None
    st.session_state.active_learning_session = None
    st.session_state.pending_next_round = None
    st.session_state.session_summary = None
    st.session_state.last_round_review = None
    st.session_state.pending_sound = None
    st.session_state.assessment_state = None
    st.session_state.game_feedback = ""
    st.session_state.assessment_feedback = ""


def _restore_gateway_login_cookie(auth_service: AuthService) -> None:
    """Restore a logged-in user from the optional FastAPI gateway cookie."""
    if st.session_state.current_user is not None or not AUTH_GATEWAY_ENABLED:
        return

    token = extract_session_token_from_cookie_header(_get_request_cookie_header())
    if token is None:
        return

    user_id = verify_session_token(token)
    if user_id is None:
        return

    try:
        st.session_state.current_user = auth_service.get_user_by_id(user_id)
    except ValueError:
        return

    st.session_state.navigation = "Home"
    st.session_state.builder_override = None
    st.session_state.active_game = None
    st.session_state.active_learning_session = None
    st.session_state.pending_next_round = None
    st.session_state.session_summary = None
    st.session_state.last_round_review = None
    st.session_state.pending_sound = None
    st.session_state.assessment_state = None
    st.session_state.game_feedback = ""
    st.session_state.assessment_feedback = ""


def _get_request_cookie_header() -> str:
    """Return the Cookie header exposed by Streamlit, if available."""
    context = getattr(st, "context", None)
    headers = getattr(context, "headers", None)
    if headers is None:
        return ""

    try:
        return str(headers.get("Cookie") or headers.get("cookie") or "")
    except AttributeError:
        return ""


def _redirect_to_gateway_login() -> None:
    """Send gateway-mode users back to the standalone login page."""
    st.markdown(
        f'<meta http-equiv="refresh" content="0;url={AUTH_GATEWAY_LOGIN_URL}">',
        unsafe_allow_html=True,
    )
    st.info("Redirecting to the Language Learning Hangman sign-in page...")
    st.stop()


def _compact_html(markup: str) -> str:
    """Strip Markdown-triggering indentation while preserving the pasted HTML."""
    return "\n".join(line.strip() for line in dedent(markup).splitlines() if line.strip())


def _render_auth_landing(
    auth_service: AuthService,
    word_service: WordService,
) -> None:
    """Render the sign-in and sign-up experience."""
    _sync_auth_mode_from_query()
    _inject_pasted_auth_styles()

    st.markdown(
        _compact_html(
            """
        <div class="title-bar auth-window-bar">
            <div class="title-left">
                <div class="logo">LH</div>
                <div class="app-title">Language Learning Hangman</div>
            </div>
            <div class="window-icons">&minus; &#9633; &times;</div>
        </div>
        """
        ),
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([1, 1.1], gap="large")

    with left_col:
        st.markdown(
            _compact_html(
            """
            <div class="left-panel">
                <div class="cloud cloud-1"></div>
                <div class="cloud cloud-2"></div>
                <div class="leaf-cluster" aria-hidden="true">
                    <span></span><span></span><span></span><span></span><span></span>
                </div>

                <div class="hero-title">
                    Play.<br>
                    Learn.<br>
                    Get Fluent.
                </div>

                <div class="green-line"></div>

                <div class="hero-subtitle">
                    Improve your vocabulary and<br>
                    language skills with the classic<br>
                    Hangman game.
                </div>

                <div class="hangman-area">
                    <div class="gallows">
                        <div class="base"></div>
                        <div class="pole"></div>
                        <div class="top-beam"></div>
                        <div class="brace"></div>
                        <div class="rope"></div>

                        <div class="person" aria-hidden="true">
                            <svg viewBox="0 0 78 150" role="img" aria-label="Hangman figure">
                                <circle class="head-ring" cx="39" cy="25" r="19"></circle>
                                <path class="stick-line" d="M39 44 L39 88"></path>
                                <path class="stick-line" d="M39 59 L16 82"></path>
                                <path class="stick-line" d="M39 59 L62 82"></path>
                                <path class="stick-line" d="M39 88 L18 132"></path>
                                <path class="stick-line" d="M39 88 L60 132"></path>
                            </svg>
                        </div>
                    </div>

                    <div>
                        <div class="word-boxes">
                            <div class="letter-box">_</div>
                            <div class="letter-box">A</div>
                            <div class="letter-box">N</div>
                            <div class="letter-box">G</div>
                            <div class="letter-box">_</div>
                            <div class="letter-box">A</div>
                            <div class="letter-box">N</div>
                        </div>

                        <div class="guess-lines">_ _ _ _ _ _</div>
                    </div>
                </div>

                <div class="tip-card">
                    <div class="tip-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                             stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M9 18h6"></path>
                            <path d="M10 22h4"></path>
                            <path d="M8.2 14.4A6 6 0 1 1 15.8 14c-.9.7-1.4 1.7-1.6 2.8H9.8c-.2-1-.7-1.8-1.6-2.4Z"></path>
                            <path d="M12 2v2"></path>
                            <path d="M4.9 4.9l1.4 1.4"></path>
                            <path d="M19.1 4.9l-1.4 1.4"></path>
                        </svg>
                    </div>
                    <div class="tip-text">
                        <b>Tip:</b> Think of common words<br>
                        and practice every day!
                    </div>
                </div>
            </div>
            """
            ),
            unsafe_allow_html=True,
        )

    with right_col:
        _render_pasted_auth_header()

        if st.session_state.auth_mode == "create_account":
            _render_pasted_create_account_form(
                auth_service=auth_service,
                word_service=word_service,
            )
        else:
            _render_pasted_sign_in_form(auth_service=auth_service)


def _sync_auth_mode_from_query() -> None:
    """Use lightweight query-string links for the pasted Sign In/Create tabs."""
    mode = st.query_params.get("auth_mode")
    if mode in {"create", "create_account", "join"}:
        st.session_state.auth_mode = "create_account"
    elif mode == "sign_in":
        st.session_state.auth_mode = "sign_in"


def _render_pasted_auth_header() -> None:
    """Render the pasted auth header and visual tab row."""
    sign_in_class = "tab-active" if st.session_state.auth_mode == "sign_in" else "tab"
    create_class = "tab-active" if st.session_state.auth_mode == "create_account" else "tab"
    st.markdown(
        _compact_html(
            f"""
        <div class="login-logo">LH</div>
        <div class="welcome">Welcome back!</div>
        <div class="welcome-subtitle">Sign in to continue your language journey.</div>

        <div class="tabs">
            <a class="{sign_in_class}" href="?auth_mode=sign_in" target="_self">Sign In</a>
            <a class="{create_class}" href="?auth_mode=create_account" target="_self">
                Create Account
            </a>
        </div>
        """
        ),
        unsafe_allow_html=True,
    )


def _render_pasted_sign_in_form(auth_service: AuthService) -> None:
    """Render the pasted sign-in form and wire it to the existing auth service."""
    username = st.text_input(
        "Username or Email",
        placeholder="Enter your username or email",
        key="pasted_login_username",
    )

    password = st.text_input(
        "Password",
        placeholder="Enter your password",
        type="password",
        key="pasted_login_password",
    )

    remember_col, forgot_col = st.columns([1, 1], vertical_alignment="center")
    with remember_col:
        st.checkbox("Remember me", key="pasted_login_remember")
    with forgot_col:
        st.markdown(
            _compact_html(
                """
            <div class="auth-forgot">
                Forgot password?
            </div>
            """
            ),
            unsafe_allow_html=True,
        )

    sign_in = st.button("↪  Sign In", key="pasted_sign_in")

    st.markdown(
        _compact_html(
            """
        <div class="divider">
            <div class="divider-line"></div>
            <div class="divider-circle">or</div>
            <div class="divider-line"></div>
        </div>
        """
        ),
        unsafe_allow_html=True,
    )

    guest_text_col, guest_button_col = st.columns([1.25, 0.95], vertical_alignment="center")
    with guest_text_col:
        st.markdown(
            _compact_html(
                """
            <div class="guest-title">Practice as guest</div>
            <div class="guest-subtitle">Try the game without creating an account.</div>
            """
            ),
            unsafe_allow_html=True,
        )
    with guest_button_col:
        st.markdown('<div class="demo-button">', unsafe_allow_html=True)
        demo = st.button("🎮  Try Demo Game  ›", key="pasted_demo")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        _compact_html(
            """
        <div class="guest-row-end"></div>
        """
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        _compact_html(
            """
        <div class="terms">
            🛡 By signing in, you agree to our
            <span>Terms of Service</span> and
            <span>Privacy Policy</span>.
        </div>
        """
        ),
        unsafe_allow_html=True,
    )

    if sign_in:
        if username and password:
            user = auth_service.authenticate_user(username=username, password=password)
            if user is None:
                st.warning("Invalid username or password.")
                return
            _complete_login(user=user)
        else:
            st.warning("Please enter username/email and password.")

    if demo:
        st.query_params["demo"] = "1"
        st.rerun()


def _render_pasted_create_account_form(
    auth_service: AuthService,
    word_service: WordService,
) -> None:
    """Render the pasted create-account card with the existing auth service."""
    languages = word_service.get_available_languages()

    username = st.text_input(
        "Username",
        placeholder="Choose a username",
        key="pasted_signup_username",
    )
    password = st.text_input(
        "Password",
        placeholder="Create a password",
        type="password",
        key="pasted_signup_password",
    )
    selected_language = st.selectbox(
        "Target language",
        languages,
        index=0 if languages else None,
        format_func=format_language_label,
        key="pasted_signup_language",
    )
    level = st.selectbox(
        "Current level",
        SUPPORTED_LEVELS,
        key="pasted_signup_level",
    )
    with st.expander("Optional preferences", expanded=False):
        preferred_categories = st.multiselect(
            "Preferred categories",
            options=list(DEFAULT_PREFERRED_CATEGORIES),
            default=list(DEFAULT_PREFERRED_CATEGORIES),
            key="pasted_signup_categories",
        )

    submitted = st.button("Create account", key="pasted_create_account")

    if submitted:
        try:
            user = auth_service.register_user(
                username=username,
                password=password,
                target_language=selected_language,
                level=level,
                preferred_categories=preferred_categories,
            )
        except ValueError as error:
            st.warning(str(error))
            return

        st.session_state.current_user = user
        st.session_state.navigation = "Home"
        st.session_state.builder_override = None
        st.session_state.active_game = None
        st.session_state.active_learning_session = None
        st.session_state.pending_next_round = None
        st.session_state.session_summary = None
        st.session_state.last_round_review = None
        st.session_state.pending_sound = None
        st.session_state.assessment_state = None
        st.session_state.show_onboarding = True
        st.session_state.game_feedback = ""
        st.session_state.assessment_feedback = ""
        st.session_state.assessment_feedback_type = "info"
        st.rerun()


def _complete_login(user: dict[str, object]) -> None:
    """Apply the existing successful-login session state transitions."""
    st.session_state.current_user = user
    st.session_state.navigation = "Play"
    st.session_state.builder_override = None
    st.session_state.active_game = None
    st.session_state.active_learning_session = None
    st.session_state.pending_next_round = None
    st.session_state.session_summary = None
    st.session_state.last_round_review = None
    st.session_state.pending_sound = None
    st.session_state.assessment_state = None
    st.session_state.show_onboarding = False
    st.session_state.game_feedback = ""
    st.session_state.assessment_feedback = ""
    st.session_state.assessment_feedback_type = "info"
    st.rerun()


def _inject_pasted_auth_styles() -> None:
    """Inject login styles that work with Streamlit's real column/container DOM."""
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }

            .stApp {
                background: #f7f8f5;
                overflow-x: hidden;
            }

            [data-testid="stAppViewContainer"] .block-container {
                max-width: 1536px;
                padding: 8px;
            }

            header[data-testid="stHeader"] {
                visibility: hidden;
                height: 0;
            }

            .main-window {
                margin: 8px;
                border: 1px solid #d7ddd8;
                border-radius: 18px;
                overflow: hidden;
                background: white;
                box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            }

            .title-bar {
                height: 70px;
                background: white;
                border-bottom: 1px solid #d7ddd8;
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0 32px;
            }

            .auth-window-bar {
                height: 70px;
                background: white;
                border: 1px solid #d7ddd8;
                border-bottom: 0;
                border-radius: 18px 18px 0 0;
                box-shadow: 0 10px 30px rgba(0,0,0,0.08);
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0 32px;
            }

            .content {
                display: grid;
                grid-template-columns: 1fr 1.1fr;
                min-height: 830px;
            }

            .title-left {
                display: flex;
                align-items: center;
                gap: 18px;
            }

            .logo {
                width: 42px;
                height: 42px;
                background: linear-gradient(135deg, #00452f, #006b48);
                color: white;
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 800;
                font-size: 15px;
            }

            .app-title {
                font-size: 22px;
                font-weight: 800;
                color: #073f2c;
            }

            .window-icons {
                font-size: 28px;
                letter-spacing: 22px;
                color: #111827;
            }

            div[data-testid="stHorizontalBlock"]:has(.left-panel) {
                background: white;
                border: 1px solid #d7ddd8;
                border-radius: 0 0 18px 18px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.08);
                gap: 0 !important;
                min-height: min(830px, calc(100vh - 86px));
                overflow: hidden;
            }

            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"] {
                padding: 0 !important;
            }

            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:first-child
            [data-testid="stVerticalBlock"],
            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:first-child
            [data-testid="stElementContainer"],
            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:first-child
            [data-testid="stMarkdown"],
            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:first-child
            [data-testid="stMarkdown"] > div,
            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:first-child
            [data-testid="stMarkdownContainer"] {
                height: 100%;
            }

            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:nth-of-type(2) {
                background: #fafafa;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 42px !important;
            }

            .left-panel {
                position: relative;
                background: linear-gradient(180deg, #f4f6e9 0%, #e9f3df 55%, #6cb16d 100%);
                padding: 80px 80px;
                overflow: hidden;
                min-height: 100%;
                height: 100%;
                box-sizing: border-box;
            }

            .hero-title {
                font-size: clamp(56px, 5vw, 72px);
                line-height: 1.04;
                font-weight: 900;
                color: #00452f;
                margin-bottom: 24px;
                letter-spacing: -0.04em;
            }

            .green-line {
                width: 58px;
                height: 6px;
                background: #66ac65;
                border-radius: 8px;
                margin-bottom: 26px;
            }

            .hero-subtitle {
                font-size: 24px;
                line-height: 1.45;
                color: #374151;
                max-width: 430px;
                margin-bottom: 36px;
            }

            .cloud {
                position: absolute;
                background: white;
                opacity: 0.85;
                border-radius: 999px;
            }

            .cloud-1 {
                width: 110px;
                height: 35px;
                top: 130px;
                right: 120px;
            }

            .cloud-2 {
                width: 120px;
                height: 35px;
                top: 330px;
                right: 60px;
            }

            .cloud::before {
                content: "";
                position: absolute;
                width: 55px;
                height: 55px;
                background: white;
                border-radius: 50%;
                top: -28px;
                left: 28px;
            }

            .cloud::after {
                content: "";
                position: absolute;
                width: 45px;
                height: 45px;
                background: white;
                border-radius: 50%;
                top: -18px;
                right: 22px;
            }

            .hangman-area {
                margin-top: 30px;
                display: flex;
                align-items: center;
                gap: clamp(24px, 4vw, 60px);
            }

            .gallows {
                position: relative;
                width: 220px;
                height: 280px;
            }

            .base {
                position: absolute;
                bottom: 0;
                left: 0;
                width: 175px;
                height: 20px;
                background: #70410f;
                border-radius: 4px;
            }

            .pole {
                position: absolute;
                bottom: 0;
                left: 35px;
                width: 24px;
                height: 250px;
                background: #70410f;
            }

            .top-beam {
                position: absolute;
                top: 20px;
                left: 35px;
                width: 185px;
                height: 18px;
                background: #70410f;
                border-radius: 4px;
            }

            .rope {
                position: absolute;
                top: 38px;
                left: 195px;
                width: 5px;
                height: 55px;
                background: #70410f;
            }

            .person {
                position: absolute;
                top: 94px;
                left: 165px;
                width: 75px;
                height: 150px;
            }

            .head {
                width: 48px;
                height: 48px;
                border: 6px solid #00452f;
                border-radius: 50%;
                margin: auto;
            }

            .body {
                width: 6px;
                height: 62px;
                background: #00452f;
                margin: 0 auto;
            }

            .arms {
                position: absolute;
                top: 65px;
                left: 16px;
                width: 48px;
                height: 48px;
            }

            .arms::before,
            .arms::after {
                content: "";
                position: absolute;
                width: 6px;
                height: 60px;
                background: #00452f;
                top: 0;
                border-radius: 8px;
            }

            .arms::before {
                transform: rotate(45deg);
                left: 8px;
            }

            .arms::after {
                transform: rotate(-45deg);
                right: 8px;
            }

            .legs {
                position: absolute;
                top: 110px;
                left: 18px;
                width: 45px;
                height: 70px;
            }

            .legs::before,
            .legs::after {
                content: "";
                position: absolute;
                width: 6px;
                height: 70px;
                background: #00452f;
                border-radius: 8px;
            }

            .legs::before {
                transform: rotate(35deg);
                left: 8px;
            }

            .legs::after {
                transform: rotate(-35deg);
                right: 8px;
            }

            .word-boxes {
                display: flex;
                gap: 8px;
                margin-bottom: 30px;
            }

            .letter-box {
                width: 42px;
                height: 52px;
                border: 1px solid #dfe8dc;
                background: white;
                box-shadow: 0 4px 8px rgba(0,0,0,0.12);
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #00452f;
                font-size: 24px;
                font-weight: 900;
            }

            .guess-lines {
                color: #00452f;
                font-size: 36px;
                letter-spacing: 14px;
                font-weight: 900;
            }

            .tip-card {
                position: absolute;
                left: 95px;
                bottom: 100px;
                background: rgba(255,255,255,0.78);
                backdrop-filter: blur(8px);
                border: 1px solid #d8e6d1;
                border-radius: 12px;
                padding: 22px 30px;
                display: flex;
                align-items: center;
                gap: 18px;
                width: 390px;
            }

            .tip-icon {
                width: 64px;
                height: 64px;
                border-radius: 50%;
                background: #00452f;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 34px;
            }

            .tip-text {
                font-size: 18px;
                line-height: 1.45;
                color: #073f2c;
            }

            .right-panel {
                background: #fafafa;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 42px;
            }

            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:nth-of-type(2)
            > div[data-testid="stVerticalBlock"] {
                width: 100%;
                max-width: 680px;
                margin: 0 auto;
                background: white;
                border: 1px solid #e5e7eb !important;
                border-radius: 22px !important;
                box-shadow: 0 16px 36px rgba(0,0,0,0.10);
                padding: 32px 42px 36px !important;
            }

            .login-card {
                width: 100%;
                max-width: 680px;
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 22px;
                padding: 32px 42px 36px;
                box-shadow: 0 16px 36px rgba(0,0,0,0.10);
            }

            .login-logo {
                margin: 0 auto 18px;
                width: 54px;
                height: 54px;
                background: linear-gradient(135deg, #00452f, #006b48);
                color: white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 900;
            }

            .welcome {
                text-align: center;
                color: #00452f;
                font-size: 30px;
                font-weight: 900;
                margin-bottom: 8px;
            }

            .welcome-subtitle {
                text-align: center;
                color: #4b5563;
                font-size: 18px;
                margin-bottom: 34px;
            }

            .tabs {
                display: grid;
                grid-template-columns: 1fr 1fr;
                margin-bottom: 28px;
            }

            .tab-active {
                text-align: center;
                color: #00452f;
                font-size: 18px;
                font-weight: 900;
                padding-bottom: 12px;
                border-bottom: 4px solid #007044;
            }

            .tab {
                text-align: center;
                color: #374151;
                font-size: 18px;
                font-weight: 800;
                padding-bottom: 12px;
                border-bottom: 1px solid #d9dee4;
            }

            .tabs a {
                display: block;
                text-decoration: none;
            }

            .guest-card {
                background: #edf5ea;
                border-radius: 12px;
                padding: 20px 24px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-top: 24px;
            }

            .guest-title {
                color: #00452f;
                font-size: 20px;
                font-weight: 900;
                margin-bottom: 6px;
            }

            .guest-subtitle {
                color: #4b5563;
                font-size: 15px;
            }

            .terms {
                text-align: center;
                color: #4b5563;
                font-size: 14px;
                margin-top: 26px;
            }

            .terms span {
                color: #006b48;
                font-weight: 700;
            }

            .divider {
                display: flex;
                align-items: center;
                gap: 16px;
                margin: 24px 0;
                color: #6b7280;
            }

            .divider-line {
                height: 1px;
                background: #e5e7eb;
                flex: 1;
            }

            .divider-circle {
                border: 1px solid #e5e7eb;
                border-radius: 50%;
                width: 34px;
                height: 34px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: white;
            }

            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:nth-of-type(2)
            div[data-testid="stTextInput"] label {
                font-weight: 800;
                color: #111827;
                font-size: 15px;
            }

            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:nth-of-type(2)
            div[data-testid="stTextInput"] input {
                height: 56px;
                border-radius: 10px;
                font-size: 16px;
            }

            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:nth-of-type(2)
            div[data-testid="stCheckbox"] label {
                color: #374151;
                font-size: 15px;
            }

            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:nth-of-type(2)
            div[data-testid="stButton"],
            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:nth-of-type(2)
            .stButton {
                width: 100%;
            }

            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:nth-of-type(2)
            .stButton > button {
                height: 58px;
                border-radius: 10px;
                font-size: 18px;
                font-weight: 800;
                background: #005f3f;
                color: white;
                border: none;
                justify-content: center;
                width: 100% !important;
            }

            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:nth-of-type(2)
            .stButton > button:hover {
                background: #00734d;
                color: white;
                border: none;
            }

            .auth-forgot {
                text-align: right;
                color: #006b48;
                font-weight: 600;
                margin-top: 2px;
            }

            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:nth-of-type(2)
            div[data-testid="stHorizontalBlock"]:has(.guest-title) {
                align-items: center;
                background: #edf5ea;
                border-radius: 12px;
                gap: 14px !important;
                margin-top: 24px;
                padding: 20px 24px;
            }

            .demo-button button {
                background: #f8fbf4 !important;
                color: #00452f !important;
                border: 1px solid #00452f !important;
                font-size: 16px !important;
            }

            .stButton,
            div[data-testid="stElementContainer"]:has(.stButton),
            div[data-testid="stButton"] {
                width: 100% !important;
            }

            .stButton > button,
            div[data-testid="stButton"] button {
                justify-content: center;
                width: 100% !important;
            }

            /* Polished mockup pass: keep Streamlit as a fallback, but match the
               gateway login's composition and illustration language. */
            header[data-testid="stHeader"] {
                display: none;
            }

            [data-testid="stAppViewContainer"] .block-container {
                max-width: 100%;
                padding: 4px;
            }

            div[data-testid="stVerticalBlock"]:has(.auth-window-bar) {
                gap: 0 !important;
            }

            div[data-testid="stElementContainer"]:has(.auth-window-bar),
            div[data-testid="stMarkdown"]:has(.auth-window-bar),
            div[data-testid="stMarkdownContainer"]:has(.auth-window-bar) {
                height: 72px !important;
                margin: 0 !important;
            }

            .auth-window-bar {
                border-radius: 18px 18px 0 0;
                box-shadow: 0 18px 60px rgba(24, 40, 35, 0.12);
                height: 56px;
                padding: 0 28px;
            }

            .logo,
            .login-logo {
                box-shadow:
                    inset 0 1px 0 rgba(255,255,255,0.18),
                    0 12px 22px rgba(0,69,47,0.22);
            }

            div[data-testid="stHorizontalBlock"]:has(.left-panel) {
                border-radius: 0 0 18px 18px;
                box-shadow: 0 18px 60px rgba(24, 40, 35, 0.12);
                min-height: calc(100vh - 64px);
            }

            .left-panel {
                background:
                    radial-gradient(circle at 23% 76%, rgba(255,255,255,0.60) 0 8%, transparent 26%),
                    radial-gradient(circle at 77% 77%, rgba(255,255,255,0.48) 0 8%, transparent 28%),
                    linear-gradient(180deg, #f8faeb 0%, #edf5df 47%, #a8d09d 74%, #67ad70 100%);
                min-height: calc(100vh - 64px);
                padding: clamp(38px, 5.8vh, 70px) clamp(42px, 6vw, 86px) 18px;
            }

            .left-panel::before,
            .left-panel::after {
                content: "";
                position: absolute;
                left: -10%;
                right: -10%;
                bottom: -72px;
                height: 260px;
                border-radius: 50% 50% 0 0;
                pointer-events: none;
            }

            .left-panel::before {
                bottom: 92px;
                left: -22%;
                right: -4%;
                height: 220px;
                background:
                    radial-gradient(circle at 9% 30%, rgba(109,169,109,0.42) 0 12%, transparent 13%),
                    radial-gradient(circle at 96% 18%, rgba(124,186,124,0.38) 0 14%, transparent 15%),
                    linear-gradient(180deg, rgba(194,223,180,0.72), rgba(153,207,148,0.72));
                opacity: 0.78;
            }

            .left-panel::after {
                background:
                    radial-gradient(circle at 3% 16%, rgba(97,161,98,0.50) 0 10%, transparent 11%),
                    radial-gradient(circle at 94% 14%, rgba(79,150,92,0.56) 0 13%, transparent 14%),
                    linear-gradient(180deg, rgba(132,195,130,0.88), rgba(87,164,101,0.96));
            }

            .left-panel > * {
                position: relative;
                z-index: 3;
            }

            .leaf-cluster {
                position: absolute;
                z-index: 2;
                width: 115px;
                height: 200px;
                left: 18px;
                bottom: 112px;
                opacity: 0.44;
                transform: rotate(-8deg);
            }

            .leaf-cluster span {
                position: absolute;
                width: 31px;
                height: 61px;
                border-radius: 70% 20% 70% 20%;
                background: #4f9d69;
                transform-origin: 50% 96%;
            }

            .leaf-cluster span:nth-child(1) { left: 30px; top: 0; transform: rotate(-28deg); }
            .leaf-cluster span:nth-child(2) { left: 45px; top: 34px; transform: rotate(24deg); }
            .leaf-cluster span:nth-child(3) { left: 16px; top: 61px; transform: rotate(-38deg); }
            .leaf-cluster span:nth-child(4) { left: 54px; top: 88px; transform: rotate(31deg); }
            .leaf-cluster span:nth-child(5) { left: 7px; top: 119px; transform: rotate(-31deg); }

            .hero-title {
                font-size: clamp(56px, 4.4vw, 68px);
                letter-spacing: 0;
                margin-bottom: 16px;
                text-shadow: 0 1px 0 rgba(255,255,255,0.32);
            }

            .green-line {
                margin-bottom: 18px;
            }

            .hero-subtitle {
                font-size: 20px;
                font-weight: 500;
                line-height: 1.38;
                margin-bottom: 18px;
            }

            .hangman-area {
                display: block;
                min-height: 250px;
                position: relative;
            }

            .hangman-area > div:last-child {
                left: min(34vw, 225px);
                min-width: 300px;
                position: absolute;
                top: 64px;
            }

            .gallows {
                height: 250px;
                left: 10px;
                position: absolute;
                top: 10px;
                width: 210px;
            }

            .base,
            .pole,
            .top-beam,
            .brace {
                background: linear-gradient(90deg, #76440f, #5d3106);
                box-shadow:
                    inset 0 3px 0 rgba(255,255,255,0.16),
                    0 6px 12px rgba(71,48,23,0.22);
            }

            .base {
                height: 17px;
                width: 140px;
            }

            .pole {
                border-radius: 4px 4px 0 0;
                height: 232px;
                left: 28px;
                width: 18px;
            }

            .top-beam {
                height: 17px;
                left: 28px;
                top: 1px;
                width: 168px;
            }

            .brace {
                border-radius: 3px;
                height: 14px;
                left: 47px;
                position: absolute;
                top: 20px;
                transform: rotate(132deg);
                transform-origin: left center;
                width: 70px;
            }

            .rope {
                background: #8b5a21;
                border-radius: 999px;
                height: 60px;
                left: 171px;
                top: 18px;
                width: 5px;
            }

            .rope::after {
                content: "";
                position: absolute;
                left: -5px;
                bottom: -5px;
                width: 15px;
                height: 10px;
                border-radius: 999px;
                background: #8b5a21;
            }

            .person {
                height: 150px;
                left: 135px;
                top: 73px;
                width: 78px;
            }

            .person svg {
                display: block;
                height: 100%;
                overflow: visible;
                width: 100%;
            }

            .stick-line,
            .head-ring {
                fill: none;
                stroke: #00452f;
                stroke-linecap: round;
                stroke-linejoin: round;
                stroke-width: 7;
            }

            .head-ring {
                fill: rgba(255,255,255,0.28);
            }

            .letter-box {
                background: rgba(255,255,255,0.93);
                box-shadow: 0 8px 14px rgba(24, 62, 46, 0.16);
                font-size: 21px;
                height: 47px;
                width: 38px;
            }

            .word-boxes {
                gap: 7px;
                margin-bottom: 24px;
            }

            .guess-lines {
                font-size: 30px;
                letter-spacing: 14px;
            }

            .tip-card {
                background: rgba(255,255,255,0.76);
                bottom: auto;
                box-shadow: 0 12px 30px rgba(28, 84, 45, 0.12);
                left: auto;
                margin: 14px 0 0 clamp(10px, 2.5vw, 52px);
                min-height: 76px;
                padding: 14px 22px;
                position: relative;
                right: auto;
                width: min(370px, calc(100% - 96px));
            }

            .tip-icon {
                background: radial-gradient(circle at 34% 24%, #168565, #00452f);
                box-shadow: 0 12px 22px rgba(0,69,47,0.22);
                flex: 0 0 auto;
                height: 50px;
                width: 50px;
            }

            .tip-icon svg {
                display: block;
                height: 28px;
                width: 28px;
            }

            .tip-text {
                font-size: 16px;
            }

            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:nth-of-type(2) {
                background:
                    radial-gradient(circle at 50% 0%, rgba(255,255,255,0.85), transparent 38%),
                    #fbfbfb;
                padding: clamp(24px, 3.4vw, 52px) !important;
            }

            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:nth-of-type(2)
            > div[data-testid="stVerticalBlock"] {
                background: rgba(255,255,255,0.92);
                border-radius: 18px !important;
                box-shadow: 0 24px 64px rgba(16,24,40,0.13);
                padding: 24px clamp(34px, 3.6vw, 48px) 22px !important;
            }

            .login-logo {
                font-size: 14px;
                height: 42px;
                margin-bottom: 14px;
                width: 42px;
            }

            .welcome {
                font-size: 26px;
                letter-spacing: 0;
                margin-bottom: 6px;
            }

            .welcome-subtitle {
                font-size: 15px;
                line-height: 1.45;
                margin-bottom: 22px;
            }

            .tab-active {
                border-bottom: 4px solid #0d7651;
            }

            .tab,
            .tab-active {
                font-size: 15px;
                padding-bottom: 9px;
            }

            .tabs {
                margin-bottom: 20px;
            }

            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:nth-of-type(2)
            div[data-testid="stTextInput"] label {
                font-size: 13px;
            }

            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:nth-of-type(2)
            div[data-testid="stTextInput"] input {
                background: #ffffff;
                border: 1px solid #d3dbe0;
                border-radius: 10px;
                font-size: 14px;
                height: 44px;
            }

            .st-key-pasted_login_username input,
            .st-key-pasted_signup_username input {
                padding-left: 54px !important;
            }

            .st-key-pasted_login_password input,
            .st-key-pasted_signup_password input {
                padding-left: 54px !important;
            }

            .st-key-pasted_login_username div[data-testid="stTextInputRootElement"],
            .st-key-pasted_signup_username div[data-testid="stTextInputRootElement"],
            .st-key-pasted_login_password div[data-testid="stTextInputRootElement"],
            .st-key-pasted_signup_password div[data-testid="stTextInputRootElement"] {
                position: relative;
            }

            .st-key-pasted_login_username div[data-testid="stTextInputRootElement"]::before,
            .st-key-pasted_signup_username div[data-testid="stTextInputRootElement"]::before,
            .st-key-pasted_login_password div[data-testid="stTextInputRootElement"]::before,
            .st-key-pasted_signup_password div[data-testid="stTextInputRootElement"]::before {
                background-position: center;
                background-repeat: no-repeat;
                background-size: 24px 24px;
                content: "";
                height: 24px;
                left: 18px;
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                width: 24px;
                z-index: 5;
            }

            .st-key-pasted_login_username div[data-testid="stTextInputRootElement"]::before,
            .st-key-pasted_signup_username div[data-testid="stTextInputRootElement"]::before {
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23596477' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 21a8 8 0 0 0-16 0'/%3E%3Ccircle cx='12' cy='7' r='4'/%3E%3C/svg%3E");
            }

            .st-key-pasted_login_password div[data-testid="stTextInputRootElement"]::before,
            .st-key-pasted_signup_password div[data-testid="stTextInputRootElement"]::before {
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23596477' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='4' y='11' width='16' height='9' rx='2'/%3E%3Cpath d='M8 11V8a4 4 0 0 1 8 0v3'/%3E%3Cpath d='M12 15v2'/%3E%3C/svg%3E");
            }

            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:nth-of-type(2)
            .stButton > button {
                background: linear-gradient(135deg, #006b48, #004b35);
                border-radius: 10px;
                box-shadow: 0 10px 20px rgba(0,69,47,0.18);
                font-size: 16px;
                height: 52px;
            }

            div[data-testid="stHorizontalBlock"]:has(.left-panel)
            > div[data-testid="stColumn"]:nth-of-type(2)
            div[data-testid="stHorizontalBlock"]:has(.guest-title) {
                background: linear-gradient(135deg, #edf6ea, #f4f9ef);
                border-radius: 10px;
                min-height: 82px;
                padding: 16px 20px;
            }

            .guest-title {
                font-size: 17px;
                margin-bottom: 6px;
            }

            .guest-subtitle {
                font-size: 13px;
            }

            .demo-button button {
                background: rgba(255,255,255,0.70) !important;
                border-radius: 9px !important;
                box-shadow: none !important;
                color: #00452f !important;
                font-size: 15px !important;
                height: 52px !important;
            }

            .divider {
                margin: 20px 0;
            }

            .terms {
                font-size: 13px;
                margin-top: 20px;
            }

            @media (min-width: 1121px) {
                html,
                .stApp {
                    height: 100vh;
                    overflow: hidden;
                }

                div[data-testid="stHorizontalBlock"]:has(.left-panel) {
                    height: calc(100vh - 64px);
                    min-height: 0;
                }

                .left-panel,
                div[data-testid="stHorizontalBlock"]:has(.left-panel)
                > div[data-testid="stColumn"]:nth-of-type(2) {
                    min-height: 0;
                }
            }

            @media (min-width: 1121px) and (max-height: 800px) {
                .left-panel {
                    padding-top: 30px;
                }

                .hero-title {
                    font-size: clamp(48px, 4vw, 58px);
                    margin-bottom: 12px;
                }

                .green-line {
                    margin-bottom: 12px;
                }

                .hero-subtitle {
                    font-size: 17px;
                    margin-bottom: 8px;
                }

                .hangman-area {
                    min-height: 218px;
                }

                .gallows,
                .hangman-area > div:last-child {
                    transform: scale(0.86);
                    transform-origin: left top;
                }

                .tip-card {
                    margin-top: 8px;
                    min-height: 68px;
                    padding: 12px 18px;
                }

                .tip-icon {
                    height: 44px;
                    width: 44px;
                }

                .tip-text {
                    font-size: 14px;
                }

                div[data-testid="stHorizontalBlock"]:has(.left-panel)
                > div[data-testid="stColumn"]:nth-of-type(2) {
                    padding: 18px 28px !important;
                }

                div[data-testid="stHorizontalBlock"]:has(.left-panel)
                > div[data-testid="stColumn"]:nth-of-type(2)
                > div[data-testid="stVerticalBlock"] {
                    padding: 18px 36px 16px !important;
                }

                .login-logo {
                    height: 36px;
                    margin-bottom: 10px;
                    width: 36px;
                }

                .welcome {
                    font-size: 23px;
                }

                .welcome-subtitle {
                    margin-bottom: 16px;
                }

                .tabs {
                    margin-bottom: 14px;
                }

                .tab,
                .tab-active {
                    padding-bottom: 7px;
                }

                div[data-testid="stHorizontalBlock"]:has(.left-panel)
                > div[data-testid="stColumn"]:nth-of-type(2)
                div[data-testid="stTextInput"] input {
                    height: 40px;
                }

                div[data-testid="stHorizontalBlock"]:has(.left-panel)
                > div[data-testid="stColumn"]:nth-of-type(2)
                .stButton > button {
                    height: 46px;
                }

                .divider {
                    margin: 14px 0;
                }

                div[data-testid="stHorizontalBlock"]:has(.left-panel)
                > div[data-testid="stColumn"]:nth-of-type(2)
                div[data-testid="stHorizontalBlock"]:has(.guest-title) {
                    min-height: 70px;
                    padding: 12px 16px;
                }

                .demo-button button {
                    height: 46px !important;
                }

                .terms {
                    margin-top: 12px;
                }
            }

            @media (max-width: 1100px) {
                .left-panel {
                    min-height: 720px;
                    padding: 56px 48px;
                }

                div[data-testid="stHorizontalBlock"]:has(.left-panel) {
                    min-height: auto;
                }

                div[data-testid="stHorizontalBlock"]:has(.left-panel)
                > div[data-testid="stColumn"]:nth-of-type(2) {
                    padding: 28px !important;
                }
            }

            @media (max-width: 900px) {
                .auth-window-bar {
                    border-radius: 14px 14px 0 0;
                    padding: 0 18px;
                }

                .app-title {
                    font-size: 18px;
                }

                .window-icons {
                    display: none;
                }

                div[data-testid="stHorizontalBlock"]:has(.left-panel)
                > div[data-testid="stColumn"]:nth-of-type(2)
                > div[data-testid="stVerticalBlock"] {
                    padding: 28px 24px 32px !important;
                }

                .tip-card {
                    margin-left: 0;
                    width: min(100%, 370px);
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_auth_mockup_hero_panel() -> None:
    """Render the screenshot-inspired signed-out hero panel."""
    st.markdown(
        """
        <section class="auth-hero-panel" aria-label="Language Learning Hangman overview">
            <div class="hero-cloud hero-cloud-one"></div>
            <div class="hero-cloud hero-cloud-two"></div>
            <h1>Play.<br />Learn.<br />Get Fluent.</h1>
            <div class="hero-rule"></div>
            <p>
                Improve your vocabulary and language skills with the classic Hangman game.
            </p>
            <div class="hero-game-scene" aria-label="Mini Hangman illustration">
                <pre class="gallows">________
|      |
|      O
|     /|\\
|     / \\
|</pre>
                <div class="hero-word">
                    <div class="letter-tiles">
                        <span>_</span><span>A</span><span>N</span><span>G</span>
                        <span>_</span><span>A</span><span>N</span>
                    </div>
                    <div class="answer-lines">
                        <span></span><span></span><span></span><span></span><span></span><span></span>
                    </div>
                </div>
            </div>
            <div class="hero-tip">
                <div class="tip-icon">?</div>
                <strong>Tip:</strong>
                <span>Think of common words and practice every day!</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_auth_hero_panel() -> None:
    """Render the signed-out product story panel."""
    st.markdown(
        """
        <section class="auth-hero-panel" aria-label="Language Learning Hangman overview">
            <div class="hero-cloud hero-cloud-one"></div>
            <div class="hero-cloud hero-cloud-two"></div>
            <h1>Play.<br />Learn.<br />Get Fluent.</h1>
            <div class="hero-rule"></div>
            <p>
                Improve your vocabulary and language skills with the classic Hangman game.
            </p>
            <div class="hero-benefits" aria-label="Benefits">
                <div><span>✓</span>Daily word games</div>
                <div><span>✓</span>Language streaks</div>
                <div><span>✓</span>Practice reminders</div>
            </div>
            <div class="mini-hangman" aria-label="Mini Hangman illustration">
                <pre> +---+
 |   |
 O   |
/|\\  |
/ \\  |</pre>
                <div class="letter-tiles">
                    <span>L</span><span>A</span><span>N</span><span>G</span>
                    <span>_</span><span>A</span><span>G</span><span>E</span>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_login_form(auth_service: AuthService) -> None:
    """Render the login form."""
    with st.form("login_form"):
        username = st.text_input(
            "Username or Email",
            placeholder="Enter your username or email",
        )
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        remember_column, forgot_column = st.columns([1, 1])
        with remember_column:
            st.checkbox("Remember me", key="remember_me")
        with forgot_column:
            st.caption("Forgot password?")
            st.caption("Password reset is not available in local beta.")
        submitted = st.form_submit_button("Sign In", use_container_width=True)

    if submitted:
        user = auth_service.authenticate_user(username=username, password=password)
        if user is None:
            st.error("Invalid username or password.")
            return

        st.session_state.current_user = user
        st.session_state.navigation = "Play"
        st.session_state.builder_override = None
        st.session_state.active_game = None
        st.session_state.active_learning_session = None
        st.session_state.pending_next_round = None
        st.session_state.session_summary = None
        st.session_state.last_round_review = None
        st.session_state.pending_sound = None
        st.session_state.assessment_state = None
        st.session_state.show_onboarding = False
        st.session_state.game_feedback = ""
        st.session_state.assessment_feedback = ""
        st.session_state.assessment_feedback_type = "info"
        st.rerun()

    if st.button("New? Create account", key="switch_to_join", use_container_width=True):
        st.session_state.auth_mode = "Join"
        st.rerun()

    st.markdown(
        """
        <div class="guest-card">
            <div>
                <strong>Practice as guest</strong>
                <span>Demo play is coming later in the local beta.</span>
            </div>
            <button type="button" disabled>Try Demo Game</button>
        </div>
        <p class="terms-note">
            By signing in, you keep your practice data local to this device.
        </p>
        """,
        unsafe_allow_html=True,
    )


def _render_signup_form(auth_service: AuthService, word_service: WordService) -> None:
    """Render the registration form."""
    languages = word_service.get_available_languages()

    with st.form("signup_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        selected_language = st.selectbox(
            "Language",
            languages,
            index=0 if languages else None,
            format_func=format_language_label,
        )
        level = st.selectbox("Current level", SUPPORTED_LEVELS)
        with st.expander("Optional preferences", expanded=False):
            preferred_categories = st.multiselect(
                "Preferred categories",
                options=list(DEFAULT_PREFERRED_CATEGORIES),
                default=list(DEFAULT_PREFERRED_CATEGORIES),
            )
        submitted = st.form_submit_button("Create account", use_container_width=True)

    if submitted:
        try:
            new_user = auth_service.register_user(
                username=username,
                password=password,
                target_language=selected_language,
                level=level,
                preferred_categories=preferred_categories,
            )
        except ValueError as error:
            st.error(str(error))
            return

        st.session_state.current_user = new_user
        st.session_state.navigation = "Home"
        st.session_state.builder_override = None
        st.session_state.active_game = None
        st.session_state.active_learning_session = None
        st.session_state.pending_next_round = None
        st.session_state.session_summary = None
        st.session_state.last_round_review = None
        st.session_state.pending_sound = None
        st.session_state.assessment_state = None
        st.session_state.show_onboarding = True
        st.session_state.game_feedback = ""
        st.session_state.assessment_feedback = ""
        st.session_state.assessment_feedback_type = "info"
        st.rerun()

    if st.button(
        "Already have an account? Sign in",
        key="switch_to_signin",
        use_container_width=True,
    ):
        st.session_state.auth_mode = "Sign In"
        st.rerun()


def _render_onboarding(current_user: dict[str, object]) -> None:
    """Render a simple first-time path before the assessment."""
    onboarding = build_onboarding_state(current_user)
    st.title(APP_NAME)
    st.subheader("Welcome to your learning dashboard")
    st.write("Here is the short path from account setup to your first daily practice session.")

    for step in onboarding["steps"]:
        status = "Done" if step["complete"] else "Next"
        with st.container(border=True):
            st.write(f"{status}: {step['title']}")
            st.caption(step["detail"])

    st.info(
        "The assessment is only three Hangman rounds. It helps the app choose a "
        "comfortable starting difficulty for you."
    )
    left_column, right_column = st.columns(2)
    with left_column:
        if st.button("Start Assessment", use_container_width=True):
            st.session_state.show_onboarding = False
            st.rerun()
    with right_column:
        if st.button("Review Preferences First", use_container_width=True):
            st.session_state.show_onboarding = False
            st.session_state.navigation = "Preferences"
            st.rerun()


def _render_dashboard(current_user: dict[str, object], report_service: ReportService) -> None:
    """Render a lightweight home dashboard for logged-in users."""
    report_context = report_service.build_summary_report(
        user_id=int(current_user["id"]),
        language=str(current_user["target_language"]),
    )
    dashboard = report_context["dashboard"]
    daily_goal = report_context["daily_goal"]

    render_page_header(
        "Dashboard",
        "Start the next useful session, track today's goal, and revisit words that need another look.",
        eyebrow="Learning hub",
        meta=[
            f"Language: {format_language_label(str(dashboard['current_language']))}",
            f"Level: {str(dashboard['current_level']).title()}",
        ],
    )

    active_session_exists = st.session_state.active_learning_session is not None
    primary_label = "Resume Current Session" if active_session_exists else "Start Practice Session"
    if st.button(primary_label, type="primary", use_container_width=True):
        st.session_state.navigation = "Play"
        st.session_state.navigation_control = "Play"
        st.session_state.navigation_control_last_sync = "Play"
        st.rerun()

    strongest = dashboard.get("strongest_situation")
    weakest = dashboard.get("weakest_situation")
    recommended = dashboard.get("recommended_next_situation")
    render_kpi_grid(
        [
            {
                "label": "Suggested mode",
                "value": dashboard["suggested_practice_mode"],
                "caption": "Best next session type",
            },
            {
                "label": "Words practiced",
                "value": dashboard["total_words_practiced"],
                "caption": "All-time saved rounds",
            },
            {
                "label": "Current streak",
                "value": dashboard["current_streak"],
                "caption": f"Best streak: {dashboard['best_streak']}",
            },
            {
                "label": "Review due",
                "value": dashboard["review_items_due"],
                "caption": "Words ready for another pass",
            },
            {
                "label": "Strongest situation",
                "value": SITUATION_LABELS.get(str(strongest), "Not enough data")
                if strongest
                else "Not yet",
            },
            {
                "label": "Try next",
                "value": SITUATION_LABELS.get(str(recommended), "Restaurant")
                if recommended
                else "Restaurant",
                "caption": (
                    "Weakest: "
                    + (
                        SITUATION_LABELS.get(str(weakest), "Not enough data")
                        if weakest
                        else "Not enough data"
                    )
                ),
            },
        ]
    )

    render_section_intro("Today's Goal", "A small daily session is enough to keep momentum visible.")
    st.progress(int(daily_goal["progress_percent"]) / 100)
    goal_copy = (
        f"{daily_goal['words_today']} of {daily_goal['word_goal']} word(s), or "
        f"{daily_goal['sessions_today']} of {daily_goal['session_goal']} session(s), completed today."
    )
    if daily_goal["goal_met"]:
        render_callout("Goal complete", f"{goal_copy} {daily_goal['status_message']}", tone="success")
    else:
        render_callout("Next step", f"{goal_copy} {daily_goal['status_message']}", tone="neutral")

    empty_messages = [message for message in dashboard["empty_states"].values() if message]
    if empty_messages:
        render_section_intro("Needs Attention")
        for message in empty_messages:
            render_callout("Practice signal", message, tone="neutral")

    if report_context["last_seven_days"]:
        render_section_intro("Last 7 Days")
        st.dataframe(
            report_context["last_seven_days"],
            use_container_width=True,
            hide_index=True,
        )

    if st.session_state.active_learning_session is not None:
        active_session = st.session_state.active_learning_session
        render_callout(
            "Session in progress",
            "Active session: "
            f"round {active_session.current_round_number} of {active_session.planned_rounds} "
            f"in {active_session.practice_mode.replace('_', ' ').title()}.",
            tone="neutral",
        )
        if st.button("Resume Current Session", type="primary", use_container_width=True):
            st.session_state.navigation = "Play"
            st.session_state.navigation_control = "Play"
            st.session_state.navigation_control_last_sync = "Play"
            st.rerun()

    if report_context["milestones"]:
        render_section_intro("Milestones")
        for milestone in report_context["milestones"]:
            st.write(f"{milestone['title']}: {milestone['detail']}")

    unlocked_badges = [badge["title"] for badge in report_context["badges"] if badge["unlocked"]]
    if unlocked_badges:
        render_section_intro("Progress Badges")
        st.write(" | ".join(unlocked_badges))

    if report_context["guided_study_plan"]:
        render_section_intro(
            "Guided Study Plan",
            "The app turns your current history into a launchable practice setup.",
        )
        for index, plan in enumerate(report_context["guided_study_plan"], start=1):
            render_callout(plan["title"], f"{plan['summary']} {plan['reason']}", tone="neutral")
            if st.button(
                "Open This Plan In Practice Builder",
                key=f"dashboard_plan_{index}",
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
            st.caption("Finish or resume your active session before launching a new guided plan.")

    if st.session_state.get("content_import_summary"):
        content_summary = st.session_state["content_import_summary"]
        render_callout(
            "Latest Content Reload",
            f"Valid words processed: {content_summary['valid_words']} | "
            f"Invalid words skipped: {content_summary['invalid_words']}",
            tone="neutral",
        )

    if report_context["summaries"]:
        render_section_intro("Category Snapshot")
        st.dataframe(report_context["summaries"], use_container_width=True, hide_index=True)

    render_section_intro("Current Preferences")
    render_kpi_grid(
        [
            {
                "label": "Profile language",
                "value": format_language_label(str(current_user["target_language"])),
                "caption": f"Self-declared: {str(current_user['self_declared_level']).title()}",
            },
            {
                "label": "Calibrated level",
                "value": str(current_user["calibrated_level"]).title()
                if current_user["calibrated_level"]
                else "Not set yet",
            },
            {
                "label": "Preferred categories",
                "value": ", ".join(
                    str(category).title() for category in current_user["preferred_categories"]
                ),
            },
        ]
    )


def _logout() -> None:
    """Clear the local session state for a logout."""
    guest = st.session_state.pop("guest_session", None)
    if guest is not None:
        guest.close()
    st.query_params.clear()
    st.session_state.current_user = None
    st.session_state.navigation = "Home"
    st.session_state.builder_override = None
    st.session_state.active_game = None
    st.session_state.active_learning_session = None
    st.session_state.pending_next_round = None
    st.session_state.session_summary = None
    st.session_state.last_round_review = None
    st.session_state.pending_sound = None
    st.session_state.assessment_state = None
    st.session_state.show_onboarding = False
    st.session_state.game_feedback = ""
    st.session_state.game_feedback_type = "info"
    st.session_state.assessment_feedback = ""
    st.session_state.assessment_feedback_type = "info"
    if AUTH_GATEWAY_ENABLED:
        st.markdown(
            f'<meta http-equiv="refresh" content="0;url={AUTH_GATEWAY_LOGOUT_URL}">',
            unsafe_allow_html=True,
        )
        st.stop()
    st.rerun()


def _render_media_toggles() -> None:
    """Render optional sound/music controls."""
    audio_status = get_audio_asset_status()
    if not audio_status["has_any_audio"]:
        st.session_state.sound_enabled = False
        st.session_state.music_enabled = False
        st.caption("Audio assets are not available in this build.")
        return

    if audio_status["sound_available"]:
        st.session_state.sound_enabled = st.checkbox(
            "Sound effects",
            value=bool(st.session_state.sound_enabled),
            help="Optional. Browser playback rules may still block sounds.",
        )
    else:
        st.session_state.sound_enabled = False

    if audio_status["music_available"]:
        st.session_state.music_enabled = st.checkbox(
            "Background music",
            value=bool(st.session_state.music_enabled),
            help="Optional and off by default. Browser autoplay rules may block playback.",
        )
    else:
        st.session_state.music_enabled = False


def _inject_auth_styles() -> None:
    """Add a light, focused style layer for the signed-out experience."""
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at 12% 14%, rgba(56, 84, 165, 0.10), transparent 28rem),
                radial-gradient(circle at 88% 82%, rgba(47, 112, 100, 0.08), transparent 24rem),
                linear-gradient(135deg, #f6f8fb 0%, #eef3f7 100%);
        }
        section.main > div {
            padding-bottom: 3rem;
            padding-top: 3.4rem;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid #d8e1dd;
            border-radius: 24px;
            box-shadow: 0 1.4rem 3.8rem rgba(23, 37, 34, 0.11);
            padding: 1.15rem;
        }
        .auth-hero-panel {
            background:
                radial-gradient(circle at 88% 12%, rgba(255, 255, 255, 0.16), transparent 13rem),
                linear-gradient(145deg, #3854a5 0%, #23356f 100%);
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 28px;
            box-shadow: 0 1.25rem 3rem rgba(35, 53, 111, 0.16);
            color: #ffffff;
            min-height: 34rem;
            overflow: hidden;
            padding: 2.4rem;
            position: relative;
        }
        .auth-hero-panel::after {
            background: rgba(255, 255, 255, 0.08);
            border-radius: 999px;
            content: "";
            height: 15rem;
            position: absolute;
            right: -5rem;
            top: -5rem;
            width: 15rem;
        }
        .hero-kicker {
            color: rgba(255, 255, 255, 0.72);
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.16em;
            margin-bottom: 4.2rem;
            position: relative;
            text-transform: uppercase;
            z-index: 1;
        }
        .auth-hero-panel h1 {
            font-size: clamp(2.45rem, 4.2vw, 4.8rem);
            font-weight: 900;
            letter-spacing: -0.055em;
            line-height: 0.98;
            margin: 0;
            max-width: 34rem;
            position: relative;
            z-index: 1;
        }
        .auth-hero-panel p {
            color: rgba(255, 255, 255, 0.78);
            font-size: 1.04rem;
            line-height: 1.75;
            margin: 1.35rem 0 0;
            max-width: 29rem;
            position: relative;
            z-index: 1;
        }
        .hero-benefits {
            display: grid;
            gap: 0.8rem;
            margin-top: 2.1rem;
            position: relative;
            z-index: 1;
        }
        .hero-benefits div {
            align-items: center;
            display: flex;
            font-weight: 750;
            gap: 0.75rem;
        }
        .hero-benefits span {
            align-items: center;
            background: rgba(255, 255, 255, 0.14);
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 999px;
            display: inline-flex;
            height: 1.75rem;
            justify-content: center;
            width: 1.75rem;
        }
        .mini-hangman {
            background: rgba(255, 255, 255, 0.10);
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 22px;
            bottom: 2.4rem;
            box-shadow: 0 1rem 2.4rem rgba(0, 0, 0, 0.10);
            left: 2.4rem;
            max-width: 28rem;
            padding: 1.15rem;
            position: absolute;
            right: 2.4rem;
            z-index: 1;
        }
        .mini-hangman pre {
            color: rgba(255, 255, 255, 0.82);
            font-size: 0.9rem;
            line-height: 1.15;
            margin: 0 0 0.85rem;
        }
        .letter-tiles {
            display: grid;
            gap: 0.42rem;
            grid-template-columns: repeat(8, minmax(0, 1fr));
        }
        .letter-tiles span {
            align-items: center;
            aspect-ratio: 1;
            background: #ffffff;
            border-radius: 0.75rem;
            color: #3854a5;
            display: flex;
            font-weight: 900;
            justify-content: center;
        }
        .auth-brand {
            text-align: center;
            padding: 0.35rem 0.4rem 1.1rem;
        }
        .auth-logo {
            align-items: center;
            background: #3854a5;
            border-radius: 0.95rem;
            box-shadow: 0 0.45rem 1rem rgba(56, 84, 165, 0.22);
            color: #ffffff;
            display: inline-flex;
            font-size: 0.95rem;
            font-weight: 800;
            height: 2.55rem;
            justify-content: center;
            letter-spacing: 0.04em;
            margin-bottom: 0.75rem;
            width: 2.55rem;
        }
        .auth-brand h1 {
            color: #172522;
            font-size: 1.85rem;
            font-weight: 900;
            line-height: 1.2;
            margin: 0;
        }
        .auth-brand p {
            color: #5f6f6b;
            font-size: 1rem;
            margin: 0.4rem auto 0;
            max-width: 24rem;
        }
        .auth-brand span {
            color: #788783;
            display: inline-block;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            margin-top: 0.85rem;
            text-transform: uppercase;
        }
        div[role="radiogroup"] {
            background: #f3f6fb;
            border: 1px solid #d8e1dd;
            border-radius: 999px;
            gap: 0.4rem;
            margin-bottom: 1.2rem;
            padding: 0.35rem;
        }
        div[role="radiogroup"] label {
            border-radius: 999px;
            padding: 0.32rem 0.65rem;
        }
        div[data-testid="stForm"] {
            border: 0;
            padding: 0.25rem 0 0;
        }
        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div {
            border-radius: 14px;
            min-height: 3.15rem;
        }
        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="select"]:focus-within {
            box-shadow: 0 0 0 0.2rem rgba(56, 84, 165, 0.14);
        }
        div.stFormSubmitButton > button {
            background: #3854a5;
            border: 1px solid #3854a5;
            border-radius: 0.9rem;
            color: #ffffff;
            min-height: 3.25rem;
            font-weight: 700;
            transition: transform 120ms ease, box-shadow 120ms ease;
        }
        div.stFormSubmitButton > button:hover {
            border-color: #2f4688;
            box-shadow: 0 0.55rem 1.15rem rgba(56, 84, 165, 0.18);
            transform: translateY(-1px);
        }
        div.stButton > button {
            border-color: #d8e1dd;
            border-radius: 0.9rem;
            color: #3854a5;
            font-weight: 700;
            min-height: 2.9rem;
        }
        @media (max-width: 900px) {
            section.main > div {
                padding-top: 1.5rem;
            }
            .auth-hero-panel {
                min-height: 28rem;
                padding: 1.7rem;
            }
            .mini-hangman {
                bottom: auto;
                left: auto;
                margin-top: 1.5rem;
                position: relative;
                right: auto;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _inject_mockup_auth_styles() -> None:
    """Add screenshot-inspired auth layout overrides."""
    st.markdown(
        """
        <style>
        .stApp {
            background: #f6f7f5;
        }
        header[data-testid="stHeader"] {
            background: transparent;
        }
        [data-testid="stAppViewContainer"] .block-container {
            max-width: 1500px;
            padding: 0.75rem 1.25rem 1.25rem;
        }
        section.main > div {
            max-width: 1500px;
        }
        .auth-window-bar {
            align-items: center;
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid #dde3df;
            border-bottom: 0;
            border-radius: 22px 22px 0 0;
            box-shadow: 0 0.6rem 1.8rem rgba(24, 40, 35, 0.08);
            display: flex;
            justify-content: space-between;
            min-height: 4.6rem;
            padding: 0 1.7rem;
        }
        .window-brand {
            align-items: center;
            color: #143f36;
            display: flex;
            font-size: 1.25rem;
            gap: 1.2rem;
            letter-spacing: -0.02em;
        }
        .window-logo,
        .auth-logo {
            background: linear-gradient(145deg, #0f604f, #0a443a);
            box-shadow: 0 0.6rem 1.4rem rgba(11, 77, 65, 0.20);
        }
        .window-logo {
            align-items: center;
            border-radius: 0.7rem;
            color: #ffffff;
            display: flex;
            font-size: 1rem;
            font-weight: 900;
            height: 2.35rem;
            justify-content: center;
            width: 2.35rem;
        }
        .auth-brand {
            padding: 0.4rem 0 1.35rem;
            text-align: center;
        }
        .auth-logo {
            align-items: center;
            border-radius: 999px;
            color: #ffffff;
            display: inline-flex;
            font-size: 1rem;
            font-weight: 900;
            height: 3.05rem;
            justify-content: center;
            margin-bottom: 1rem;
            width: 3.05rem;
        }
        .window-controls {
            align-items: center;
            display: flex;
            gap: 1.35rem;
        }
        .window-controls span {
            border: 1.5px solid #1f2c2a;
            display: block;
            height: 1rem;
            opacity: 0.9;
            position: relative;
            width: 1rem;
        }
        .window-controls span:first-child {
            border-left: 0;
            border-right: 0;
            border-top: 0;
            height: 0.4rem;
        }
        .window-controls span:last-child {
            border: 0;
            transform: rotate(45deg);
        }
        .window-controls span:last-child::before,
        .window-controls span:last-child::after {
            background: #1f2c2a;
            content: "";
            left: 50%;
            position: absolute;
            top: 50%;
            transform: translate(-50%, -50%);
        }
        .window-controls span:last-child::before {
            height: 1.55rem;
            width: 1.5px;
        }
        .window-controls span:last-child::after {
            height: 1.5px;
            width: 1.55rem;
        }
        .auth-hero-panel {
            background:
                radial-gradient(circle at 98% 56%, rgba(129, 172, 139, 0.30), transparent 6rem),
                radial-gradient(circle at 8% 72%, rgba(91, 151, 104, 0.24), transparent 8rem),
                linear-gradient(180deg, #faf9ed 0%, #eaf1de 58%, #97c29b 100%);
            border: 1px solid #dde3df;
            border-radius: 0 0 0 22px;
            box-shadow: none;
            color: #0a443a;
            min-height: min(50.5rem, calc(100vh - 6.25rem));
            min-width: 0;
            overflow: hidden;
            padding: 4.9rem clamp(2.4rem, 4vw, 4.2rem) 2.4rem;
            position: relative;
        }
        .auth-hero-panel::after {
            background:
                radial-gradient(ellipse at 24% 72%, rgba(92, 142, 84, 0.38), transparent 18rem),
                radial-gradient(ellipse at 75% 78%, rgba(72, 125, 78, 0.34), transparent 17rem);
            border-radius: 0;
            bottom: -5rem;
            height: 18rem;
            left: -2rem;
            right: -2rem;
            top: auto;
            width: auto;
        }
        .hero-cloud {
            background: rgba(255, 255, 255, 0.58);
            border-radius: 999px;
            height: 1rem;
            position: absolute;
            z-index: 1;
        }
        .hero-cloud::before,
        .hero-cloud::after {
            background: inherit;
            border-radius: 999px;
            content: "";
            position: absolute;
        }
        .hero-cloud::before {
            height: 1.7rem;
            left: 1.1rem;
            top: -0.8rem;
            width: 1.7rem;
        }
        .hero-cloud::after {
            height: 1.1rem;
            right: 0.8rem;
            top: -0.45rem;
            width: 1.1rem;
        }
        .hero-cloud-one {
            right: 6.7rem;
            top: 8.8rem;
            width: 5.5rem;
        }
        .hero-cloud-two {
            right: 2.2rem;
            top: 21rem;
            width: 5.1rem;
        }
        .auth-hero-panel h1 {
            color: #0a443a;
            font-size: clamp(3.6rem, 5.3vw, 6.2rem);
            font-weight: 900;
            letter-spacing: -0.06em;
            line-height: 0.96;
            max-width: 32rem;
            overflow-wrap: normal;
            text-shadow: 0 0.2rem 0.6rem rgba(10, 68, 58, 0.08);
            white-space: normal;
            word-break: normal;
        }
        .hero-rule {
            background: #67aa78;
            border-radius: 999px;
            height: 0.32rem;
            margin-top: 1.45rem;
            position: relative;
            width: 3.5rem;
            z-index: 1;
        }
        .auth-hero-panel p {
            color: #46515f;
            font-size: 1.38rem;
            line-height: 1.42;
            margin-top: 1.25rem;
            max-width: 23rem;
        }
        .hero-game-scene {
            align-items: center;
            display: grid;
            gap: 2.2rem;
            grid-template-columns: 13rem 1fr;
            margin-top: 2.6rem;
            position: relative;
            z-index: 1;
        }
        .gallows {
            color: #5a3e24;
            font-size: 2.05rem;
            font-weight: 900;
            line-height: 0.9;
            margin: 0;
            text-shadow: 0 0.15rem 0.15rem rgba(90, 62, 36, 0.20);
        }
        .hero-word {
            display: grid;
            gap: 1.4rem;
        }
        .letter-tiles {
            display: grid;
            gap: 0.42rem;
            grid-template-columns: repeat(7, minmax(0, 1fr));
            max-width: 18rem;
            min-width: 14rem;
        }
        .letter-tiles span {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(197, 212, 202, 0.86);
            border-radius: 0.45rem;
            box-shadow: 0 0.35rem 0.7rem rgba(28, 72, 53, 0.13);
            color: #0a443a;
            font-size: 1.45rem;
            min-height: 2.6rem;
        }
        .answer-lines {
            display: grid;
            gap: 0.7rem;
            grid-template-columns: repeat(6, 2rem);
        }
        .answer-lines span {
            background: #0a443a;
            border-radius: 999px;
            display: block;
            height: 0.18rem;
        }
        .hero-tip {
            align-items: center;
            background: rgba(255, 255, 255, 0.54);
            border: 1px solid rgba(255, 255, 255, 0.62);
            border-radius: 1rem;
            bottom: 4.5rem;
            box-shadow: 0 1rem 2rem rgba(41, 100, 61, 0.12);
            color: #143f36;
            display: flex;
            gap: 0.75rem;
            left: 4rem;
            max-width: 24rem;
            padding: 1.05rem 1.25rem;
            position: absolute;
            z-index: 2;
        }
        .tip-icon {
            align-items: center;
            background: linear-gradient(145deg, #0f604f, #0a443a);
            border-radius: 999px;
            color: #ffffff;
            display: flex;
            flex: 0 0 auto;
            font-weight: 900;
            height: 3rem;
            justify-content: center;
            width: 3rem;
        }
        .hero-tip span {
            color: #143f36;
            font-size: 1rem;
            line-height: 1.45;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid #e1e6e3;
            border-radius: 1.15rem;
            box-shadow: 0 1.2rem 3.8rem rgba(24, 40, 35, 0.13);
            margin: 2.2rem auto 0;
            max-width: 680px;
            min-width: min(100%, 520px);
            padding: clamp(2rem, 3vw, 3rem);
        }
        .auth-brand h1 {
            color: #0a443a;
            font-size: 2rem;
            font-weight: 900;
            letter-spacing: -0.025em;
            margin: 0;
        }
        .auth-brand p {
            color: #5f6678;
            font-size: 1.08rem;
            margin: 0.45rem 0 0;
        }
        div[role="radiogroup"] {
            background: transparent;
            border: 0;
            border-bottom: 1px solid #dfe4e2;
            border-radius: 0;
            justify-content: stretch;
            margin-bottom: 1.25rem;
            padding: 0;
        }
        div[role="radiogroup"] label {
            border-radius: 0;
            flex: 1;
            justify-content: center;
            padding-bottom: 0.72rem;
        }
        div[role="radiogroup"] label:has(input:checked) {
            border-bottom: 0.18rem solid #0f604f;
            color: #0f604f;
            font-weight: 800;
        }
        div[data-testid="stForm"] label p {
            color: #172522;
            font-weight: 800;
        }
        div[data-baseweb="input"] > div {
            border-color: #d8e1dd;
            border-radius: 0.65rem;
            min-height: 3.35rem;
        }
        div[data-baseweb="input"]:focus-within {
            box-shadow: 0 0 0 0.2rem rgba(15, 96, 79, 0.13);
        }
        div.stFormSubmitButton > button {
            background: linear-gradient(135deg, #0f604f, #0b4e41);
            border-color: #0f604f;
            border-radius: 0.65rem;
            min-height: 3.55rem;
        }
        div.stFormSubmitButton > button:hover {
            border-color: #0a443a;
            box-shadow: 0 0.7rem 1.45rem rgba(15, 96, 79, 0.18);
        }
        .guest-card {
            align-items: center;
            background: linear-gradient(135deg, #edf5ec, #f8fbf6);
            border-radius: 0.85rem;
            display: flex;
            gap: 1rem;
            justify-content: space-between;
            margin-top: 1.25rem;
            padding: 1rem 1.15rem;
        }
        .guest-card strong,
        .guest-card span {
            display: block;
        }
        .guest-card strong {
            color: #0a443a;
            font-size: 1.05rem;
        }
        .guest-card span,
        .terms-note {
            color: #5f6678;
            font-size: 0.9rem;
        }
        .guest-card button {
            background: transparent;
            border: 1px solid #0f604f;
            border-radius: 0.55rem;
            color: #0f604f;
            font-weight: 800;
            min-height: 2.55rem;
            opacity: 0.72;
            padding: 0 1rem;
        }
        .terms-note {
            margin-top: 1.25rem;
            text-align: center;
        }
        @media (max-width: 900px) {
            [data-testid="stAppViewContainer"] .block-container {
                padding: 0.5rem 0.75rem 1rem;
            }
            .auth-window-bar {
                border-radius: 18px 18px 0 0;
            }
            .auth-hero-panel {
                border-radius: 0;
                min-height: 42rem;
                padding: 3rem 2rem;
            }
            .hero-game-scene {
                grid-template-columns: 1fr;
            }
            .hero-tip {
                bottom: auto;
                left: auto;
                margin-top: 1.6rem;
                position: relative;
            }
            div[data-testid="stVerticalBlockBorderWrapper"] {
                margin-top: 1rem;
                max-width: 100%;
                min-width: 0;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _inject_polish_styles() -> None:
    """Add app-wide visual polish for the logged-in Streamlit experience."""
    st.markdown(
        """
        <style>
        :root {
            --llh-ink: #0f241d;
            --llh-muted: #52615b;
            --llh-green: #006b48;
            --llh-green-dark: #00452f;
            --llh-line: #dbe5dc;
            --llh-surface: #ffffff;
            --llh-soft: #f2f7ee;
            --llh-warning: #fff8e6;
        }

        .stApp {
            background: #f7f8f5;
            color: var(--llh-ink);
        }

        [data-testid="stAppViewContainer"] .block-container {
            max-width: 1180px;
            padding-top: 3.25rem;
            padding-bottom: 3rem;
        }

        [data-testid="stAppViewContainer"] h1 {
            color: var(--llh-green-dark);
            font-size: 2.25rem !important;
            line-height: 1.12 !important;
            letter-spacing: 0 !important;
            margin-bottom: 0.85rem !important;
            padding: 0 0 0.75rem !important;
        }

        h2, h3 {
            color: var(--llh-ink);
            letter-spacing: 0;
        }

        p, li, label, [data-testid="stMarkdownContainer"] {
            color: var(--llh-ink);
        }

        [data-testid="stSidebar"] {
            background: #eef3ed;
            border-right: 1px solid var(--llh-line);
        }

        [data-testid="stSidebar"] h3 {
            color: var(--llh-green-dark);
            font-size: 1.05rem;
        }

        [data-testid="stSidebar"] p {
            color: var(--llh-muted);
        }

        input[type="checkbox"],
        input[type="radio"] {
            accent-color: var(--llh-green);
        }

        [data-testid="stSegmentedControl"] {
            margin: 0.25rem 0 1.4rem;
        }

        [data-testid="stSegmentedControl"] div[role="radiogroup"] {
            flex-wrap: wrap;
            gap: 0.45rem;
        }

        [data-testid="stSegmentedControl"] label {
            border-radius: 999px;
        }

        .llh-page-heading {
            border-bottom: 1px solid var(--llh-line);
            margin: 0.15rem 0 1.25rem;
            padding-bottom: 1rem;
        }

        .llh-page-heading h2 {
            font-size: 1.9rem;
            line-height: 1.16;
            margin: 0.1rem 0 0.4rem;
        }

        .llh-page-heading p {
            color: var(--llh-muted);
            font-size: 1rem;
            line-height: 1.55;
            margin: 0;
            max-width: 760px;
        }

        .llh-eyebrow {
            color: var(--llh-green);
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .llh-meta-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.85rem;
        }

        .llh-meta-pill {
            background: var(--llh-soft);
            border: 1px solid #d6e7d2;
            border-radius: 999px;
            color: var(--llh-green-dark);
            font-size: 0.84rem;
            font-weight: 700;
            padding: 0.35rem 0.7rem;
        }

        .llh-section-intro {
            margin: 1.45rem 0 0.65rem;
        }

        .llh-section-intro h3 {
            font-size: 1.18rem;
            margin: 0;
        }

        .llh-section-intro p {
            color: var(--llh-muted);
            margin: 0.25rem 0 0;
        }

        .llh-kpi-grid {
            display: grid;
            gap: 0.85rem;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            margin: 0.7rem 0 1.2rem;
        }

        .llh-kpi {
            background: var(--llh-surface);
            border: 1px solid var(--llh-line);
            border-radius: 10px;
            min-height: 96px;
            padding: 0.95rem 1rem;
        }

        .llh-kpi-label {
            color: var(--llh-muted);
            display: block;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }

        .llh-kpi strong {
            color: var(--llh-green-dark);
            display: block;
            font-size: 1.35rem;
            line-height: 1.2;
            margin-top: 0.35rem;
            overflow-wrap: anywhere;
        }

        .llh-kpi-caption {
            color: var(--llh-muted);
            display: block;
            font-size: 0.86rem;
            line-height: 1.35;
            margin-top: 0.35rem;
        }

        .llh-callout {
            align-items: flex-start;
            background: var(--llh-soft);
            border: 1px solid #d6e7d2;
            border-radius: 10px;
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            margin: 0.7rem 0;
            padding: 0.9rem 1rem;
        }

        .llh-callout strong {
            color: var(--llh-green-dark);
        }

        .llh-callout span {
            color: var(--llh-muted);
            line-height: 1.45;
        }

        .llh-callout-warning {
            background: var(--llh-warning);
            border-color: #f1dfad;
        }

        div[data-testid="stMetric"] {
            background: var(--llh-surface);
            border: 1px solid var(--llh-line);
            border-radius: 10px;
            min-height: 96px;
            padding: 0.9rem 1rem;
        }

        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] p {
            color: var(--llh-muted);
        }

        div[data-testid="stExpander"] {
            border-color: var(--llh-line);
            border-radius: 10px;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--llh-line);
            border-radius: 10px;
            overflow: hidden;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-baseweb="select"] > div,
        textarea {
            border-color: #ccd8d0;
            border-radius: 10px;
        }

        div.stButton > button {
            border-radius: 10px;
            min-height: 2.65rem;
            transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease;
        }

        div.stButton > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] button[kind="primary"] {
            background: var(--llh-green);
            border-color: var(--llh-green);
            color: white;
            font-weight: 800;
        }

        div.stButton > button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
            background: #007a52;
            border-color: #007a52;
            color: white;
        }

        div.stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 0.35rem 0.9rem rgba(18, 38, 63, 0.12);
            border-color: rgba(0, 107, 72, 0.45);
        }

        button:focus-visible,
        input:focus-visible,
        textarea:focus-visible,
        [role="button"]:focus-visible {
            outline: 3px solid rgba(0, 107, 72, 0.28) !important;
            outline-offset: 2px;
        }

        @media (max-width: 760px) {
            [data-testid="stAppViewContainer"] .block-container {
                padding: 3.35rem 1rem 2rem;
            }

            [data-testid="stAppViewContainer"] h1 {
                font-size: 1.72rem !important;
                line-height: 1.16;
                padding: 0 0 0.4rem !important;
            }

            .llh-page-heading h2 {
                font-size: 1.45rem;
            }

            .llh-page-heading {
                margin-bottom: 0.85rem;
                padding-bottom: 0.65rem;
            }

            .llh-meta-row {
                margin-top: 0.55rem;
            }

            .llh-meta-pill {
                font-size: 0.78rem;
                padding: 0.25rem 0.55rem;
            }

            .llh-kpi-grid {
                grid-template-columns: 1fr;
            }

            [data-testid="stSidebar"] {
                max-width: 82vw;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
