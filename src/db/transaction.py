"""One connection per unit of work, including nested repository calls."""

from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from src.db.database import create_connection

_active = ContextVar("hangman_transaction", default=None)


def current_connection(path):
    active = _active.get()
    if active is not None and active[0] == Path(path).resolve():
        return active[1]
    return None


@contextmanager
def transaction(path):
    existing = current_connection(path)
    if existing is not None:
        yield existing
        return
    connection = create_connection(path)
    token = _active.set((Path(path).resolve(), connection))
    try:
        connection.execute("BEGIN IMMEDIATE")
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        _active.reset(token)
        connection.close()
