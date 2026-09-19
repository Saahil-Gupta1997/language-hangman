"""Native desktop app: profiles, durable practice, reports and local recovery."""

from __future__ import annotations

from tkinter import ttk

import customtkinter as ctk

from src.services.curated_content import CuratedWordService
from src.services.desktop_storage import (
    progress_report,
)

BLUE = "#155E75"


class ReportsView:
    def show_words(self):
        self.clear("Words")
        self.heading(
            "Word cards",
            "English definitions and examples · Approximate pronunciation "
            "spelling · Independent educator review is still pending.",
        )
        for word in CuratedWordService(self.active_db).get_words("english"):
            self.text(
                f"{word['word']} · {word['category']} · {', '.join(word['situations'])}", bold=True
            )
            self.text(
                f"{word['meaning']}\n{word['example_sentence']}\n"
                f"Pronunciation: {word['pronunciation_text']}\n{word['usage_note']}"
            )

    def show_reports(self):
        self.clear("Reports")
        self.heading("Your progress", "All time · Current local profile · Completed rounds only")
        data = progress_report(self.active_db, self.user["id"])
        self.text(
            f"Rounds: {data['rounds']}   Wins: {data['wins']}   Losses: {data['losses']}\n"
            f"Completed sessions: {data['sessions']}   Distinct words: {data['words']}",
            bold=True,
        )
        self.text(
            f"Round win rate: {data['win_rate']:.1f}% = wins / completed rounds\n"
            f"Letter accuracy: {data['guess_accuracy']:.1f}% = "
            f"{data['correct_guesses']} correct guesses / {data['guesses']} accepted guesses\n"
            "Repeated and invalid guesses are excluded. Empty histories display 0%.\n"
            "These describe game performance, not retained vocabulary or language proficiency."
        )
        frame = ctk.CTkFrame(self.body)
        frame.pack(fill="both", expand=True, padx=22, pady=12)
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
        table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
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
