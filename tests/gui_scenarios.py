"""Native GUI scenarios, each run in a fresh process by tests/test_desktop_gui.py.

The shipped app creates its windows once per process. Inside pytest, output capture swaps
the process's standard handles between tests, and Tcl caches those handles, so a new Tk
window in a long-lived test process intermittently failed to read Tcl's own library files
(reproduced outside pytest by swapping handles the same way; see docs/VERIFICATION.md).
Running each scenario in its own process removes that interaction.

Usage: python tests/gui_scenarios.py <scenario> <data_dir>. Exit code 0 means passed.
Keys are exercised through their bound actions, never by taking OS keyboard focus, so
these are not evidence of real keyboard behaviour; see the manual checks in ACCEPTANCE.md.
"""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import customtkinter as ctk  # noqa: E402
from customtkinter.windows.widgets.scaling import ScalingTracker  # noqa: E402

KEYS = {"<Key-Up>", "<Key-Down>", "<Key-Left>", "<Key-Right>", "<Key-Return>", "<Key-space>"}


def signed_in_app(data):
    from src.desktop.application import HangmanDesktop

    app = HangmanDesktop(data / "app.db", data)
    app.show_login(register=True)
    app.username_entry.insert(0, "keys")
    app.password_entry.insert(0, "keys-password-1")
    app.confirm_entry.insert(0, "keys-password-1")
    app.authenticate(register=True)
    return app


def press(menu, key):
    assert KEYS <= set(menu._canvas.bind()), "arrow, Enter and Space must be bound"
    menu.keyboard_step({"<Down>": 1, "<Up>": -1}[key])


def practice_dropdowns_change_from_the_keyboard(data):
    app = signed_in_app(data)
    try:
        app.show_practice()
        for menu, first, second in (
            (app.language, "English", "Spanish"),
            (app.level, "Beginner", "Novice"),
            (app.mode, "Easy", "Hard"),
            (app.focus, "All words", "Review my words"),
        ):
            assert str(menu._canvas.cget("takefocus")) == "1", "dropdown must take Tab focus"
            assert menu.get() == first
            press(menu, "<Down>")
            assert menu.get() == second
            press(menu, "<Up>")
            assert menu.get() == first
    finally:
        app.close_application()


def text_size_dropdown_and_shortcuts(data):
    app = signed_in_app(data)
    try:
        app.show_settings()
        menu = next(w for w in app.body.winfo_children() if isinstance(w, ctk.CTkOptionMenu))
        press(menu, "<Down>")
        assert app.scale == "Large" and ScalingTracker.widget_scaling == 1.15
        press(menu, "<Up>")
        assert app.scale == "Standard" and ScalingTracker.widget_scaling == 1.0
        bound = set(app.bind())
        for sequence in (
            "<Control-Key-equal>",
            "<Control-Key-KP_Add>",
            "<Control-Key-KP_Subtract>",
        ):
            assert sequence in bound, sequence
    finally:
        app.close_application()


def text_size_after_dropdown_is_destroyed(data):
    from src.desktop.runtime import fix_dropdown_scaling_leak
    from src.desktop.widgets import release_window

    fix_dropdown_scaling_leak()
    root = ctk.CTk()
    try:
        ctk.CTkOptionMenu(root, values=["Standard", "Large"]).destroy()
        ctk.set_widget_scaling(1.15)  # raised TclError before R-03
        ctk.set_widget_scaling(1.0)
    finally:
        release_window(root)


def settle(window, seconds=1.2):
    """Let CustomTkinter finish applying a size change before measuring the layout.

    It pins a window's size for about a second after creation or a scaling change, so a
    measurement taken immediately can be against a layout that is still moving.
    """
    import time

    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        window.update()
        time.sleep(0.02)


