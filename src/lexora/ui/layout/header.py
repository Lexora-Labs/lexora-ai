"""
Header Component

Top header bar with title, search, and actions.
"""

import flet as ft
from typing import Optional

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
    ):
        super().__init__()
        self._title = title
        self._subtitle = subtitle
        self._show_search = show_search
        
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
                self.notification_btn,
                self.user_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        
        self.padding = ft.padding.symmetric(horizontal=24, vertical=16)
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
