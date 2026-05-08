#!/usr/bin/env python3
"""
Lexora AI Desktop UI Launcher (Flet ≥ 0.23)

Usage:
    python run_ui.py              # Opens browser automatically (default)
    python run_ui.py --no-browser # Desktop app window only, no browser
    python run_ui.py -nb          # Same as --no-browser
"""

from __future__ import annotations

import argparse
import asyncio
import os
import socket
import sys
from pathlib import Path

import flet as ft
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lexora.runtime_paths import lexora_repo_root
from lexora.ui.app_shell import attach_lexora_shell
from lexora.ui.desktop_branding import apply_desktop_branding

REPO_ROOT = lexora_repo_root(anchor_file=Path(__file__))

load_dotenv(REPO_ROOT / ".env")


def _set_app_icon(page: ft.Page, theme_mode: ft.ThemeMode) -> None:
    apply_desktop_branding(page, theme_mode, anchor_file=Path(__file__))


async def main(page: ft.Page) -> None:
    await attach_lexora_shell(page, set_app_icon=_set_app_icon)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lexora AI Desktop UI")
    parser.add_argument(
        "--no-browser",
        "-nb",
        action="store_true",
        help="Skip auto-opening browser (server runs on localhost only)",
    )
    args = parser.parse_args()

    if sys.platform.startswith("win") and not args.no_browser:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    def _is_port_available(port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False

    def _pick_port() -> int:
        env_port = os.getenv("LEXORA_UI_PORT")
        if env_port:
            try:
                requested = int(env_port)
                if _is_port_available(requested):
                    return requested
            except ValueError:
                pass
        return 0

    port = _pick_port()
    # Use real desktop window mode for --no-browser so OS window/taskbar icon
    # overrides are applied by the native host (HIDDEN mode can keep default icon).
    view_mode = ft.AppView.FLET_APP if args.no_browser else ft.AppView.WEB_BROWSER
    print(f"Starting Lexora UI on port {port if port else 'auto'}")
    print(f"View mode: {'Desktop app window (no browser auto-open)' if args.no_browser else 'Web Browser (auto-open)'}")
    ft.app(target=main, view=view_mode, port=port, assets_dir=str(REPO_ROOT / "assets"))
