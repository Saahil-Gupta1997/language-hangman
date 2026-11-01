"""Native GUI regression checks (R-03, D-07, D-22 to D-25, D-31), one fresh process each.

See tests/gui_scenarios.py for why each scenario runs in its own process.
"""

import subprocess
import sys
from pathlib import Path

import pytest
from conftest import require_display

RUNNER = Path(__file__).with_name("gui_scenarios.py")
SCENARIOS = [
    "practice_dropdowns_change_from_the_keyboard",
    "text_size_dropdown_and_shortcuts",
    "text_size_after_dropdown_is_destroyed",
    "focused_control_scrolls_into_view",
    "window_opens_inside_the_work_area",
    "window_stays_inside_a_narrow_work_area",
    "automatic_backup_failure_does_not_block_start_up",
    "recovery_window_fits_at_minimum_size",
    "main_window_text_wraps_at_minimum_size",
    "letter_keys_guess_on_click",
    "removed_screens_and_settings_stay_removed",
    "plain_keys_reveal_accented_letters",
    "board_stays_put_whatever_the_feedback_says",
    "clues_leave_the_card_border_alone",
    "long_phrases_fit_the_board_at_minimum_size",
    "level_word_card_shows_its_clues",
    "endless_play_runs_until_end_session",
]


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_gui_scenario(scenario, tmp_path):
    require_display()
    completed = subprocess.run(
        [sys.executable, str(RUNNER), scenario, str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert f"PASSED {scenario}" in completed.stdout
