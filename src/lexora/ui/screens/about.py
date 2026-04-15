"""About screen — version and links."""

from __future__ import annotations

import importlib.metadata
import sys
from typing import Callable

import flet as ft

from lexora.ui.theme import Colors


class AboutScreen(ft.Container):
    def __init__(self, page: ft.Page, t: Callable[[str], str]):
        super().__init__()
        self._page = page
        self._t = t
        self._build()

    def _version(self) -> str:
        try:
            return importlib.metadata.version("lexora-ai")
        except importlib.metadata.PackageNotFoundError:
            return "dev"

    def _build(self) -> None:
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.content = ft.Container(
            padding=32,
            expand=True,
            content=ft.Column(
                [
                    ft.Text(self._t("page.about.title"), size=24, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                    ft.Text(self._t("page.about.subtitle"), size=14, color=Colors.TEXT_SECONDARY),
                    ft.Container(height=24),
                    ft.Container(
                        padding=20,
                        bgcolor=Colors.SURFACE,
                        border_radius=10,
                        content=ft.Column(
                            [
                                ft.Text(self._t("about.version"), weight=ft.FontWeight.W_500, color=Colors.TEXT_PRIMARY),
                                ft.Text(f"Package: lexora-ai {self._version()}", size=13, color=Colors.TEXT_SECONDARY, font_family="JetBrains Mono, Consolas, monospace"),
                                ft.Text(f"Python: {py_ver}", size=13, color=Colors.TEXT_SECONDARY, font_family="JetBrains Mono, Consolas, monospace"),
                                ft.Container(height=12),
                                ft.Text(self._t("about.body"), size=14, color=Colors.TEXT_SECONDARY),
                            ],
                            spacing=8,
                        ),
                    ),
                ],
                spacing=4,
            ),
        )
        self.expand = True
