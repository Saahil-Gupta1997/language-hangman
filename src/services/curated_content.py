"""Explicit release corpus; legacy words remain available only for old reports."""

from src.db.database import WORD_INSERT_SQL, create_connection
from src.services.word_service import WordService
from src.utils.config import CURATED_WORDS_DIR, LEVEL_WORDS_DIR
from src.utils.constants import GENERAL_SITUATION, LEVEL_WORD_SOURCE, PRACTICE_LANGUAGES
from src.utils.word_bank_loader import build_seed_rows

LEVEL_WORD_COUNT = 1538  # the level lists after repeats and travel-card words are removed
# Optional text columns of WORD_INSERT_SQL that must be stored as "" rather than NULL.
BLANK_ALLOWED_COLUMNS = (9, 10, 11, 12, 13, 16)


def seed_curated(db_path):
    travel = build_seed_rows(CURATED_WORDS_DIR)
    levels = build_seed_rows(LEVEL_WORDS_DIR)
    if (
        travel["has_errors"]
        or travel["valid_words"] != 30
        or levels["has_errors"]
        or levels["valid_words"] != LEVEL_WORD_COUNT
    ):
        raise ValueError("The installed word content is missing or damaged.")
    with create_connection(db_path) as connection:
        connection.executemany(
            WORD_INSERT_SQL,
            [
                tuple(
                    "" if index in BLANK_ALLOWED_COLUMNS and value is None else value
                    for index, value in enumerate(row)
                )
                for row in travel["rows"] + levels["rows"]
            ],
        )


CURATED_SOURCE = "desktop-core"


class CuratedWordService(WordService):
    """Desktop word service: listing, counting and selection never leave the two desktop packs.

    Legacy words stay in the database so older results remain reportable, but they are
    never offered for desktop practice.
    """

    sources = (CURATED_SOURCE, LEVEL_WORD_SOURCE)

    def __init__(self, db_path):
        super().__init__(words_dir=CURATED_WORDS_DIR, db_path=db_path)

    def get_available_languages(self):
        return list(PRACTICE_LANGUAGES)

    def travel_cards(self):
        """The 30 English cards with examples, pronunciation and usage notes."""
        return [word for word in self.get_words("english") if word["source"] == CURATED_SOURCE]

    def level_words(self, language, level):
        """One language and level of the older word sheet, in alphabetical order."""
        words = self.get_words(language, difficulties=[level], situation=GENERAL_SITUATION)
        return sorted(words, key=lambda word: word["word"].casefold())
