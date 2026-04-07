"""
Output Panel Component

Displays translation output with file path and action buttons.
"""

import flet as ft
import os
import subprocess
import platform
from typing import Optional
from pathlib import Path


class Colors:
    BACKGROUND = "#0F172A"
    SURFACE = "#1E293B"
    PRIMARY = "#06B6D4"
    TEXT_PRIMARY = "#F8FAFC"
    TEXT_SECONDARY = "#94A3B8"
    ERROR = "#F43F5E"
    SUCCESS = "#10B981"


class OutputPanel(ft.Container):
    """Translation output display component."""

    def __init__(self):
        super().__init__()
        self.output_path: Optional[str] = None
        self._build_ui()
        self.visible = False

    def _build_ui(self):
        """Build the output panel UI."""
        
        # Output file info
        self.file_icon = ft.Icon(
            ft.Icons.DESCRIPTION,
            color=Colors.SUCCESS,
            size=32,
        )
        
        self.file_name = ft.Text(
            "",
            size=16,
            weight=ft.FontWeight.W_500,
            color=Colors.TEXT_PRIMARY,
        )
        
        self.file_path_text = ft.Text(
            "",
            size=12,
            color=Colors.TEXT_SECONDARY,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        
        # Action buttons
        self.open_file_btn = ft.ElevatedButton(
            text="Open File",
            icon=ft.Icons.OPEN_IN_NEW,
            bgcolor=Colors.PRIMARY,
            color=Colors.TEXT_PRIMARY,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
            ),
            on_click=self._on_open_file,
        )
        
        self.open_folder_btn = ft.OutlinedButton(
            text="Open Folder",
            icon=ft.Icons.FOLDER_OPEN,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                side=ft.BorderSide(color=Colors.TEXT_SECONDARY),
            ),
            on_click=self._on_open_folder,
        )
        
        # Layout
        self.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Output",
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    ft.Container(height=12),
                    
                    # File info row
                    ft.Row(
                        controls=[
                            self.file_icon,
                            ft.Column(
                                controls=[
                                    self.file_name,
                                    self.file_path_text,
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                    ),
                    
                    ft.Container(height=16),
                    
                    # Buttons row
                    ft.Row(
                        controls=[
                            self.open_file_btn,
                            self.open_folder_btn,
                        ],
                        spacing=12,
                    ),
                ],
                spacing=0,
            ),
            padding=ft.padding.all(24),
            bgcolor=Colors.SURFACE,
            border_radius=10,
            margin=ft.margin.symmetric(horizontal=24, vertical=12),
        )

    def set_output_path(self, path: str):
        """Set the output file path."""
        self.output_path = path
        p = Path(path)
        self.file_name.value = p.name
        self.file_path_text.value = str(p.parent)
        self.update()

    def _on_open_file(self, e):
        """Open the output file with default application."""
        if not self.output_path or not os.path.exists(self.output_path):
            return
        
        system = platform.system()
        try:
            if system == "Darwin":  # macOS
                subprocess.run(["open", self.output_path], check=True)
            elif system == "Windows":
                os.startfile(self.output_path)
            else:  # Linux
                subprocess.run(["xdg-open", self.output_path], check=True)
        except Exception as ex:
            print(f"Error opening file: {ex}")

    def _on_open_folder(self, e):
        """Open the folder containing the output file."""
        if not self.output_path:
            return
        
        folder = str(Path(self.output_path).parent)
        if not os.path.exists(folder):
            return
        
        system = platform.system()
        try:
            if system == "Darwin":  # macOS
                subprocess.run(["open", folder], check=True)
            elif system == "Windows":
                os.startfile(folder)
            else:  # Linux
                subprocess.run(["xdg-open", folder], check=True)
        except Exception as ex:
            print(f"Error opening folder: {ex}")
