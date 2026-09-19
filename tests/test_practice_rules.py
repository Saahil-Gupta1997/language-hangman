"""Review eligibility (D-01) and curated-only desktop practice (D-02).

Every test drives the real desktop PracticeService through whole sessions, including the
later rounds, against either a fresh curated database or one imported from legacy data.
"""

import random
import sqlite3

import pytest

from src.db.database import init_db
from src.services.auth_service import AuthService
from src.services.curated_content import CURATED_SOURCE, CuratedWordService, seed_curated
from src.services.desktop_storage import progress_report, restore_database
from src.services.game_service import GameService, NoReviewWordsError
from src.services.practice_service import PracticeService
from src.utils.helpers import shift_utc_iso, utc_now_iso

SITUATIONS = ("restaurant", "airport", "hotel")


def practice_settings(situation="restaurant", review=False, rounds=3):
    return {
        "language": "english",
        "categories": ["noun", "verb", "adjective", "adverb"],
        "difficulties": ["beginner"],
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

    The seeded legacy session loses happy, quiet, simple, safely and apple in Restaurant.
    "quiet" is also a curated word (Hotel); the other four exist only in the legacy bank.
    """
    legacy_path = init_db(tmp_path / "old-app.db", seed_words=True)
    user = AuthService(legacy_path).register_user("legacy", "password123")
    game = GameService(legacy_path)  # legacy selection over the 324-word banks
    rng = random.Random(20260919)
    start = game.start_custom_learning_session(user, practice_settings(rounds=5), rng=rng)
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
            user, practice_settings("office", rounds=5), rng=rng
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
    assert words.count_candidate_words("english", situation="restaurant") == 10
    no_candidates = words.count_candidate_words(
        "english", situation="restaurant", candidate_word_ids=[]
    )
    assert no_candidates == 0
    with pytest.raises(ValueError):
        words.select_word("english", "beginner", candidate_word_ids=[], strict_mode=True)


def test_fresh_profile_cannot_start_review(desktop):
    path, user, service = desktop
    for situation in SITUATIONS:
        with pytest.raises(NoReviewWordsError, match="no review words"):
            service.start(user, practice_settings(situation, review=True))
    assert service.load(user["id"]) is None
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT count(*) FROM learning_sessions").fetchone()[0] == 0


def test_standard_practice_still_works_for_fresh_profile(desktop):
    path, user, service = desktop
    payload = service.start(user, practice_settings("airport", rounds=5))
    played, _ = play_session(service, user, payload)
    assert len(played) == len(set(played)) == 5
    for word in words_by_id(path, played).values():
        assert word["source"] == CURATED_SOURCE
        assert "airport" in word["situations"]
    assert progress_report(path, user["id"])["sessions"] == 1


def test_review_uses_only_practised_words_from_the_situation(desktop):
    path, user, service = desktop
    restaurant, _ = play_session(service, user, service.start(user, practice_settings()))
    play_session(service, user, service.start(user, practice_settings("airport")))

    payload = service.start(user, practice_settings("restaurant", review=True, rounds=10))
    assert payload["session"]["planned_rounds"] == 3
    assert "Only 3 review word(s) are available for Restaurant" in payload["notice"]
    reviewed, final = play_session(service, user, payload)
    assert sorted(reviewed) == sorted(restaurant)  # each eligible word once, nothing else
    assert final["session"]["completed_rounds"] == 3
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


def test_imported_legacy_review_items_are_not_offered(imported):
    path, user, service = imported
    active = active_review_words(path, user)
    legacy_only = {word for word, source in active.items() if source != CURATED_SOURCE}
    assert {"happy", "simple", "safely", "apple"} <= legacy_only  # active legacy-only items
    with pytest.raises(NoReviewWordsError):
        service.start(user, practice_settings("restaurant", review=True))


def test_word_shared_with_legacy_bank_counts_as_practised(imported):
    path, user, service = imported
    assert active_review_words(path, user)["quiet"] == CURATED_SOURCE
    payload = service.start(user, practice_settings("hotel", review=True, rounds=5))
    assert "Only 1 review word(s) are available for Hotel" in payload["notice"]
    reviewed, _ = play_session(service, user, payload)
    assert [word["word"] for word in words_by_id(path, reviewed).values()] == ["quiet"]


def test_imported_database_practice_uses_curated_words_only(imported):
    path, user, service = imported
    history_before = progress_report(path, user["id"])["rounds"]

    def legacy_queue():
        with sqlite3.connect(path) as connection:
            return connection.execute(
                "SELECT r.* FROM review_queue r JOIN words w ON w.id=r.word_id "
                "WHERE r.user_id=? AND w.source != ? ORDER BY r.id",
                (user["id"], CURATED_SOURCE),
            ).fetchall()

    legacy_before = legacy_queue()
    played = []
    for situation in SITUATIONS:
        words, _ = play_session(service, user, service.start(user, practice_settings(situation)))
        played += words
    reviewed, _ = play_session(
        service, user, service.start(user, practice_settings("hotel", review=True, rounds=10))
    )
    hotel_words = {word_id for word_id in played[-3:]}
    quiet = {i for i, w in words_by_id(path, reviewed).items() if w["word"] == "quiet"}
    assert set(reviewed) <= hotel_words | quiet
    played += reviewed
    assert {word["source"] for word in words_by_id(path, played).values()} == {CURATED_SOURCE}

    words = CuratedWordService(path)
    for situation in SITUATIONS:
        assert words.count_candidate_words("english", situation=situation) == 10
    assert words.get_difficulties("english") == ["beginner"]
    legacy_ids = [row[2] for row in legacy_before]
    fallback = words.select_word("english", "beginner", candidate_word_ids=legacy_ids)
    assert fallback["source"] == CURATED_SOURCE

    # Legacy history and review items are kept, unchanged, for reporting.
    assert progress_report(path, user["id"])["rounds"] == history_before + len(played)
    assert legacy_queue() == legacy_before
