"""
Sidebar Component - Navigation Rail

Collapsible sidebar for primary destinations.
"""

import flet as ft
from typing import Callable, List, Optional

from lexora.ui.theme import Colors

_RAIL_COLLAPSED_WIDTH = 80


_DESTINATION_ICONS: list[tuple[str, str]] = [
    (ft.icons.TRANSLATE_OUTLINED, ft.icons.TRANSLATE),
    (ft.icons.WORK_HISTORY_OUTLINED, ft.icons.WORK_HISTORY),
    (ft.icons.FOLDER_OUTLINED, ft.icons.FOLDER),
    (ft.icons.SETTINGS_OUTLINED, ft.icons.SETTINGS),
    (ft.icons.INFO_OUTLINED, ft.icons.INFO),
]


def _make_destinations(labels: List[str]) -> list[ft.NavigationRailDestination]:
    out: list[ft.NavigationRailDestination] = []
    for i, (ico, sel) in enumerate(_DESTINATION_ICONS):
        label = labels[i] if i < len(labels) else ""
        out.append(ft.NavigationRailDestination(icon=ico, selected_icon=sel, label=label))
    return out


class Sidebar(ft.Container):
    """Collapsible sidebar with NavigationRail."""

    def __init__(
        self,
        page: ft.Page,
        on_navigate: Optional[Callable[[int], None]] = None,
        selected_index: int = 0,
        labels: Optional[List[str]] = None,
    ):
        super().__init__()
        self._page = page
        self.on_navigate = on_navigate
        self._selected_index = selected_index
        self._expanded = False
        self._labels = labels or [""] * len(_DESTINATION_ICONS)

        self._build()

    def _build(self) -> None:
        """Build the sidebar UI."""
        self.nav_rail = ft.NavigationRail(
            selected_index=self._selected_index,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=_RAIL_COLLAPSED_WIDTH,
            min_extended_width=200,
            extended=self._expanded,
            bgcolor=Colors.SURFACE,
            indicator_color=Colors.PRIMARY,
            on_change=self._on_nav_change,
            destinations=_make_destinations(self._labels),
        )

        self.toggle_btn = ft.IconButton(
            icon=ft.icons.MENU_OPEN if self._expanded else ft.icons.MENU,
            icon_size=20,
            icon_color=Colors.TEXT_SECONDARY,
            tooltip="Toggle sidebar",
            width=36,
            height=36,
            style=ft.ButtonStyle(padding=0),
            on_click=self._toggle_sidebar,
        )

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
            width=_RAIL_COLLAPSED_WIDTH if not self._expanded else None,
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(vertical=16),
        )

        self.top_divider = ft.Divider(height=1, color=Colors.DIVIDER)
        self.bottom_divider = ft.Divider(height=1, color=Colors.DIVIDER)
        self.toggle_container = ft.Container(
            content=self.toggle_btn,
            width=_RAIL_COLLAPSED_WIDTH if not self._expanded else None,
            alignment=ft.alignment.center,
            padding=8,
        )

        self.content = ft.Column(
            controls=[
                self.logo,
                self.top_divider,
                ft.Container(
                    content=self.nav_rail,
                    expand=True,
                ),
                self.bottom_divider,
                self.toggle_container,
            ],
            spacing=0,
            expand=True,
        )

        self.bgcolor = Colors.SURFACE
        self.border_radius = ft.border_radius.only(top_right=12, bottom_right=12)
        self._sync_collapsed_layout()
        self._apply_theme()

    def set_labels(self, labels: List[str]) -> None:
        """Update localized navigation labels."""
        self._labels = labels
        self.nav_rail.destinations = _make_destinations(self._labels)

    def _apply_theme(self) -> None:
        """Refresh theme-sensitive sidebar colors."""
        self.logo_mark.color = Colors.PRIMARY
        self.logo_text.color = Colors.TEXT_PRIMARY
        self.nav_rail.bgcolor = Colors.SURFACE
        self.nav_rail.indicator_color = Colors.PRIMARY
        self.toggle_btn.icon_color = Colors.TEXT_SECONDARY
        self.top_divider.color = Colors.DIVIDER
        self.bottom_divider.color = Colors.DIVIDER
        self.bgcolor = Colors.SURFACE

    def before_update(self) -> None:
        """Keep sidebar visuals in sync with the active theme."""
        self._apply_theme()

    def _on_nav_change(self, e) -> None:
        """Handle navigation change."""
        self._selected_index = e.control.selected_index
        if self.on_navigate:
            self.on_navigate(self._selected_index)

    def _toggle_sidebar(self, e) -> None:
        """Toggle sidebar expanded/collapsed state."""
        self._expanded = not self._expanded
        self.nav_rail.extended = self._expanded
        self.toggle_btn.icon = ft.icons.MENU_OPEN if self._expanded else ft.icons.MENU
        self.logo_text.visible = self._expanded
        self._sync_collapsed_layout()
        self.update()

    def _sync_collapsed_layout(self) -> None:
        """Keep brand/toggle centered when sidebar is collapsed."""
        self.logo.alignment = ft.alignment.center
        self.logo.width = _RAIL_COLLAPSED_WIDTH if not self._expanded else None
        self.logo.padding = ft.padding.symmetric(vertical=16 if self._expanded else 12)
        self.logo_mark.size = 32 if self._expanded else 26
        self.toggle_container.alignment = ft.alignment.center
        self.toggle_container.width = _RAIL_COLLAPSED_WIDTH if not self._expanded else None
        self.toggle_container.padding = ft.padding.symmetric(vertical=8 if self._expanded else 6)

    def set_selected(self, index: int) -> None:
        """Set selected navigation index."""
        self._selected_index = index
        self.nav_rail.selected_index = index
        self.update()

    @property
    def is_expanded(self) -> bool:
        return self._expanded
