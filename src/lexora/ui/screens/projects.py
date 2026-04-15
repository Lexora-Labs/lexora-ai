"""
Projects screen — workspace (planned) plus Library tab for translated outputs.
"""

from __future__ import annotations

import flet as ft
from typing import Callable

from lexora.ui.theme import Colors
from lexora.ui.screens.library import LibraryScreen


class ProjectsScreen(ft.Container):
    """Projects hub: future project grid + current library of outputs."""

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
        workspace = ft.Container(
            padding=24,
            bgcolor=Colors.SURFACE,
            border_radius=10,
            content=ft.Column(
                [
                    ft.Icon(ft.icons.FOLDER_SPECIAL_OUTLINED, size=48, color=Colors.PRIMARY),
                    ft.Container(height=12),
                    ft.Text(
                        self._t("page.projects.title"),
                        size=20,
                        weight=ft.FontWeight.W_600,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        self._t("placeholder.projects_workspace"),
                        size=14,
                        color=Colors.TEXT_SECONDARY,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
        )

        library = LibraryScreen(self._page)

        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=200,
            tabs=[
                ft.Tab(text=self._t("nav.projects"), icon=ft.icons.FOLDER_OUTLINED, content=workspace),
                ft.Tab(text=self._t("nav.library"), icon=ft.icons.LIBRARY_BOOKS_OUTLINED, content=library),
            ],
            expand=True,
        )

        self.content = ft.Column([self.tabs], expand=True)
        self.expand = True

    def select_library_tab(self) -> None:
        """Show translated outputs tab (index 1)."""
        self.tabs.selected_index = 1
        self._page.update()

    def select_workspace_tab(self) -> None:
        """Show workspace (first tab)."""
        self.tabs.selected_index = 0
        self._page.update()

    def relocalize(self, t: Callable[[str], str]) -> None:
        """Refresh tab labels after locale change."""
        self._t = t
        if len(self.tabs.tabs) >= 2:
            self.tabs.tabs[0].text = t("nav.projects")
            self.tabs.tabs[1].text = t("nav.library")
        self.tabs.update()