def focused_control_scrolls_into_view(data):
    from src.desktop.application import MINIMUM_WINDOW

    app = signed_in_app(data)
    try:
        app.logout()
        app.geometry(f"{MINIMUM_WINDOW[0]}x{MINIMUM_WINDOW[1]}")
        app.show_login(register=True)
        settle(app)
        last = [w for w in app.body.winfo_children() if isinstance(w, ctk.CTkButton)][-1]
        # Fire the focus binding directly; focus_force() would take OS focus from other apps.
        last._canvas.event_generate("<FocusIn>", when="now")
        app.update()
        canvas = app.body._parent_canvas
        visible_top = canvas.winfo_rooty() - app.body.winfo_rooty()
        top = last.winfo_rooty() - app.body.winfo_rooty()
        assert visible_top <= top, "focused control is above the visible area"
        assert top + last.winfo_height() <= visible_top + canvas.winfo_height(), "below the fold"
    finally:
        app.close_application()


def window_opens_inside_the_work_area(data):
    import ctypes
    from ctypes import wintypes

    from src.desktop.widgets import _work_area

    app = signed_in_app(data)
    try:
        area = _work_area()
        if area is None:
            return
        user32 = ctypes.windll.user32
        user32.GetAncestor.restype = wintypes.HWND
        hwnd = user32.GetAncestor(wintypes.HWND(app.winfo_id()), 2)
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        left, top, right, bottom = area
        assert rect.left >= left and rect.top >= top, (rect.left, rect.top, area)
        assert rect.right <= right and rect.bottom <= bottom, (rect.right, rect.bottom, area)
    finally:
        app.close_application()


def window_stays_inside_a_narrow_work_area(data):
    """D-38: centring counts the frame, so a screen barely wider than the window holds it."""
    import ctypes
    from ctypes import wintypes

    from src.desktop import widgets

    app = signed_in_app(data)
    try:
        real = widgets._work_area()
        if real is None:
            return
        scaling = widgets.ScalingTracker.get_window_scaling(app)
        narrow = (0, 0, round(1024 * scaling), real[3])
        widgets._work_area = lambda: narrow
        widgets.fit_to_work_area(app, 1060, 760, minimum=(800, 600))
        for _ in range(4):
            app.update()
        user32 = ctypes.windll.user32
        user32.GetAncestor.restype = wintypes.HWND
        hwnd = user32.GetAncestor(wintypes.HWND(app.winfo_id()), 2)
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        assert rect.left >= 0 and rect.right <= narrow[2], (rect.left, rect.right, narrow)
    finally:
        app.close_application()


def automatic_backup_failure_does_not_block_start_up(data):
    from src.desktop.application import HangmanDesktop
    from src.desktop.runtime import recent_events

    (data / "backups").write_text("a file where the backups folder should be")
    app = HangmanDesktop(data / "app.db", data)
    try:
        assert app.backup_warning and "backup protection is reduced" in app.backup_warning
        assert any("stage=automatic_backup" in line for line in recent_events(data))
        app.show_login(register=True)  # the app remains usable
    finally:
        app.close_application()


EMULATED = (("Standard", 1.0), ("Large", 1.0), ("Large", 1.2))  # 1.2 x this display's scaling


def emulate(window, size, factor):
    """Apply a text size on top of an emulated display factor (not the Windows setting).

    CustomTkinter pins the window's size for one second after a scaling change, so wait
    that out before resizing.
    """

    from src.desktop.widgets import TEXT_SCALING

    ctk.set_window_scaling(factor)
    ctk.set_widget_scaling(factor * TEXT_SCALING[size])
    settle(window)


def every_widget(parent):
    """Every descendant, because screens group their content into cards and columns."""
    for child in parent.winfo_children():
        yield child
        yield from every_widget(child)


def assert_text_fits(body, where):
    """No label wider than its space and no control past the right edge of the view."""
    canvas = body._parent_canvas
    right = canvas.winfo_rootx() + canvas.winfo_width()
    for widget in every_widget(body):
        if isinstance(widget, ctk.CTkLabel):
            needed, given = widget._label.winfo_reqwidth(), widget.winfo_width()
            assert needed <= given, (where, widget.cget("text")[:50], needed, given)
        if isinstance(widget, (ctk.CTkLabel, ctk.CTkButton)):
            edge = widget.winfo_rootx() + widget.winfo_width()
            assert edge <= right, (where, widget.cget("text")[:50], edge, right)


