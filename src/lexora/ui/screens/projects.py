"""
Library root screen.
"""

from __future__ import annotations

import flet as ft
from typing import Callable

from lexora.ui.screens.library import LibraryScreen


class ProjectsScreen(ft.Container):
    """Compatibility wrapper: left-nav Library points to LibraryScreen."""

    def __init__(
        self,
        page: ft.Page,
        t: Callable[[str], str],
    ):
        super().__init__()
        self._page = page
        self._t = t
        self._build()

    def _build(self) -> None:
        self.library = LibraryScreen(self._page)
        self.content = ft.Column([self.library], expand=True)
        self.expand = True

    def select_library_tab(self) -> None:
        """Compatibility no-op: screen is library-only."""
        self._page.update()

    def select_workspace_tab(self) -> None:
        """Compatibility no-op: workspace tab was removed."""
        self._page.update()

    def relocalize(self, t: Callable[[str], str]) -> None:
        """Refresh localized callbacks/state."""
        self._t = t
