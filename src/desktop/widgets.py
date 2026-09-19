"""Widget helpers shared by the main window and the recovery window."""

import sys

import customtkinter as ctk
from customtkinter.windows.widgets.scaling import ScalingTracker

BLUE = "#155E75"
FOCUS_RING = "#F59E0B"
TITLE_BAR_ALLOWANCE = 48  # logical pixels for the title bar and window borders


def _work_area():
    """Return the desktop work area (excluding the taskbar) in physical pixels, if known."""
    if sys.platform != "win32":
        return None
    import ctypes
    from ctypes import wintypes

    area = wintypes.RECT()
    if not ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(area), 0):
        return None
    return area.left, area.top, area.right, area.bottom


def fit_to_work_area(window, width, height, minimum):
    """Open ``window`` at up to ``width`` x ``height`` (logical), shrunk to fit the screen.

    At 150% display scaling a 1080p screen has about 672 logical pixels of height, so a
    fixed 760-pixel window would open with its bottom off-screen. Call after the window
    exists: the process is then DPI aware and the work area is in physical pixels.
    """
    window.minsize(*minimum)
    area = _work_area()
    if area is None:
        window.geometry(f"{width}x{height}")
        return
    left, top, right, bottom = area
    scaling = ScalingTracker.get_window_scaling(window)
    width = max(minimum[0], min(width, int((right - left) / scaling) - 16))
    height = max(minimum[1], min(height, int((bottom - top) / scaling) - TITLE_BAR_ALLOWANCE))
    # CustomTkinter scales width and height but not the position, which stays physical.
    x = left + max(0, (right - left - round(width * scaling)) // 2)
    y = top + max(0, (bottom - top - round((height + TITLE_BAR_ALLOWANCE) * scaling)) // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


def scroll_into_view(widget):
    """Scroll the enclosing scrollable frame so a newly focused widget is visible.

    CustomTkinter's scrollable frame does not follow keyboard focus, so at small window
    sizes Tab could otherwise move the focus ring below the visible area.
    """
    frame = widget.master
    while frame is not None and not isinstance(frame, ctk.CTkScrollableFrame):
        frame = frame.master
    if frame is None:
        return
    frame.update_idletasks()
    content = frame.winfo_height()
    if content <= 0:
        return
    canvas = frame._parent_canvas
    top = widget.winfo_rooty() - frame.winfo_rooty()
    bottom = top + widget.winfo_height()
    first, last = canvas.yview()
    visible_top, visible_bottom = first * content, last * content
    if top < visible_top:
        canvas.yview_moveto(max(0, top - 12) / content)
    elif bottom > visible_bottom:
        canvas.yview_moveto(max(0, bottom + 12 - (visible_bottom - visible_top)) / content)


def keyboard_option_menu(parent, values, command=None, width=200):
    """Return an option menu that Tab reaches, shows focus and changes from the keyboard.

    CustomTkinter's option menu responds only to the mouse. Up/Down (or Left/Right) pick the
    previous/next value; Enter or Space opens the list, which Windows then navigates with
    the arrow keys, Enter and Escape.
    """
    menu = ctk.CTkOptionMenu(parent, values=list(values), command=command, width=width)
    menu._canvas.configure(takefocus=1)
    normal = {key: menu.cget(key) for key in ("fg_color", "button_color", "text_color")}

    def step(offset):
        current = menu.get()
        index = values.index(current) if current in values else 0
        choice = values[(index + offset) % len(values)]
        menu.set(choice)
        if command:
            command(choice)
        return "break"

    def open_list(event):
        menu._open_dropdown_menu()
        return "break"

    def focus_in(event):
        menu.configure(fg_color=FOCUS_RING, button_color="#B45309", text_color="#1F2937")
        scroll_into_view(menu)

    for key, offset in (("<Up>", -1), ("<Left>", -1), ("<Down>", 1), ("<Right>", 1)):
        menu._canvas.bind(key, lambda event, offset=offset: step(offset))
    menu._canvas.bind("<Return>", open_list)
    menu._canvas.bind("<space>", open_list)
    menu._canvas.bind("<FocusIn>", focus_in)
    menu._canvas.bind("<FocusOut>", lambda event: menu.configure(**normal))
    menu.keyboard_step = step  # the Up/Down action, exposed for tests that cannot take focus
    return menu


def keyboard_button(parent, label, command, width=180):
    """Return a button that takes Tab focus, shows a focus ring and activates on Enter/Space."""
    button = ctk.CTkButton(
        parent,
        text=label,
        command=command,
        width=width,
        height=38,
        fg_color=BLUE,
        hover_color="#0E4657",
        font=("Arial", 14),
    )
    # CTk's canvas must be explicitly focusable for keyboard activation.
    button._canvas.configure(takefocus=1)

    def activate(event):
        button.invoke()
        return "break"

    button.bind("<Return>", activate)
    button.bind("<space>", activate)

    def focus_in(event):
        button.configure(border_width=3, border_color=FOCUS_RING)
        scroll_into_view(button)

    button.bind("<FocusIn>", focus_in)
    button.bind("<FocusOut>", lambda event: button.configure(border_width=0))
    return button
