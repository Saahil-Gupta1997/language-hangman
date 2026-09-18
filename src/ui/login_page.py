"""CustomTkinter login window used by the desktop launcher."""

from __future__ import annotations

from collections.abc import Callable
from tkinter import Canvas, messagebox

import customtkinter as ctk

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")


class LoginPage(ctk.CTk):
    def __init__(
        self,
        on_sign_in: Callable[[str, str, bool], None] | None = None,
        on_create_account: Callable[[], None] | None = None,
        on_guest: Callable[[], None] | None = None,
    ):
        super().__init__()

        self.on_sign_in = on_sign_in
        self.on_create_account = on_create_account
        self.on_guest = on_guest

        self.title("Language Learning Hangman")
        self.geometry("1400x900")
        self.minsize(1200, 760)
        self.configure(fg_color="#f7f8f5")

        self.green = "#00452f"
        self.dark_green = "#003d2a"
        self.soft_green = "#e9f3e8"
        self.text_dark = "#143d30"
        self.text_muted = "#4b5563"

        self.build_window()

    def build_window(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.build_title_bar()
        self.build_left_panel()
        self.build_right_panel()

    def build_title_bar(self):
        title_bar = ctk.CTkFrame(
            self,
            height=70,
            fg_color="#ffffff",
            corner_radius=0,
            border_width=1,
            border_color="#d9ddd8",
        )
        title_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        title_bar.grid_columnconfigure(1, weight=1)

        logo = ctk.CTkLabel(
            title_bar,
            text="LH",
            width=38,
            height=38,
            fg_color=self.green,
            text_color="white",
            corner_radius=10,
            font=("Segoe UI", 14, "bold"),
        )
        logo.grid(row=0, column=0, padx=(36, 14), pady=16)

        title = ctk.CTkLabel(
            title_bar,
            text="Language Learning Hangman",
            text_color=self.text_dark,
            font=("Segoe UI", 20, "bold"),
        )
        title.grid(row=0, column=1, sticky="w")

        controls = ctk.CTkLabel(
            title_bar,
            text="—     □     ✕",
            text_color="#111827",
            font=("Segoe UI", 22),
        )
        controls.grid(row=0, column=2, padx=32)

    def build_left_panel(self):
        left = ctk.CTkFrame(self, fg_color="#eff5e9", corner_radius=0)
        left.grid(row=1, column=0, sticky="nsew")
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        canvas = Canvas(left, bg="#eff5e9", highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")

        def draw_scene(event=None):
            canvas.delete("all")
            w = canvas.winfo_width()
            h = canvas.winfo_height()

            # Background hills
            canvas.create_oval(-150, h - 260, w * 0.55, h + 180, fill="#cfe4c4", outline="")
            canvas.create_oval(w * 0.35, h - 300, w + 220, h + 160, fill="#b8d8ad", outline="")
            canvas.create_oval(-120, h - 150, w + 120, h + 220, fill="#78b873", outline="")

            # Clouds
            self.draw_cloud(canvas, w * 0.70, 140, 1.0)
            self.draw_cloud(canvas, w * 0.82, 330, 0.9)

            # Main text
            canvas.create_text(
                95,
                90,
                text="Play.\nLearn.\nGet Fluent.",
                anchor="nw",
                fill=self.green,
                font=("Segoe UI", 58, "bold"),
                justify="left",
            )

            canvas.create_line(
                100,
                345,
                150,
                345,
                fill="#6caf6c",
                width=5,
                capstyle="round",
            )

            canvas.create_text(
                100,
                375,
                text="Improve your vocabulary and\nlanguage skills with the classic\nHangman game.",
                anchor="nw",
                fill="#374151",
                font=("Segoe UI", 22),
                justify="left",
                spacing=8,
            )

            # Hangman stand
            base_x = 110
            base_y = h - 250
            canvas.create_rectangle(
                base_x,
                base_y,
                base_x + 170,
                base_y + 18,
                fill="#70410f",
                outline="",
            )
            canvas.create_rectangle(
                base_x + 25,
                base_y - 235,
                base_x + 45,
                base_y,
                fill="#70410f",
                outline="",
            )
            canvas.create_rectangle(
                base_x + 25,
                base_y - 235,
                base_x + 195,
                base_y - 220,
                fill="#70410f",
                outline="",
            )
            canvas.create_line(
                base_x + 185,
                base_y - 220,
                base_x + 185,
                base_y - 170,
                fill="#70410f",
                width=5,
            )
            canvas.create_line(
                base_x + 45,
                base_y - 220,
                base_x + 90,
                base_y - 175,
                fill="#70410f",
                width=10,
            )

            # Hangman body
            cx = base_x + 185
            cy = base_y - 125
            canvas.create_oval(cx - 23, cy - 65, cx + 23, cy - 20, outline=self.green, width=5)
            canvas.create_line(cx, cy - 20, cx, cy + 48, fill=self.green, width=5)
            canvas.create_line(cx, cy + 5, cx - 34, cy + 34, fill=self.green, width=5)
            canvas.create_line(cx, cy + 5, cx + 34, cy + 34, fill=self.green, width=5)
            canvas.create_line(cx, cy + 48, cx - 35, cy + 95, fill=self.green, width=5)
            canvas.create_line(cx, cy + 48, cx + 35, cy + 95, fill=self.green, width=5)

            # Word tiles
            start_x = w * 0.52
            tile_y = h - 385
            letters = ["_", "A", "N", "G", "_", "A", "N"]

            for i, letter in enumerate(letters):
                x = start_x + i * 42
                canvas.create_rectangle(
                    x,
                    tile_y,
                    x + 34,
                    tile_y + 48,
                    fill="#ffffff",
                    outline="#dfe8dc",
                    width=2,
                )
                canvas.create_text(
                    x + 17,
                    tile_y + 24,
                    text=letter,
                    fill=self.green,
                    font=("Segoe UI", 22, "bold"),
                )

            canvas.create_text(
                start_x + 10,
                tile_y + 90,
                text="_  _  _  _  _  _",
                anchor="nw",
                fill=self.green,
                font=("Segoe UI", 30, "bold"),
            )

            # Tip card
            card_x = 100
            card_y = h - 185
            canvas.create_rectangle(
                card_x,
                card_y,
                card_x + 360,
                card_y + 95,
                fill="#f8fbf4",
                outline="#d8e6d1",
                width=1,
            )
            canvas.create_oval(
                card_x + 25,
                card_y + 22,
                card_x + 85,
                card_y + 82,
                fill=self.green,
                outline="",
            )
            canvas.create_text(
                card_x + 55,
                card_y + 52,
                text="☼",
                fill="white",
                font=("Segoe UI", 28, "bold"),
            )
            canvas.create_text(
                card_x + 105,
                card_y + 25,
                text="Tip: Think of common words\nand practice every day!",
                anchor="nw",
                fill=self.text_dark,
                font=("Segoe UI", 17),
                spacing=7,
            )

        canvas.bind("<Configure>", draw_scene)

    def draw_cloud(self, canvas, x, y, scale=1):
        canvas.create_oval(
            x,
            y + 20 * scale,
            x + 70 * scale,
            y + 70 * scale,
            fill="white",
            outline="",
        )
        canvas.create_oval(
            x + 35 * scale,
            y,
            x + 105 * scale,
            y + 75 * scale,
            fill="white",
            outline="",
        )
        canvas.create_oval(
            x + 80 * scale,
            y + 25 * scale,
            x + 145 * scale,
            y + 72 * scale,
            fill="white",
            outline="",
        )

    def build_right_panel(self):
        right = ctk.CTkFrame(self, fg_color="#fafafa", corner_radius=0)
        right.grid(row=1, column=1, sticky="nsew")
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(
            right,
            width=640,
            fg_color="#ffffff",
            corner_radius=22,
            border_width=1,
            border_color="#e5e7eb",
        )
        card.grid(row=0, column=0, padx=48, pady=38, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        logo = ctk.CTkLabel(
            card,
            text="LH",
            width=50,
            height=50,
            fg_color=self.green,
            text_color="white",
            corner_radius=25,
            font=("Segoe UI", 16, "bold"),
        )
        logo.grid(row=0, column=0, pady=(30, 12))

        heading = ctk.CTkLabel(
            card,
            text="Welcome back!",
            text_color=self.green,
            font=("Segoe UI", 28, "bold"),
        )
        heading.grid(row=1, column=0)

        subheading = ctk.CTkLabel(
            card,
            text="Sign in to continue your language journey.",
            text_color="#4b5563",
            font=("Segoe UI", 17),
        )
        subheading.grid(row=2, column=0, pady=(6, 30))

        self.build_tabs(card)
        self.build_form(card)

    def build_tabs(self, parent):
        tabs = ctk.CTkFrame(parent, fg_color="transparent")
        tabs.grid(row=3, column=0, sticky="ew", padx=40)
        tabs.grid_columnconfigure((0, 1), weight=1)

        sign_in = ctk.CTkLabel(
            tabs,
            text="Sign In",
            text_color=self.green,
            font=("Segoe UI", 17, "bold"),
        )
        sign_in.grid(row=0, column=0, pady=(0, 10))

        create = ctk.CTkLabel(
            tabs,
            text="Create Account",
            text_color="#374151",
            font=("Segoe UI", 17, "bold"),
        )
        create.grid(row=0, column=1, pady=(0, 10))
        create.bind("<Button-1>", lambda _event: self.handle_create_account())

        underline = ctk.CTkFrame(tabs, height=3, fg_color=self.green)
        underline.grid(row=1, column=0, sticky="ew")

        line = ctk.CTkFrame(tabs, height=1, fg_color="#d8dee4")
        line.grid(row=1, column=1, sticky="ew")

    def build_form(self, parent):
        form = ctk.CTkFrame(parent, fg_color="transparent")
        form.grid(row=4, column=0, sticky="ew", padx=40, pady=(25, 0))
        form.grid_columnconfigure(0, weight=1)

        username_label = ctk.CTkLabel(
            form,
            text="Username or Email",
            anchor="w",
            text_color="#111827",
            font=("Segoe UI", 15, "bold"),
        )
        username_label.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self.username = ctk.CTkEntry(
            form,
            height=56,
            placeholder_text="  👤   Enter your username or email",
            font=("Segoe UI", 16),
            corner_radius=9,
            border_color="#d1d5db",
            fg_color="#ffffff",
        )
        self.username.grid(row=1, column=0, sticky="ew")

        password_label = ctk.CTkLabel(
            form,
            text="Password",
            anchor="w",
            text_color="#111827",
            font=("Segoe UI", 15, "bold"),
        )
        password_label.grid(row=2, column=0, sticky="ew", pady=(24, 8))

        self.password = ctk.CTkEntry(
            form,
            height=56,
            placeholder_text="  🔒   Enter your password",
            show="*",
            font=("Segoe UI", 16),
            corner_radius=9,
            border_color="#d1d5db",
            fg_color="#ffffff",
        )
        self.password.grid(row=3, column=0, sticky="ew")

        options = ctk.CTkFrame(form, fg_color="transparent")
        options.grid(row=4, column=0, sticky="ew", pady=(18, 18))
        options.grid_columnconfigure(1, weight=1)

        self.remember = ctk.CTkCheckBox(
            options,
            text="Remember me",
            text_color="#374151",
            font=("Segoe UI", 15),
            fg_color=self.green,
            hover_color=self.green,
            border_color="#cbd5e1",
        )
        self.remember.grid(row=0, column=0, sticky="w")

        forgot = ctk.CTkLabel(
            options,
            text="Forgot password?",
            text_color=self.green,
            font=("Segoe UI", 15),
        )
        forgot.grid(row=0, column=2, sticky="e")

        sign_in_btn = ctk.CTkButton(
            form,
            text="↪   Sign In",
            height=60,
            fg_color=self.green,
            hover_color="#006144",
            corner_radius=9,
            font=("Segoe UI", 18, "bold"),
            command=self.handle_sign_in,
        )
        sign_in_btn.grid(row=5, column=0, sticky="ew")

        divider = ctk.CTkFrame(form, fg_color="transparent")
        divider.grid(row=6, column=0, sticky="ew", pady=22)
        divider.grid_columnconfigure((0, 2), weight=1)

        ctk.CTkFrame(divider, height=1, fg_color="#e5e7eb").grid(
            row=0,
            column=0,
            sticky="ew",
        )
        ctk.CTkLabel(
            divider,
            text="or",
            width=36,
            height=36,
            fg_color="#ffffff",
            text_color="#6b7280",
            corner_radius=18,
            font=("Segoe UI", 14),
        ).grid(row=0, column=1, padx=8)
        ctk.CTkFrame(divider, height=1, fg_color="#e5e7eb").grid(
            row=0,
            column=2,
            sticky="ew",
        )

        guest_card = ctk.CTkFrame(form, fg_color="#edf5ea", corner_radius=12)
        guest_card.grid(row=7, column=0, sticky="ew")
        guest_card.grid_columnconfigure(0, weight=1)

        guest_text = ctk.CTkFrame(guest_card, fg_color="transparent")
        guest_text.grid(row=0, column=0, sticky="w", padx=22, pady=18)

        ctk.CTkLabel(
            guest_text,
            text="Practice as guest",
            text_color=self.green,
            font=("Segoe UI", 19, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            guest_text,
            text="Try the game without creating an account.",
            text_color="#4b5563",
            font=("Segoe UI", 14),
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        demo_btn = ctk.CTkButton(
            guest_card,
            text="🎮   Try Demo Game   ›",
            width=230,
            height=56,
            fg_color="#f8fbf4",
            hover_color="#e4efe1",
            border_width=1,
            border_color=self.green,
            text_color=self.green,
            corner_radius=8,
            font=("Segoe UI", 16, "bold"),
            command=self.handle_guest,
        )
        demo_btn.grid(row=0, column=1, padx=16)

        terms = ctk.CTkLabel(
            form,
            text="🛡  By signing in, you agree to our Terms of Service and Privacy Policy.",
            text_color="#4b5563",
            font=("Segoe UI", 13),
        )
        terms.grid(row=8, column=0, pady=(26, 20))

    def handle_sign_in(self) -> None:
        if self.on_sign_in is None:
            return
        self.on_sign_in(
            self.username.get(),
            self.password.get(),
            bool(self.remember.get()),
        )

    def handle_create_account(self) -> None:
        # TODO: Add a CustomTkinter registration panel if the desktop app needs one.
        if self.on_create_account is None:
            messagebox.showinfo(
                "Create Account",
                "Create account is available in the Streamlit app for now.",
            )
            return
        self.on_create_account()

    def handle_guest(self) -> None:
        if self.on_guest is None:
            messagebox.showinfo(
                "Demo Game",
                "Guest/demo play is not available in this local beta yet.",
            )
            return
        self.on_guest()

    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str) -> None:
        messagebox.showinfo(title, message)


if __name__ == "__main__":
    app = LoginPage()
    app.mainloop()
