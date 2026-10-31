"""Widget helpers shared by the main window and the recovery window."""

import sys

import customtkinter as ctk
from customtkinter.windows.widgets.scaling import ScalingTracker

BLUE = "#155E75"
FOCUS_RING = "#F59E0B"
TITLE_BAR_ALLOWANCE = 48  # logical pixels for the title bar and window borders

# Design tokens. One brand colour, one neutral ramp, and three button weights, so that the
# primary action on a screen is never drawn like its navigation (UI review, 2026-11-01).
BRAND, BRAND_DARK, BRAND_TINT = "#155E75", "#0E4657", "#DCE7EC"
INK, MUTED, FAINT = "#0F172A", "#475569", "#94A3B8"
SURFACE, CANVAS, BORDER = "#FFFFFF", "#EEF2F6", "#CBD5E1"
SUCCESS, DANGER, WARNING_INK = "#15803D", "#B91C1C", "#92400E"
SPACE = 8  # spacing unit: paddings are multiples of this

_FAMILY = None


def ui_font(size=15, bold=False):
    """Return the best available UI font at ``size``, preferring the Windows system face."""
    global _FAMILY
    if _FAMILY is None:
        try:
            import tkinter.font

            available = set(tkinter.font.families())
        except Exception:  # noqa: BLE001 - no root yet or a headless build
            available = set()
        _FAMILY = next(
            (name for name in ("Segoe UI Variable Text", "Segoe UI", "Arial") if name in available),
            "Arial",
        )
    return (_FAMILY, size, "bold") if bold else (_FAMILY, size)


BUTTON_VARIANTS = {
    # fg, hover, text, border width, border colour
    "primary": (BRAND, BRAND_DARK, "white", 0, BRAND),
    "secondary": (SURFACE, BRAND_TINT, BRAND, 2, BORDER),
    "quiet": ("transparent", BRAND_TINT, MUTED, 0, BORDER),
    "nav": ("transparent", BRAND_TINT, BRAND, 0, BRAND),
    "nav_active": (BRAND, BRAND_DARK, "white", 0, BRAND),
    "danger": (SURFACE, "#FEE2E2", DANGER, 2, "#FCA5A5"),
}


def release_window(window):
    """Destroy a CustomTkinter root without leaving its timers or tracker entries behind.

    CustomTkinter schedules timers that would otherwise fire after the window is gone
    ("invalid command name ..." noise), and its scaling tracker keeps a reference to every
    root it has seen, so the recovery-then-start path would keep the first window alive.
    """
    import tkinter

    try:
        for identifier in window.tk.call("after", "info"):
            window.after_cancel(identifier)
    except tkinter.TclError:
        pass
    try:
        window.destroy()
    except tkinter.TclError:
        pass
    ScalingTracker.window_widgets_dict.pop(window, None)
    ScalingTracker.window_dpi_scaling_dict.pop(window, None)


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


def wrap_to_width(label):
    """Wrap a label's text to the width it is actually given, not a fixed pixel count.

    A fixed ``wraplength`` clips text on the right whenever the label is narrower than
    assumed: a smaller window, Large text or higher display scaling (D-31). The label must
    be packed or gridded to fill the available width. CustomTkinter scales ``wraplength``
    itself, so it is set in logical pixels, less the label's rounded-corner padding.
    """
    import tkinter

    def rewrap(event):
        scaling = label._apply_widget_scaling(1.0)
        wrap = max(120, int(event.width / scaling) - 2 * label._corner_radius)
        if wrap != label.cget("wraplength"):
            label.configure(wraplength=wrap)

    # CTkLabel.bind targets its inner canvas and text label; the outer frame has the width.
    tkinter.Frame.bind(label, "<Configure>", rewrap, "+")
    return label


def saved_text_size(data_dir):
    """Return the saved text size ("Standard" or "Large"), defaulting to Standard."""
    import json
    from pathlib import Path

    try:
        size = json.loads((Path(data_dir) / "settings.json").read_text())["text_size"]
    except (OSError, ValueError, KeyError, TypeError):
        return "Standard"
    return size if size in ("Standard", "Large") else "Standard"


TEXT_SCALING = {"Standard": 1.0, "Large": 1.15}


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
    menu = ctk.CTkOptionMenu(
        parent,
        values=list(values),
        command=command,
        width=width,
        height=36,
        corner_radius=8,
        # A filled control: on a white card an unfilled one reads as plain text.
        fg_color=CANVAS,
        button_color=BRAND,
        button_hover_color=BRAND_DARK,
        text_color=INK,
        dropdown_fg_color=SURFACE,
        dropdown_text_color=INK,
        dropdown_hover_color=BRAND_TINT,
        font=ui_font(14),
        dropdown_font=ui_font(14),
    )
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


