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
from lexora.secrets import (
    delete_secret,
    delete_setting,
    get_setting,
    get_setting_first,
    has_secret,
    set_secret,
    set_setting,
)
from lexora.ui.i18n import translate
from lexora.ui.theme import Colors


# Provider configurations
PROVIDERS_CONFIG = {
    "OpenAI": {
        "env_var": "OPENAI_API_KEY",
        "secret_vars": ["OPENAI_API_KEY"],
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4"],
        "default_model": "gpt-4o",
        "config_fields": [],
    },
    "Azure OpenAI": {
        "env_var": "AZURE_OPENAI_KEY",
        "secret_vars": ["AZURE_OPENAI_KEY", "AZURE_OPENAI_API_KEY"],
        "env_vars": ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_KEY", "AZURE_OPENAI_DEPLOYMENT"],
        "models": ["gpt-4o", "gpt-4", "gpt-35-turbo"],
        "default_model": "gpt-4o",
        "config_fields": [
            ("AZURE_OPENAI_ENDPOINT", "Endpoint"),
            ("AZURE_OPENAI_DEPLOYMENT", "Deployment"),
            ("AZURE_OPENAI_API_VERSION", "API version"),
        ],
    },
    "Azure Foundry": {
        "env_var": "AZURE_AI_FOUNDRY_API_KEY",
        "secret_vars": ["AZURE_AI_FOUNDRY_API_KEY"],
        "env_vars": ["AZURE_AI_FOUNDRY_ENDPOINT", "AZURE_AI_FOUNDRY_API_KEY", "AZURE_AI_FOUNDRY_MODEL"],
        "models": ["gpt-4.1", "gpt-4o-mini", "gpt-4o"],
        "default_model": "gpt-4.1",
        "config_fields": [
            ("AZURE_AI_FOUNDRY_ENDPOINT", "Endpoint"),
            ("AZURE_AI_FOUNDRY_MODEL", "Model/Deployment"),
        ],
    },
    "Gemini": {
        "env_var": "GOOGLE_API_KEY",
        "secret_vars": ["GOOGLE_API_KEY"],
        "models": ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro"],
        "default_model": "gemini-2.0-flash",
        "config_fields": [
            ("GEMINI_MODEL", "Model"),
        ],
    },
    "Anthropic": {
        "env_var": "ANTHROPIC_API_KEY",
        "secret_vars": ["ANTHROPIC_API_KEY"],
        "models": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
        "default_model": "claude-sonnet-4-20250514",
        "config_fields": [],
    },
    "Qwen": {
        "env_var": "DASHSCOPE_API_KEY",
        "secret_vars": ["DASHSCOPE_API_KEY", "QWEN_API_KEY"],
        "models": ["qwen-max", "qwen-plus", "qwen-turbo"],
        "default_model": "qwen-max",
        "config_fields": [
            ("QWEN_MODEL", "Model"),
            ("QWEN_BASE_URL", "Base URL"),
        ],
    },
}

UI_CACHE_SCOPE_KEY = "lexora_ui_cache_scope"
UI_CACHE_PATH_KEY = "lexora_ui_cache_path"
UI_NO_CACHE_KEY = "lexora_ui_no_cache"
UI_CLEAR_CACHE_KEY = "lexora_ui_clear_cache"
API_KEY_GUIDE_URL = "https://github.com/Lexora-Labs/lexora-ai/blob/main/docs/provider-api-key-guide.md"
README_HELP_URL = "https://github.com/Lexora-Labs/lexora-ai/blob/main/README.md"
SETTING_ALIASES = {
    "AZURE_AI_FOUNDRY_ENDPOINT": [
        "AZURE_AI_FOUNDRY_API_ENDPOINT",
        "AZURE_AI_FOUNDRY_BASE_URL",
    ],
}


