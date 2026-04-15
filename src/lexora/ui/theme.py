"""
Lexora AI – Centralized Theme System

Defines color palettes for dark and light modes and provides
utility functions for building Flet Theme objects.

Usage:
    from lexora.ui.theme import Colors, DARK_PALETTE, LIGHT_PALETTE
    from lexora.ui.theme import make_flet_theme, get_palette, apply_theme

    # In main():
    apply_theme(page, ft.ThemeMode.DARK)
    ...
    # When the user switches theme:
    apply_theme(page, ft.ThemeMode.LIGHT)
    page.update()
"""

from __future__ import annotations

import flet as ft
import threading
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Color Palettes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ColorPalette:
    """Immutable color palette for a single theme variant."""

    BACKGROUND: str
    SURFACE: str
    SURFACE_VARIANT: str
    PRIMARY: str
    PRIMARY_DARK: str       # darker variant for hover / emphasis
    TEXT_PRIMARY: str
    TEXT_SECONDARY: str
    ERROR: str
    SUCCESS: str
    WARNING: str
    DIVIDER: str
    BORDER: str
    INFO: str               # accent color for variety


# Lexora Blueprint – Dark (see lexora-project/docs/40-planning/flet-ui-desktop-web-plan.md)
DARK_PALETTE = ColorPalette(
    BACKGROUND="#0F1724",
    SURFACE="#162233",
    SURFACE_VARIANT="#1B2A3F",
    PRIMARY="#2F6FED",
    PRIMARY_DARK="#255ECE",
    TEXT_PRIMARY="#E5ECF6",
    TEXT_SECONDARY="#8FA4BF",
    ERROR="#D94C4C",
    SUCCESS="#1FA971",
    WARNING="#F0A43A",
    DIVIDER="#2B3A52",
    BORDER="#2B3A52",
    INFO="#5A8BB0",
)

# Lexora Blueprint – Light
LIGHT_PALETTE = ColorPalette(
    BACKGROUND="#EEF3FA",
    SURFACE="#F5F8FC",
    SURFACE_VARIANT="#E8EEF6",
    PRIMARY="#2F6FED",
    PRIMARY_DARK="#255ECE",
    TEXT_PRIMARY="#0F172A",
    TEXT_SECONDARY="#475569",
    ERROR="#D94C4C",
    SUCCESS="#1FA971",
    WARNING="#F0A43A",
    DIVIDER="#D4DEEA",
    BORDER="#D4DEEA",
    INFO="#5A8BB0",
)


# ---------------------------------------------------------------------------
# Convenience class – backward-compatible alias used across UI files
# ---------------------------------------------------------------------------

class Colors:
    """
    Current-theme color tokens.

    This class is populated by :func:`apply_theme` and acts as a
    module-level singleton that all UI components can import directly::

        from lexora.ui.theme import Colors
        ...
        bgcolor=Colors.BACKGROUND

    Colors are updated in-place when the user switches themes, so components
    that rebuild on navigation will automatically use the correct palette.
    """

    BACKGROUND: str = DARK_PALETTE.BACKGROUND
    SURFACE: str = DARK_PALETTE.SURFACE
    SURFACE_VARIANT: str = DARK_PALETTE.SURFACE_VARIANT
    PRIMARY: str = DARK_PALETTE.PRIMARY
    PRIMARY_DARK: str = DARK_PALETTE.PRIMARY_DARK
    TEXT_PRIMARY: str = DARK_PALETTE.TEXT_PRIMARY
    TEXT_SECONDARY: str = DARK_PALETTE.TEXT_SECONDARY
    ERROR: str = DARK_PALETTE.ERROR
    SUCCESS: str = DARK_PALETTE.SUCCESS
    WARNING: str = DARK_PALETTE.WARNING
    DIVIDER: str = DARK_PALETTE.DIVIDER
    BORDER: str = DARK_PALETTE.BORDER
    INFO: str = DARK_PALETTE.INFO

    _lock: threading.Lock = threading.Lock()

    @classmethod
    def update_from_palette(cls, palette: ColorPalette) -> None:
        """Update all color tokens from *palette* in a thread-safe manner."""
        with cls._lock:
            cls.BACKGROUND = palette.BACKGROUND
            cls.SURFACE = palette.SURFACE
            cls.SURFACE_VARIANT = palette.SURFACE_VARIANT
            cls.PRIMARY = palette.PRIMARY
            cls.PRIMARY_DARK = palette.PRIMARY_DARK
            cls.TEXT_PRIMARY = palette.TEXT_PRIMARY
            cls.TEXT_SECONDARY = palette.TEXT_SECONDARY
            cls.ERROR = palette.ERROR
            cls.SUCCESS = palette.SUCCESS
            cls.WARNING = palette.WARNING
            cls.DIVIDER = palette.DIVIDER
            cls.BORDER = palette.BORDER
            cls.INFO = palette.INFO


