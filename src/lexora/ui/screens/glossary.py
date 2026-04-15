"""Glossary screen — MVP placeholder aligned with UI plan."""

from __future__ import annotations

import flet as ft
from typing import Callable

from lexora.ui.theme import Colors


class GlossaryScreen(ft.Container):
    def __init__(self, page: ft.Page, t: Callable[[str], str]):
        super().__init__()
        self._page = page
        self._t = t
        self._build()

    def _build(self) -> None:
        self.content = ft.Container(
            padding=32,
            expand=True,
            alignment=ft.alignment.center,
            content=ft.Column(
                [
                    ft.Icon(ft.icons.BOOKMARKS_OUTLINED, size=56, color=Colors.PRIMARY),
                    ft.Container(height=16),
                    ft.Text(self._t("page.glossary.title"), size=22, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                    ft.Container(height=8),
                    ft.Text(self._t("placeholder.glossary"), text_align=ft.TextAlign.CENTER, color=Colors.TEXT_SECONDARY, size=14),
                    ft.Container(height=24),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                self._t("common.import") + " CSV",
                                icon=ft.icons.UPLOAD_FILE,
                                disabled=True,
                                bgcolor=Colors.PRIMARY,
                                color="#FFFFFF",
                            ),
                            ft.OutlinedButton(self._t("common.export") + " CSV", icon=ft.icons.DOWNLOAD_OUTLINED, disabled=True),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=12,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
            ),
        )
        self.expand = True
