"""Exercise the actual Streamlit widgets and saved results."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.db.database import create_connection


def button(app, label):
    return next(item for item in app.button if item.label == label)


def test_guest_can_play_round_and_view_reports():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
    app.query_params["demo"] = "1"
    app.run(timeout=30)
    assert not app.exception
    guest = app.session_state["guest_session"]
    try:
        button(app, "Start Session").click().run(timeout=30)
        assert not app.exception
        game = app.session_state["active_game"]
        assert game is not None
        for letter in sorted(set(game.word)):
            if not letter.isalpha():
                continue
            app.text_input[0].set_value(letter)
            button(app, "Submit Guess").click().run(timeout=30)
            assert not app.exception
        with create_connection(guest.db_path) as connection:
            results = connection.execute("SELECT result FROM game_sessions").fetchall()
            assert len(results) == 1
            assert results[0][0] == "won"
        reports = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
        reports.session_state["guest_session"] = guest
        reports.session_state["current_user"] = guest.user
        reports.session_state["navigation"] = "Reports"
        reports.run(timeout=30)
        assert not reports.exception
    finally:
        guest.close()
