"""Explicit release corpus; legacy words remain available only for old reports."""

from src.db.database import WORD_INSERT_SQL, create_connection
from src.services.word_service import WordService
from src.utils.config import LEVEL_WORDS_DIR
from src.utils.constants import LEVEL_WORD_SOURCE, PRACTICE_LANGUAGES
from src.utils.word_bank_loader import build_seed_rows

LEVEL_WORD_COUNT = 1544  # the word lists once repeats within a language are removed
# Optional text columns of WORD_INSERT_SQL that must be stored as "" rather than NULL.
BLANK_ALLOWED_COLUMNS = (9, 10, 11, 12, 13, 16)


def seed_curated(db_path):
    levels = build_seed_rows(LEVEL_WORDS_DIR)
    if levels["has_errors"] or levels["valid_words"] != LEVEL_WORD_COUNT:
        raise ValueError("The installed word content is missing or damaged.")
    with create_connection(db_path) as connection:
        connection.executemany(
            WORD_INSERT_SQL,
            [
                tuple(
                    "" if index in BLANK_ALLOWED_COLUMNS and value is None else value
                    for index, value in enumerate(row)
                )
                for row in levels["rows"]
            ],
        )


class CuratedWordService(WordService):
    """Desktop word service: listing, counting and selection never leave the word lists.

    Legacy words and the travel cards removed in rc6 stay in existing databases so older
    results remain reportable, but they are never offered for desktop practice.
    """

    sources = (LEVEL_WORD_SOURCE,)

    def __init__(self, db_path):
        super().__init__(words_dir=LEVEL_WORDS_DIR, db_path=db_path)

    def get_available_languages(self):
        return list(PRACTICE_LANGUAGES)
