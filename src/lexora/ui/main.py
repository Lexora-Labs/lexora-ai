"""
Lexora AI Desktop UI - Main Entry Point

Full app shell (navigation, EN/VI, jobs, translate, settings) per UI plan.
"""

from __future__ import annotations

import asyncio
import base64
import os
import socket
import sys
from pathlib import Path
from typing import Any, cast

import flet as ft

from lexora.runtime_paths import lexora_repo_root
from lexora.ui.app_shell import attach_lexora_shell


REPO_ROOT = lexora_repo_root(anchor_file=Path(__file__))
BRANDING_DIR = REPO_ROOT / "assets" / "branding"
BRANDING_APP_ICON_ICO = REPO_ROOT / "lexora-ai-icon.ico"
BRANDING_APP_ICON_ASSET_PATH = "./lexora-ai-icon.ico"
BRANDING_LOGO_DARK_SVG = BRANDING_DIR / "lexora-ai-logo-dark-v2.2.svg"
BRANDING_LOGO_LIGHT_SVG = BRANDING_DIR / "lexora-ai-logo-light-v2.2.svg"
BRANDING_LOGO_FALLBACK_SVG = BRANDING_DIR / "lexora-ai-logo.svg"


def _resolve_logo_path(theme_mode: ft.ThemeMode) -> Path:
    preferred = BRANDING_LOGO_LIGHT_SVG
    if preferred.exists():
        return preferred
    return BRANDING_LOGO_FALLBACK_SVG


def _load_logo_data_uri(theme_mode: ft.ThemeMode) -> str | None:
    logo_path = _resolve_logo_path(theme_mode)
    if not logo_path.exists():
        return None
    svg_bytes = logo_path.read_bytes()
    encoded = base64.b64encode(svg_bytes).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _set_app_icon(page: ft.Page, theme_mode: ft.ThemeMode) -> None:
    page_any = cast(Any, page)
    logo_path = _resolve_logo_path(theme_mode)
    logo_data_uri = _load_logo_data_uri(theme_mode)
    has_svg = bool(logo_data_uri) or logo_path.exists()
    has_ico = BRANDING_APP_ICON_ICO.exists()
    if not has_svg and not has_ico:
        return

    icon_path = str((BRANDING_APP_ICON_ICO if has_ico else logo_path).resolve())
    window_obj = getattr(page_any, "window", None)
    if window_obj is not None and hasattr(window_obj, "icon"):
        setattr(window_obj, "icon", icon_path)
    if hasattr(page_any, "window_icon"):
        setattr(page_any, "window_icon", icon_path)

    if hasattr(page_any, "favicon"):
        if has_svg:
            setattr(page_any, "favicon", logo_data_uri or logo_path.as_posix())
        elif has_ico:
            setattr(page_any, "favicon", BRANDING_APP_ICON_ASSET_PATH)
    try:
        page.update()
    except Exception:
        pass


def main(page: ft.Page) -> None:
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

    attach_lexora_shell(page, set_app_icon=_set_app_icon)


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
