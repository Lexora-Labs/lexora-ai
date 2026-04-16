"""Library screen placeholder while real implementation is pending."""

from __future__ import annotations

import flet as ft
from typing import Callable, Optional

from lexora.ui.i18n import translate
from lexora.ui.theme import Colors


class LibraryScreen(ft.Container):
    """Under-development placeholder for Library."""

    def __init__(self, page: ft.Page, get_text: Optional[Callable[[str], str]] = None):
        super().__init__()
        self.page = page
        self._t = get_text or (lambda key: translate("en", key))
        self._build()

    def _build(self) -> None:
        self.content = ft.Container(
            expand=True,
            alignment=ft.alignment.center,
            content=ft.Column(
                [
                    ft.Icon(ft.icons.CONSTRUCTION, size=64, color=Colors.TEXT_SECONDARY),
                    ft.Container(height=12),
                    ft.Text("Under development", size=22, weight=ft.FontWeight.W_700, color=Colors.TEXT_PRIMARY),
                    ft.Text(
                        "Library features are being rebuilt in a later task.",
                        size=14,
                        color=Colors.TEXT_SECONDARY,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4,
            ),
        )
        self.expand = True
