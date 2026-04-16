"""
Main Layout Component

Combines sidebar, header, and main content area.
"""

import flet as ft
from typing import Callable, Dict, Optional

from .sidebar import Sidebar
from .header import Header
from lexora.ui.theme import Colors


PAGE_KEYS: list[tuple[str, str]] = [
    ("page.library.title", "page.library.subtitle"),
    ("page.translate.title", "page.translate.subtitle"),
    ("page.jobs.title", "page.jobs.subtitle"),
    ("page.settings.title", "page.settings.subtitle"),
    ("page.about.title", "page.about.subtitle"),
]


class MainLayout(ft.Container):
    """
    Main application layout.

    Structure:
    | Sidebar | Header        |
    |         |---------------|
    |         | Main Content  |
    """

    def __init__(
        self,
        page: ft.Page,
        views: Optional[Dict[int, ft.Control]] = None,
        on_navigate: Optional[Callable[[int], None]] = None,
        on_toggle_theme: Optional[Callable[[ft.ControlEvent], None]] = None,
        on_open_help: Optional[Callable[[ft.ControlEvent], None]] = None,
        theme_icon: Optional[str] = None,
        get_text: Optional[Callable[[str], str]] = None,
        on_new_translation: Optional[Callable[[ft.ControlEvent], None]] = None,
        on_new_project: Optional[Callable[[ft.ControlEvent], None]] = None,
    ):
        super().__init__()
        self._page = page
        self._views = views or {}
        self._on_navigate = on_navigate
        self._on_toggle_theme = on_toggle_theme
        self._on_open_help = on_open_help
        self._theme_icon = theme_icon
        self._get_text = get_text or (lambda k: k)
        self._on_new_translation = on_new_translation
        self._on_new_project = on_new_project
        self._current_index = 0

        self._build()

    def _nav_labels(self) -> list[str]:
        keys = [
            "nav.library",
            "nav.translate",
            "nav.jobs_queue",
            "nav.settings",
            "nav.about",
        ]
        return [self._get_text(k) for k in keys]

    def _build(self) -> None:
        """Build the main layout."""
        self.sidebar = Sidebar(
            page=self._page,
            on_navigate=self._handle_navigation,
            selected_index=self._current_index,
            labels=self._nav_labels(),
        )

        title_key, subtitle_key = PAGE_KEYS[self._current_index]
        self.header = Header(
            title=self._get_text(title_key),
            subtitle=self._get_text(subtitle_key),
            show_search=True,
            workspace_hint=self._get_text("app.workspace"),
            on_toggle_theme=self._on_toggle_theme,
            on_open_help=self._on_open_help,
            theme_icon=self._theme_icon,
            get_text=self._get_text,
            on_new_translation=self._on_new_translation,
            on_new_project=self._on_new_project,
        )

        self.content_area = ft.Container(
            content=self._get_current_view(),
            expand=True,
            padding=24,
        )

        right_panel = ft.Column(
            controls=[
                self.header,
                self.content_area,
            ],
            spacing=0,
            expand=True,
        )

        self.vertical_divider = ft.VerticalDivider(width=1, color=Colors.BORDER)
        self.right_panel = ft.Container(
            content=right_panel,
            expand=True,
            bgcolor=Colors.BACKGROUND,
        )

        self.content = ft.Row(
            controls=[
                self.sidebar,
                self.vertical_divider,
                self.right_panel,
            ],
            spacing=0,
            expand=True,
        )

        self.expand = True
        self.bgcolor = Colors.BACKGROUND

    def _get_current_view(self) -> ft.Control:
        """Get the current view based on navigation index."""
        if self._current_index in self._views:
            return self._views[self._current_index]

        return self._create_placeholder_view()

    def _create_placeholder_view(self) -> ft.Control:
        """Create a placeholder view for unimplemented pages."""
        title_key, subtitle_key = PAGE_KEYS[self._current_index]
        return ft.Column(
            controls=[
                ft.Icon(
                    ft.icons.CONSTRUCTION,
                    size=64,
                    color=Colors.TEXT_SECONDARY,
                ),
                ft.Container(height=16),
                ft.Text(
                    self._get_text(title_key),
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=Colors.TEXT_PRIMARY,
                ),
                ft.Text(
                    self._get_text(subtitle_key),
                    size=14,
                    color=Colors.TEXT_SECONDARY,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )

    def _handle_navigation(self, index: int) -> None:
        """Handle navigation change."""
        self._current_index = index

        title_key, subtitle_key = PAGE_KEYS[index]
        self.header.set_title(self._get_text(title_key), self._get_text(subtitle_key))

        self.content_area.content = self._get_current_view()

        if self._on_navigate:
            self._on_navigate(index)

        self._page.update()

    def set_view(self, index: int, view: ft.Control) -> None:
        """Set a view for a specific navigation index."""
        self._views[index] = view
        if self._current_index == index:
            self.content_area.content = view
            self._page.update()

    def navigate_to(self, index: int) -> None:
        """Navigate to a specific page."""
        self.sidebar.set_selected(index)
        self._handle_navigation(index)

    def refresh_theme(self, theme_icon: Optional[str] = None) -> None:
        """Refresh layout chrome colors after theme changes."""
        if theme_icon:
            self.header.set_theme_icon(theme_icon)

        self.header.refresh_theme()
        self.sidebar._apply_theme()
        self.vertical_divider.color = Colors.BORDER
        self.right_panel.bgcolor = Colors.BACKGROUND
        self.bgcolor = Colors.BACKGROUND

    def replace_all_views(self, views: Dict[int, ft.Control]) -> None:
        """Swap all section roots (e.g. after theme or full rebuild)."""
        self._views = views
        self.content_area.content = self._get_current_view()

    def relocalize_shell(self, get_text: Callable[[str], str], views: Dict[int, ft.Control]) -> None:
        """Update strings, navigation labels, and view roots after locale change."""
        self._get_text = get_text
        self._views = views
        self.sidebar.set_labels(self._nav_labels())
        title_key, subtitle_key = PAGE_KEYS[self._current_index]
        self.header.apply_strings(
            get_text,
            title=self._get_text(title_key),
            subtitle=self._get_text(subtitle_key),
        )
        self.content_area.content = self._get_current_view()