def recovery_window_fits_at_minimum_size(data):
    """D-31: recovery text wraps to the window; every action scrolls into view and is
    reached by Tk's own Tab traversal. Display scaling is emulated, not the Windows setting."""
    import json

    from src.desktop.recovery import RecoveryWindow
    from src.desktop.widgets import scroll_into_view

    backups = data / "backups"
    backups.mkdir()
    for name in ("daily-a.sqlite", "before-restore-b.sqlite", "pre-upgrade-c.sqlite"):
        (backups / name).write_bytes(b"")
    for size, factor in EMULATED:
        (data / "settings.json").write_text(json.dumps({"text_size": size}))
        window = RecoveryWindow(
            data / "app.db", data, "The data file could not be opened (DatabaseError)."
        )
        try:
            emulate(window, size, factor)
            window.geometry("640x480")  # the window's minimum size
            window.update()
            where = f"{size} text, factor {factor}"
            assert_text_fits(window.body, where)
            canvas = window.body._parent_canvas
            assert window.body.winfo_reqheight() > canvas.winfo_height(), "expected scrolling"
            buttons = [w for w in window.body.winfo_children() if isinstance(w, ctk.CTkButton)]
            assert len(buttons) == 6, [b.cget("text") for b in buttons]
            for button in buttons:
                scroll_into_view(button)
                window.update()
                top, bottom = canvas.winfo_rooty(), canvas.winfo_rooty() + canvas.winfo_height()
                assert top <= button.winfo_rooty(), (where, button.cget("text"))
                assert button.winfo_rooty() + button.winfo_height() <= bottom, (where, button)
            reached, current = set(), buttons[0]._canvas
            for _ in range(40):
                reached.add(str(current))
                current = current.tk_focusNext()
            assert {str(b._canvas) for b in buttons} <= reached, "Tab must reach every action"
            assert "<Key-Escape>" in window.bind(), "Escape must close the window"
        finally:
            window.close()
            ctk.set_window_scaling(1.0)
            ctk.set_widget_scaling(1.0)


def main_window_text_wraps_at_minimum_size(data):
    """D-31: body text wraps to the window on the text-heavy pages (emulated scaling)."""
    from src.desktop.application import MINIMUM_WINDOW

    app = signed_in_app(data)
    try:
        for size, factor in EMULATED:
            emulate(app, size, factor)
            app.geometry(f"{MINIMUM_WINDOW[0]}x{MINIMUM_WINDOW[1]}")
            for page in (app.show_home, app.show_practice, app.show_settings, app.show_help):
                page()
                app.update()
                assert_text_fits(app.body, f"{page.__name__}, {size} text, factor {factor}")
    finally:
        app.close_application()
        ctk.set_window_scaling(1.0)
        ctk.set_widget_scaling(1.0)


def letter_keys_guess_on_click(data):
    """The A-Z keys are drawn on a canvas, so clicking one must still submit that letter."""
    app = signed_in_app(data)
    try:
        app.show_practice()
        app.start_session()
        board = app.board
        app.update()
        word = app.payload["round"]["word"]
        letter = sorted(set(word))[0]
        box, used, (left, top, right, bottom) = board._keys[letter]
        assert not used, f"{letter} should not be used yet"
        factor = board.scaling()
        board.event_generate(
            "<Button-1>",
            x=round((left + right) / 2 * factor),
            y=round((top + bottom) / 2 * factor),
            when="now",
        )
        app.update()
        assert letter in app.payload["round"]["guessed_letters"], (
            f"clicking {letter} did not register",
            app.payload["round"]["guessed_letters"],
        )
        # A used key must not fire again, and the board must redraw it as used.
        assert app.board._keys[letter][1], "the clicked key should now be marked used"
        before = list(app.payload["round"]["guessed_letters"])
        app.board.event_generate(
            "<Button-1>",
            x=round((left + right) / 2 * factor),
            y=round((top + bottom) / 2 * factor),
            when="now",
        )
        app.update()
        assert app.payload["round"]["guessed_letters"] == before, "a used key fired again"
    finally:
        app.close_application()


