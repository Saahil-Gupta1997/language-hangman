"""Supported native desktop entry point; no browser or local server required."""

from src.desktop.runtime import InstanceLock
from src.utils.config import DATABASE_PATH


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Language Hangman desktop")
    parser.add_argument("--smoke-test", metavar="OUTPUT_DIRECTORY")
    # Internal: a child process of --smoke-test that is ended abruptly to test recovery.
    parser.add_argument("--smoke-crash", nargs=2, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.smoke_test:
        from src.desktop.smoke import run

        return run(args.smoke_test)
    if args.smoke_crash:
        from src.desktop.smoke import crash_child

        return crash_child(*args.smoke_crash)
    import tkinter as tk
    from tkinter import messagebox

    try:
        lock = InstanceLock(DATABASE_PATH.with_suffix(".lock"))
    except RuntimeError as error:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Language Hangman", str(error))
        root.destroy()
        return 1
    try:
        from src.desktop.application import HangmanDesktop
        from src.desktop.recovery import RecoveryWindow
        from src.services.desktop_storage import DatabaseUnavailableError
        from src.utils.config import DATA_DIR

        while True:
            try:
                app = HangmanDesktop()
            except DatabaseUnavailableError as error:
                # Recovery never opens the damaged file; after a restore, start normally.
                recovery = RecoveryWindow(DATABASE_PATH, DATA_DIR, str(error))
                recovery.mainloop()
                if recovery.restored:
                    continue
                return 1
            app.mainloop()
            return 0
    except Exception as error:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Unable to start",
            "Language Hangman could not start. Check disk space and folder permissions, "
            "then reinstall if the problem continues. Your saved data is not deleted.\n"
            f"Error type: {type(error).__name__}",
        )
        root.destroy()
        return 1
    finally:
        lock.close()


if __name__ == "__main__":
    raise SystemExit(main())
