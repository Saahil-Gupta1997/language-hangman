"""Single-process ownership and bounded local event logs."""

import logging
import os
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path


class InstanceLock:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.handle = open(path, "a+b")
        try:
            if os.name == "nt":
                import msvcrt

                self.handle.seek(0, 2)
                if self.handle.tell() == 0:
                    self.handle.write(b"0")
                    self.handle.flush()
                self.handle.seek(0)
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.handle.close()
            raise RuntimeError(
                "Language Hangman is already running for this data folder."
            ) from None

    def close(self):
        self.handle.close()


EVENT_PATTERN = re.compile(
    r"^\S+ \S+ (INFO|WARNING|ERROR) op=[a-z_.]+ stage=[a-z_]+ error=[A-Za-z_]+ version=[\w.+-]+$"
)


def log_event(operation, stage, error=None, level=logging.ERROR):
    """Record one privacy-safe event: operation code, stage, error type and version only.

    Operation and stage are code identifiers chosen by the application, never user input,
    so names, passwords, words, saved-session payloads and paths cannot reach the log.
    """
    from src import __version__

    logging.getLogger("hangman").log(
        level,
        "op=%s stage=%s error=%s version=%s",
        operation,
        stage,
        type(error).__name__ if error is not None else "none",
        __version__,
    )


def recent_events(data_dir, limit=50):
    """Return the newest coded events; any line not in the fixed format is dropped."""
    for handler in logging.getLogger("hangman").handlers:
        handler.flush()
    path = Path(data_dir) / "logs" / "events.log"
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    return [line for line in lines if EVENT_PATTERN.match(line)][-limit:]


def failure_location(traceback):
    """Return (operation, stage): the last desktop-view function and the deepest app function."""
    operation = stage = "unknown"
    while traceback is not None:
        code = traceback.tb_frame.f_code
        path = code.co_filename.replace("\\", "/")
        if "/src/" in path:
            stage = code.co_name.strip("_<>") or "unknown"
            if "/src/desktop/" in path:
                operation = "ui." + (code.co_name.strip("_<>") or "unknown")
        traceback = traceback.tb_next
    return operation, stage


def configure_logging(data_dir):
    directory = Path(data_dir) / "logs"
    directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("hangman")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        handler = RotatingFileHandler(directory / "events.log", maxBytes=256_000, backupCount=3)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    return logger


def fix_dropdown_scaling_leak():
    """Unregister destroyed dropdowns from CustomTkinter's scaling tracker.

    CustomTkinter 5.2.2's DropdownMenu.destroy skips CTkScalingBaseClass.destroy, so every
    closed option menu stays registered and the next text-size change raises TclError.
    Removing an already-removed callback is a no-op, so this is safe if fixed upstream.
    """
    try:
        from customtkinter.windows.widgets.core_widget_classes.dropdown_menu import DropdownMenu
        from customtkinter.windows.widgets.scaling import CTkScalingBaseClass
    except ImportError:
        return  # Internals moved in a newer release; never block startup for a workaround.

    if getattr(DropdownMenu.destroy, "unregisters_scaling", False):
        return
    library_destroy = DropdownMenu.destroy

    def destroy(self):
        CTkScalingBaseClass.destroy(self)
        library_destroy(self)

    destroy.unregisters_scaling = True
    DropdownMenu.destroy = destroy


def close_logging():
    """Release the log file; Windows cannot delete or rotate a file that is still open."""
    logger = logging.getLogger("hangman")
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
