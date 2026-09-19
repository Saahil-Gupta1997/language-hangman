"""D-07: does a failed automatic backup stop the desktop app from starting?"""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from src.desktop.application import HangmanDesktop
data = Path(tempfile.mkdtemp(prefix="hangman-d07-"))
(data / "backups").write_text("a file where the backups folder should be")
try:
    app = HangmanDesktop(data / "app.db", data)
except Exception as error:  # noqa: BLE001
    print(f"D-07 REPRODUCED: start-up failed with {type(error).__name__}")
else:
    print(f"D-07 NOT REPRODUCED: app started; warning shown: {bool(getattr(app, 'backup_warning', None))}")
    app.close_application()
