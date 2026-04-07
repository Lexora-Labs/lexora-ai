"""
Home View - Main translation workflow screen.

Layout:
- Header
- File Selection
- Translation Settings
- Action Buttons
- Progress
- Output
"""

import flet as ft
from typing import Optional
from enum import Enum

from lexora.ui.components.file_picker import FilePicker
from lexora.ui.components.provider_selector import ProviderSelector
from lexora.ui.components.progress_panel import ProgressPanel
from lexora.ui.components.output_panel import OutputPanel


class UIState(Enum):
    """Application UI states."""
    IDLE = "idle"
    FILE_SELECTED = "file_selected"
    TRANSLATING = "translating"
    COMPLETED = "completed"
    ERROR = "error"


# Colors (duplicated for component access)
class Colors:
    BACKGROUND = "#0F172A"
    SURFACE = "#1E293B"
    PRIMARY = "#06B6D4"
    TEXT_PRIMARY = "#F8FAFC"
    TEXT_SECONDARY = "#94A3B8"
    ERROR = "#F43F5E"
    SUCCESS = "#10B981"


class HomeView(ft.Container):
    """Main home view with translation workflow."""

    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.state = UIState.IDLE
        self.selected_file: Optional[str] = None
        self.output_file: Optional[str] = None
        
        # Build UI
        self._build_ui()

    def _build_ui(self):
        """Build the main UI layout."""
        
        # Header
        self.header = self._build_header()
        
        # File Picker
        self.file_picker = FilePicker(
            on_file_selected=self._on_file_selected
        )
        
        # Provider Selector
        self.provider_selector = ProviderSelector()
        
        # Action Buttons
        self.action_section = self._build_action_section()
        
        # Progress Panel
        self.progress_panel = ProgressPanel()
        
        # Output Panel
        self.output_panel = OutputPanel()
        
        # Main layout
        self.content = ft.Column(
            controls=[
                self.header,
                ft.Divider(height=1, color=Colors.SURFACE),
                
                # Scrollable content
                ft.Container(
                    content=ft.Column(
                        controls=[
                            self.file_picker,
                            ft.Divider(height=1, color=Colors.SURFACE),
                            self.provider_selector,
                            ft.Divider(height=1, color=Colors.SURFACE),
                            self.action_section,
                            self.progress_panel,
                            self.output_panel,
                        ],
                        spacing=0,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    expand=True,
                    padding=0,
                ),
            ],
            spacing=0,
            expand=True,
        )
        
        self.expand = True
        self.bgcolor = Colors.BACKGROUND

    def _build_header(self) -> ft.Container:
        """Build the app header."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Lexora AI",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        "AI-powered eBook Translation",
                        size=14,
                        color=Colors.TEXT_SECONDARY,
                    ),
                ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(vertical=24),
            alignment=ft.alignment.center,
        )

    def _build_action_section(self) -> ft.Container:
        """Build the action buttons section."""
        
        self.translate_btn = ft.ElevatedButton(
            text="Translate",
            icon=ft.Icons.TRANSLATE,
            bgcolor=Colors.PRIMARY,
            color=Colors.TEXT_PRIMARY,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=32, vertical=16),
            ),
            on_click=self._on_translate_click,
            disabled=True,
        )
        
        self.cancel_btn = ft.OutlinedButton(
            text="Cancel",
            icon=ft.Icons.CANCEL,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=24, vertical=16),
                side=ft.BorderSide(color=Colors.TEXT_SECONDARY),
            ),
            on_click=self._on_cancel_click,
            visible=False,
        )
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    self.translate_btn,
                    self.cancel_btn,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=16,
            ),
            padding=ft.padding.symmetric(vertical=24),
        )

    def _on_file_selected(self, file_path: str):
        """Handle file selection."""
        self.selected_file = file_path
        self.state = UIState.FILE_SELECTED
        self.translate_btn.disabled = False
        self.output_panel.visible = False
        self.progress_panel.reset()
        self.page.update()

    def _on_translate_click(self, e):
        """Handle translate button click."""
        if not self.selected_file:
            return
        
        # Update state
        self.state = UIState.TRANSLATING
        self._update_ui_for_translating()
        
        # TODO: Run translation async
        # For now, simulate progress
        self._simulate_translation()

    def _on_cancel_click(self, e):
        """Handle cancel button click."""
        self.state = UIState.FILE_SELECTED
        self._update_ui_for_idle()
        self.progress_panel.reset()
        self.page.update()

    def _update_ui_for_translating(self):
        """Update UI when translation starts."""
        self.translate_btn.disabled = True
        self.cancel_btn.visible = True
        self.file_picker.set_enabled(False)
        self.provider_selector.set_enabled(False)
        self.progress_panel.visible = True
        self.progress_panel.set_status("Starting translation...")
        self.output_panel.visible = False
        self.page.update()

    def _update_ui_for_idle(self):
        """Update UI back to idle state."""
        self.translate_btn.disabled = self.selected_file is None
        self.cancel_btn.visible = False
        self.file_picker.set_enabled(True)
        self.provider_selector.set_enabled(True)

    def _update_ui_for_completed(self, output_path: str):
        """Update UI when translation completes."""
        self.state = UIState.COMPLETED
        self.output_file = output_path
        self.translate_btn.disabled = False
        self.cancel_btn.visible = False
        self.file_picker.set_enabled(True)
        self.provider_selector.set_enabled(True)
        self.progress_panel.set_completed()
        self.output_panel.set_output_path(output_path)
        self.output_panel.visible = True
        self.page.update()

    def _simulate_translation(self):
        """Simulate translation progress (placeholder)."""
        import threading
        import time
        
        def run():
            chapters = ["Chapter 1", "Chapter 2", "Chapter 3", "Chapter 4", "Chapter 5"]
            for i, chapter in enumerate(chapters):
                if self.state != UIState.TRANSLATING:
                    return
                progress = (i + 1) / len(chapters)
                self.progress_panel.set_progress(progress, f"Translating {chapter}...")
                self.page.update()
                time.sleep(1)
            
            # Completed
            if self.state == UIState.TRANSLATING:
                output_path = self.selected_file.replace(".epub", "_vi.epub")
                self._update_ui_for_completed(output_path)
        
        threading.Thread(target=run, daemon=True).start()
