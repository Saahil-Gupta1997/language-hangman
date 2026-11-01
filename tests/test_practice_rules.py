"""Review eligibility (D-01) and word-list-only desktop practice (D-02).

Every test drives the real desktop PracticeService through whole sessions, including the
later rounds, against either a fresh curated database or one imported from legacy data.
"""

import random
import sqlite3

import pytest

from src.db.database import init_db
from src.services.auth_service import AuthService
from src.services.curated_content import CuratedWordService, seed_curated
from src.services.desktop_storage import progress_report, restore_database
from src.services.game_service import GameService, NoReviewWordsError
from src.services.practice_service import PracticeService
from src.utils.constants import ENDLESS_ROUNDS, GENERAL_SITUATION, LEVEL_WORD_SOURCE, WORD_LEVELS
from src.utils.helpers import shift_utc_iso, utc_now_iso

LEVELS = ("beginner", "novice", "advanced")


def practice_settings(level="beginner", review=False, rounds=3, situation=GENERAL_SITUATION):
    return {
        "language": "english",
        "categories": ["noun", "verb", "adjective", "adverb"],
        "difficulties": [level],
        "rounds": rounds,
        "game_mode": "easy",
        "situation": situation,
        "practice_mode": "review" if review else "standard",
        "review_policy": "review_only" if review else "prefer_review",
        "show_hint_immediately": False,
    }


def play_session(service, user, payload, *, lose=False):
    """Play every round via PracticeService, as the desktop does; return played word ids."""
    played = []
    while True:
        state = payload["round"]
        played.append(state["word_id"])
        letters = (
            [letter for letter in "abcdefghijklmnopqrstuvwxyz" if letter not in state["word"]]
            if lose
            else sorted(set(state["word"]))
        )
        for letter in letters:
            payload = service.guess(user, letter, state["round_key"])
            if payload["round"]["saved"]:
                break
        assert payload["round"]["saved"]
        if not payload["next_round"]:
            service.discard(user["id"])  # what "Finish session" does
            return played, payload
        payload = service.next_round(user["id"])


def words_by_id(path, word_ids):
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            f"SELECT id, word, source, situations FROM words WHERE id IN "
            f"({','.join('?' * len(word_ids))})",
            list(word_ids),
        ).fetchall()
    return {row["id"]: dict(row) for row in rows}


@pytest.fixture
def desktop(tmp_path):
    path = init_db(tmp_path / "app.db", seed_words=False)
    seed_curated(path)
    user = AuthService(path).register_user("learner", "password123", target_language="english")
    return path, user, PracticeService(path, curated=True)


@pytest.fixture
def imported(tmp_path):
    """A legacy database with legacy history and review items, imported through Restore.

    The seeded legacy session loses words from the legacy bank in Restaurant. Some of them
    are also word-list words, and the rest exist only in the legacy bank.
    """
    legacy_path = init_db(tmp_path / "old-app.db", seed_words=True)
    user = AuthService(legacy_path).register_user("legacy", "password123")
    game = GameService(legacy_path)  # legacy selection over the 324-word banks
    rng = random.Random(20260919)
    start = game.start_custom_learning_session(
        user, practice_settings(rounds=5, situation="restaurant"), rng=rng
    )
    session, current = start["learning_session"], start["first_round"]
    while current is not None:  # lose, so the legacy words enter the review queue
        for letter in "qxzjvkwyfb":
            if not current.is_complete:
                game.record_guess(current, letter)
        current.result = current.result if current.is_complete else "lost"
        current = game.finalize_round(user, current, session, rng=rng)["next_round"]
    with sqlite3.connect(legacy_path) as connection:
        connection.execute("UPDATE game_sessions SET played_at='2026-08-01T10:00:00+00:00'")
        connection.execute("UPDATE review_queue SET review_due_at='2026-08-02T10:00:00+00:00'")
    for _ in range(2):  # later practice elsewhere moves them out of the recent-word window
        later = game.start_custom_learning_session(
            user, practice_settings(rounds=5, situation="office"), rng=rng
        )
        later_session, current = later["learning_session"], later["first_round"]
        while current is not None:
            for letter in sorted(set(current.word)):
                game.record_guess(current, letter)
            current = game.finalize_round(user, current, later_session, rng=rng)["next_round"]

    path = init_db(tmp_path / "app.db", seed_words=False)
    seed_curated(path)
    restore_database(path, legacy_path)  # the desktop Restore / import path
    seed_curated(path)
    restored_user = AuthService(path).authenticate_user("legacy", "password123")
    assert restored_user is not None
    return path, restored_user, PracticeService(path, curated=True)


