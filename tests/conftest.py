"""Shared test setup.

Tests must never touch a learner's real application data. Unless a data folder is given
explicitly, the whole run uses a temporary one, set before any application module reads
its configuration.
"""

import atexit
import os
import shutil
import sys
import tempfile

import pytest

if "LANGUAGE_HANGMAN_DATA_DIR" not in os.environ:
    _test_data = tempfile.mkdtemp(prefix="hangman-tests-")
    os.environ["LANGUAGE_HANGMAN_DATA_DIR"] = _test_data
    atexit.register(shutil.rmtree, _test_data, ignore_errors=True)


def require_display():
    """Skip only on a headless non-Windows machine; elsewhere GUI errors must fail."""
    if sys.platform != "win32" and not os.environ.get("DISPLAY"):
        pytest.skip("Needs a graphical desktop (no DISPLAY).")
