"""
Provider Selector Component

Handles AI provider and model selection with dynamic dropdowns.
"""

import flet as ft
from typing import Optional, Dict, List

from lexora.ui.theme import Colors


# Provider configurations
PROVIDERS: Dict[str, Dict] = {
    "OpenAI": {
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
        "env_var": "OPENAI_API_KEY",
    },
    "Azure OpenAI": {
        "models": ["gpt-4o", "gpt-4", "gpt-35-turbo"],
        "env_var": "AZURE_OPENAI_KEY",
    },
    "Gemini": {
        "models": ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro"],
        "env_var": "GOOGLE_API_KEY",
    },
    "Anthropic": {
        "models": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
        "env_var": "ANTHROPIC_API_KEY",
    },
    "Qwen": {
        "models": ["qwen-max", "qwen-plus", "qwen-turbo", "qwen-long"],
        "env_var": "DASHSCOPE_API_KEY",
    },
}

LANGUAGES: List[Dict[str, str]] = [
    {"code": "vi", "name": "Vietnamese"},
    {"code": "en", "name": "English"},
    {"code": "ja", "name": "Japanese"},
    {"code": "zh", "name": "Chinese"},
    {"code": "ko", "name": "Korean"},
    {"code": "fr", "name": "French"},
    {"code": "de", "name": "German"},
    {"code": "es", "name": "Spanish"},
]


class ProviderSelector(ft.Container):
    """Provider and model selector component."""

    def __init__(self):
        super().__init__()
        self._enabled = True
        self._expanded = False
        
        self._build_ui()

    def _build_ui(self):
        """Build the selector UI."""
        
        # Provider dropdown
        self.provider_dropdown = ft.Dropdown(
            label="Provider",
            hint_text="Select AI Provider",
            options=[
                ft.dropdown.Option(key=name, text=name)
                for name in PROVIDERS.keys()
            ],
            value="OpenAI",
            width=250,
            bgcolor=Colors.SURFACE,
            border_radius=8,
            on_change=self._on_provider_change,
        )
        
        # Model dropdown
        self.model_dropdown = ft.Dropdown(
            label="Model",
            hint_text="Select Model",
            options=[
                ft.dropdown.Option(key=m, text=m)
                for m in PROVIDERS["OpenAI"]["models"]
            ],
            value="gpt-4o",
            width=250,
            bgcolor=Colors.SURFACE,
            border_radius=8,
        )
        
        # Target language dropdown
        self.language_dropdown = ft.Dropdown(
            label="Target Language",
            hint_text="Select Language",
            options=[
                ft.dropdown.Option(key=lang["code"], text=lang["name"])
                for lang in LANGUAGES
            ],
            value="vi",
            width=250,
            bgcolor=Colors.SURFACE,
            border_radius=8,
        )
        
        # Optional settings (collapsible)
        self.temperature_slider = ft.Slider(
            min=0,
            max=1,
            value=0.2,
            divisions=10,
            label="{value}",
            active_color=Colors.PRIMARY,
        )
        
        self.temperature_label = ft.Text(
            "Temperature: 0.2",
            size=12,
            color=Colors.TEXT_SECONDARY,
        )
        
        self.optional_settings = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(height=8),
                    self.temperature_label,
                    self.temperature_slider,
                ],
                spacing=4,
            ),
            visible=False,
        )
        
        self.expand_btn = ft.TextButton(
            text="Advanced Settings",
            icon=ft.Icons.EXPAND_MORE,
            style=ft.ButtonStyle(
                color=Colors.TEXT_SECONDARY,
            ),
            on_click=self._toggle_advanced,
        )
        
        # Layout
        self.content = ft.Column(
            controls=[
                ft.Text(
                    "Translation Settings",
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=Colors.TEXT_SECONDARY,
                ),
                ft.Container(height=12),
                
                # Dropdowns row
                ft.ResponsiveRow(
                    controls=[
                        ft.Container(
                            content=self.provider_dropdown,
                            col={"sm": 12, "md": 4},
                        ),
                        ft.Container(
                            content=self.model_dropdown,
                            col={"sm": 12, "md": 4},
                        ),
                        ft.Container(
                            content=self.language_dropdown,
                            col={"sm": 12, "md": 4},
                        ),
                    ],
                ),
                
                ft.Container(height=8),
                self.expand_btn,
                self.optional_settings,
            ],
            spacing=0,
        )
        
        self.padding = ft.padding.all(24)
        self.bgcolor = Colors.BACKGROUND

    def _on_provider_change(self, e):
        """Handle provider selection change."""
        provider = e.control.value
        if provider in PROVIDERS:
            models = PROVIDERS[provider]["models"]
            self.model_dropdown.options = [
                ft.dropdown.Option(key=m, text=m)
                for m in models
            ]
            self.model_dropdown.value = models[0] if models else None
            self.update()

    def _toggle_advanced(self, e):
        """Toggle advanced settings visibility."""
        self._expanded = not self._expanded
        self.optional_settings.visible = self._expanded
        self.expand_btn.icon = (
            ft.Icons.EXPAND_LESS if self._expanded else ft.Icons.EXPAND_MORE
        )
        self.update()

    def set_enabled(self, enabled: bool):
        """Enable or disable the selector."""
        self._enabled = enabled
        self.provider_dropdown.disabled = not enabled
        self.model_dropdown.disabled = not enabled
        self.language_dropdown.disabled = not enabled
        self.temperature_slider.disabled = not enabled
        self.update()

    def get_provider(self) -> str:
        """Get selected provider name."""
        return self.provider_dropdown.value or "OpenAI"

    def get_model(self) -> str:
        """Get selected model name."""
        return self.model_dropdown.value or "gpt-4o"

    def get_target_language(self) -> str:
        """Get selected target language code."""
        return self.language_dropdown.value or "vi"

    def get_temperature(self) -> float:
        """Get selected temperature."""
        return self.temperature_slider.value or 0.2
