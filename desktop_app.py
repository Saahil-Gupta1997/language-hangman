"""Supported native desktop entry point; no browser or local server required."""

from src.desktop.runtime import InstanceLock
from src.utils.config import DATABASE_PATH


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Language Hangman desktop")
    parser.add_argument("--smoke-test", metavar="OUTPUT_DIRECTORY")
    args = parser.parse_args()
    if args.smoke_test:
        from src.desktop.smoke import run

        return run(args.smoke_test)
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

        app = HangmanDesktop()
        app.mainloop()
    except Exception as error:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Unable to start",
            "Hangman could not open its local data. "
            "Check disk space and folder permissions, or restore a backup.\n"
            f"Error type: {type(error).__name__}",
        )
        root.destroy()
        return 1
    finally:
        lock.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
