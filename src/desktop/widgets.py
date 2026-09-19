"""Widget helpers shared by the main window and the recovery window."""

import customtkinter as ctk

BLUE = "#155E75"
FOCUS_RING = "#F59E0B"


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
    button.bind(
        "<FocusIn>", lambda event: button.configure(border_width=3, border_color=FOCUS_RING)
    )
    button.bind("<FocusOut>", lambda event: button.configure(border_width=0))
    return button
