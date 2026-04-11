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

import base64
import flet as ft
from typing import Optional
from enum import Enum
from pathlib import Path

from lexora.ui.components.file_picker import FilePicker
from lexora.ui.components.provider_selector import ProviderSelector
from lexora.ui.components.progress_panel import ProgressPanel
from lexora.ui.components.output_panel import OutputPanel
from lexora.ui.theme import Colors


REPO_ROOT = Path(__file__).resolve().parents[4]
BRANDING_DIR = REPO_ROOT / "assets" / "branding"
BRANDING_LOGO_DARK_SVG = BRANDING_DIR / "lexora-ai-logo-dark-v2.2.svg"
BRANDING_LOGO_LIGHT_SVG = BRANDING_DIR / "lexora-ai-logo-light-v2.2.svg"
BRANDING_LOGO_FALLBACK_SVG = BRANDING_DIR / "lexora-ai-logo.svg"


def _resolve_logo_path(theme_mode: ft.ThemeMode) -> Path:
    """Return the best logo asset for the active theme."""
    if theme_mode == ft.ThemeMode.LIGHT:
        preferred = BRANDING_LOGO_LIGHT_SVG
    else:
        preferred = BRANDING_LOGO_DARK_SVG
    if preferred.exists():
        return preferred
    return BRANDING_LOGO_FALLBACK_SVG


def _load_logo_data_uri(theme_mode: ft.ThemeMode) -> str | None:
    """Embed the SVG so the header logo renders reliably in Flet."""
    logo_path = _resolve_logo_path(theme_mode)
    if not logo_path.exists():
        return None
    svg_bytes = logo_path.read_bytes()
    encoded = base64.b64encode(svg_bytes).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


class UIState(Enum):
    """Application UI states."""
    IDLE = "idle"
    FILE_SELECTED = "file_selected"
    TRANSLATING = "translating"
    COMPLETED = "completed"
    ERROR = "error"


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
        logo_data_uri = _load_logo_data_uri(self.page.theme_mode)
        if logo_data_uri:
            logo = ft.Image(src=logo_data_uri, width=36, height=36, fit=ft.ImageFit.CONTAIN)
        else:
            logo = ft.Icon(ft.icons.AUTO_STORIES, size=36, color=Colors.PRIMARY)

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            logo,
                            ft.Text(
                                "Lexora AI 1.0",
                                size=28,
                                weight=ft.FontWeight.BOLD,
                                color=Colors.TEXT_PRIMARY,
                            ),
                        ],
                        spacing=12,
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
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
        
        # Run translation async
        import threading
        threading.Thread(target=self._run_translation, daemon=True).start()

    def _run_translation(self):
        """Run the actual Lexora pipeline targeting the selected file."""
        import os
        from pathlib import Path
        from lexora.translator import Translator
        from lexora.providers import create_provider

        try:
            # 1. Get configurations from ProviderSelector
            provider_label = self.provider_selector.provider_dropdown.value
            model_name = self.provider_selector.model_dropdown.value
            target_lang = self.provider_selector.language_dropdown.value

            # Map UI to canonical
            ui_to_canonical = {
                "OpenAI": "openai",
                "Azure OpenAI": "azure-openai",
                "Gemini": "gemini",
                "Anthropic": "anthropic",
                "Qwen": "qwen",
            }
            canonical_name = ui_to_canonical.get(provider_label)
            if not canonical_name:
                raise ValueError(f"Unsupported provider: {provider_label}")
            
            provider_kwargs = {"debug": False}
            if canonical_name == "azure-openai":
                provider_kwargs["deployment"] = model_name
            else:
                provider_kwargs["model"] = model_name
                
            self.progress_panel.set_progress(0.1, f"Configuring {provider_label}...")
            self.page.update()

            provider = create_provider(canonical_name, **provider_kwargs)
            if not provider.is_configured():
                raise ValueError(f"Provider '{provider_label}' is not configured")
            
            translator = Translator(provider=provider)

            # 2. Prepare output path
            source = Path(self.selected_file)
            output_dir_env = os.getenv("LEXORA_UI_OUTPUT_DIR")
            output_dir = Path(output_dir_env) if output_dir_env else source.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            ext = ".md" if source.suffix.lower() == ".md" else ".txt"
            output_path = str(output_dir / f"{source.stem}_{target_lang}{ext}")

            # 3. Translate
            self.progress_panel.set_progress(0.4, "Translating... this may take a while")
            self.page.update()

            translator.translate_file(
                input_file=self.selected_file,
                output_file=output_path,
                target_language=target_lang,
            )

            # 4. Success handling
            if self.state == UIState.TRANSLATING:
                self.progress_panel.set_progress(1.0, "Translation completed!")
                self._update_ui_for_completed(output_path)
            
        except Exception as e:
            if self.state == UIState.TRANSLATING:
                self.state = UIState.ERROR
                self.progress_panel.set_status(f"Error: {e}")
                self.translate_btn.disabled = False
                self.cancel_btn.visible = False
                self.file_picker.set_enabled(True)
                self.provider_selector.set_enabled(True)
                self.page.update()

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