def keyboard_button(
    parent, label, command, width=180, variant="primary", height=38, font=None, takefocus=True
):
    """Return a button that takes Tab focus, shows a focus ring and activates on Enter/Space.

    ``variant`` selects one of BUTTON_VARIANTS, so a screen's primary action, its secondary
    actions and its navigation can be told apart. ``takefocus=False`` keeps a button out of
    the Tab order for controls that duplicate a keyboard route (the A–Z letter keys), so the
    keyboard journey stays the short one described in ACCEPTANCE.md.
    """
    fg, hover, text_color, border_width, border_color = BUTTON_VARIANTS[variant]
    button = ctk.CTkButton(
        parent,
        text=label,
        command=command,
        width=width,
        height=height,
        corner_radius=8,
        fg_color=fg,
        hover_color=hover,
        text_color=text_color,
        border_width=border_width,
        border_color=border_color,
        font=font or ui_font(14, bold=variant in ("primary", "nav_active")),
    )
    # CTk's canvas must be explicitly focusable for keyboard activation.
    button._canvas.configure(takefocus=1 if takefocus else 0)

    def activate(event):
        button.invoke()
        return "break"

    button.bind("<Return>", activate)
    button.bind("<space>", activate)

    def focus_in(event):
        button.configure(border_width=3, border_color=FOCUS_RING)
        scroll_into_view(button)

    def focus_out(event):
        button.configure(border_width=border_width, border_color=border_color)

    button.bind("<FocusIn>", focus_in)
    button.bind("<FocusOut>", focus_out)
    return button


def card(parent, fg_color=SURFACE, border=True):
    """A panel that groups related content: white, rounded, with a hairline border."""
    return ctk.CTkFrame(
        parent,
        fg_color=fg_color,
        corner_radius=12,
        border_width=1 if border else 0,
        border_color=BORDER,
    )


def responsive_split(parent, threshold=900, weights=(3, 2)):
    """Two panes side by side in a wide window, stacked in a narrow one.

    Returns (container, left, right). The window's supported minimum is 800 logical pixels,
    where two columns would squeeze the game board, so the panes stack instead (D-31).
    """
    container = ctk.CTkFrame(parent, fg_color="transparent")
    left = ctk.CTkFrame(container, fg_color="transparent")
    right = ctk.CTkFrame(container, fg_color="transparent")
    state = {"wide": None}

    def layout(event=None):
        try:
            factor = container._apply_widget_scaling(1.0)
        except AttributeError:
            factor = 1.0
        width = (event.width if event is not None else container.winfo_width()) / factor
        wide = width >= threshold
        if wide == state["wide"]:
            return
        state["wide"] = wide
        left.grid_forget()
        right.grid_forget()
        if wide:
            left.grid(row=0, column=0, sticky="new", padx=(0, SPACE))
            right.grid(row=0, column=1, sticky="new")
            container.grid_columnconfigure(0, weight=weights[0])
            container.grid_columnconfigure(1, weight=weights[1])
        else:
            left.grid(row=0, column=0, columnspan=2, sticky="ew")
            right.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(SPACE, 0))
            container.grid_columnconfigure(0, weight=1)
            container.grid_columnconfigure(1, weight=0)

    container.bind("<Configure>", layout)
    layout()
    return container, left, right


GALLOWS_PARTS = (
    ("oval", (84, 46, 116, 78)),  # head
    ("line", (100, 78, 100, 128)),  # body
    ("line", (100, 92, 76, 112)),  # left arm
    ("line", (100, 92, 124, 112)),  # right arm
    ("line", (100, 128, 80, 160)),  # left leg
    ("line", (100, 128, 120, 160)),  # right leg
)
LETTERS = "abcdefghijklmnopqrstuvwxyz"


