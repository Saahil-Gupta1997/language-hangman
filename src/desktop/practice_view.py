"""Home and practice screens: session set-up, the guessing round and the learning card."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from src.desktop.widgets import (
    BORDER,
    BRAND,
    DANGER,
    INK,
    MUTED,
    SPACE,
    SUCCESS,
    SURFACE,
    GameBoard,
    card,
    keyboard_option_menu,
    responsive_split,
    ui_font,
)
from src.models.game_round import GameRound
from src.services.desktop_storage import (
    progress_report,
)
from src.services.game_service import NoReviewWordsError
from src.services.hint_service import get_revealed_hints
from src.utils.constants import GENERAL_SITUATION, PRACTICE_LANGUAGES, WORD_LEVELS

TRAVEL_CARDS = "Travel cards"
LANGUAGE_CHOICES = [language.title() for language in PRACTICE_LANGUAGES]
NOT_REVIEWED = "Level lists have not been reviewed by a teacher yet."


def word_choices(language):
    """The word sets for a language: only English has the travel cards."""
    levels = [level.title() for level in WORD_LEVELS]
    return [TRAVEL_CARDS, *levels] if language == "English" else levels


class PracticeView:
    def show_home(self):
        self.clear("Home")
        self.heading(
            f"Hello, {self.user['username']}",
            "Short vocabulary sessions: 30 English travel cards, and word lists in "
            "English, Spanish, Italian and German at five levels.",
        )
        if self.guest:
            self.text(
                "Guest progress is temporary and will be deleted when you sign out or close.",
                bold=True,
            )
        report = progress_report(self.active_db, self.user["id"])
        self.stat_row(
            (
                (report["rounds"], "rounds played"),
                (report["words"], "words practised"),
                (report["sessions"], "sessions completed"),
            )
        )
        saved = self.practice.load(self.user["id"])
        self.practice.pause(self.user["id"])
        if saved:
            self.text("Your saved session is ready to resume.", bold=True)
            self.button(
                self.body, "Resume saved session", self.show_practice, variant="primary", width=220
            )
        else:
            self.button(
                self.body, "Start practising", self.show_practice, variant="primary", width=220
            )
        self.text(
            "Choose Easy for seven lives and earlier clues, or Hard for five lives. "
            "These are game settings, not measures of language proficiency.",
            muted=True,
        )
        self.text(
            "Progress reports describe game performance. To check your learning, "
            "try recalling yesterday’s word meanings without opening their cards.",
            muted=True,
        )

    def stat_row(self, stats):
        """All-time numbers as three tiles rather than one run-on sentence."""
        row = ctk.CTkFrame(self.body, fg_color="transparent")
        row.pack(fill="x", padx=2 * SPACE, pady=SPACE)
        for column, (value, label) in enumerate(stats):
            tile = card(row)
            tile.grid(row=0, column=column, sticky="ew", padx=(0, SPACE))
            row.grid_columnconfigure(column, weight=1)
            ctk.CTkLabel(tile, text=str(value), font=ui_font(28, bold=True), text_color=BRAND).pack(
                anchor="w", padx=2 * SPACE, pady=(SPACE + 4, 0)
            )
            ctk.CTkLabel(tile, text=label, font=ui_font(13), text_color=MUTED).pack(
                anchor="w", padx=2 * SPACE, pady=(0, SPACE + 4)
            )

    def show_practice(self):
        self.clear("Practice")
        self.payload = self.practice.load(self.user["id"])
        if self.payload:
            self.render_round()
            return
        self.heading(
            "Set up your practice", "Choose travel cards, or a word list in one of four languages."
        )
        setup = self.card()
        grid = ctk.CTkFrame(setup, fg_color="transparent")
        grid.pack(fill="x", padx=2 * SPACE, pady=(SPACE + 4, 4))
        self.language = self.setting(
            grid, 0, "Language", LANGUAGE_CHOICES, command=self.language_changed
        )
        self.level = self.setting(
            grid, 1, "Words", word_choices("English"), command=self.word_set_changed
        )
        self.mode = self.setting(grid, 2, "Game difficulty", ["Easy", "Hard"])
        self.rounds = self.setting(grid, 3, "Number of rounds", ["3", "5", "10"])
        self.focus = self.setting(grid, 4, "Practice focus", ["Standard", "Review"])
        self.situation = self.setting(grid, 5, "Situation", ["Restaurant", "Airport", "Hotel"])
        self.setup_note = self.text(
            self.word_set_note(TRAVEL_CARDS), parent=setup, muted=True, size=14
        )
        self.button(self.body, "Start session", self.start_session, variant="primary", width=220)

    def setting(self, grid, column, label, values, command=None):
        """One labelled dropdown in the set-up row; two per row when the window is narrow."""
        cell = ctk.CTkFrame(grid, fg_color="transparent")
        cell.grid(row=column // 2, column=column % 2, sticky="ew", padx=(0, SPACE), pady=4)
        grid.grid_columnconfigure(column % 2, weight=1)
        ctk.CTkLabel(
            cell, text=label, anchor="w", font=ui_font(13, bold=True), text_color=MUTED
        ).pack(fill="x", pady=(0, 2))
        menu = keyboard_option_menu(cell, values, command=command)
        menu.pack(anchor="w")
        return menu

    def language_changed(self, language):
        choices = word_choices(language)
        self.level.configure(values=choices)
        if self.level.get() not in choices:
            self.level.set(choices[0])
        self.word_set_changed(self.level.get())

    def word_set_changed(self, word_set):
        """Situation belongs to the travel cards; the level lists have none."""
        cell = self.situation.master
        cell.grid() if word_set == TRAVEL_CARDS else cell.grid_remove()
        self.setup_note.configure(text=self.word_set_note(word_set))

    @staticmethod
    def word_set_note(word_set):
        if word_set == TRAVEL_CARDS:
            return (
                "Standard chooses from all 10 words for the situation, favouring words that "
                "need practice. Review only uses words you have already completed in this "
                "situation and that are still in your review queue: due words first, then the "
                "rest, each word once per session. If fewer review words exist than the rounds "
                "you choose, the session is shortened and you are told why."
            )
        return (
            "Standard chooses from the words at this level, favouring words that need "
            "practice. Review only uses words you have already completed at this level and "
            "that are still in your review queue. Clues are in English, and each word has "
            f"three. {NOT_REVIEWED}"
        )

    def start_session(self):
        self.begin_session(
            self.situation.get(),
            self.mode.get(),
            int(self.rounds.get()),
            self.focus.get(),
            self.language.get(),
            self.level.get(),
        )

    def begin_session(self, situation, mode, rounds, focus, language="English", level=TRAVEL_CARDS):
        review = focus == "Review"
        travel = level == TRAVEL_CARDS
        try:
            self.practice.start(
                self.user,
                {
                    "language": language.lower(),
                    "categories": ["noun", "verb", "adjective", "adverb"],
                    "difficulties": ["beginner" if travel else level.lower()],
                    "rounds": rounds,
                    "game_mode": mode.lower(),
                    "situation": situation.lower() if travel else GENERAL_SITUATION,
                    "practice_mode": "review" if review else "standard",
                    "review_policy": "review_only" if review else "prefer_review",
                    "show_hint_immediately": False,
                },
            )
        except NoReviewWordsError as error:
            message = (
                str(error)
                if travel
                else (
                    f"There are no review words for {language} {level} yet. "
                    "Play a Standard session first."
                )
            )
            self.show_review_unavailable(message, situation, mode, rounds, language, level)
            return
        self.show_practice()

    def show_review_unavailable(self, message, situation, mode, rounds, language, level):
        self.clear("Practice")
        self.heading("No review words yet", message)
        where = situation if level == TRAVEL_CARDS else f"{language} {level}"
        self.button(
            self.body,
            f"Start Standard practice in {where}",
            lambda: self.begin_session(situation, mode, rounds, "Standard", language, level),
            variant="primary",
            width=340,
        )
        self.button(self.body, "Back to practice setup", self.show_practice)

    def render_round(self):
        state = GameRound(**self.payload["round"])
        session = self.payload["session"]
        self.round_header(session)
        if self.payload.get("notice"):
            self.text(self.payload["notice"], bold=True)
        if state.saved:
            self.render_result(state, session)
        else:
            self.render_guessing(state, session)
        actions = ctk.CTkFrame(self.body, fg_color="transparent")
        actions.pack(fill="x", padx=2 * SPACE, pady=(SPACE, 2 * SPACE))
        self.button(actions, "Save and return home", self.show_home, side="left")
        self.button(
            actions, "Discard this session", self.discard_session, side="left", variant="quiet"
        )

    def round_header(self, session):
        """Title and session progress on one line, so the board fits the smallest window."""
        done, planned = session["completed_rounds"], session["planned_rounds"]
        row = ctk.CTkFrame(self.body, fg_color="transparent")
        row.pack(fill="x", padx=2 * SPACE, pady=(SPACE + 2, SPACE))
        where = session["situation"].title()
        if session["situation"] == GENERAL_SITUATION:
            where = f"{session['language'].title()} · {session['difficulty_filter'][0].title()}"
        ctk.CTkLabel(
            row,
            text=f"{where} · {session['game_mode'].title()}",
            font=ui_font(24, bold=True),
            text_color=INK,
        ).pack(side="left")
        bar = ctk.CTkProgressBar(
            row, width=140, height=8, progress_color=BRAND, fg_color=BORDER, corner_radius=4
        )
        bar.set(done / planned if planned else 0)
        bar.pack(side="right", pady=4)
        ctk.CTkLabel(
            row,
            text=f"Round {min(done + 1, planned)} of {planned}",
            font=ui_font(14, bold=True),
            text_color=MUTED,
        ).pack(side="right", padx=SPACE)

    def render_guessing(self, state, session):
        container, left, right = responsive_split(self.body)
        container.pack(fill="x", padx=2 * SPACE)
        board = card(left)
        board.pack(fill="x")
        # One drawn canvas rather than about 55 widgets: see GameBoard for why.
        self.board = GameBoard(board, self.guess_letter)
        self.board.pack(fill="x", padx=SPACE, pady=SPACE)
        self.board.redraw(state)
        guess_row = ctk.CTkFrame(board, fg_color="transparent")
        guess_row.pack(fill="x", padx=SPACE, pady=(0, SPACE + 4))
        self.text(
            "Guess one letter (Enter to submit), or click a letter above.",
            parent=guess_row,
            muted=True,
            size=13,
            pady=(0, 2),
        )
        entry_row = ctk.CTkFrame(guess_row, fg_color="transparent")
        entry_row.pack(fill="x", padx=2 * SPACE)
        self.guess_entry = self.entry("", parent=entry_row, width=120, side="left")
        self.button(entry_row, "Submit guess", self.submit_guess, side="left", variant="primary")
        self.bind("<Return>", lambda event: self.submit_guess())
        self.board_status = self.status_card(right, state)
        self.board_clues = self.clue_card(right, state, session)
        self.board_round_key = state.round_key
        self.board_clue_count = len(set(get_revealed_hints(state).values()))
        self.guess_entry.focus_set()

    def status_card(self, parent, state):
        """The result of the last guess, coloured so it can be found without reading."""
        last = state.guessed_letters[-1] if state.guessed_letters else None
        colour = INK if last is None else (DANGER if last in state.wrong_letters else SUCCESS)
        panel = card(parent)
        panel.pack(fill="x", pady=(0, SPACE))
        label = self.text(
            self.payload["message"], parent=panel, bold=True, size=15, pady=(SPACE + 4, SPACE + 4)
        )
        label.configure(text_color=colour)
        return label

    def clue_card(self, parent, state, session):
        panel = card(parent)
        panel.pack(fill="x")
        self.clue_session = session
        ctk.CTkLabel(
            panel, text="Clues", anchor="w", font=ui_font(13, bold=True), text_color=MUTED
        ).pack(fill="x", padx=2 * SPACE, pady=(SPACE + 4, 0))
        clues = ctk.CTkFrame(panel, fg_color="transparent")
        clues.pack(fill="x")
        self.fill_clues(clues, state)
        self.text(
            f"Why this word: {self.selection_explanation(session)}",
            parent=panel,
            muted=True,
            size=13,
            pady=(SPACE, SPACE + 4),
        )
        return clues

    def fill_clues(self, parent, state):
        for child in parent.winfo_children():
            child.destroy()
        hints = get_revealed_hints(state)
        if hints:
            for index, text in enumerate(dict.fromkeys(hints.values()), 1):
                self.text(f"{index}. {text}", parent=parent, size=14)
        else:
            self.text("Clues appear as lives are used.", parent=parent, muted=True, size=14)

    def render_result(self, state, session):
        won = state.result == "won"
        banner = ctk.CTkFrame(self.body, fg_color="#DCFCE7" if won else "#FEF3C7", corner_radius=10)
        banner.pack(fill="x", padx=2 * SPACE, pady=(0, SPACE))
        ctk.CTkLabel(
            banner,
            text="Round won" if won else "Round finished — keep practising",
            font=ui_font(16, bold=True),
            text_color=SUCCESS if won else "#92400E",
        ).pack(anchor="w", padx=2 * SPACE, pady=SPACE + 2)
        self.word_card(state)
        if self.payload["next_round"]:
            self.button(self.body, "Next round", self.advance, variant="primary", width=220)
            self.bind("<Return>", lambda event: self.advance())
        else:
            self.text(
                f"Session complete: {session['wins']} wins, {session['losses']} losses.",
                bold=True,
            )
            self.button(
                self.body, "Finish session", self.finish_session, variant="primary", width=220
            )
        self.text(
            "This result contributes to game progress, not a language qualification.",
            muted=True,
            size=13,
        )

    @staticmethod
    def selection_explanation(session):
        """Describe the desktop selection rule; the legacy engine's reason text is not used."""
        if session["situation"] == GENERAL_SITUATION:
            if session["practice_mode"] == "review":
                return (
                    "you have practised it before at this level and it is in your review "
                    "queue (due words come first)."
                )
            return (
                f"one of the {session['language'].title()} words at this level; words you "
                "have not played recently are chosen first when possible."
            )
        situation = str(session["situation"]).replace("_", " ").title()
        if session["practice_mode"] == "review":
            return (
                f"you have practised it before in {situation} and it is in your review "
                "queue (due words come first)."
            )
        return (
            f"one of the 10 {situation} words; words you have not played recently are "
            "chosen first when possible."
        )

    def guess_letter(self, letter):
        """Clicking a letter key takes the same route as typing it."""
        self.guess_entry.delete(0, "end")
        self.guess_entry.insert(0, letter)
        self.submit_guess()

    def submit_guess(self):
        guessed = self.guess_entry.get().strip().lower()
        payload = self.practice.guess(
            self.user, self.guess_entry.get(), self.payload["round"]["round_key"]
        )
        self.payload = payload
        state = GameRound(**payload["round"])
        # Rebuilding the screen costs about a second: CustomTkinter widgets are expensive to
        # create, and the board has around a hundred. While the round continues, update the
        # parts that changed. A finished round changes the whole screen, so it is redrawn.
        if state.saved or payload.get("notice") or state.round_key != self.board_round_key:
            self.show_practice()
        else:
            self.refresh_round(state, guessed)

    def refresh_round(self, state, guessed=None):
        """Update the board in place after a guess that leaves the round in progress."""
        self.board.redraw(state)
        last = state.guessed_letters[-1] if state.guessed_letters else None
        colour = INK if last is None else (DANGER if last in state.wrong_letters else SUCCESS)
        self.board_status.configure(text=self.payload["message"], text_color=colour)
        clue_count = len(set(get_revealed_hints(state).values()))
        if clue_count != self.board_clue_count:  # a clue appears only when a life is used
            self.fill_clues(self.board_clues, state)
            self.board_clue_count = clue_count
        self.guess_entry.delete(0, "end")
        self.guess_entry.focus_set()

    def advance(self):
        self.practice.next_round(self.user["id"])
        self.show_practice()

    def finish_session(self):
        self.practice.discard(self.user["id"])
        self.show_reports()

    def discard_session(self):
        if messagebox.askyesno(
            "Discard session?",
            "Completed rounds stay in your reports. "
            "The unfinished round and remaining session will be discarded.",
            parent=self,
        ):
            self.practice.discard(self.user["id"])
            self.show_practice()

    def word_card(self, state):
        """The learning card shown after a round: the word, then what it means and how to use it.

        Level-list words have clues but no teaching notes, so they show the clues instead.
        """
        panel = self.card()
        travel_card = bool(state.example_sentence)
        ctk.CTkLabel(
            panel, text=state.word, anchor="w", font=ui_font(30, bold=True), text_color=BRAND
        ).pack(fill="x", padx=2 * SPACE, pady=(SPACE + 4, 0 if travel_card else SPACE))
        if travel_card:
            ctk.CTkLabel(
                panel,
                text=f"Say it like: {state.pronunciation_text}",
                anchor="w",
                font=ui_font(14),
                text_color=MUTED,
            ).pack(fill="x", padx=2 * SPACE, pady=(0, SPACE))
            details = (
                ("Meaning", state.meaning or state.translation),
                ("Example", state.example_sentence),
                ("Usage", state.usage_note),
            )
        else:
            details = (
                ("Meaning", state.meaning or state.translation),
                ("Synonyms", state.synonym_hint),
                ("Association", state.association_hint),
            )
        for label, value in details:
            row = ctk.CTkFrame(panel, fg_color=SURFACE)
            row.pack(fill="x", padx=2 * SPACE, pady=(0, 2))
            ctk.CTkLabel(
                row, text=label, anchor="w", width=96, font=ui_font(13, bold=True), text_color=MUTED
            ).pack(side="left", anchor="n", pady=2)
            self.text(value, parent=row, size=15, pady=2)
        if not travel_card:
            self.text(NOT_REVIEWED, parent=panel, muted=True, size=13, pady=(2, 2))
        ctk.CTkLabel(panel, text="", height=2).pack()
