"""
Lexora AI Desktop UI - Main Entry Point

A minimal desktop test harness for the lexora-ai translation engine.
Built with Flet for cross-platform support.
"""

import flet as ft
from lexora.ui.views.home import HomeView
from lexora.ui.theme import (
    Colors,
    apply_theme,
    cycle_theme_mode,
    theme_mode_icon,
    theme_mode_label,
)


def main(page: ft.Page):
    """Main application entry point."""

    # Page configuration
    page.title = "Lexora AI"
    page.window.width = 600
    page.window.height = 800
    page.window.min_width = 500
    page.window.min_height = 600
    page.padding = 0

    # Apply default theme (dark) – also sets page.theme / page.dark_theme
    apply_theme(page, ft.ThemeMode.DARK)
    page.bgcolor = Colors.BACKGROUND

    # Create home view
    home_view = HomeView(page)

    # Add to page
    page.add(home_view)
    page.update()


if __name__ == "__main__":
    ft.app(target=main)