class GameBoard(ctk.CTkCanvas):
    """The figure, the word, the lives and the A-Z keys, drawn on one canvas.

    Built from widgets this board was about 55 CustomTkinter widgets, and each one costs
    roughly 4 ms to create, so every guess rebuilt the screen for over a second. Drawing it
    takes a couple of milliseconds, and the layout can follow the window width exactly.

    The keys repeat the typing route for mouse users: they are not focusable, and the guess
    entry and Submit button beside the board remain ordinary widgets.
    """

    def __init__(self, parent, on_letter, background=SURFACE):
        super().__init__(parent, bg=background, highlightthickness=0, height=10)
        self.on_letter, self.background, self.state = on_letter, background, None
        self._keys, self._hovered = {}, None
        self.bind("<Configure>", lambda event: self.redraw(width=event.width))
        self.bind("<Button-1>", self._click)
        self.bind("<Motion>", self._hover)
        self.bind("<Leave>", lambda event: self._hover(None))

    def scaling(self):
        try:
            return self._apply_widget_scaling(1.0)
        except AttributeError:
            return 1.0

    def redraw(self, state=None, width=None):
        """Draw the board for ``state`` at the current width; cheap enough to call per guess."""
        if state is not None:
            self.state = state
        if self.state is None:
            return
        factor = self.scaling()
        available = (width if width is not None else self.winfo_width()) / factor
        if available <= 1:
            return
        self.delete("all")
        self._keys.clear()
        figure = 160 if available >= 430 else 0
        if figure:
            self._figure(len(self.state.wrong_letters), self.state.max_attempts, factor)
        reached = self._word(self.state, figure + 16, available - figure - 16, factor)
        height = self._letter_keys(
            self.state, available, max(reached, 150 if figure else 0) + 16, factor
        )
        self.configure(height=round(height * factor))

    def _at(self, points, factor, ratio=1.0):
        return [round(value * ratio * factor) for value in points]

    def _figure(self, wrong_count, max_wrong, factor, height=150):
        ratio = height / 180
        line = max(2, round(3 * factor))
        for frame in (
            (40, 165, 160, 165),
            (60, 165, 60, 30),
            (60, 30, 100, 30),
            (100, 30, 100, 46),
        ):
            self.create_line(
                *self._at(frame, factor, ratio),
                width=max(2, round(4 * factor)),
                fill=FAINT,
                capstyle="round",
            )
        drawn = round(len(GALLOWS_PARTS) * min(wrong_count, max_wrong) / max(1, max_wrong))
        for shape, points in GALLOWS_PARTS[:drawn]:
            scaled = self._at(points, factor, ratio)
            if shape == "oval":
                self.create_oval(*scaled, width=line, outline=INK)
            else:
                self.create_line(*scaled, width=line, fill=INK, capstyle="round")

    def _word(self, state, left, available, factor):
        """Letter tiles, then the lives. Returns the lowest y the word block reaches."""
        letters = state.masked_word.split()
        size = min(44, max(20, int(available / max(1, len(letters))) - 6))
        x = left + max(0, (available - len(letters) * (size + 6)) / 2)
        top = 34
        for letter in letters:
            revealed = letter != "_"
            self.create_rectangle(
                *self._at((x, top, x + size, top + size * 1.2), factor),
                fill=SURFACE if revealed else CANVAS,
                outline=BRAND if revealed else BORDER,
                width=max(1, round(2 * factor)),
            )
            if revealed:
                self.create_text(
                    *self._at((x + size / 2, top + size * 0.6), factor),
                    text=letter,
                    fill=BRAND,
                    font=ui_font(max(10, round(size * 0.55)), bold=True),
                )
            x += size + 6
        lives_y = top + size * 1.2 + 22
        pip, gap = 12, 6
        block = state.max_attempts * (pip + gap)
        start = left + max(0, (available - block) / 2)
        self.create_text(
            *self._at((start - 10, lives_y), factor),
            text=f"{state.remaining_attempts} of {state.max_attempts} lives",
            fill=MUTED,
            font=ui_font(14, bold=True),
            anchor="e",
        )
        for index in range(state.max_attempts):
            lit = index < state.remaining_attempts
            self.create_oval(
                *self._at((start, lives_y - pip / 2, start + pip, lives_y + pip / 2), factor),
                fill=BRAND if lit else self.background,
                outline=BRAND if lit else BORDER,
                width=max(1, round(2 * factor)),
            )
            start += pip + gap
        return lives_y + pip

    def _letter_keys(self, state, available, top, factor, columns=9):
        correct = {c for c in state.guessed_letters if c not in state.wrong_letters}
        wrong = set(state.wrong_letters)
        size = min(34, max(18, int(available / columns) - 4))
        left = max(0, (available - columns * (size + 4)) / 2)
        for index, letter in enumerate(LETTERS):
            x = left + (index % columns) * (size + 4)
            y = top + (index // columns) * (size + 4)
            used = letter in correct or letter in wrong
            variant = (
                "primary" if letter in correct else ("quiet" if letter in wrong else "secondary")
            )
            fill, _, text_colour, border, border_colour = BUTTON_VARIANTS[variant]
            box = self.create_rectangle(
                *self._at((x, y, x + size, y + size), factor),
                fill=self.background if fill == "transparent" else fill,
                outline=border_colour if border else BORDER,
                width=max(1, round((border or 1) * factor)),
            )
            self.create_text(
                *self._at((x + size / 2, y + size / 2), factor),
                text=letter.upper(),
                fill=FAINT if letter in wrong else text_colour,
                font=ui_font(max(9, round(size * 0.42)), bold=not used),
            )
            self._keys[letter] = (box, used, (x, y, x + size, y + size))
        rows = (len(LETTERS) + columns - 1) // columns
        return top + rows * (size + 4) + 6

    def _letter_at(self, event):
        factor = self.scaling()
        x, y = event.x / factor, event.y / factor
        for letter, (_, used, (left, top, right, bottom)) in self._keys.items():
            if left <= x <= right and top <= y <= bottom:
                return None if used else letter
        return None

    def _click(self, event):
        letter = self._letter_at(event)
        if letter:
            self.on_letter(letter)

    def _hover(self, event):
        letter = self._letter_at(event) if event is not None else None
        if letter == self._hovered:
            return
        for name in (self._hovered, letter):
            if name in self._keys:
                box, used, _ = self._keys[name]
                self.itemconfigure(box, fill=BRAND_TINT if name == letter and not used else SURFACE)
        self._hovered = letter
        self.configure(cursor="hand2" if letter else "")
