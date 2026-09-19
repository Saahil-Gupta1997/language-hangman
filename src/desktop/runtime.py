"""Single-process ownership and bounded local event logs."""

import logging
import os
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
