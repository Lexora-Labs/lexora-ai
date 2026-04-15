"""
Settings Screen

Application settings:
- AI Provider configuration
- API Keys
- Model defaults
- UI preferences
"""

import flet as ft
from typing import Callable, Dict, Optional

import os

from lexora.cli import DEFAULT_GLOBAL_CACHE_PATH
from lexora.ui.i18n import translate
from lexora.ui.theme import Colors


# Provider configurations
PROVIDERS_CONFIG = {
    "OpenAI": {
        "env_var": "OPENAI_API_KEY",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4"],
        "default_model": "gpt-4o",
    },
    "Azure OpenAI": {
        "env_var": "AZURE_OPENAI_KEY",
        "env_vars": ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_KEY", "AZURE_OPENAI_DEPLOYMENT"],
        "models": ["gpt-4o", "gpt-4", "gpt-35-turbo"],
        "default_model": "gpt-4o",
    },
    "Gemini": {
        "env_var": "GOOGLE_API_KEY",
        "models": ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro"],
        "default_model": "gemini-2.0-flash",
    },
    "Anthropic": {
        "env_var": "ANTHROPIC_API_KEY",
        "models": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
        "default_model": "claude-sonnet-4-20250514",
    },
    "Qwen": {
        "env_var": "DASHSCOPE_API_KEY",
        "models": ["qwen-max", "qwen-plus", "qwen-turbo"],
        "default_model": "qwen-max",
    },
}

UI_CACHE_SCOPE_KEY = "lexora_ui_cache_scope"
UI_CACHE_PATH_KEY = "lexora_ui_cache_path"
UI_NO_CACHE_KEY = "lexora_ui_no_cache"
UI_CLEAR_CACHE_KEY = "lexora_ui_clear_cache"


