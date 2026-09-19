"""Native desktop app: profiles, durable practice, reports and local recovery."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from src.models.game_round import GameRound
from src.services.desktop_storage import (
    progress_report,
)
from src.services.game_service import NoReviewWordsError
from src.services.hint_service import get_revealed_hints

BLUE = "#155E75"


class PracticeView:
    def show_home(self):
        self.clear("Home")
        self.heading(
            f"Hello, {self.user['username']}",
            "Short vocabulary sessions for everyday travel. "
            "The starter pack contains 30 English words in three situations.",
        )
        if self.guest:
            self.text(
                "Guest progress is temporary and will be deleted when you sign out or close.",
                bold=True,
            )
        report = progress_report(self.active_db, self.user["id"])
        self.text(
            f"{report['rounds']} rounds played    ·    {report['words']} words practised    ·    "
            f"{report['sessions']} sessions completed",
            bold=True,
        )
        self.text(
            "Choose Easy for seven lives and earlier clues, or Hard for five lives. "
            "These are game settings, not measures of language proficiency."
        )
        saved = self.practice.load(self.user["id"])
        self.practice.pause(self.user["id"])
        if saved:
            self.text("Your saved session is ready to resume.", bold=True)
            self.button(self.body, "Resume saved session", self.show_practice)
        else:
            self.button(self.body, "Start practising", self.show_practice)
        self.text(
            "Progress reports describe game performance. To check your learning, "
            "try recalling yesterday’s word meanings without opening their cards."
        )

    def show_practice(self):
        self.clear("Practice")
        self.payload = self.practice.load(self.user["id"])
        if self.payload:
            self.render_round()
            return
        self.heading(
            "Set up your practice", "English starter pack · All vocabulary is introductory."
        )
        self.text("Situation")
        self.situation = ctk.CTkOptionMenu(self.body, values=["Restaurant", "Airport", "Hotel"])
        self.situation.pack(anchor="w", padx=22, pady=8)
        self.text("Game difficulty")
        self.mode = ctk.CTkOptionMenu(self.body, values=["Easy", "Hard"])
        self.mode.pack(anchor="w", padx=22, pady=8)
        self.text("Number of rounds")
        self.rounds = ctk.CTkOptionMenu(self.body, values=["3", "5", "10"])
        self.rounds.pack(anchor="w", padx=22, pady=8)
        self.text("Practice focus")
        self.focus = ctk.CTkOptionMenu(self.body, values=["Standard", "Review"])
        self.focus.pack(anchor="w", padx=22, pady=8)
        self.text(
            "Standard chooses from all 10 words for the situation, favouring words that need "
            "practice. Review only uses words you have already completed in this situation "
            "and that are still in your review queue: due words first, then the rest, each "
            "word once per session. If fewer review words exist than the rounds you choose, "
            "the session is shortened and you are told why."
        )
        self.button(self.body, "Start session", self.start_session)

    def start_session(self):
        self.begin_session(
            self.situation.get(), self.mode.get(), int(self.rounds.get()), self.focus.get()
        )

    def begin_session(self, situation, mode, rounds, focus):
        review = focus == "Review"
        try:
            self.practice.start(
                self.user,
                {
                    "language": "english",
                    "categories": ["noun", "verb", "adjective", "adverb"],
                    "difficulties": ["beginner"],
                    "rounds": rounds,
                    "game_mode": mode.lower(),
                    "situation": situation.lower(),
                    "practice_mode": "review" if review else "standard",
                    "review_policy": "review_only" if review else "prefer_review",
                    "show_hint_immediately": False,
                },
            )
        except NoReviewWordsError as error:
            self.show_review_unavailable(str(error), situation, mode, rounds)
            return
        self.show_practice()

    def show_review_unavailable(self, message, situation, mode, rounds):
        self.clear("Practice")
        self.heading("No review words yet", message)
        self.button(
            self.body,
            f"Start Standard practice in {situation}",
            lambda: self.begin_session(situation, mode, rounds, "Standard"),
        )
        self.button(self.body, "Back to practice setup", self.show_practice)

    def render_round(self):
        state = GameRound(**self.payload["round"])
        session = self.payload["session"]
        self.heading(
            f"{session['situation'].title()} · {session['game_mode'].title()}",
            f"{session['completed_rounds']} of {session['planned_rounds']} rounds completed",
        )
        if self.payload.get("notice"):
            self.text(self.payload["notice"], bold=True)
        if state.saved:
            self.text(
                "Round won" if state.result == "won" else "Round finished — keep practising",
                bold=True,
            )
            self.word_card(state)
            if self.payload["next_round"]:
                self.button(self.body, "Next round", self.advance)
                self.bind("<Return>", lambda event: self.advance())
            else:
                self.text(
                    f"Session complete: {session['wins']} wins, {session['losses']} losses.",
                    bold=True,
                )
                self.button(self.body, "Finish session", self.finish_session)
            self.text("This result contributes to game progress, not a language qualification.")
        else:
            self.text(state.masked_word, bold=True)
            self.text(
                f"Lives remaining: {state.remaining_attempts}    ·    "
                f"Guessed: {state.guessed_letters_display}"
            )
            self.guess_entry = self.entry("Guess one letter (Enter to submit)")
            self.button(self.body, "Submit guess", self.submit_guess)
            self.bind("<Return>", lambda event: self.submit_guess())
            self.text(self.payload["message"])
            hints = get_revealed_hints(state)
            for index, text in enumerate(dict.fromkeys(hints.values()), 1):
                self.text(f"Clue {index}: {text}")
            if not hints:
                self.text("Clues will appear as lives are used.")
            self.text(f"Why this word: {self.selection_explanation(session)}")
            self.guess_entry.focus_set()
        self.button(self.body, "Save and return home", self.show_home)
        self.button(self.body, "Discard this session", self.discard_session)

    @staticmethod
    def selection_explanation(session):
        """Describe the desktop selection rule; the legacy engine's reason text is not used."""
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

    def submit_guess(self):
        self.practice.guess(self.user, self.guess_entry.get(), self.payload["round"]["round_key"])
        self.show_practice()

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
        self.text(state.word, bold=True)
        self.text(f"Meaning: {state.meaning or state.translation}")
        self.text(f"Example: {state.example_sentence}")
        self.text(f"Pronunciation spelling (approximate): {state.pronunciation_text}")
        self.text(f"Usage: {state.usage_note}")
