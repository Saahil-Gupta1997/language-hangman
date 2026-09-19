"""Keyboard operability and window fit (D-22 to D-25).

Tk delivers generated key events only to the window with OS focus, and taking focus would
interrupt whoever is using the machine. These tests therefore check that each key is bound
and run the bound actions directly. They are not evidence of real keyboard, focus-visibility
or screen-reader behaviour; those are the manual checks in docs/ACCEPTANCE.md.
"""

import pytest
from conftest import require_display


@pytest.fixture
def app(tmp_path):
    require_display()
    from src.desktop.application import HangmanDesktop

    window = HangmanDesktop(tmp_path / "app.db", tmp_path)
    window.show_login(register=True)
    window.username_entry.insert(0, "keys")
    window.password_entry.insert(0, "keys-password-1")
    window.confirm_entry.insert(0, "keys-password-1")
    window.authenticate(register=True)
    yield window
    window.close_application()


KEYS = {"<Key-Up>", "<Key-Down>", "<Key-Left>", "<Key-Right>", "<Key-Return>", "<Key-space>"}


def press(menu, key):
    assert KEYS <= set(menu._canvas.bind())
    menu.keyboard_step({"<Down>": 1, "<Up>": -1}[key])


def test_practice_dropdowns_are_reachable_and_change_from_the_keyboard(app):
    app.show_practice()
    for menu, first, second in (
        (app.situation, "Restaurant", "Airport"),
        (app.mode, "Easy", "Hard"),
        (app.rounds, "3", "5"),
        (app.focus, "Standard", "Review"),
    ):
        assert str(menu._canvas.cget("takefocus")) == "1"
        assert menu.get() == first
        press(menu, "<Down>")
        assert menu.get() == second
        press(menu, "<Up>")
        assert menu.get() == first


def test_text_size_dropdown_and_shortcuts(app):
    from customtkinter.windows.widgets.scaling import ScalingTracker

    app.show_settings()
    import customtkinter as ctk

    menu = next(w for w in app.body.winfo_children() if isinstance(w, ctk.CTkOptionMenu))
    press(menu, "<Down>")
    assert app.scale == "Large" and ScalingTracker.widget_scaling == 1.15
    press(menu, "<Up>")
    assert app.scale == "Standard" and ScalingTracker.widget_scaling == 1.0
    bound = set(app.bind())
    for sequence in ("<Control-Key-equal>", "<Control-Key-KP_Add>", "<Control-Key-KP_Subtract>"):
        assert sequence in bound


def test_focused_control_below_the_fold_scrolls_into_view(app):
    import customtkinter as ctk

    from src.desktop.application import MINIMUM_WINDOW

    app.logout()
    app.geometry(f"{MINIMUM_WINDOW[0]}x{MINIMUM_WINDOW[1]}")
    app.show_login(register=True)
    app.update()
    last = [w for w in app.body.winfo_children() if isinstance(w, ctk.CTkButton)][-1]
    # Fire the focus binding directly; focus_force() would take OS focus from other apps.
    last._canvas.event_generate("<FocusIn>", when="now")
    app.update()
    canvas = app.body._parent_canvas
    visible_top = app.body._parent_canvas.winfo_rooty() - app.body.winfo_rooty()
    top = last.winfo_rooty() - app.body.winfo_rooty()
    assert visible_top <= top and top + last.winfo_height() <= visible_top + canvas.winfo_height()


def test_window_opens_inside_the_screen_work_area(app):
    import ctypes
    from ctypes import wintypes

    from src.desktop.widgets import _work_area

    area = _work_area()
    if area is None:
        pytest.skip("Work area is only measured on Windows.")
    user32 = ctypes.windll.user32
    user32.GetAncestor.restype = wintypes.HWND
    hwnd = user32.GetAncestor(wintypes.HWND(app.winfo_id()), 2)
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    left, top, right, bottom = area
    assert rect.left >= left and rect.top >= top
    assert rect.right <= right and rect.bottom <= bottom
