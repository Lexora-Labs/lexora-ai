"""
Lexora AI Desktop UI - Main Entry Point

A minimal desktop test harness for the lexora-ai translation engine.
Built with Flet for cross-platform support.
"""

import os
import socket
import sys
import asyncio
from pathlib import Path
import flet as ft
from lexora.ui.views.home import HomeView
from lexora.ui.theme import (
    Colors,
    apply_theme,
    cycle_theme_mode,
    theme_mode_icon,
    theme_mode_label,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
BRANDING_DIR = REPO_ROOT / "assets" / "branding"
BRANDING_APP_ICON_ICO = BRANDING_DIR / "lexora-ai-icon.ico"
BRANDING_APP_ICON_ASSET_PATH = "branding/lexora-ai-icon.ico"
BRANDING_LOGO_DARK_SVG = BRANDING_DIR / "lexora-ai-logo-dark-v2.2.svg"
BRANDING_LOGO_LIGHT_SVG = BRANDING_DIR / "lexora-ai-logo-light-v2.2.svg"
BRANDING_LOGO_FALLBACK_SVG = BRANDING_DIR / "lexora-ai-logo.svg"


def _resolve_logo_path(theme_mode: ft.ThemeMode) -> Path:
    if theme_mode == ft.ThemeMode.LIGHT:
        preferred = BRANDING_LOGO_LIGHT_SVG
    else:
        preferred = BRANDING_LOGO_DARK_SVG
    if preferred.exists():
        return preferred
    return BRANDING_LOGO_FALLBACK_SVG


def _set_app_icon(page: ft.Page, theme_mode: ft.ThemeMode) -> None:
    """Set app/window icon and favicon from the branding ICO when available."""
    logo_path = _resolve_logo_path(theme_mode)
    has_svg = logo_path.exists()
    has_ico = BRANDING_APP_ICON_ICO.exists()
    if not has_svg and not has_ico:
        return

    icon_path = str((BRANDING_APP_ICON_ICO if has_ico else logo_path).resolve())
    if hasattr(page, "window") and hasattr(page.window, "icon"):
        page.window.icon = icon_path
    elif hasattr(page, "window_icon"):
        page.window_icon = icon_path

    if hasattr(page, "favicon"):
        page.favicon = BRANDING_APP_ICON_ASSET_PATH if has_ico else logo_path.as_posix()


def main(page: ft.Page):
    """Main application entry point."""

    current_theme_mode = ft.ThemeMode.DARK

    # Page configuration
    page.title = "Lexora AI"
    _set_app_icon(page, current_theme_mode)
    if hasattr(page, "window"):
        page.window.width = 600
        page.window.height = 800
        page.window.min_width = 500
        page.window.min_height = 600
    else:
        page.window_width = 600
        page.window_height = 800
        page.window_min_width = 500
        page.window_min_height = 600
    page.padding = 0

    # Apply default theme (dark) – also sets page.theme / page.dark_theme
    apply_theme(page, current_theme_mode)
    page.bgcolor = Colors.BACKGROUND

    # Create home view
    home_view = HomeView(page)

    # Add to page
    page.add(home_view)
    page.update()


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        # Avoid Proactor transport shutdown races on Windows (WinError 10054).
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    def _is_port_available(port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False

    def _pick_port(default: int = 8550) -> int:
        env_port = os.getenv("LEXORA_UI_PORT")
        if env_port:
            try:
                requested = int(env_port)
                if _is_port_available(requested):
                    return requested
            except ValueError:
                pass

        return 0

    ft.app(target=main, port=_pick_port(), assets_dir=str(REPO_ROOT / "assets"))
