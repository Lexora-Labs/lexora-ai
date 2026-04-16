"""
Dashboard Screen

Overview of translations with KPI strip, recent activity, and quick actions.
"""

from __future__ import annotations

import flet as ft
from typing import Callable, Optional

from lexora.ui import nav as nav_ids
from lexora.ui.theme import Colors


class DashboardScreen(ft.Container):
    """Dashboard screen with overview stats and recent activity."""

    def __init__(
        self,
        page: ft.Page,
        on_navigate: Optional[Callable[[int], None]] = None,
        t: Optional[Callable[[str], str]] = None,
        on_open_library: Optional[Callable[[], None]] = None,
    ):
        super().__init__()
        self.page = page
        self.on_navigate = on_navigate
        self._t = t or (lambda k: k)
        self._on_open_library = on_open_library
        self._build()

    def _build(self) -> None:
        """Build the dashboard UI."""
        stats_row = ft.Row(
            [
                self._stat_card("Books translated", "12", ft.icons.MENU_BOOK, Colors.PRIMARY),
                self._stat_card("Running jobs", "3", ft.icons.PENDING, Colors.WARNING),
                self._stat_card("Total pages", "1,248", ft.icons.DESCRIPTION, Colors.SUCCESS),
                self._stat_card("This month", "5", ft.icons.CALENDAR_TODAY, Colors.INFO),
            ],
            spacing=16,
            wrap=True,
        )

        recent_section = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                self._t("dashboard.recent"),
                                size=18,
                                weight=ft.FontWeight.W_600,
                                color=Colors.TEXT_PRIMARY,
                            ),
                            ft.Container(expand=True),
                            ft.TextButton(
                                self._t("dashboard.view_all"),
                                on_click=lambda _: self._navigate_to(nav_ids.JOBS),
                            ),
                        ],
                    ),
                    ft.Container(height=8),
                    self._activity_item(
                        "Clean Code.epub",
                        "Translated to Vietnamese • 2 hours ago",
                        "completed",
                    ),
                    self._activity_item(
                        "Design Patterns.epub",
                        "Translated to Vietnamese • 1 day ago",
                        "completed",
                    ),
                    self._activity_item(
                        "Refactoring.epub",
                        "In progress • 45% complete",
                        "in_progress",
                    ),
                    self._activity_item(
                        "The Pragmatic Programmer.epub",
                        "Queued • waiting",
                        "queued",
                    ),
                ],
            ),
            padding=20,
            bgcolor=Colors.SURFACE,
            border_radius=10,
        )

        def _library_click(_: ft.ControlEvent) -> None:
            if self._on_open_library:
                self._on_open_library()
            else:
                self._navigate_to(nav_ids.LIBRARY)

        quick_section = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        self._t("dashboard.quick"),
                        size=18,
                        weight=ft.FontWeight.W_600,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    ft.Container(height=12),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                self._t("common.new_translation"),
                                icon=ft.icons.ADD,
                                bgcolor=Colors.PRIMARY,
                                color="#FFFFFF",
                                on_click=lambda _: self._navigate_to(nav_ids.TRANSLATE),
                            ),
                            ft.OutlinedButton(
                                self._t("dashboard.import_books"),
                                icon=ft.icons.UPLOAD_FILE,
                                disabled=True,
                                tooltip="Coming soon",
                            ),
                            ft.OutlinedButton(
                                self._t("dashboard.view_library"),
                                icon=ft.icons.LIBRARY_BOOKS,
                                on_click=_library_click,
                            ),
                            ft.OutlinedButton(
                                self._t("dashboard.view_jobs"),
                                icon=ft.icons.WORK_HISTORY_OUTLINED,
                                on_click=lambda _: self._navigate_to(nav_ids.JOBS),
                            ),
                        ],
                        spacing=12,
                        wrap=True,
                    ),
                ],
            ),
            padding=20,
            bgcolor=Colors.SURFACE,
            border_radius=10,
        )

        provider_section = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Provider status",
                        size=18,
                        weight=ft.FontWeight.W_600,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    ft.Container(height=12),
                    self._provider_status("OpenAI", "gpt-4o", True),
                    self._provider_status("Azure OpenAI", "gpt-4", False),
                    self._provider_status("Gemini", "gemini-2.0-flash", True),
                ],
            ),
            padding=20,
            bgcolor=Colors.SURFACE,
            border_radius=10,
        )

        self.content = ft.Column(
            [
                stats_row,
                ft.Container(height=20),
                ft.Row(
                    [
                        ft.Container(content=recent_section, expand=2),
                        ft.Container(width=16),
                        ft.Container(content=provider_section, expand=1),
                    ],
                    spacing=0,
                ),
                ft.Container(height=20),
                quick_section,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.expand = True

    def _stat_card(self, title: str, value: str, icon: str, color: str) -> ft.Container:
        """Create a stat card."""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(icon, size=32, color=color),
                        bgcolor=f"{color}20",
                        padding=12,
                        border_radius=8,
                    ),
                    ft.Container(width=12),
                    ft.Column(
                        [
                            ft.Text(value, size=28, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                            ft.Text(title, size=12, color=Colors.TEXT_SECONDARY),
                        ],
                        spacing=2,
                    ),
                ],
            ),
            padding=20,
            bgcolor=Colors.SURFACE,
            border_radius=10,
            expand=True,
        )

    def _activity_item(self, title: str, subtitle: str, status: str) -> ft.Container:
        """Create an activity list item."""
        icon = (
            ft.icons.CHECK_CIRCLE
            if status == "completed"
            else ft.icons.PENDING
            if status == "in_progress"
            else ft.icons.SCHEDULE
        )
        color = (
            Colors.SUCCESS
            if status == "completed"
            else Colors.WARNING
            if status == "in_progress"
            else Colors.TEXT_SECONDARY
        )

        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, color=color, size=24),
                    ft.Container(width=12),
                    ft.Column(
                        [
                            ft.Text(title, size=14, weight=ft.FontWeight.W_500, color=Colors.TEXT_PRIMARY),
                            ft.Text(subtitle, size=12, color=Colors.TEXT_SECONDARY),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.IconButton(icon=ft.icons.MORE_VERT, icon_color=Colors.TEXT_SECONDARY, icon_size=20),
                ],
            ),
            padding=ft.padding.symmetric(vertical=8),
        )

    def _provider_status(self, name: str, model: str, configured: bool) -> ft.Container:
        """Create a provider status row."""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        ft.icons.CHECK_CIRCLE if configured else ft.icons.ERROR_OUTLINE,
                        color=Colors.SUCCESS if configured else Colors.ERROR,
                        size=20,
                    ),
                    ft.Container(width=8),
                    ft.Column(
                        [
                            ft.Text(name, size=14, weight=ft.FontWeight.W_500, color=Colors.TEXT_PRIMARY),
                            ft.Text(model, size=12, color=Colors.TEXT_SECONDARY),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    ft.Text(
                        "Connected" if configured else "Not configured",
                        size=12,
                        color=Colors.SUCCESS if configured else Colors.TEXT_SECONDARY,
                    ),
                ],
            ),
            padding=ft.padding.symmetric(vertical=8),
        )

    def _navigate_to(self, index: int) -> None:
        """Navigate to another screen."""
        if self.on_navigate:
            self.on_navigate(index)
