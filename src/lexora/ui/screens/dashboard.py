"""
Dashboard Screen

Overview of translations with:
- Status cards (stats summary)
- Recent files
- Quick actions
"""

import flet as ft
from typing import Optional, Callable

from lexora.ui.theme import Colors


class DashboardScreen(ft.Container):
    """Dashboard screen with overview stats and recent activity."""

    def __init__(
        self,
        page: ft.Page,
        on_navigate: Optional[Callable[[int], None]] = None,
    ):
        super().__init__()
        self.page = page
        self.on_navigate = on_navigate
        self._build()

    def _build(self):
        """Build the dashboard UI."""
        
        # Stats Cards Row
        stats_row = ft.Row([
            self._stat_card(
                title="Books Translated",
                value="12",
                icon=ft.icons.MENU_BOOK,
                color=Colors.PRIMARY,
            ),
            self._stat_card(
                title="In Progress",
                value="3",
                icon=ft.icons.PENDING,
                color=Colors.WARNING,
            ),
            self._stat_card(
                title="Total Pages",
                value="1,248",
                icon=ft.icons.DESCRIPTION,
                color=Colors.SUCCESS,
            ),
            self._stat_card(
                title="This Month",
                value="5",
                icon=ft.icons.CALENDAR_TODAY,
                color=Colors.INFO,
            ),
        ], spacing=16, wrap=True)
        
        # Recent Activity Section
        recent_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("📋 Recent Activity", size=18, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                    ft.Container(expand=True),
                    ft.TextButton("View All", on_click=lambda _: self._navigate_to(3)),
                ]),
                ft.Container(height=8),
                self._activity_item(
                    title="Clean Code.epub",
                    subtitle="Translated to Vietnamese • 2 hours ago",
                    status="completed",
                ),
                self._activity_item(
                    title="Design Patterns.epub",
                    subtitle="Translated to Vietnamese • 1 day ago",
                    status="completed",
                ),
                self._activity_item(
                    title="Refactoring.epub",
                    subtitle="In progress • 45% complete",
                    status="in_progress",
                ),
                self._activity_item(
                    title="The Pragmatic Programmer.epub",
                    subtitle="Queued • Waiting",
                    status="queued",
                ),
            ]),
            padding=20,
            bgcolor=Colors.SURFACE,
            border_radius=10,
        )
        
        # Quick Actions Section
        quick_section = ft.Container(
            content=ft.Column([
                ft.Text("⚡ Quick Actions", size=18, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                ft.Container(height=12),
                ft.Row([
                    ft.ElevatedButton(
                        "New Translation",
                        icon=ft.icons.ADD,
                        bgcolor=Colors.PRIMARY,
                        color=Colors.TEXT_PRIMARY,
                        on_click=lambda _: self._navigate_to(1),
                    ),
                    ft.OutlinedButton(
                        "Import Books",
                        icon=ft.icons.UPLOAD_FILE,
                    ),
                    ft.OutlinedButton(
                        "View Library",
                        icon=ft.icons.LIBRARY_BOOKS,
                        on_click=lambda _: self._navigate_to(2),
                    ),
                ], spacing=12, wrap=True),
            ]),
            padding=20,
            bgcolor=Colors.SURFACE,
            border_radius=10,
        )
        
        # Provider Status Section
        provider_section = ft.Container(
            content=ft.Column([
                ft.Text("🔗 Provider Status", size=18, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                ft.Container(height=12),
                self._provider_status("OpenAI", "gpt-4o", True),
                self._provider_status("Azure OpenAI", "gpt-4", False),
                self._provider_status("Gemini", "gemini-2.0-flash", True),
            ]),
            padding=20,
            bgcolor=Colors.SURFACE,
            border_radius=10,
        )
        
        # Layout
        self.content = ft.Column([
            stats_row,
            ft.Container(height=20),
            ft.Row([
                ft.Container(content=recent_section, expand=2),
                ft.Container(width=16),
                ft.Container(content=provider_section, expand=1),
            ], spacing=0),
            ft.Container(height=20),
            quick_section,
        ], scroll=ft.ScrollMode.AUTO, expand=True)
        
        self.expand = True

    def _stat_card(self, title: str, value: str, icon: str, color: str) -> ft.Container:
        """Create a stat card."""
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, size=32, color=color),
                    bgcolor=f"{color}20",
                    padding=12,
                    border_radius=8,
                ),
                ft.Container(width=12),
                ft.Column([
                    ft.Text(value, size=28, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                    ft.Text(title, size=12, color=Colors.TEXT_SECONDARY),
                ], spacing=2),
            ]),
            padding=20,
            bgcolor=Colors.SURFACE,
            border_radius=10,
            expand=True,
        )

    def _activity_item(self, title: str, subtitle: str, status: str) -> ft.Container:
        """Create an activity list item."""
        icon = ft.icons.CHECK_CIRCLE if status == "completed" else (
            ft.icons.PENDING if status == "in_progress" else ft.icons.SCHEDULE
        )
        color = Colors.SUCCESS if status == "completed" else (
            Colors.WARNING if status == "in_progress" else Colors.TEXT_SECONDARY
        )
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=color, size=24),
                ft.Container(width=12),
                ft.Column([
                    ft.Text(title, size=14, weight=ft.FontWeight.W_500, color=Colors.TEXT_PRIMARY),
                    ft.Text(subtitle, size=12, color=Colors.TEXT_SECONDARY),
                ], spacing=2, expand=True),
                ft.IconButton(icon=ft.icons.MORE_VERT, icon_color=Colors.TEXT_SECONDARY, icon_size=20),
            ]),
            padding=ft.padding.symmetric(vertical=8),
        )

    def _provider_status(self, name: str, model: str, configured: bool) -> ft.Container:
        """Create a provider status row."""
        return ft.Container(
            content=ft.Row([
                ft.Icon(
                    ft.icons.CHECK_CIRCLE if configured else ft.icons.ERROR_OUTLINE,
                    color=Colors.SUCCESS if configured else Colors.ERROR,
                    size=20,
                ),
                ft.Container(width=8),
                ft.Column([
                    ft.Text(name, size=14, weight=ft.FontWeight.W_500, color=Colors.TEXT_PRIMARY),
                    ft.Text(model, size=12, color=Colors.TEXT_SECONDARY),
                ], spacing=0, expand=True),
                ft.Text(
                    "Connected" if configured else "Not configured",
                    size=12,
                    color=Colors.SUCCESS if configured else Colors.TEXT_SECONDARY,
                ),
            ]),
            padding=ft.padding.symmetric(vertical=8),
        )

    def _navigate_to(self, index: int):
        """Navigate to another screen."""
        if self.on_navigate:
            self.on_navigate(index)