def test_empty_candidate_list_means_no_eligible_words(desktop):
    path, _, _ = desktop
    words = CuratedWordService(path)
    beginner = {"difficulties": ["beginner"], "situation": GENERAL_SITUATION}
    assert words.count_candidate_words("english", **beginner) == 80
    no_candidates = words.count_candidate_words("english", **beginner, candidate_word_ids=[])
    assert no_candidates == 0
    with pytest.raises(ValueError):
        words.select_word("english", "beginner", candidate_word_ids=[], strict_mode=True)


def test_fresh_profile_cannot_start_review(desktop):
    path, user, service = desktop
    for level in LEVELS:
        with pytest.raises(NoReviewWordsError, match="no review words"):
            service.start(user, practice_settings(level, review=True))
    assert service.load(user["id"]) is None
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT count(*) FROM learning_sessions").fetchone()[0] == 0


def test_standard_practice_still_works_for_fresh_profile(desktop):
    path, user, service = desktop
    payload = service.start(user, practice_settings("novice", rounds=5))
    played, _ = play_session(service, user, payload)
    assert len(played) == len(set(played)) == 5
    for word in words_by_id(path, played).values():
        assert word["source"] == LEVEL_WORD_SOURCE
    assert progress_report(path, user["id"])["sessions"] == 1


def test_review_uses_only_practised_words_from_the_level(desktop):
    path, user, service = desktop
    beginner, _ = play_session(service, user, service.start(user, practice_settings()))
    play_session(service, user, service.start(user, practice_settings("novice")))

    payload = service.start(user, practice_settings("beginner", review=True, rounds=10))
    assert payload["session"]["planned_rounds"] == 3
    assert "Only 3 review word(s) are available" in payload["notice"]
    reviewed, final = play_session(service, user, payload)
    assert sorted(reviewed) == sorted(beginner)  # each eligible word once, nothing else
    assert final["session"]["completed_rounds"] == 3
    assert final["session"]["status"] == "completed"


def test_review_from_the_app_plays_every_eligible_word_once_with_no_notice(desktop):
    _, user, service = desktop
    practised, _ = play_session(service, user, service.start(user, practice_settings()))
    payload = service.start(user, practice_settings(review=True, rounds=ENDLESS_ROUNDS))
    assert payload["session"]["planned_rounds"] == 3 and payload["notice"] is None
    reviewed, final = play_session(service, user, payload)
    assert sorted(reviewed) == sorted(practised)
    assert final["session"]["status"] == "completed"


def test_review_plays_due_words_before_words_not_yet_due(desktop):
    path, user, service = desktop
    practised, _ = play_session(service, user, service.start(user, practice_settings()))
    due_word, *later_words = practised
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE review_queue SET review_due_at=? WHERE word_id=?",
            (shift_utc_iso(utc_now_iso(), days=-1), due_word),
        )
        connection.execute(
            f"UPDATE review_queue SET review_due_at=? WHERE word_id IN "
            f"({','.join('?' * len(later_words))})",
            (shift_utc_iso(utc_now_iso(), days=5), *later_words),
        )
    reviewed, _ = play_session(
        service, user, service.start(user, practice_settings(review=True, rounds=3))
    )
    assert reviewed[0] == due_word
    assert sorted(reviewed[1:]) == sorted(later_words)


