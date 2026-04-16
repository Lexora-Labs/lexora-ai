#!/usr/bin/env python3
"""
Lexora AI Desktop UI Launcher (Flet 0.21.x)

Usage:
    python run_ui.py              # Opens browser automatically (default)
    python run_ui.py --no-browser # Desktop app window only, no browser
    python run_ui.py -nb          # Same as --no-browser
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import os
import socket
import sys
from pathlib import Path
from typing import Any, cast

import flet as ft
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lexora.ui.app_shell import attach_lexora_shell

REPO_ROOT = Path(__file__).resolve().parent
BRANDING_DIR = REPO_ROOT / "assets" / "branding"
BRANDING_APP_ICON_ICO = REPO_ROOT / "lexora-ai-icon.ico"
BRANDING_APP_ICON_ASSET_PATH = "./lexora-ai-icon.ico"
BRANDING_LOGO_DARK_SVG = BRANDING_DIR / "lexora-ai-logo-dark-v2.2.svg"
BRANDING_LOGO_LIGHT_SVG = BRANDING_DIR / "lexora-ai-logo-light-v2.2.svg"
BRANDING_LOGO_FALLBACK_SVG = BRANDING_DIR / "lexora-ai-logo.svg"

load_dotenv(REPO_ROOT / ".env")


def _resolve_logo_path(theme_mode: ft.ThemeMode, page: ft.Page | None = None) -> Path:
    preferred = BRANDING_LOGO_LIGHT_SVG
    if preferred.exists():
        return preferred
    return BRANDING_LOGO_FALLBACK_SVG


def _load_logo_data_uri(theme_mode: ft.ThemeMode, page: ft.Page | None = None) -> str | None:
    logo_path = _resolve_logo_path(theme_mode, page)
    if not logo_path.exists():
        return None
    svg_bytes = logo_path.read_bytes()
    encoded = base64.b64encode(svg_bytes).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _set_app_icon(page: ft.Page, theme_mode: ft.ThemeMode) -> None:
    page_any = cast(Any, page)
    logo_path = _resolve_logo_path(theme_mode, page)
    logo_data_uri = _load_logo_data_uri(theme_mode, page)
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
    attach_lexora_shell(page, set_app_icon=_set_app_icon)


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