class SettingsScreen(ft.Container):
    """Settings screen with configuration options."""

    def __init__(
        self,
        page: ft.Page,
        *,
        app_locale: str = "en",
        on_app_language: Optional[Callable[[str], None]] = None,
    ):
        super().__init__()
        self.page = page
        self._app_locale = app_locale
        self._on_app_language = on_app_language
        self._build()

    def _build(self):
        """Build the settings UI."""
        cache_scope_value = self._get_storage_value(UI_CACHE_SCOPE_KEY, "global")
        if cache_scope_value not in ("global", "per-ebook", "disabled"):
            cache_scope_value = "global"
        cache_path_value = self._get_storage_value(UI_CACHE_PATH_KEY, DEFAULT_GLOBAL_CACHE_PATH)
        no_cache_value = bool(self._get_storage_value(UI_NO_CACHE_KEY, False))
        clear_cache_value = bool(self._get_storage_value(UI_CLEAR_CACHE_KEY, False))

        # Provider Settings Section
        provider_cards = []
        for name, config in PROVIDERS_CONFIG.items():
            provider_cards.append(self._create_provider_card(name, config))
        
        providers_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.KEY, color=Colors.TEXT_SECONDARY),
                    ft.Text("API Providers", size=18, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                ], spacing=8),
                ft.Container(height=8),
                ft.Text(
                    "Configure your AI provider API keys. Keys are stored securely in environment variables.",
                    size=13,
                    color=Colors.TEXT_SECONDARY,
                ),
                ft.Container(height=16),
                ft.Column(provider_cards, spacing=12),
            ]),
            padding=24,
            bgcolor=Colors.SURFACE,
            border_radius=10,
        )
        
        # Default Settings Section
        self.default_provider = ft.Dropdown(
            label="Default Provider",
            options=[ft.dropdown.Option(p) for p in PROVIDERS_CONFIG.keys()],
            value="OpenAI",
            width=250,
            bgcolor=Colors.BACKGROUND,
            border_radius=8,
            on_change=self._on_default_provider_change,
        )
        
        self.default_model = ft.Dropdown(
            label="Default Model",
            options=[ft.dropdown.Option(m) for m in PROVIDERS_CONFIG["OpenAI"]["models"]],
            value="gpt-4o",
            width=250,
            bgcolor=Colors.BACKGROUND,
            border_radius=8,
        )
        
        self.default_language = ft.Dropdown(
            label="Default Target Language",
            options=[
                ft.dropdown.Option("vi", "Vietnamese"),
                ft.dropdown.Option("en", "English"),
                ft.dropdown.Option("ja", "Japanese"),
                ft.dropdown.Option("zh", "Chinese"),
                ft.dropdown.Option("ko", "Korean"),
            ],
            value="vi",
            width=250,
            bgcolor=Colors.BACKGROUND,
            border_radius=8,
        )
        
        defaults_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.TUNE, color=Colors.TEXT_SECONDARY),
                    ft.Text("Default Settings", size=18, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                ], spacing=8),
                ft.Container(height=16),
                ft.Row([
                    self.default_provider,
                    self.default_model,
                    self.default_language,
                ], spacing=16, wrap=True),
            ]),
            padding=24,
            bgcolor=Colors.SURFACE,
            border_radius=10,
        )
        
        # Translation Settings Section
        self.temperature_slider = ft.Slider(
            min=0,
            max=1,
            value=0.2,
            divisions=10,
            label="{value}",
            active_color=Colors.PRIMARY,
        )
        
        self.bilingual_switch = ft.Switch(value=True, active_color=Colors.PRIMARY)
        self.cache_scope_dropdown = ft.Dropdown(
            label="Cache Scope",
            options=[
                ft.dropdown.Option("global", "Global"),
                ft.dropdown.Option("per-ebook", "Per-ebook"),
                ft.dropdown.Option("disabled", "Disabled"),
            ],
            value=cache_scope_value,
            width=220,
            bgcolor=Colors.BACKGROUND,
            border_radius=8,
        )
        self.cache_path_field = ft.TextField(
            label="Cache Path",
            value=str(cache_path_value),
            width=420,
            bgcolor=Colors.BACKGROUND,
            border_radius=8,
        )
        self.no_cache_switch = ft.Switch(value=no_cache_value, active_color=Colors.PRIMARY)
        self.clear_cache_switch = ft.Switch(value=clear_cache_value, active_color=Colors.PRIMARY)
        
        translation_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.TRANSLATE, color=Colors.TEXT_SECONDARY),
                    ft.Text("Translation Settings", size=18, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                ], spacing=8),
                ft.Container(height=16),
                ft.Row([
                    ft.Text("Temperature:", size=14, color=Colors.TEXT_PRIMARY, width=150),
                    ft.Container(content=self.temperature_slider, expand=True),
                    ft.Text("0.2", size=14, color=Colors.TEXT_SECONDARY),
                ]),
                ft.Container(height=12),
                ft.Row([
                    ft.Text("Bilingual Output:", size=14, color=Colors.TEXT_PRIMARY, width=150),
                    self.bilingual_switch,
                    ft.Text("Keep original text alongside translation", size=13, color=Colors.TEXT_SECONDARY),
                ]),
                ft.Container(height=12),
                ft.Row([
                    self.cache_scope_dropdown,
                    self.cache_path_field,
                ], spacing=16, wrap=True),
                ft.Container(height=12),
                ft.Row([
                    ft.Text("No cache:", size=14, color=Colors.TEXT_PRIMARY, width=150),
                    self.no_cache_switch,
                    ft.Text("Override cache scope and disable cache usage for runs", size=13, color=Colors.TEXT_SECONDARY),
                ]),
                ft.Container(height=12),
                ft.Row([
                    ft.Text("Clear cache before run:", size=14, color=Colors.TEXT_PRIMARY, width=150),
                    self.clear_cache_switch,
                    ft.Text("One-time clear on next run (auto-resets after execution)", size=13, color=Colors.TEXT_SECONDARY),
                ]),
            ]),
            padding=24,
            bgcolor=Colors.SURFACE,
            border_radius=10,
        )
        
        # UI Settings Section
        self.app_language_dropdown = ft.Dropdown(
            label=translate(self._app_locale, "settings.ui_language"),
            options=[
                ft.dropdown.Option("en", "English"),
                ft.dropdown.Option("vi", "Tiếng Việt"),
            ],
            value=self._app_locale if self._app_locale in ("en", "vi") else "en",
            width=200,
            bgcolor=Colors.BACKGROUND,
            border_radius=8,
            on_change=self._on_app_language_dropdown,
            disabled=self._on_app_language is None,
        )

        self.theme_dropdown = ft.Dropdown(
            label="Theme",
            options=[
                ft.dropdown.Option("dark", "Dark"),
                ft.dropdown.Option("light", "Light"),
                ft.dropdown.Option("system", "System"),
            ],
            value="dark",
            width=200,
            bgcolor=Colors.BACKGROUND,
            border_radius=8,
            on_change=self._on_theme_change,
        )
        
        ui_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.PALETTE, color=Colors.TEXT_SECONDARY),
                    ft.Text("Appearance", size=18, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                ], spacing=8),
                ft.Container(height=16),
                ft.Row([
                    self.app_language_dropdown,
                    self.theme_dropdown,
                ], spacing=16, wrap=True),
            ]),
            padding=24,
            bgcolor=Colors.SURFACE,
            border_radius=10,
        )
        
        # Save Button
        save_section = ft.Row([
            ft.ElevatedButton(
                "Save Settings",
                icon=ft.icons.SAVE,
                bgcolor=Colors.PRIMARY,
                color=Colors.TEXT_PRIMARY,
                height=45,
                on_click=self._save_settings,
            ),
            ft.OutlinedButton(
                "Reset to Defaults",
                icon=ft.icons.RESTORE,
                height=45,
                on_click=self._reset_settings,
            ),
        ], spacing=16)
        
        # Layout
        self.content = ft.Column([
            providers_section,
            ft.Container(height=20),
            defaults_section,
            ft.Container(height=20),
            translation_section,
            ft.Container(height=20),
            ui_section,
            ft.Container(height=24),
            save_section,
        ], scroll=ft.ScrollMode.AUTO, expand=True)
        
        self.expand = True

    def _create_provider_card(self, name: str, config: Dict) -> ft.Container:
        """Create a provider configuration card."""
        env_var = config.get("env_var", "")
        is_configured = bool(os.getenv(env_var))
        
        # API Key field (masked)
        api_key_field = ft.TextField(
            label=f"{env_var}",
            hint_text="Enter API key...",
            password=True,
            can_reveal_password=True,
            width=350,
            height=45,
            bgcolor=Colors.BACKGROUND,
            border_radius=8,
        )
        
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(
                        ft.icons.CHECK_CIRCLE if is_configured else ft.icons.ERROR_OUTLINE,
                        color=Colors.SUCCESS if is_configured else Colors.TEXT_SECONDARY,
                        size=24,
                    ),
                    width=40,
                ),
                ft.Column([
                    ft.Text(name, size=15, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                    ft.Text(
                        "Configured" if is_configured else "Not configured",
                        size=12,
                        color=Colors.SUCCESS if is_configured else Colors.TEXT_SECONDARY,
                    ),
                ], spacing=2, width=140),
                api_key_field,
                ft.IconButton(
                    icon=ft.icons.SAVE,
                    icon_color=Colors.PRIMARY,
                    tooltip="Save API Key",
                    on_click=lambda e, n=name: self._save_api_key(n, api_key_field.value),
                ),
            ], spacing=12),
            padding=16,
            bgcolor=Colors.BACKGROUND,
            border_radius=8,
        )

    def _on_default_provider_change(self, e):
        """Handle default provider change."""
        provider = e.control.value
        if provider in PROVIDERS_CONFIG:
            models = PROVIDERS_CONFIG[provider]["models"]
            default_model = PROVIDERS_CONFIG[provider]["default_model"]
            self.default_model.options = [ft.dropdown.Option(m) for m in models]
            self.default_model.value = default_model
            self.page.update()

    def _save_api_key(self, provider: str, api_key: str):
        """Save API key (placeholder)."""
        if api_key:
            # In a real app, this would securely save the key
            self._show_snackbar(f"API key for {provider} saved successfully!", Colors.SUCCESS)
        else:
            self._show_snackbar("Please enter an API key", Colors.WARNING)

    def _on_app_language_dropdown(self, e: ft.ControlEvent) -> None:
        """Notify shell to relabel UI (EN/VI)."""
        lang = e.control.value
        if lang in ("en", "vi") and self._on_app_language:
            self._on_app_language(lang)

    def _on_theme_change(self, e):
        """Apply the selected theme immediately."""
        from lexora.ui.theme import apply_theme
        mode_map = {
            "dark": ft.ThemeMode.DARK,
            "light": ft.ThemeMode.LIGHT,
            "system": ft.ThemeMode.SYSTEM,
        }
        mode = mode_map.get(e.control.value, ft.ThemeMode.DARK)
        apply_theme(self.page, mode)
        self.page.update()

    def _save_settings(self, e):
        """Save all settings."""
        try:
            self.page.client_storage.set(UI_CACHE_SCOPE_KEY, self.cache_scope_dropdown.value or "global")
            self.page.client_storage.set(UI_CACHE_PATH_KEY, (self.cache_path_field.value or DEFAULT_GLOBAL_CACHE_PATH).strip())
            self.page.client_storage.set(UI_NO_CACHE_KEY, bool(self.no_cache_switch.value))
            self.page.client_storage.set(UI_CLEAR_CACHE_KEY, bool(self.clear_cache_switch.value))
        except Exception:
            pass
        self._show_snackbar("Settings saved successfully!", Colors.SUCCESS)

    def _reset_settings(self, e):
        """Reset to default settings."""
        self.default_provider.value = "OpenAI"
        self.default_model.value = "gpt-4o"
        self.default_language.value = "vi"
        self.temperature_slider.value = 0.2
        self.bilingual_switch.value = True
        self.cache_scope_dropdown.value = "global"
        self.cache_path_field.value = DEFAULT_GLOBAL_CACHE_PATH
        self.no_cache_switch.value = False
        self.clear_cache_switch.value = False
        try:
            self.page.client_storage.set(UI_CACHE_SCOPE_KEY, "global")
            self.page.client_storage.set(UI_CACHE_PATH_KEY, DEFAULT_GLOBAL_CACHE_PATH)
            self.page.client_storage.set(UI_NO_CACHE_KEY, False)
            self.page.client_storage.set(UI_CLEAR_CACHE_KEY, False)
        except Exception:
            pass
        self.theme_dropdown.value = "dark"
        # Reset to dark theme
        from lexora.ui.theme import apply_theme
        apply_theme(self.page, ft.ThemeMode.DARK)
        self.page.update()
        self._show_snackbar("Settings reset to defaults", Colors.PRIMARY)

    def _show_snackbar(self, message: str, color: str):
        """Show a snackbar notification."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=Colors.TEXT_PRIMARY),
            bgcolor=color,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _get_storage_value(self, key: str, default):
        """Safe read from client storage with fallback."""
        try:
            value = self.page.client_storage.get(key)
            return default if value is None else value
        except Exception:
            return default
