"""
Sidebar Component - Navigation Rail

Collapsible sidebar with main navigation menu.
"""

import flet as ft
from typing import Callable, Optional

from lexora.ui.theme import Colors


class Sidebar(ft.Container):
    """
    Collapsible sidebar with NavigationRail.
    
    Menu items:
    - Translate
    - Library
    - Jobs
    - Settings
    """

    def __init__(
        self,
        page: ft.Page,
        on_navigate: Optional[Callable[[int], None]] = None,
        selected_index: int = 0,
    ):
        super().__init__()
        self._page = page
        self.on_navigate = on_navigate
        self._selected_index = selected_index
        self._expanded = True
        
        self._build()

    def _build(self):
        """Build the sidebar UI."""
        
        # Navigation items
        self.nav_rail = ft.NavigationRail(
            selected_index=self._selected_index,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=80,
            min_extended_width=200,
            extended=self._expanded,
            bgcolor=Colors.SURFACE,
            indicator_color=Colors.PRIMARY,
            on_change=self._on_nav_change,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.icons.TRANSLATE_OUTLINED,
                    selected_icon=ft.icons.TRANSLATE,
                    label="Translate",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.LIBRARY_BOOKS_OUTLINED,
                    selected_icon=ft.icons.LIBRARY_BOOKS,
                    label="Library",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.WORK_HISTORY_OUTLINED,
                    selected_icon=ft.icons.WORK_HISTORY,
                    label="Jobs",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.SETTINGS_OUTLINED,
                    selected_icon=ft.icons.SETTINGS,
                    label="Settings",
                ),
            ],
        )
        
        # Toggle button
        self.toggle_btn = ft.IconButton(
            icon=ft.icons.MENU_OPEN if self._expanded else ft.icons.MENU,
            icon_color=Colors.TEXT_SECONDARY,
            tooltip="Toggle sidebar",
            on_click=self._toggle_sidebar,
        )

        # Logo mark - simple book icon
        self.logo_mark = ft.Icon(
            ft.icons.MENU_BOOK,
            color=Colors.PRIMARY,
            size=32,
        )

        self.logo_text = ft.Text(
            "Lexora",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=Colors.TEXT_PRIMARY,
            visible=self._expanded,
        )

        # Logo/Brand
        self.logo = ft.Container(
            content=ft.Row(
                controls=[
                    self.logo_mark,
                    self.logo_text,
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(vertical=16),
        )

        self.top_divider = ft.Divider(height=1, color=Colors.DIVIDER)
        self.bottom_divider = ft.Divider(height=1, color=Colors.DIVIDER)

        # Layout
        self.content = ft.Column(
            controls=[
                self.logo,
                self.top_divider,
                ft.Container(
                    content=self.nav_rail,
                    expand=True,
                ),
                self.bottom_divider,
                ft.Container(
                    content=self.toggle_btn,
                    alignment=ft.alignment.center,
                    padding=8,
                ),
            ],
            spacing=0,
            expand=True,
        )
        
        self.bgcolor = Colors.SURFACE
        self.border_radius = ft.border_radius.only(top_right=12, bottom_right=12)
        self._apply_theme()

    def _apply_theme(self):
        """Refresh theme-sensitive sidebar colors."""
        self.logo_mark.color = Colors.PRIMARY
        self.logo_text.color = Colors.TEXT_PRIMARY
        self.nav_rail.bgcolor = Colors.SURFACE
        self.nav_rail.indicator_color = Colors.PRIMARY
        self.toggle_btn.icon_color = Colors.TEXT_SECONDARY
        self.top_divider.color = Colors.DIVIDER
        self.bottom_divider.color = Colors.DIVIDER
        self.bgcolor = Colors.SURFACE

    def before_update(self):
        """Keep sidebar visuals in sync with the active theme."""
        self._apply_theme()

    def _on_nav_change(self, e):
        """Handle navigation change."""
        self._selected_index = e.control.selected_index
        if self.on_navigate:
            self.on_navigate(self._selected_index)

    def _toggle_sidebar(self, e):
        """Toggle sidebar expanded/collapsed state."""
        self._expanded = not self._expanded
        self.nav_rail.extended = self._expanded
        self.toggle_btn.icon = ft.icons.MENU_OPEN if self._expanded else ft.icons.MENU
        
        # Toggle logo text visibility
        self.logo_text.visible = self._expanded
        
        self.update()

    def set_selected(self, index: int):
        """Set selected navigation index."""
        self._selected_index = index
        self.nav_rail.selected_index = index
        self.update()

    @property
    def is_expanded(self) -> bool:
        """Check if sidebar is expanded."""
        return self._expanded