class SettingsScreen(ft.Container):
    """Settings screen with configuration options."""

    def __init__(
        self,
        page: ft.Page,
        *,
        app_locale: str = "en",
        on_app_language: Optional[Callable[[str], None]] = None,
        get_theme_mode: Optional[Callable[[], ft.ThemeMode]] = None,
        on_theme_mode: Optional[Callable[[ft.ThemeMode], None]] = None,
    ):
        super().__init__()
        self.page = page
        self._app_locale = app_locale
        self._on_app_language = on_app_language
        self._get_theme_mode = get_theme_mode
        self._on_theme_mode = on_theme_mode
        self._build()

    def _build(self):
        """Build the settings UI."""
        t = lambda key: translate(self._app_locale, key)
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

        help_row = ft.Container(
            content=ft.Row(
                [
                    ft.OutlinedButton(
                        t("settings.help.api_keys"),
                        icon=ft.icons.HELP_OUTLINE,
                        on_click=self._open_api_key_guide,
                    ),
                    ft.TextButton(
                        t("settings.help.readme"),
                        icon=ft.icons.MENU_BOOK,
                        on_click=self._open_readme_help,
                    ),
                ],
                spacing=12,
                wrap=True,
            ),
            padding=ft.padding.only(bottom=12),
        )
        
        providers_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.KEY, color=Colors.TEXT_SECONDARY),
                    ft.Text(t("settings.section.providers"), size=18, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                ], spacing=8),
                ft.Container(height=8),
                ft.Text(
                    t("settings.section.providers.subtitle"),
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
            label=t("settings.default_provider"),
            options=[ft.dropdown.Option(p) for p in PROVIDERS_CONFIG.keys()],
            value="OpenAI",
            width=250,
            bgcolor=Colors.BACKGROUND,
            border_radius=8,
            on_change=self._on_default_provider_change,
        )
        
        self.default_model = ft.Dropdown(
            label=t("settings.default_model"),
            options=[ft.dropdown.Option(m) for m in PROVIDERS_CONFIG["OpenAI"]["models"]],
            value="gpt-4o",
            width=250,
            bgcolor=Colors.BACKGROUND,
            border_radius=8,
        )
        
        self.default_language = ft.Dropdown(
            label=t("settings.default_target_language"),
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
                    ft.Text(t("settings.section.defaults"), size=18, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
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
        self.cache_scope_dropdown = ft.Dropdown(
            label=t("settings.cache_scope"),
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
            label=t("settings.cache_path"),
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
                    ft.Text(t("settings.section.translation"), size=18, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                ], spacing=8),
                ft.Container(height=16),
                ft.Row([
                    self.cache_scope_dropdown,
                    self.cache_path_field,
                ], spacing=16, wrap=True),
                ft.Container(height=12),
                ft.Row([
                    ft.Text(t("settings.no_cache"), size=14, color=Colors.TEXT_PRIMARY, width=150),
                    self.no_cache_switch,
                    ft.Text(t("settings.no_cache_hint"), size=13, color=Colors.TEXT_SECONDARY),
                ]),
                ft.Container(height=12),
                ft.Row([
                    ft.Text(t("settings.clear_cache"), size=14, color=Colors.TEXT_PRIMARY, width=150),
                    self.clear_cache_switch,
                    ft.Text(t("settings.clear_cache_hint"), size=13, color=Colors.TEXT_SECONDARY),
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

        theme_mode = self._get_theme_mode() if self._get_theme_mode else ft.ThemeMode.SYSTEM
        theme_value = {ft.ThemeMode.DARK: "dark", ft.ThemeMode.LIGHT: "light", ft.ThemeMode.SYSTEM: "system"}.get(
            theme_mode, "system"
        )
        self.theme_dropdown = ft.Dropdown(
            label=t("settings.theme"),
            options=[
                ft.dropdown.Option("dark", "Dark"),
                ft.dropdown.Option("light", "Light"),
                ft.dropdown.Option("system", "System"),
            ],
            value=theme_value,
            width=200,
            bgcolor=Colors.BACKGROUND,
            border_radius=8,
            on_change=self._on_theme_change,
            disabled=self._on_theme_mode is None,
        )
        
        ui_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.PALETTE, color=Colors.TEXT_SECONDARY),
                    ft.Text(t("settings.section.appearance"), size=18, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
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
                t("settings.save"),
                icon=ft.icons.SAVE,
                bgcolor=Colors.PRIMARY,
                color=Colors.TEXT_PRIMARY,
                height=45,
                on_click=self._save_settings,
            ),
            ft.OutlinedButton(
                t("settings.reset"),
                icon=ft.icons.RESTORE,
                height=45,
                on_click=self._reset_settings,
            ),
        ], spacing=16)
        
        # Layout
        self.content = ft.Column([
            help_row,
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
        secret_vars = config.get("secret_vars", [env_var])
        source = self._secret_source(secret_vars)
        is_configured = source is not None

        api_key_field = ft.TextField(
            label=f"{env_var}",
            hint_text="Enter API key...",
            password=True,
            can_reveal_password=True,
            value="********" if is_configured else "",
            width=280,
            height=45,
            text_size=12,
            bgcolor=Colors.BACKGROUND,
            border_radius=8,
        )
        extra_fields: Dict[str, ft.TextField] = {}
        for field_key, field_label in config.get("config_fields", []):
            extra_fields[field_key] = ft.TextField(
                label=f"{field_label} ({field_key})",
                value=self._get_setting_with_aliases(field_key),
                width=280,
                height=45,
                text_size=12,
                bgcolor=Colors.BACKGROUND,
                border_radius=8,
            )

        inputs_row = ft.Row(
            controls=[api_key_field] + list(extra_fields.values()),
            spacing=10,
            wrap=True,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        [
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
                                    f"Configured ({source})" if is_configured and source else "Not configured",
                                    size=12,
                                    color=Colors.SUCCESS if is_configured else Colors.TEXT_SECONDARY,
                                ),
                            ], spacing=2, width=180),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.icons.SAVE,
                                icon_color=Colors.PRIMARY,
                                tooltip="Save Provider Config",
                                on_click=lambda e, n=name, k=api_key_field, extras=extra_fields: self._save_api_key(
                                    n,
                                    k.value,
                                    {key: field.value for key, field in extras.items()},
                                ),
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE_OUTLINE,
                                icon_color=Colors.WARNING,
                                tooltip="Delete Local Provider Config",
                                on_click=lambda e, n=name, k=api_key_field, extras=extra_fields: self._delete_provider_config(
                                    n,
                                    k,
                                    extras,
                                ),
                            ),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    inputs_row,
                ],
                spacing=8,
            ),
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

    def _save_api_key(self, provider: str, api_key: str, extra_values: Optional[Dict[str, str]] = None):
        """Save provider secrets and config values to local SQLite store."""
        t = lambda key: translate(self._app_locale, key)
        config = PROVIDERS_CONFIG.get(provider, {})
        env_var = config.get("env_var")
        if not env_var:
            self._show_snackbar(t("settings.snackbar.enter_api"), Colors.WARNING)
            return
        try:
            if api_key and api_key.strip() != "********":
                set_secret(str(env_var), api_key)
            elif not extra_values:
                self._show_snackbar(t("settings.snackbar.enter_api"), Colors.WARNING)
                return

            for k, v in (extra_values or {}).items():
                set_setting(k, v or "")

            self._show_snackbar(t("settings.snackbar.api_saved").format(provider=provider), Colors.SUCCESS)
            self._build()
            self.page.update()
        except Exception:
            self._show_snackbar("Unable to save provider configuration locally.", Colors.ERROR)
            return

        if not api_key and not extra_values:
            self._show_snackbar(t("settings.snackbar.enter_api"), Colors.WARNING)

    def _secret_source(self, names: list[str]) -> Optional[str]:
        """Return where provider key is coming from: env or local store."""
        for name in names:
            if not name:
                continue
            env_val = os.getenv(name)
            if env_val is not None and str(env_val).strip():
                return "env"
        for name in names:
            if name and has_secret(name):
                return "local"
        return None

    def _get_setting_with_aliases(self, key: str) -> str:
        aliases = [key] + SETTING_ALIASES.get(key, [])
        return get_setting_first(aliases, "") or ""

    def _delete_provider_config(
        self,
        provider: str,
        api_key_field: ft.TextField,
        extra_fields: Dict[str, ft.TextField],
    ) -> None:
        config = PROVIDERS_CONFIG.get(provider, {})
        secret_vars = config.get("secret_vars", [])
        field_keys = [k for k, _ in config.get("config_fields", [])]
        try:
            for secret_name in secret_vars:
                if secret_name:
                    delete_secret(secret_name)

            for key in field_keys:
                delete_setting(key)
                for alias in SETTING_ALIASES.get(key, []):
                    delete_setting(alias)

            api_key_field.value = ""
            for field in extra_fields.values():
                field.value = ""

            env_still_active = self._secret_source(secret_vars) == "env"
            message = (
                f"Deleted local config for {provider}. Environment values are still active."
                if env_still_active
                else f"Deleted local config for {provider}."
            )
            self._show_snackbar(message, Colors.SUCCESS)
            self._build()
            self.page.update()
        except Exception:
            self._show_snackbar("Unable to delete local provider configuration.", Colors.ERROR)

    def _on_app_language_dropdown(self, e: ft.ControlEvent) -> None:
        """Notify shell to relabel UI (EN/VI)."""
        lang = e.control.value
        if lang in ("en", "vi") and self._on_app_language:
            self._on_app_language(lang)

    def _on_theme_change(self, e: ft.ControlEvent) -> None:
        """Apply the selected theme (same pipeline as the header theme control)."""
        mode_map = {
            "dark": ft.ThemeMode.DARK,
            "light": ft.ThemeMode.LIGHT,
            "system": ft.ThemeMode.SYSTEM,
        }
        mode = mode_map.get(str(e.control.value), ft.ThemeMode.SYSTEM)
        if self._get_theme_mode and mode == self._get_theme_mode():
            return
        if self._on_theme_mode:
            self._on_theme_mode(mode)

    def _save_settings(self, e):
        """Save all settings."""
        t = lambda key: translate(self._app_locale, key)
        try:
            self.page.client_storage.set(UI_CACHE_SCOPE_KEY, self.cache_scope_dropdown.value or "global")
            self.page.client_storage.set(UI_CACHE_PATH_KEY, (self.cache_path_field.value or DEFAULT_GLOBAL_CACHE_PATH).strip())
            self.page.client_storage.set(UI_NO_CACHE_KEY, bool(self.no_cache_switch.value))
            self.page.client_storage.set(UI_CLEAR_CACHE_KEY, bool(self.clear_cache_switch.value))
        except Exception:
            pass
        self._show_snackbar(t("settings.snackbar.saved"), Colors.SUCCESS)

    def _reset_settings(self, e):
        """Reset to default settings."""
        t = lambda key: translate(self._app_locale, key)
        self.default_provider.value = "OpenAI"
        self.default_model.value = "gpt-4o"
        self.default_language.value = "vi"
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
        if self._on_theme_mode:
            self._on_theme_mode(ft.ThemeMode.DARK)
        else:
            from lexora.ui.theme import apply_theme

            apply_theme(self.page, ft.ThemeMode.DARK)
            self.page.update()
        self._show_snackbar(t("settings.snackbar.reset"), Colors.PRIMARY)

    def _show_snackbar(self, message: str, color: str):
        """Show a snackbar notification."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=Colors.TEXT_PRIMARY),
            bgcolor=color,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _open_api_key_guide(self, _: ft.ControlEvent) -> None:
        """Open provider API key guide on GitHub."""
        try:
            self.page.launch_url(API_KEY_GUIDE_URL)
        except Exception:
            self._show_snackbar("Unable to open API key guide URL.", Colors.WARNING)

    def _open_readme_help(self, _: ft.ControlEvent) -> None:
        """Open project README help on GitHub."""
        try:
            self.page.launch_url(README_HELP_URL)
        except Exception:
            self._show_snackbar("Unable to open README URL.", Colors.WARNING)

    def _get_storage_value(self, key: str, default):
        """Safe read from client storage with fallback."""
        try:
            value = self.page.client_storage.get(key)
            return default if value is None else value
        except Exception:
            return default
