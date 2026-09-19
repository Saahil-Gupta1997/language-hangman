"""Capture only the application's own window, never the rest of the screen.

Screen-region grabs copy whatever is visible, so another program in front of the app would
be recorded. PrintWindow asks Windows to paint just this window into an off-screen bitmap,
even when it is covered. Used by the smoke journey and the demo recorder; Windows only.
"""

import ctypes
from ctypes import wintypes

PW_RENDERFULLCONTENT = 0x2
GA_ROOT = 2


class _BitmapInfoHeader(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


def _win32():
    """Declare exact prototypes; 64-bit handles are truncated by ctypes' int default."""
    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
    signatures = [
        (user32.GetAncestor, wintypes.HWND, [wintypes.HWND, wintypes.UINT]),
        (user32.GetWindowRect, wintypes.BOOL, [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]),
        (user32.GetWindowDC, wintypes.HDC, [wintypes.HWND]),
        (user32.ReleaseDC, ctypes.c_int, [wintypes.HWND, wintypes.HDC]),
        (user32.PrintWindow, wintypes.BOOL, [wintypes.HWND, wintypes.HDC, wintypes.UINT]),
        (gdi32.CreateCompatibleDC, wintypes.HDC, [wintypes.HDC]),
        (
            gdi32.CreateCompatibleBitmap,
            wintypes.HBITMAP,
            [wintypes.HDC, ctypes.c_int, ctypes.c_int],
        ),
        (gdi32.SelectObject, wintypes.HGDIOBJ, [wintypes.HDC, wintypes.HGDIOBJ]),
        (gdi32.DeleteObject, wintypes.BOOL, [wintypes.HGDIOBJ]),
        (gdi32.DeleteDC, wintypes.BOOL, [wintypes.HDC]),
        (
            gdi32.GetDIBits,
            ctypes.c_int,
            [
                wintypes.HDC,
                wintypes.HBITMAP,
                wintypes.UINT,
                wintypes.UINT,
                ctypes.c_void_p,
                ctypes.c_void_p,
                wintypes.UINT,
            ],
        ),
    ]
    for function, result, arguments in signatures:
        function.restype, function.argtypes = result, arguments
    return user32, gdi32


def capture_window(window):
    """Return a PIL image of ``window`` (a Tk toplevel) rendered by Windows itself."""
    from PIL import Image

    user32, gdi32 = _win32()
    window.update()
    hwnd = user32.GetAncestor(wintypes.HWND(window.winfo_id()), GA_ROOT)
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width, height = rect.right - rect.left, rect.bottom - rect.top
    if width <= 0 or height <= 0:
        raise OSError("The window is not visible.")
    window_dc = user32.GetWindowDC(hwnd)
    memory_dc = gdi32.CreateCompatibleDC(window_dc)
    bitmap = gdi32.CreateCompatibleBitmap(window_dc, width, height)
    previous = gdi32.SelectObject(memory_dc, bitmap)
    try:
        if not user32.PrintWindow(hwnd, memory_dc, PW_RENDERFULLCONTENT):
            raise OSError("Windows could not render the window.")
        header = _BitmapInfoHeader(
            biSize=ctypes.sizeof(_BitmapInfoHeader),
            biWidth=width,
            biHeight=-height,  # top-down rows
            biPlanes=1,
            biBitCount=32,
            biCompression=0,
        )
        buffer = ctypes.create_string_buffer(width * height * 4)
        if not gdi32.GetDIBits(memory_dc, bitmap, 0, height, buffer, ctypes.byref(header), 0):
            raise OSError("Windows could not read the rendered window.")
        return Image.frombuffer("RGB", (width, height), buffer, "raw", "BGRX", 0, 1)
    finally:
        gdi32.SelectObject(memory_dc, previous)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(memory_dc)
        user32.ReleaseDC(hwnd, window_dc)