def removed_screens_and_settings_stay_removed(data):
    """Word cards, travel cards and the rounds question are gone from the app."""
    app = signed_in_app(data)
    try:
        labels = [
            widget.cget("text")
            for widget in every_widget(app.navigation)
            if isinstance(widget, ctk.CTkButton)
        ]
        assert "Word cards" not in labels and "Practice" in labels, labels
        app.show_practice()
        app.update()
        assert not hasattr(app, "show_words")
        assert not hasattr(app, "rounds") and not hasattr(app, "situation")
        assert app.level.cget("values") == [
            "Beginner",
            "Novice",
            "Intermediate",
            "Advanced",
            "Expert",
        ]
        shown = [w.cget("text") for w in every_widget(app.body) if isinstance(w, ctk.CTkLabel)]
        assert not any("Travel" in text or "Standard" in text for text in shown), shown
    finally:
        app.close_application()


def set_round_word(app, word):
    """Put ``word`` in the saved round, so a test can name the letters it guesses."""
    from src.db.transaction import transaction

    with transaction(app.practice.db_path) as connection:
        payload = app.practice._read(connection, app.user["id"])
        payload["round"]["word"] = word
        app.practice._write(connection, app.user["id"], payload)
    app.show_practice()
    app.update()


def start_level_round(app, language, level, word):
    """Start a session on ``word`` and return the round as the board draws it."""
    from src.models.game_round import GameRound

    app.show_practice()
    app.language.set(language)
    app.level.set(level)
    app.start_session()
    set_round_word(app, word)
    return GameRound(**app.payload["round"])


def click_key(app, letter):
    board = app.board
    _, _, (left, top, right, bottom) = board._keys[letter]
    factor = board.scaling()
    board.event_generate(
        "<Button-1>",
        x=round((left + right) / 2 * factor),
        y=round((top + bottom) / 2 * factor),
        when="now",
    )
    app.update()


def plain_keys_reveal_accented_letters(data):
    """The board is plain A-Z, and a plain letter fills in every accented form of it."""
    from src.models.game_round import GameRound

    app = signed_in_app(data)
    try:
        start_level_round(app, "Spanish", "Beginner", "niño")
        assert sorted(app.board._keys) == list("abcdefghijklmnopqrstuvwxyz")
        click_key(app, "n")
        state = GameRound(**app.payload["round"])
        assert state.masked_letters == ["n", "_", "ñ", "_"], state.masked_letters
        assert app.board._keys["n"][1], "the key should be marked used"
        app.practice.discard(app.user["id"])

        start_level_round(app, "German", "Beginner", "Straße")
        click_key(app, "s")
        state = GameRound(**app.payload["round"])
        assert state.masked_letters == ["S", "_", "_", "_", "ß", "_"], state.masked_letters
    finally:
        app.close_application()


def board_stays_put_whatever_the_feedback_says(data):
    """D-33: a long feedback line must not move the keys under the mouse."""
    from src.utils.feedback_lines import CORRECT_LINES, INCORRECT_LINES

    app = signed_in_app(data)
    try:
        app.show_practice()
        app.start_session()
        app.update()
        lines = sorted(CORRECT_LINES + INCORRECT_LINES, key=len)
        seen = set()
        for line in lines:
            app.board_status.configure(text=line)
            app.update()
            app.update()
            seen.add((app.board.winfo_width(), app.board._keys["a"][2]))
        assert len(seen) == 1, f"the board moved: {sorted(seen)}"
    finally:
        app.close_application()


def clues_leave_the_card_border_alone(data):
    """D-35: the clue lines sit inside the card, so its border stays unbroken."""
    app = signed_in_app(data)
    try:
        app.show_practice()
        app.start_session()
        app.update()
        clues, panel = app.board_clues, app.board_clues.master
        assert clues.winfo_x() > 0
        assert clues.winfo_x() + clues.winfo_width() < panel.winfo_width()
    finally:
        app.close_application()


