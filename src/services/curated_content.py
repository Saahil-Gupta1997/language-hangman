"""Explicit release corpus; legacy words remain available only for old reports."""

from src.db.database import WORD_INSERT_SQL, create_connection
from src.services.word_service import WordService
from src.utils.config import CURATED_WORDS_DIR
from src.utils.word_bank_loader import build_seed_rows


def seed_curated(db_path):
    payload = build_seed_rows(CURATED_WORDS_DIR)
    if payload["has_errors"] or payload["valid_words"] != 30:
        raise ValueError("The installed English content pack is missing or damaged.")
    with create_connection(db_path) as connection:
        connection.executemany(
            WORD_INSERT_SQL,
            [
                tuple(
                    "" if index in (13, 16) and value is None else value
                    for index, value in enumerate(row)
                )
                for row in payload["rows"]
            ],
        )


class CuratedWordService(WordService):
    def __init__(self, db_path):
        super().__init__(words_dir=CURATED_WORDS_DIR, db_path=db_path)

    def get_words(self, *args, **kwargs):
        # Apply limit after filtering; never fall back to archived teaching material.
        limit = kwargs.pop("limit", None)
        words = super().get_words(*args, **kwargs)
        words = [word for word in words if word.get("source") == "desktop-core"]
        return words[:limit] if limit is not None else words

    def get_available_languages(self):
        return ["english"]
