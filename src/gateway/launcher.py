"""Local launcher for the optional FastAPI auth gateway plus Streamlit."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import webbrowser
from collections.abc import Sequence
from threading import Timer
from urllib.error import URLError
from urllib.request import urlopen

import uvicorn

from src.utils.config import PROJECT_ROOT


def run_gateway_with_streamlit(
    *,
    gateway_host: str = "127.0.0.1",
    gateway_port: int = 8000,
    streamlit_port: int = 8501,
    headless: bool = True,
) -> int:
    """Start Streamlit behind the local auth gateway."""
    gateway_port = _available_port(gateway_host, gateway_port)
    streamlit_port = _available_port(gateway_host, streamlit_port, exclude=gateway_port)
    streamlit_url = f"http://localhost:{streamlit_port}"
    login_url = f"http://localhost:{gateway_port}/login"
    logout_url = f"http://localhost:{gateway_port}/logout"
    gateway_environment = {
        "LANGUAGE_HANGMAN_AUTH_GATEWAY_ENABLED": "1",
        "LANGUAGE_HANGMAN_LOGIN_URL": login_url,
        "LANGUAGE_HANGMAN_LOGOUT_URL": logout_url,
        "LANGUAGE_HANGMAN_STREAMLIT_URL": streamlit_url,
    }
    os.environ.update(gateway_environment)
    streamlit_process = subprocess.Popen(
        _build_streamlit_command(port=streamlit_port, headless=True),
        cwd=PROJECT_ROOT,
        env={
            **os.environ,
            **gateway_environment,
        },
    )

    try:
        deadline = time.monotonic() + 45
        while True:
            if streamlit_process.poll() is not None:
                raise RuntimeError("Streamlit exited before it was ready.")
            try:
                with urlopen(f"{streamlit_url}/_stcore/health", timeout=1) as response:
                    if response.status == 200:
                        break
            except (URLError, TimeoutError):
                pass
            if time.monotonic() >= deadline:
                raise RuntimeError("Streamlit did not become ready within 45 seconds.")
            time.sleep(0.2)
        print(f"Open Hangman: {login_url}", flush=True)
        if not headless:
            Timer(1, webbrowser.open, args=(login_url,)).start()
        uvicorn.run(
            "src.gateway.app:create_gateway_app",
            factory=True,
            host=gateway_host,
            port=gateway_port,
            reload=False,
        )
    finally:
        streamlit_process.terminate()
        try:
            streamlit_process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            streamlit_process.kill()
            streamlit_process.wait()

    return 0


def _available_port(host: str, preferred: int, *, exclude: int | None = None) -> int:
    """Choose an unused nearby port without displacing an existing server."""
    for port in range(preferred, min(preferred + 100, 65536)):
        if port == exclude:
            continue
        with socket.socket() as probe:
            try:
                probe.bind((host, port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"No available port near {preferred}.")


def _build_streamlit_command(*, port: int, headless: bool) -> Sequence[str]:
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(PROJECT_ROOT / "app.py"),
        "--server.port",
        str(port),
    ]
    if headless:
        command.extend(["--server.headless", "true"])
    return command