def test_review_queue_exhausted_mid_session_ends_with_explanation(desktop):
    path, user, service = desktop
    play_session(service, user, service.start(user, practice_settings()))
    payload = service.start(user, practice_settings(review=True, rounds=3))
    first = payload["round"]["word_id"]
    with sqlite3.connect(path) as connection:  # the other review items retire mid-session
        connection.execute("UPDATE review_queue SET is_active=0 WHERE word_id != ?", (first,))
    reviewed, final = play_session(service, user, payload)
    assert reviewed == [first]
    assert "ended after 1 of 3 rounds" in final["notice"]
    assert final["session"]["status"] == "completed"
    assert progress_report(path, user["id"])["rounds"] == 4


def active_review_words(path, user):
    with sqlite3.connect(path) as connection:
        return dict(
            connection.execute(
                "SELECT w.word, w.source FROM review_queue r JOIN words w ON w.id=r.word_id "
                "WHERE r.user_id=? AND r.is_active=1",
                (user["id"],),
            ).fetchall()
        )


def review_every_level(service, user):
    """Run Review at every level and return the word ids it offered."""
    reviewed = []
    for level in WORD_LEVELS:
        try:
            payload = service.start(user, practice_settings(level, review=True, rounds=10))
        except NoReviewWordsError:
            continue
        words, _ = play_session(service, user, payload)
        reviewed += words
    return reviewed


def test_imported_legacy_review_items_are_not_offered(imported):
    path, user, service = imported
    active = active_review_words(path, user)
    legacy_only = {word for word, source in active.items() if source != LEVEL_WORD_SOURCE}
    assert legacy_only, active  # active items that exist only in the legacy bank
    reviewed = review_every_level(service, user)
    assert not {w["word"] for w in words_by_id(path, reviewed).values()} & legacy_only


def test_word_shared_with_legacy_bank_counts_as_practised(imported):
    path, user, service = imported
    active = active_review_words(path, user)
    shared = {word for word, source in active.items() if source == LEVEL_WORD_SOURCE}
    assert shared, active  # a legacy row that matches a word-list word takes its content
    reviewed = review_every_level(service, user)
    assert {w["word"] for w in words_by_id(path, reviewed).values()} == shared


def test_imported_database_practice_uses_word_lists_only(imported):
    path, user, service = imported
    history_before = progress_report(path, user["id"])["rounds"]

    def legacy_queue():
        with sqlite3.connect(path) as connection:
            return connection.execute(
                "SELECT r.* FROM review_queue r JOIN words w ON w.id=r.word_id "
                "WHERE r.user_id=? AND w.source != ? ORDER BY r.id",
                (user["id"], LEVEL_WORD_SOURCE),
            ).fetchall()

    legacy_before = legacy_queue()
    played = []
    for level in LEVELS:
        words, _ = play_session(service, user, service.start(user, practice_settings(level)))
        played += words
    played += review_every_level(service, user)
    assert {word["source"] for word in words_by_id(path, played).values()} == {LEVEL_WORD_SOURCE}

    words = CuratedWordService(path)
    legacy_ids = [row[2] for row in legacy_before]
    fallback = words.select_word("english", "beginner", candidate_word_ids=legacy_ids)
    assert fallback["source"] == LEVEL_WORD_SOURCE

    # Legacy history and review items are kept, unchanged, for reporting.
    assert progress_report(path, user["id"])["rounds"] == history_before + len(played)
    assert legacy_queue() == legacy_before


def test_why_this_word_describes_the_desktop_rule_not_a_category():
    from src.desktop.practice_view import PracticeView

    session = {"situation": GENERAL_SITUATION, "language": "spanish"}
    review = PracticeView.selection_explanation({**session, "practice_mode": "review"})
    standard = PracticeView.selection_explanation({**session, "practice_mode": "standard"})
    assert "at this level" in review and "due words come first" in review
    assert "one of the Spanish words at this level" in standard
    for text in (review, standard):
        assert "focus on" not in text.lower()
