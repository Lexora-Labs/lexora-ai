"""
Header Component

Top app bar: workspace context, quick actions, search, theme, notifications.
"""

import flet as ft
from typing import Callable, Optional

from lexora.ui.theme import Colors


class Header(ft.Container):
    """
    Top header bar with title, quick actions, search, and utilities.
    """

    def __init__(
        self,
        title: str = "Dashboard",
        subtitle: Optional[str] = None,
        show_search: bool = False,
        workspace_hint: Optional[str] = None,
        on_toggle_theme: Optional[Callable[[ft.ControlEvent], None]] = None,
        on_open_help: Optional[Callable[[ft.ControlEvent], None]] = None,
        on_change_language: Optional[Callable[[str], None]] = None,
        current_language: str = "en",
        theme_icon: Optional[str] = None,
        get_text: Optional[Callable[[str], str]] = None,
        on_new_translation: Optional[Callable[[ft.ControlEvent], None]] = None,
        on_new_project: Optional[Callable[[ft.ControlEvent], None]] = None,
    ):
        super().__init__()
        self._title = title
        self._subtitle = subtitle
        self._show_search = show_search
        self._workspace_hint = workspace_hint
        self._on_toggle_theme = on_toggle_theme
        self._on_open_help = on_open_help
        self._on_change_language = on_change_language
        self._current_language = current_language if current_language in ("en", "vi") else "en"
        self._theme_icon = theme_icon or ft.icons.DARK_MODE
        self._get_text = get_text or (lambda k: k)
        self._on_new_translation = on_new_translation
        self._on_new_project = on_new_project

        self._build()

    def _build(self) -> None:
        """Build the header UI."""
        self._title_text = ft.Text(
            self._title,
            size=22,
            weight=ft.FontWeight.BOLD,
            color=Colors.TEXT_PRIMARY,
        )
        self._subtitle_text = ft.Text(
            self._subtitle or "",
            size=13,
            color=Colors.TEXT_SECONDARY,
            visible=bool(self._subtitle),
        )

        title_col = ft.Column(
            controls=[
                self._title_text,
                self._subtitle_text,
            ],
            spacing=2,
        )

        self.search_field = ft.TextField(
            hint_text=self._get_text("header.search_hint"),
            prefix_icon=ft.icons.SEARCH,
            expand=True,
            max_lines=1,
            height=42,
            bgcolor=Colors.SURFACE,
            border_radius=8,
            border_color=Colors.BORDER,
            focused_border_color=Colors.PRIMARY,
            visible=self._show_search,
        )

        self.new_translation_btn = ft.ElevatedButton(
            text=self._get_text("common.new_translation"),
            icon=ft.icons.TRANSLATE,
            visible=self._on_new_translation is not None,
            on_click=self._on_new_translation,
            bgcolor=Colors.PRIMARY,
            color="#FFFFFF",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )

        self.notification_btn = ft.IconButton(
            icon=ft.icons.NOTIFICATIONS_OUTLINED,
            icon_color=Colors.TEXT_SECONDARY,
            tooltip="Notifications",
        )

        self.theme_btn = ft.IconButton(
            icon=self._theme_icon,
            icon_color=Colors.TEXT_SECONDARY,
            tooltip="Theme",
            visible=self._on_toggle_theme is not None,
            on_click=self._on_toggle_theme,
        )
        self.help_btn = ft.IconButton(
            icon=ft.icons.HELP_OUTLINE,
            icon_color=Colors.TEXT_SECONDARY,
            tooltip="README Help",
            visible=self._on_open_help is not None,
            on_click=self._on_open_help,
        )
        self.language_label = ft.Text(
            self._language_text(),
            size=11,
            weight=ft.FontWeight.W_600,
            color=Colors.TEXT_PRIMARY,
        )
        self.language_chevron = ft.Icon(
            ft.icons.ARROW_DROP_DOWN,
            size=18,
            color=Colors.TEXT_SECONDARY,
        )
        self.language_menu = ft.PopupMenuButton(
            visible=self._on_change_language is not None,
            tooltip="Language",
            items=[
                ft.PopupMenuItem(text="EN", on_click=lambda _: self._set_language("en")),
                ft.PopupMenuItem(text="VI", on_click=lambda _: self._set_language("vi")),
            ],
            content=ft.Container(
                content=ft.Row(
                    controls=[
                        self.language_label,
                        self.language_chevron,
                    ],
                    spacing=2,
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                ),
                width=64,
                height=40,
                padding=ft.padding.symmetric(horizontal=10, vertical=0),
                alignment=ft.alignment.center,
                bgcolor=Colors.SURFACE,
                border=ft.border.all(1, Colors.BORDER),
                border_radius=8,
            ),
        )

        self.user_btn = ft.IconButton(
            icon=ft.icons.ACCOUNT_CIRCLE_OUTLINED,
            icon_color=Colors.TEXT_SECONDARY,
            tooltip="Account",
        )

        self.content = ft.Column(
            [
                ft.Row(
                    controls=[
                        title_col,
                        ft.Container(expand=True),
                        self.new_translation_btn,
                        self.language_menu,
                        self.help_btn,
                        self.theme_btn,
                        self.notification_btn,
                        self.user_btn,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=0,
        )

        self.padding = ft.padding.symmetric(horizontal=24, vertical=14)
        self.bgcolor = Colors.SURFACE_VARIANT
        self.border = ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER))

    def set_theme_icon(self, icon: str) -> None:
        """Update theme toggle icon."""
        self._theme_icon = icon
        self.theme_btn.icon = icon

    def apply_strings(
        self,
        get_text: Callable[[str], str],
        *,
        title: str,
        subtitle: Optional[str],
    ) -> None:
        """Refresh labels after locale change."""
        self._get_text = get_text
        self.search_field.hint_text = get_text("header.search_hint")
        self.new_translation_btn.text = get_text("common.new_translation")
        self.set_title(title, subtitle)

    def refresh_theme(self) -> None:
        """Refresh header colors after theme mode changes."""
        self._title_text.color = Colors.TEXT_PRIMARY
        self._subtitle_text.color = Colors.TEXT_SECONDARY

        self.search_field.bgcolor = Colors.SURFACE
        self.search_field.border_color = Colors.BORDER
        self.search_field.focused_border_color = Colors.PRIMARY
        self.language_label.color = Colors.TEXT_PRIMARY
        self.language_chevron.color = Colors.TEXT_SECONDARY
        if isinstance(self.language_menu.content, ft.Container):
            self.language_menu.content.bgcolor = Colors.SURFACE
            self.language_menu.content.border = ft.border.all(1, Colors.BORDER)
        self.help_btn.icon_color = Colors.TEXT_SECONDARY
        self.theme_btn.icon_color = Colors.TEXT_SECONDARY
        self.notification_btn.icon_color = Colors.TEXT_SECONDARY
        self.user_btn.icon_color = Colors.TEXT_SECONDARY
        self.bgcolor = Colors.SURFACE_VARIANT
        self.border = ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER))
        self.new_translation_btn.bgcolor = Colors.PRIMARY

    def _language_text(self) -> str:
        return self._current_language.upper()

    def _set_language(self, value: str) -> None:
        value = value.strip().lower()
        if value not in ("en", "vi"):
            return
        self._current_language = value
        self.language_label.value = self._language_text()
        if self._on_change_language is not None:
            self._on_change_language(value)
        if self.page:
            self.update()

    def set_title(self, title: str, subtitle: Optional[str] = None) -> None:
        """Update header title."""
        self._title = title
        self._subtitle = subtitle
        self._title_text.value = title
        self._subtitle_text.value = subtitle or ""
        self._subtitle_text.visible = bool(subtitle)
        self.update()