# ---------------------------------------------------------------------------
# Flet Theme Factories
# ---------------------------------------------------------------------------

def _make_color_scheme(palette: ColorPalette) -> ft.ColorScheme:
    """Build a Flet ColorScheme from a palette."""
    return ft.ColorScheme(
        primary=palette.PRIMARY,
        primary_container=palette.PRIMARY_DARK,
        secondary=palette.PRIMARY,
        surface=palette.SURFACE,
        background=palette.BACKGROUND,
        error=palette.ERROR,
        on_primary="#FFFFFF",
        on_primary_container="#FFFFFF",
        on_surface=palette.TEXT_PRIMARY,
        on_background=palette.TEXT_PRIMARY,
        on_error="#FFFFFF",
        outline=palette.BORDER,
    )


def make_flet_theme(palette: ColorPalette) -> ft.Theme:
    """
    Build a ``ft.Theme`` from a :class:`ColorPalette`.

    The returned theme configures component defaults so that most
    standard Flet controls will adopt Lexora branding automatically.
    """
    return ft.Theme(
        color_scheme=_make_color_scheme(palette),
        font_family="Inter, Segoe UI, Arial, sans-serif",
        scrollbar_theme=ft.ScrollbarTheme(
            thumb_color=palette.TEXT_SECONDARY,
            track_color=palette.SURFACE,
        ),
    )


# Pre-built themes – import these directly to avoid re-creating each call
DARK_THEME = make_flet_theme(DARK_PALETTE)
LIGHT_THEME = make_flet_theme(LIGHT_PALETTE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_palette(theme_mode: ft.ThemeMode, page: Optional[ft.Page] = None) -> ColorPalette:
    """
    Return the appropriate :class:`ColorPalette` for *theme_mode*.

    For ``ft.ThemeMode.SYSTEM``, checks ``page.platform_brightness`` if page
    is provided; otherwise falls back to :data:`DARK_PALETTE`.
    """
    if theme_mode == ft.ThemeMode.LIGHT:
        return LIGHT_PALETTE
    elif theme_mode == ft.ThemeMode.SYSTEM and page is not None and hasattr(page, "platform_brightness"):
        return (
            LIGHT_PALETTE
            if page.platform_brightness == ft.Brightness.LIGHT
            else DARK_PALETTE
        )
    return DARK_PALETTE  # DARK and SYSTEM (without page) default to dark palette


def apply_theme(page: ft.Page, theme_mode: ft.ThemeMode) -> ColorPalette:
    """
    Apply *theme_mode* to *page* and update the module-level
    :class:`Colors` singleton.

    Returns the active :class:`ColorPalette` so callers can pass it
    to view-builder functions that need it at construction time.

    Example::

        palette = apply_theme(page, ft.ThemeMode.LIGHT)
        page.update()
    """
    page.theme = LIGHT_THEME
    page.dark_theme = DARK_THEME
    page.theme_mode = theme_mode

    palette = get_palette(theme_mode, page)
    Colors.update_from_palette(palette)
    return palette


def cycle_theme_mode(current: ft.ThemeMode) -> ft.ThemeMode:
    """Cycle through DARK → LIGHT → SYSTEM → DARK …"""
    order = [ft.ThemeMode.DARK, ft.ThemeMode.LIGHT, ft.ThemeMode.SYSTEM]
    try:
        idx = order.index(current)
    except ValueError:
        idx = 0
    return order[(idx + 1) % len(order)]


def theme_mode_icon(mode: ft.ThemeMode) -> str:
    """Return a Flet icon name matching the current theme mode."""
    icons = {
        ft.ThemeMode.DARK: ft.icons.DARK_MODE,
        ft.ThemeMode.LIGHT: ft.icons.LIGHT_MODE,
        ft.ThemeMode.SYSTEM: ft.icons.BRIGHTNESS_AUTO,
    }
    return icons.get(mode, ft.icons.DARK_MODE)


def theme_mode_label(mode: ft.ThemeMode) -> str:
    """Return a human-readable label for *mode*."""
    labels = {
        ft.ThemeMode.DARK: "Dark",
        ft.ThemeMode.LIGHT: "Light",
        ft.ThemeMode.SYSTEM: "System",
    }
    return labels.get(mode, "Dark")
