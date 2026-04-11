"""
Header Component

Top header bar with title, search, and actions.
"""

import flet as ft
from typing import Optional, Callable

from lexora.ui.theme import Colors


class Header(ft.Container):
    """
    Top header bar.
    
    Contains:
    - Page title
    - Search (optional)
    - User actions
    """

    def __init__(
        self,
        title: str = "Dashboard",
        subtitle: Optional[str] = None,
        show_search: bool = False,
        on_toggle_theme: Optional[Callable[[ft.ControlEvent], None]] = None,
        theme_icon: Optional[str] = None,
    ):
        super().__init__()
        self._title = title
        self._subtitle = subtitle
        self._show_search = show_search
        self._on_toggle_theme = on_toggle_theme
        self._theme_icon = theme_icon or ft.icons.DARK_MODE
        
        self._build()

    def _build(self):
        """Build the header UI."""
        
        # Title section
        title_col = ft.Column(
            controls=[
                ft.Text(
                    self._title,
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=Colors.TEXT_PRIMARY,
                ),
            ],
            spacing=2,
        )
        
        if self._subtitle:
            title_col.controls.append(
                ft.Text(
                    self._subtitle,
                    size=14,
                    color=Colors.TEXT_SECONDARY,
                )
            )
        
        # Search bar (optional)
        self.search_field = ft.TextField(
            hint_text="Search...",
            prefix_icon=ft.icons.SEARCH,
            width=300,
            height=40,
            bgcolor=Colors.SURFACE,
            border_radius=8,
            border_color=Colors.BACKGROUND,
            focused_border_color=Colors.PRIMARY,
            visible=self._show_search,
        )
        
        # Action buttons
        self.notification_btn = ft.IconButton(
            icon=ft.icons.NOTIFICATIONS_OUTLINED,
            icon_color=Colors.TEXT_SECONDARY,
            tooltip="Notifications",
        )

        self.theme_btn = ft.IconButton(
            icon=self._theme_icon,
            icon_color=Colors.TEXT_SECONDARY,
            tooltip="Toggle theme",
            visible=self._on_toggle_theme is not None,
            on_click=self._on_toggle_theme,
        )
        
        self.user_btn = ft.IconButton(
            icon=ft.icons.ACCOUNT_CIRCLE_OUTLINED,
            icon_color=Colors.TEXT_SECONDARY,
            tooltip="Account",
        )
        
        # Layout
        self.content = ft.Row(
            controls=[
                title_col,
                ft.Container(expand=True),  # Spacer
                self.search_field,
                self.theme_btn,
                self.notification_btn,
                self.user_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        
        self.padding = ft.padding.symmetric(horizontal=24, vertical=16)
        self.bgcolor = Colors.BACKGROUND
        self.border = ft.border.only(bottom=ft.BorderSide(1, Colors.SURFACE))

    def set_theme_icon(self, icon: str):
        """Update theme toggle icon."""
        self._theme_icon = icon
        self.theme_btn.icon = icon

    def refresh_theme(self):
        """Refresh header colors after theme mode changes."""
        title_col = self.content.controls[0]
        if isinstance(title_col, ft.Column):
            if title_col.controls:
                title_col.controls[0].color = Colors.TEXT_PRIMARY
            if len(title_col.controls) > 1:
                title_col.controls[1].color = Colors.TEXT_SECONDARY

        self.search_field.bgcolor = Colors.SURFACE
        self.search_field.border_color = Colors.BACKGROUND
        self.search_field.focused_border_color = Colors.PRIMARY
        self.theme_btn.icon_color = Colors.TEXT_SECONDARY
        self.notification_btn.icon_color = Colors.TEXT_SECONDARY
        self.user_btn.icon_color = Colors.TEXT_SECONDARY
        self.bgcolor = Colors.BACKGROUND
        self.border = ft.border.only(bottom=ft.BorderSide(1, Colors.SURFACE))

    def set_title(self, title: str, subtitle: Optional[str] = None):
        """Update header title."""
        self._title = title
        self._subtitle = subtitle
        
        title_col = self.content.controls[0]
        if isinstance(title_col, ft.Column):
            title_col.controls[0].value = title
            if len(title_col.controls) > 1:
                title_col.controls[1].value = subtitle or ""
                title_col.controls[1].visible = subtitle is not None
        
        self.update()
