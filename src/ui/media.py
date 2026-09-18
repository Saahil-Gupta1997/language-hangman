"""Optional local audio helpers for Streamlit."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.utils.config import PROJECT_ROOT

SOUND_ENABLED = True
AUDIO_DIR = PROJECT_ROOT / "assets" / "audio"
SOUND_FILES = {
    "correct": AUDIO_DIR / "correct_guess.wav",
    "wrong": AUDIO_DIR / "wrong_guess.wav",
    "win": AUDIO_DIR / "correct_guess.wav",
    "loss": AUDIO_DIR / "wrong_guess.wav",
    "hint": AUDIO_DIR / "correct_guess.wav",
}
BACKGROUND_MUSIC_FILE = AUDIO_DIR / "background_music.wav"


def get_audio_asset_status() -> dict[str, object]:
    """Return availability details for optional local audio assets."""
    available_sound_files = {
        sound_key: sound_path
        for sound_key, sound_path in SOUND_FILES.items()
        if Path(sound_path).exists()
    }
    music_available = Path(BACKGROUND_MUSIC_FILE).exists()
    return {
        "sound_enabled_constant": SOUND_ENABLED,
        "has_any_audio": bool(available_sound_files) or music_available,
        "sound_available": bool(available_sound_files),
        "music_available": music_available,
        "available_sound_keys": sorted(available_sound_files),
    }


def play_optional_sound(sound_key: str) -> bool:
    """Play a local sound if enabled and available, otherwise stay silent."""
    if not SOUND_ENABLED or not st.session_state.get("sound_enabled", False):
        return False

    sound_path = SOUND_FILES.get(sound_key)
    if not sound_path or not Path(sound_path).exists():
        return False

    try:
        st.audio(str(sound_path), format="audio/wav", autoplay=True)
    except Exception:
        return False
    return True


def render_background_music() -> bool:
    """Render optional background music when enabled and present."""
    if not SOUND_ENABLED or not st.session_state.get("music_enabled", False):
        return False
    if not Path(BACKGROUND_MUSIC_FILE).exists():
        return False

    try:
        st.audio(str(BACKGROUND_MUSIC_FILE), format="audio/wav", loop=True)
    except Exception:
        return False
    return True
