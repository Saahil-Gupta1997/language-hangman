"""Native desktop app: profiles, durable practice, reports and local recovery."""

from __future__ import annotations

from tkinter import ttk

import customtkinter as ctk

from src.desktop.widgets import BORDER, BRAND, INK, MUTED, SPACE, SURFACE, ui_font
from src.services.desktop_storage import (
    progress_report,
)

BLUE = "#155E75"


class ReportsView:
    def show_reports(self):
        self.clear("Reports")
        self.heading("Your progress", "All time · Current local profile · Completed rounds only")
        data = progress_report(self.active_db, self.user["id"])
        self.stat_row(
            (
                (data["rounds"], "rounds"),
                (data["wins"], "wins"),
                (data["losses"], "losses"),
                (data["sessions"], "sessions"),
                (data["words"], "distinct words"),
            )
        )
        rates = self.card(title="Rates, and what they mean")
        self.text(
            f"Round win rate: {data['win_rate']:.1f}% = wins / completed rounds",
            parent=rates,
            size=14,
            pady=(SPACE - 2, 0),
        )
        self.text(
            f"Letter accuracy: {data['guess_accuracy']:.1f}% = "
            f"{data['correct_guesses']} correct guesses / {data['guesses']} accepted guesses",
            parent=rates,
            size=14,
            pady=2,
        )
        self.text(
            "Repeated and invalid guesses are excluded. Empty histories display 0%. These "
            "describe game performance, not retained vocabulary or language proficiency.",
            parent=rates,
            size=13,
            muted=True,
            pady=(2, SPACE + 2),
        )
        self.style_table()
        frame = ctk.CTkFrame(
            self.body, fg_color=SURFACE, corner_radius=12, border_width=1, border_color=BORDER
        )
        frame.pack(fill="both", expand=True, padx=2 * SPACE, pady=SPACE)
        table = ttk.Treeview(
            frame, columns=("word", "result", "guesses", "date"), show="headings", height=12
        )
        for name, label, width in [
            ("word", "Word", 180),
            ("result", "Result", 90),
            ("guesses", "Guesses", 90),
            ("date", "Completed (UTC)", 210),
        ]:
            table.heading(name, text=label)
            table.column(name, width=width)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        table.pack(side="left", fill="both", expand=True, padx=(SPACE, 0), pady=SPACE)
        scrollbar.pack(side="right", fill="y", pady=SPACE, padx=(0, SPACE))
        for row in data["history"]:
            table.insert(
                "",
                "end",
                values=(
                    row["word"],
                    row["result"],
                    row["attempts_used"],
                    row["played_at"][:19].replace("T", " "),
                ),
            )

    def style_table(self):
        """Match the round history table to the rest of the app.

        It stays a native ttk widget: Windows screen readers can read it, unlike the
        CustomTkinter controls (RK-2).
        """
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:  # noqa: BLE001 - fall back to whatever theme Tk provides
            pass
        scaled = round(self.body._apply_widget_scaling(1.0) * 28)
        style.configure(
            "Treeview",
            background=SURFACE,
            fieldbackground=SURFACE,
            foreground=INK,
            bordercolor=BORDER,
            borderwidth=0,
            rowheight=scaled,
            font=ui_font(13),
        )
        style.configure(
            "Treeview.Heading",
            background=SURFACE,
            foreground=MUTED,
            font=ui_font(12, bold=True),
            relief="flat",
        )
        style.map("Treeview", background=[("selected", BRAND)], foreground=[("selected", "white")])
