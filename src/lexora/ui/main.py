"""
Lexora AI Desktop UI - Main Entry Point

Full app shell (navigation, EN/VI, jobs, translate, settings) per UI plan.
"""

from __future__ import annotations

import asyncio
import os
import socket
import sys
from pathlib import Path
from typing import Any, cast

import flet as ft

from lexora.runtime_paths import lexora_repo_root
from lexora.ui.app_shell import attach_lexora_shell
from lexora.ui.desktop_branding import apply_desktop_branding


REPO_ROOT = lexora_repo_root(anchor_file=Path(__file__))


def _set_app_icon(page: ft.Page, theme_mode: ft.ThemeMode) -> None:
    apply_desktop_branding(page, theme_mode, anchor_file=Path(__file__))


async def main(page: ft.Page) -> None:
    page.title = "Lexora AI"
    _set_app_icon(page, ft.ThemeMode.SYSTEM)
    page.update()
    page_any = cast(Any, page)
    window_obj = getattr(page_any, "window", None)
    if window_obj is not None:
        setattr(window_obj, "width", 1100)
        setattr(window_obj, "height", 750)
        setattr(window_obj, "min_width", 800)
        setattr(window_obj, "min_height", 600)
    else:
        setattr(page_any, "window_width", 1100)
        setattr(page_any, "window_height", 750)
        setattr(page_any, "window_min_width", 800)
        setattr(page_any, "window_min_height", 600)
    page.padding = 0

    await attach_lexora_shell(page, set_app_icon=_set_app_icon)


if __name__ == "__main__":
    # Desktop ``ft.AppView.FLET_APP`` spawns the native Flet view via asyncio subprocesses.
    # ``WindowsSelectorEventLoopPolicy`` does not implement subprocess transport → NotImplementedError
    # in frozen ``flet pack`` builds. Use the proactor loop (Python default on Windows 3.8+).
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

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

    ft.app(
        target=main,
        view=ft.AppView.FLET_APP,
        port=_pick_port(),
        assets_dir=str(REPO_ROOT / "assets"),
    )
