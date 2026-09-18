"""Small onboarding helpers for first-time learners."""

from __future__ import annotations

from typing import Any

ONBOARDING_STEPS = (
    (
        "Choose your target language",
        "Pick the language you want to practice first. You can change this later.",
    ),
    (
        "Choose your current level",
        "Start with your best guess. The short assessment will calibrate it.",
    ),
    (
        "Choose preferred categories",
        "Nouns, verbs, adjectives, and adverbs help shape your practice mix.",
    ),
    (
        "Take a short assessment",
        "Three words set a simple starting level for adaptive practice.",
    ),
    (
        "Start daily practice",
        "A small daily goal helps you build momentum without pressure.",
    ),
)


def build_onboarding_state(user: dict[str, Any]) -> dict[str, Any]:
    """Return display-ready onboarding state for a local learner."""
    assessment_completed = bool(user.get("assessment_completed"))
    return {
        "should_prompt": not assessment_completed,
        "assessment_completed": assessment_completed,
        "next_action": "Start assessment" if not assessment_completed else "Start practice",
        "steps": [
            {
                "title": title,
                "detail": detail,
                "complete": index < 3 or assessment_completed,
            }
            for index, (title, detail) in enumerate(ONBOARDING_STEPS)
        ],
    }
