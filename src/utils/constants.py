"""Project-wide constants."""

APP_NAME = "Language Learning Hangman"
BACKUP_SCHEMA_VERSION = 1
DEFAULT_LANGUAGE = "english"
DEFAULT_LEVEL = "beginner"
DEFAULT_DAILY_GOAL_WORDS = 5
DEFAULT_DAILY_GOAL_SESSIONS = 1
DEFAULT_MAX_ATTEMPTS = 6
GAME_MODES = ("easy", "hard")
GAME_MODE_LABELS = {
    "easy": "Easy Mode",
    "hard": "Hard Mode",
}
GAME_MODE_SETTINGS = {
    "easy": {
        "max_attempts": 7,
        "hint_mode": "easy",
        "description": (
            "7 lives. Meaning, synonym, and association hints unlock after "
            "wrong guesses 1, 3, and 5."
        ),
    },
    "hard": {
        "max_attempts": 5,
        "hint_mode": "hard",
        "description": "5 lives. Hints stay hidden until you have 2 lives or fewer.",
    },
}
MIN_PASSWORD_LENGTH = 8
SUPPORTED_LEVELS = ("beginner", "intermediate", "advanced")
DIFFICULTY_ORDER = SUPPORTED_LEVELS
# The desktop level lists: the owner's older word sheet, kept apart from the legacy banks.
LEVEL_WORD_SOURCE = "desktop-levels"
WORD_LEVELS = ("beginner", "novice", "intermediate", "advanced", "expert")
PRACTICE_LANGUAGES = ("english", "spanish", "italian", "german")
GENERAL_SITUATION = "general"
BOARD_LETTERS = "abcdefghijklmnopqrstuvwxyz"
# Only the letters the level lists use: a key that can never be right would be a trap.
EXTRA_LETTERS = {"spanish": "áéíñóú", "italian": "à", "german": "äöüß"}
WORD_CATEGORIES = ("noun", "verb", "adjective", "adverb")
DEFAULT_PREFERRED_CATEGORIES = WORD_CATEGORIES
SITUATIONS = (
    "restaurant",
    "airport",
    "hotel",
    "supermarket",
    "cafe",
    "office",
    "hospital",
    "metro_train_station",
    "shopping",
    "school_college",
    GENERAL_SITUATION,
)
SITUATION_LABELS = {
    "restaurant": "Restaurant",
    "airport": "Airport",
    "hotel": "Hotel",
    "supermarket": "Supermarket",
    "cafe": "Cafe",
    "office": "Office",
    "hospital": "Hospital",
    "metro_train_station": "Metro/Train Station",
    "shopping": "Shopping",
    "school_college": "School/College",
    GENERAL_SITUATION: "General",
}
NAVIGATION_ITEMS = ("Home", "Preferences", "Play", "Reports", "Content")
ASSESSMENT_DIFFICULTY_SEQUENCE = ("beginner", "intermediate", "advanced")
PRACTICE_MODES = ("standard", "weak_area", "category", "review", "weak_words")
PRACTICE_MODE_LABELS = {
    "standard": "Standard Practice",
    "weak_area": "Weak Area Practice",
    "category": "Category Practice",
    "review": "Review Practice",
    "weak_words": "Review Weak Words",
}
REVIEW_POLICIES = ("prefer_review", "review_only", "new_only")
REVIEW_POLICY_LABELS = {
    "prefer_review": "Prefer Review Words",
    "review_only": "Review Words Only",
    "new_only": "New Words Only",
}
FAMILIARITY_STATES = ("new", "learning", "familiar", "strong")
FAMILIARITY_LABELS = {
    "new": "New",
    "learning": "Learning",
    "familiar": "Familiar",
    "strong": "Strong",
}
MASTERY_STATUSES = ("weak", "learning", "almost_mastered", "mastered")
MASTERY_STATUS_LABELS = {
    "weak": "Weak",
    "learning": "Learning",
    "almost_mastered": "Almost Mastered",
    "mastered": "Mastered",
}
SESSION_LENGTH_OPTIONS = (3, 5, 10)
RECENT_WORD_EXCLUSION_LIMIT = 10
RECENT_REPORT_LIMIT = 5
RECENT_WORD_REPORT_LIMIT = 10
RECENT_ADAPTATION_LIMIT = 5
RECENT_LEARNING_SESSION_LIMIT = 5
REVIEW_QUEUE_LIMIT = 10
DAILY_ACTIVITY_LIMIT = 14
GUIDED_STUDY_PLAN_LIMIT = 3
LOW_REVIEW_ACCURACY_THRESHOLD = 0.5
DIFFICULT_REVIEW_ACCURACY_THRESHOLD = 0.75
CONTENT_MIN_WORDS_PER_LANGUAGE = 100
CONTENT_MIN_WORDS_PER_LANGUAGE_CATEGORY = 24
CONTENT_MIN_WORDS_PER_LANGUAGE_DIFFICULTY = 30
REPORT_TIMEFRAME_OPTIONS = {
    "All Time": None,
    "Last 7 Days": 7,
    "Last 30 Days": 30,
}
LEVEL_TO_DIFFICULTIES = {
    "beginner": ("beginner",),
    "intermediate": ("beginner", "intermediate"),
    "advanced": ("intermediate", "advanced"),
}
HANGMAN_STAGES = (
    """
 +---+
 |   |
     |
     |
     |
     |
=========
""".strip(
        "\n"
    ),
    """
 +---+
 |   |
 O   |
     |
     |
     |
=========
""".strip(
        "\n"
    ),
    """
 +---+
 |   |
 O   |
 |   |
     |
     |
=========
""".strip(
        "\n"
    ),
    """
 +---+
 |   |
 O   |
/|   |
     |
     |
=========
""".strip(
        "\n"
    ),
    """
 +---+
 |   |
 O   |
/|\\  |
     |
     |
=========
""".strip(
        "\n"
    ),
    """
 +---+
 |   |
 O   |
/|\\  |
/    |
     |
=========
""".strip(
        "\n"
    ),
    """
 +---+
 |   |
 O   |
/|\\  |
/ \\  |
     |
=========
""".strip(
        "\n"
    ),
)
PROGRESS_BADGE_DEFINITIONS = (
    ("first_session", "First Session", "Complete your first saved learning session."),
    ("three_day_streak", "3-Day Streak", "Study on three different days in a row."),
    ("first_strong_word", "Strong Word", "Push your first word into the strong mastery stage."),
    ("category_milestone", "Category Milestone", "Reach a category milestone beyond Starting out."),
)