def long_phrases_fit_the_board_at_minimum_size(data):
    """The longest words wrap at spaces and stay inside the canvas at every size."""
    from src.desktop.application import MINIMUM_WINDOW

    app = signed_in_app(data)
    try:
        for size, factor in EMULATED:
            emulate(app, size, factor)
            app.geometry(f"{MINIMUM_WINDOW[0]}x{MINIMUM_WINDOW[1]}")
            for word in ("Espíritu de la época", "Idiosincráticamente", "Von großer Schönheit"):
                state = start_level_round(app, "Spanish", "Expert", word)
                board = app.board
                left, _, right, bottom = board.bbox("all")
                assert 0 <= left and right <= board.winfo_width(), (word, size, right)
                assert bottom <= int(board.cget("height")) + 2, (word, size, bottom)
                assert state.masked_letters.count("_") == sum(c.isalpha() for c in word)
                app.practice.discard(app.user["id"])
    finally:
        app.close_application()
        ctk.set_window_scaling(1.0)
        ctk.set_widget_scaling(1.0)


def level_word_card_shows_its_clues(data):
    app = signed_in_app(data)
    try:
        app.show_practice()
        app.language.set("German")
        app.start_session()
        word = app.payload["round"]["word"]
        for letter in sorted({c.lower() for c in word if c.isalpha()}):
            app.guess_letter(letter)
        app.update()
        assert app.payload["round"]["saved"]
        shown = [w.cget("text") for w in every_widget(app.body) if isinstance(w, ctk.CTkLabel)]
        assert word in shown
        assert "Synonyms" in shown and "Association" in shown
        assert "Example" not in shown and not any(t.startswith("Say it like") for t in shown)
        title = next(t for t in shown if t.startswith("German"))
        assert title == "German · Beginner · Easy"
    finally:
        app.close_application()


def endless_play_runs_until_end_session(data):
    """More rounds than the old longest session, then End session goes straight to Reports."""
    from src.services.desktop_storage import progress_report

    app = signed_in_app(data)
    try:
        app.show_practice()
        app.start_session()
        for number in range(1, 13):
            app.update()
            shown = [w.cget("text") for w in every_widget(app.body) if isinstance(w, ctk.CTkLabel)]
            assert f"Round {number}" in shown, shown
            for letter in sorted(set(app.payload["round"]["word"])):
                app.guess_letter(letter)
            assert app.payload["next_round"], f"round {number} should lead to another"
            if number < 12:
                app.advance()
        widgets = list(every_widget(app.body))
        assert not any(isinstance(widget, ctk.CTkProgressBar) for widget in widgets)
        ending = [
            widget
            for widget in widgets
            if isinstance(widget, ctk.CTkButton) and widget.cget("text") == "End session"
        ]
        assert len(ending) == 1
        ending[0].invoke()
        app.update()
        assert app.page == "Reports" and app.practice.load(app.user["id"]) is None
        report = progress_report(app.db_path, app.user["id"])
        assert (report["rounds"], report["sessions"]) == (12, 1), report
    finally:
        app.close_application()


SCENARIOS = {
    function.__name__: function
    for function in (
        practice_dropdowns_change_from_the_keyboard,
        text_size_dropdown_and_shortcuts,
        text_size_after_dropdown_is_destroyed,
        focused_control_scrolls_into_view,
        window_opens_inside_the_work_area,
        window_stays_inside_a_narrow_work_area,
        automatic_backup_failure_does_not_block_start_up,
        recovery_window_fits_at_minimum_size,
        main_window_text_wraps_at_minimum_size,
        letter_keys_guess_on_click,
        removed_screens_and_settings_stay_removed,
        plain_keys_reveal_accented_letters,
        board_stays_put_whatever_the_feedback_says,
        clues_leave_the_card_border_alone,
        long_phrases_fit_the_board_at_minimum_size,
        level_word_card_shows_its_clues,
        endless_play_runs_until_end_session,
    )
}

if __name__ == "__main__":
    name, data_dir = sys.argv[1], Path(sys.argv[2])
    data_dir.mkdir(parents=True, exist_ok=True)
    try:
        SCENARIOS[name](data_dir)
    except Exception:  # noqa: BLE001 - report every failure to the parent test
        traceback.print_exc()
        sys.exit(1)
    print(f"PASSED {name}")
