"""Drive and photograph the application's own window, without touching the rest of the screen.

Used by release validation to launch the installed program, time its start-up and capture
what it shows. Three rules this module exists to keep:

* Only the application's window is captured (PrintWindow, never a screen grab), so no other
  program can appear in release evidence (incident I-3).
* The capturing process is DPI aware, or Windows reports the window smaller than it is and
  the image is cropped (incident I-4).
* A minimized window cannot be captured at all, and the owner may be using the computer, so
  callers wait for it to be restored rather than saving a picture of nothing.

Windows only.
"""

from __future__ import annotations

import ctypes
import subprocess
import time
from ctypes import wintypes
from pathlib import Path

from src.desktop.capture import _BitmapInfoHeader, _win32

WM_CLOSE = 0x0010
GA_ROOT = 2
PW_RENDERFULLCONTENT = 0x2
DPI_AWARENESS_PER_MONITOR_V2 = -4


def make_dpi_aware():
    """Report true pixel sizes; without this a 125% display crops captures to 80%."""
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(
            ctypes.c_void_p(DPI_AWARENESS_PER_MONITOR_V2)
        )
    except (AttributeError, OSError):  # older Windows: already set by the manifest
        pass


make_dpi_aware()
user32, gdi32 = _win32()
_EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsIconic.argtypes = [wintypes.HWND]
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.SetWindowPos.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
]


def windows_of(pid):
    """Visible top-level windows belonging to ``pid``, as (handle, title)."""
    found = []

    def visit(hwnd, _):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(hwnd):
            title = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, title, 256)
            if title.value:
                found.append((hwnd, title.value))
        return True

    user32.EnumWindows(_EnumWindowsProc(visit), 0)
    return found


def wait_for_window(process, titled="Language Hangman", timeout=60):
    """Return (handle, title, seconds) once the program shows its window."""
    started = time.perf_counter()
    while time.perf_counter() - started < timeout:
        if process.poll() is not None:
            raise RuntimeError(f"the program exited with code {process.poll()}")
        matches = [hit for hit in windows_of(process.pid) if hit[1].startswith(titled)]
        if matches:
            return matches[0][0], matches[0][1], time.perf_counter() - started
        time.sleep(0.05)
    raise TimeoutError(f"no window titled {titled!r} appeared within {timeout}s")


def capture(hwnd, settle=1.5, attempts=5):
    """Return a PIL image of the window, waiting out a minimized or still-drawing window."""
    from PIL import Image

    for attempt in range(attempts):
        time.sleep(settle)
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE: the owner may have minimized it
            continue
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        width, height = rect.right - rect.left, rect.bottom - rect.top
        if width <= 0 or height <= 0:
            continue
        window_dc = user32.GetWindowDC(hwnd)
        memory_dc = gdi32.CreateCompatibleDC(window_dc)
        bitmap = gdi32.CreateCompatibleBitmap(window_dc, width, height)
        previous = gdi32.SelectObject(memory_dc, bitmap)
        try:
            if not user32.PrintWindow(hwnd, memory_dc, PW_RENDERFULLCONTENT):
                raise OSError("Windows could not render the window")
            header = _BitmapInfoHeader(
                biSize=ctypes.sizeof(_BitmapInfoHeader),
                biWidth=width,
                biHeight=-height,
                biPlanes=1,
                biBitCount=32,
                biCompression=0,
            )
            buffer = ctypes.create_string_buffer(width * height * 4)
            if not gdi32.GetDIBits(memory_dc, bitmap, 0, height, buffer, ctypes.byref(header), 0):
                raise OSError("Windows could not read the rendered window")
            return Image.frombuffer("RGB", (width, height), buffer, "raw", "BGRX", 0, 1)
        finally:
            gdi32.SelectObject(memory_dc, previous)
            gdi32.DeleteObject(bitmap)
            gdi32.DeleteDC(memory_dc)
            user32.ReleaseDC(hwnd, window_dc)
    raise OSError("the window stayed minimized or unmapped; nothing was captured")


def is_app_window(image, share=0.05):
    """True when enough of the image is the app's header colour to prove it is our window."""
    pixels = list(image.convert("RGB").get_flattened_data())
    header = sum(
        1
        for red, green, blue in pixels
        if abs(red - 0x15) < 6 and abs(green - 0x5E) < 6 and abs(blue - 0x75) < 6
    )
    return header / len(pixels) > share


def resize(hwnd, width, height):
    """Ask Windows to resize the window (no keyboard or mouse input is sent)."""
    user32.SetWindowPos(hwnd, None, 0, 0, width, height, 0x0002 | 0x0004 | 0x0010)
    time.sleep(1.0)


def close(hwnd, process, timeout=30):
    """Close the window the way the title-bar button does; return the exit code."""
    user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
    try:
        return process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        raise


def launch(executable, environment=None):
    """Start the program and return (process, handle, title, seconds to visible window)."""
    process = subprocess.Popen([str(Path(executable))], env=environment)
    hwnd, title, elapsed = wait_for_window(process)
    return process, hwnd, title, elapsed
