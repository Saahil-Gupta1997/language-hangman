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
            (app.situation, "Restaurant", "Airport"),
            (app.mode, "Easy", "Hard"),
            (app.rounds, "3", "5"),
            (app.focus, "Standard", "Review"),
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


def focused_control_scrolls_into_view(data):
    from src.desktop.application import MINIMUM_WINDOW

    app = signed_in_app(data)
    try:
        app.logout()
        app.geometry(f"{MINIMUM_WINDOW[0]}x{MINIMUM_WINDOW[1]}")
        app.show_login(register=True)
        app.update()
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


SCENARIOS = {
    function.__name__: function
    for function in (
        practice_dropdowns_change_from_the_keyboard,
        text_size_dropdown_and_shortcuts,
        text_size_after_dropdown_is_destroyed,
        focused_control_scrolls_into_view,
        window_opens_inside_the_work_area,
        automatic_backup_failure_does_not_block_start_up,
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
