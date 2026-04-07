"""
File Picker Component

Handles EPUB file selection with native file dialog.
"""

import flet as ft
from typing import Callable, Optional
from pathlib import Path

from lexora.ui.theme import Colors


class FilePicker(ft.Container):
    """EPUB file picker component."""

    def __init__(
        self,
        on_file_selected: Optional[Callable[[str], None]] = None,
    ):
        super().__init__()
        self.on_file_selected = on_file_selected
        self.selected_path: Optional[str] = None
        self._enabled = True
        
        self._build_ui()

    def _build_ui(self):
        """Build the file picker UI."""
        
        # File picker dialog
        self._file_picker = ft.FilePicker(
            on_result=self._on_file_picked,
        )
        
        # Select button
        self.select_btn = ft.ElevatedButton(
            text="Select EPUB File",
            icon=ft.Icons.FOLDER_OPEN,
            bgcolor=Colors.SURFACE,
            color=Colors.TEXT_PRIMARY,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=24, vertical=12),
            ),
            on_click=self._on_select_click,
        )
        
        # File info display
        self.file_icon = ft.Icon(
            ft.Icons.MENU_BOOK,
            color=Colors.PRIMARY,
            size=32,
            visible=False,
        )
        
        self.file_name = ft.Text(
            "",
            size=16,
            weight=ft.FontWeight.W_500,
            color=Colors.TEXT_PRIMARY,
            visible=False,
        )
        
        self.file_path = ft.Text(
            "",
            size=12,
            color=Colors.TEXT_SECONDARY,
            visible=False,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        
        # Layout
        self.content = ft.Column(
            controls=[
                ft.Text(
                    "File Selection",
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=Colors.TEXT_SECONDARY,
                ),
                ft.Container(height=12),
                
                # File picker overlay (invisible)
                self._file_picker,
                
                # Select button or file info
                ft.Container(
                    content=ft.Column(
                        controls=[
                            self.select_btn,
                            ft.Container(height=8),
                            ft.Row(
                                controls=[
                                    self.file_icon,
                                    ft.Column(
                                        controls=[
                                            self.file_name,
                                            self.file_path,
                                        ],
                                        spacing=2,
                                        expand=True,
                                    ),
                                ],
                                spacing=12,
                                visible=False,
                                ref=ft.Ref[ft.Row](),
                            ),
                        ],
                        spacing=0,
                    ),
                ),
            ],
            spacing=0,
        )
        
        self.padding = ft.padding.all(24)
        self.bgcolor = Colors.BACKGROUND

    def _on_select_click(self, e):
        """Handle select button click."""
        if not self._enabled:
            return
        self._file_picker.pick_files(
            allowed_extensions=["epub"],
            dialog_title="Select EPUB File",
        )

    def _on_file_picked(self, e: ft.FilePickerResultEvent):
        """Handle file picker result."""
        if e.files and len(e.files) > 0:
            file = e.files[0]
            self.selected_path = file.path
            
            # Update UI
            path = Path(file.path)
            self.file_name.value = path.name
            self.file_name.visible = True
            self.file_path.value = str(path.parent)
            self.file_path.visible = True
            self.file_icon.visible = True
            
            # Find the Row and make it visible
            for control in self.content.controls:
                if isinstance(control, ft.Container) and control.content:
                    col = control.content
                    if isinstance(col, ft.Column):
                        for c in col.controls:
                            if isinstance(c, ft.Row):
                                c.visible = True
            
            self.update()
            
            # Callback
            if self.on_file_selected:
                self.on_file_selected(file.path)

    def set_enabled(self, enabled: bool):
        """Enable or disable the file picker."""
        self._enabled = enabled
        self.select_btn.disabled = not enabled
        self.update()

    def get_selected_file(self) -> Optional[str]:
        """Get the selected file path."""
        return self.selected_path
