"""
Progress Panel Component

Displays translation progress with progress bar and status text.
"""

import flet as ft
from typing import Optional


class Colors:
    BACKGROUND = "#0F172A"
    SURFACE = "#1E293B"
    PRIMARY = "#06B6D4"
    TEXT_PRIMARY = "#F8FAFC"
    TEXT_SECONDARY = "#94A3B8"
    ERROR = "#F43F5E"
    SUCCESS = "#10B981"


class ProgressPanel(ft.Container):
    """Translation progress display component."""

    def __init__(self):
        super().__init__()
        self._build_ui()
        self.visible = False

    def _build_ui(self):
        """Build the progress panel UI."""
        
        # Progress bar
        self.progress_bar = ft.ProgressBar(
            value=0,
            bgcolor=Colors.SURFACE,
            color=Colors.PRIMARY,
            bar_height=8,
        )
        
        # Progress percentage
        self.progress_percent = ft.Text(
            "0%",
            size=14,
            weight=ft.FontWeight.W_600,
            color=Colors.TEXT_PRIMARY,
        )
        
        # Status text
        self.status_text = ft.Text(
            "Preparing...",
            size=14,
            color=Colors.TEXT_SECONDARY,
        )
        
        # Chapter info
        self.chapter_text = ft.Text(
            "",
            size=12,
            color=Colors.TEXT_SECONDARY,
            italic=True,
        )
        
        # Completion icon (hidden initially)
        self.completion_icon = ft.Icon(
            ft.Icons.CHECK_CIRCLE,
            color=Colors.SUCCESS,
            size=32,
            visible=False,
        )
        
        # Layout
        self.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Progress",
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    ft.Container(height=12),
                    
                    # Progress bar row
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=self.progress_bar,
                                expand=True,
                                border_radius=4,
                            ),
                            ft.Container(width=12),
                            self.progress_percent,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    
                    ft.Container(height=8),
                    
                    # Status row
                    ft.Row(
                        controls=[
                            self.completion_icon,
                            ft.Column(
                                controls=[
                                    self.status_text,
                                    self.chapter_text,
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=8,
                    ),
                ],
                spacing=0,
            ),
            padding=ft.padding.all(24),
            bgcolor=Colors.SURFACE,
            border_radius=10,
            margin=ft.margin.symmetric(horizontal=24, vertical=12),
        )

    def set_progress(self, value: float, status: Optional[str] = None):
        """
        Update progress.
        
        Args:
            value: Progress value (0.0 to 1.0)
            status: Optional status text
        """
        self.progress_bar.value = value
        self.progress_percent.value = f"{int(value * 100)}%"
        
        if status:
            self.status_text.value = status
        
        self.completion_icon.visible = False
        self.update()

    def set_status(self, status: str):
        """Update status text."""
        self.status_text.value = status
        self.update()

    def set_chapter(self, chapter: str):
        """Update chapter info."""
        self.chapter_text.value = chapter
        self.update()

    def set_completed(self):
        """Mark translation as completed."""
        self.progress_bar.value = 1.0
        self.progress_percent.value = "100%"
        self.status_text.value = "Translation completed!"
        self.status_text.color = Colors.SUCCESS
        self.chapter_text.value = ""
        self.completion_icon.visible = True
        self.update()

    def set_error(self, error_message: str):
        """Show error state."""
        self.status_text.value = f"Error: {error_message}"
        self.status_text.color = Colors.ERROR
        self.completion_icon.icon = ft.Icons.ERROR
        self.completion_icon.color = Colors.ERROR
        self.completion_icon.visible = True
        self.update()

    def reset(self):
        """Reset progress panel to initial state."""
        self.progress_bar.value = 0
        self.progress_percent.value = "0%"
        self.status_text.value = "Preparing..."
        self.status_text.color = Colors.TEXT_SECONDARY
        self.chapter_text.value = ""
        self.completion_icon.visible = False
        self.completion_icon.icon = ft.Icons.CHECK_CIRCLE
        self.completion_icon.color = Colors.SUCCESS
        self.visible = False
        self.update()
