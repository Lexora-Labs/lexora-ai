"""
Lexora AI Desktop UI - Main Entry Point

A minimal desktop test harness for the lexora-ai translation engine.
Built with Flet for cross-platform support.
"""

import flet as ft
from lexora.ui.views.home import HomeView


# Color System: Lexora Blueprint Expanded (Dark Mode)
class Colors:
    BACKGROUND = "#0F172A"      # Dark Navy
    SURFACE = "#1E293B"         # Dark Slate
    PRIMARY = "#06B6D4"         # Bright Cyan
    TEXT_PRIMARY = "#F8FAFC"    # Off-White
    TEXT_SECONDARY = "#94A3B8"  # Light Gray
    ERROR = "#F43F5E"           # Coral Red
    SUCCESS = "#10B981"         # Emerald Green


def main(page: ft.Page):
    """Main application entry point."""
    
    # Page configuration
    page.title = "Lexora AI"
    page.window.width = 600
    page.window.height = 800
    page.window.min_width = 500
    page.window.min_height = 600
    page.bgcolor = Colors.BACKGROUND
    page.padding = 0
    
    # Theme
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=Colors.PRIMARY,
            surface=Colors.SURFACE,
            background=Colors.BACKGROUND,
            error=Colors.ERROR,
        ),
    )
    
    # Create home view
    home_view = HomeView(page)
    
    # Add to page
    page.add(home_view)
    page.update()


if __name__ == "__main__":
    ft.app(target=main)
