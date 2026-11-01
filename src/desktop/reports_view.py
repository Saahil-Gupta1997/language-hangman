"""Native desktop app: profiles, durable practice, reports and local recovery."""

from __future__ import annotations

from tkinter import ttk

import customtkinter as ctk

from src.desktop.practice_view import (
    LANGUAGE_CHOICES,
    NOT_REVIEWED,
    TRAVEL_CARDS,
    word_choices,
)
from src.desktop.widgets import BORDER, BRAND, INK, MUTED, SPACE, SURFACE, ui_font
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
            "Travel cards have examples and pronunciation spelling; level lists have three "
            "clues · Independent educator review is still pending.",
        )
        filters = ctk.CTkFrame(self.card(), fg_color="transparent")
        filters.pack(fill="x", padx=2 * SPACE, pady=(SPACE + 4, SPACE))
        self.cards_language = self.setting(
            filters, 0, "Language", LANGUAGE_CHOICES, command=self.cards_language_changed
        )
        self.cards_level = self.setting(
            filters, 1, "Words", word_choices("English"), command=lambda _: self.fill_word_cards()
        )
        self.cards_panel = ctk.CTkFrame(self.body, fg_color="transparent")
        self.cards_panel.pack(fill="x")
        self.fill_word_cards()

    def cards_language_changed(self, language):
        choices = word_choices(language)
        self.cards_level.configure(values=choices)
        if self.cards_level.get() not in choices:
            self.cards_level.set(choices[0])
        self.fill_word_cards()

    def fill_word_cards(self):
        for child in self.cards_panel.winfo_children():
            child.destroy()
        words = CuratedWordService(self.active_db)
        if self.cards_level.get() == TRAVEL_CARDS:
            self.travel_word_cards(words.travel_cards())
        else:
            language, level = self.cards_language.get(), self.cards_level.get()
            self.level_word_list(words.level_words(language.lower(), level.lower()))

    def level_word_list(self, words):
        """One text box, not a card per word: about 80 cards of labels would take seconds."""
        note = f"{len(words)} words. {NOT_REVIEWED}"
        self.text(note, parent=self.cards_panel, muted=True, size=13)
        box = ctk.CTkTextbox(
            self.cards_panel,
            height=430,
            wrap="word",
            font=ui_font(14),
            fg_color=SURFACE,
            text_color=INK,
            border_color=BORDER,
            border_width=1,
            corner_radius=12,
        )
        box.tag_config("word", foreground=BRAND)
        for word in words:
            box.insert("end", f"{word['word']}\n", "word")
            box.insert(
                "end",
                f"{word['category']}\n"
                f"Meaning: {word['meaning']}\n"
                f"Synonyms: {word['synonym']}\n"
                f"Association: {word['association']}\n\n",
            )
        box.configure(state="disabled")
        box.pack(fill="x", padx=2 * SPACE, pady=SPACE)

    def travel_word_cards(self, words):
        for word in words:
            panel = self.card(self.cards_panel)
            header = ctk.CTkFrame(panel, fg_color="transparent")
            header.pack(fill="x", padx=2 * SPACE, pady=(SPACE + 2, 0))
            ctk.CTkLabel(
                header, text=word["word"], font=ui_font(20, bold=True), text_color=BRAND
            ).pack(side="left")
            ctk.CTkLabel(
                header,
                text=f"{word['category']} · {', '.join(word['situations'])}",
                font=ui_font(13),
                text_color=MUTED,
            ).pack(side="left", padx=SPACE, pady=(6, 0))
            self.text(word["meaning"], parent=panel, size=15, pady=(SPACE - 2, 2))
            self.text(word["example_sentence"], parent=panel, size=14, muted=True, pady=2)
            self.text(
                f"Say it like: {word['pronunciation_text']}",
                parent=panel,
                size=13,
                muted=True,
                pady=2,
            )
            self.text(word["usage_note"], parent=panel, size=14, pady=(2, SPACE + 2))

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
