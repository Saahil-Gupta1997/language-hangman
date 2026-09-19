"""LEGACY Streamlit entry point, kept for regression tests only.

Not part of the supported product. The supported entry point is desktop_app.py; see
docs/LEGACY_BROWSER.md.
"""

from pathlib import Path

import streamlit as st

from src.db.database import init_db
from src.services.guest_service import GuestSession
from src.ui.home_page import render_home_page


def main() -> None:
    """Initialize the app and render the landing page."""
    st.set_page_config(
        page_title="Language Learning Hangman",
        page_icon="LH",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    if st.query_params.get("demo") == "1" and "guest_session" not in st.session_state:
        st.session_state.clear()
        guest = GuestSession()
        st.session_state.guest_session = guest
        st.session_state.current_user = guest.user
        st.session_state.navigation = "Play"
    try:
        guest = st.session_state.get("guest_session")
        database_path: Path = guest.db_path if guest is not None else init_db()
    except Exception as error:
        st.title("Language Learning Hangman")
        st.error(
            "The app could not initialize local storage. "
            "Please check the local data folder and try again."
        )
        with st.expander("Technical details", expanded=False):
            st.code(str(error))
        return

    render_home_page(database_path=database_path)


if __name__ == "__main__":
    main()
