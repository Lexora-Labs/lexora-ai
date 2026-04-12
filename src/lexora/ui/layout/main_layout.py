"""
Main Layout Component

Combines sidebar, header, and main content area.
"""

import flet as ft
from typing import Optional, Dict, Callable

from .sidebar import Sidebar
from .header import Header
from lexora.ui.theme import Colors


# Page configurations
PAGE_CONFIG = {
    0: {"title": "Translate", "subtitle": "Translate eBooks with AI"},
    1: {"title": "Library", "subtitle": "Your translated books"},
    2: {"title": "Jobs", "subtitle": "Translation queue and history"},
    3: {"title": "Settings", "subtitle": "Application preferences"},
}


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
        theme_icon: Optional[str] = None,
    ):
        super().__init__()
        self._page = page
        self._views = views or {}
        self._on_navigate = on_navigate
        self._on_toggle_theme = on_toggle_theme
        self._theme_icon = theme_icon
        self._current_index = 0
        
        self._build()

    def _build(self):
        """Build the main layout."""
        
        # Sidebar
        self.sidebar = Sidebar(
            page=self._page,
            on_navigate=self._handle_navigation,
            selected_index=self._current_index,
        )
        
        # Header
        config = PAGE_CONFIG.get(self._current_index, PAGE_CONFIG[0])
        self.header = Header(
            title=config["title"],
            subtitle=config["subtitle"],
            on_toggle_theme=self._on_toggle_theme,
            theme_icon=self._theme_icon,
        )
        
        # Content area placeholder
        self.content_area = ft.Container(
            content=self._get_current_view(),
            expand=True,
            padding=24,
        )
        
        # Right panel (header + content)
        right_panel = ft.Column(
            controls=[
                self.header,
                self.content_area,
            ],
            spacing=0,
            expand=True,
        )

        self.vertical_divider = ft.VerticalDivider(width=1, color=Colors.SURFACE)
        self.right_panel = ft.Container(
            content=right_panel,
            expand=True,
            bgcolor=Colors.BACKGROUND,
        )
        
        # Main layout
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
        
        # Default placeholder
        return self._create_placeholder_view()

    def _create_placeholder_view(self) -> ft.Control:
        """Create a placeholder view for unimplemented pages."""
        config = PAGE_CONFIG.get(self._current_index, PAGE_CONFIG[0])
        
        return ft.Column(
            controls=[
                ft.Icon(
                    ft.icons.CONSTRUCTION,
                    size=64,
                    color=Colors.TEXT_SECONDARY,
                ),
                ft.Container(height=16),
                ft.Text(
                    f"{config['title']} Page",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=Colors.TEXT_PRIMARY,
                ),
                ft.Text(
                    "This page is under construction",
                    size=14,
                    color=Colors.TEXT_SECONDARY,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )

    def _handle_navigation(self, index: int):
        """Handle navigation change."""
        self._current_index = index
        
        # Update header
        config = PAGE_CONFIG.get(index, PAGE_CONFIG[0])
        self.header.set_title(config["title"], config["subtitle"])
        
        # Update content
        self.content_area.content = self._get_current_view()
        
        # Callback
        if self._on_navigate:
            self._on_navigate(index)
        
        self._page.update()

    def set_view(self, index: int, view: ft.Control):
        """Set a view for a specific navigation index."""
        self._views[index] = view
        if self._current_index == index:
            self.content_area.content = view
            self._page.update()

    def navigate_to(self, index: int):
        """Navigate to a specific page."""
        self.sidebar.set_selected(index)
        self._handle_navigation(index)

    def refresh_theme(self, theme_icon: Optional[str] = None):
        """Refresh layout chrome colors after theme changes."""
        if theme_icon:
            self.header.set_theme_icon(theme_icon)

        self.header.refresh_theme()
        self.sidebar._apply_theme()
        self.vertical_divider.color = Colors.SURFACE
        self.right_panel.bgcolor = Colors.BACKGROUND
        self.bgcolor = Colors.BACKGROUND
