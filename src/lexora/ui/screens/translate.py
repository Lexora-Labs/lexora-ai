"""
Translate Screen

Main translation workflow:
- Upload EPUB file
- Select AI Provider
- Select Model
- Configure options
- Translate with progress
"""

import flet as ft
from typing import Optional, Callable, Dict
import threading
import os
from pathlib import Path
from dotenv import load_dotenv

from lexora.ui.theme import Colors
from lexora.translator import Translator
from lexora.providers import create_provider


# Provider configurations
PROVIDERS: Dict[str, list] = {
    "OpenAI": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4"],
    "Azure OpenAI": ["gpt-4o", "gpt-4", "gpt-35-turbo"],
    "Gemini": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
    "Anthropic": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022"],
    "Qwen": ["qwen-max", "qwen-plus", "qwen-turbo"],
}

LANGUAGES = [
    ("vi", "Vietnamese"),
    ("en", "English"),
    ("ja", "Japanese"),
    ("zh", "Chinese"),
    ("ko", "Korean"),
    ("fr", "French"),
    ("de", "German"),
    ("es", "Spanish"),
]

UI_PROVIDER_TO_CANONICAL = {
    "OpenAI": "openai",
    "Azure OpenAI": "azure-openai",
    "Gemini": "gemini",
    "Anthropic": "anthropic",
    "Qwen": "qwen",
}

load_dotenv()


class TranslateScreen(ft.Container):
    """Translate screen with file upload and translation controls."""

    def __init__(self, page: ft.Page):
        super().__init__()
        self._page = page
        self._selected_file: Optional[str] = None
        self._selected_name: Optional[str] = None
        self._is_translating = False
        self._cancel_requested = False
        self._active_job_id = 0
        self._build()

    def _build(self):
        """Build the translate UI."""
        
        # File Picker
        self.file_picker = ft.FilePicker(on_result=self._on_file_picked)
        self._page.overlay.append(self.file_picker)
        
        # File display
        self.file_icon = ft.Icon(ft.icons.MENU_BOOK, color=Colors.PRIMARY, size=40)
        self.file_name = ft.Text("No file selected", size=16, color=Colors.TEXT_SECONDARY)
        self.file_path = ft.Text("", size=12, color=Colors.TEXT_SECONDARY)
        
        self.select_btn = ft.ElevatedButton(
            "Select EPUB File",
            icon=ft.icons.FOLDER_OPEN,
            bgcolor=Colors.PRIMARY,
            color=Colors.TEXT_PRIMARY,
            height=45,
            on_click=self._pick_file,
        )
        
        file_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.UPLOAD_FILE, color=Colors.TEXT_SECONDARY),
                    ft.Text("File Selection", size=16, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                ], spacing=8),
                ft.Container(height=16),
                ft.Row([
                    self.file_icon,
                    ft.Container(width=16),
                    ft.Column([
                        self.file_name,
                        self.file_path,
                    ], spacing=2, expand=True),
                    self.select_btn,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ]),
            padding=24,
            bgcolor=Colors.SURFACE,
            border_radius=10,
        )
        
        # Provider & Model Selection
        self.model_dropdown = ft.Dropdown(
            label="Model",
            options=[ft.dropdown.Option(m) for m in PROVIDERS["OpenAI"]],
            value="gpt-4o",
            width=200,
            bgcolor=Colors.BACKGROUND,
            border_radius=8,
        )
        
        self.provider_dropdown = ft.Dropdown(
            label="AI Provider",
            options=[ft.dropdown.Option(p) for p in PROVIDERS.keys()],
            value="OpenAI",
            width=200,
            bgcolor=Colors.BACKGROUND,
            border_radius=8,
            on_change=self._on_provider_change,
        )
        
        self.language_dropdown = ft.Dropdown(
            label="Target Language",
            options=[ft.dropdown.Option(key=code, text=name) for code, name in LANGUAGES],
            value="vi",
            width=200,
            bgcolor=Colors.BACKGROUND,
            border_radius=8,
        )
        
        settings_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.SETTINGS, color=Colors.TEXT_SECONDARY),
                    ft.Text("Translation Settings", size=16, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                ], spacing=8),
                ft.Container(height=16),
                ft.Row([
                    self.provider_dropdown,
                    self.model_dropdown,
                    self.language_dropdown,
                ], spacing=16, wrap=True),
                ft.Container(height=16),
                # Advanced options
                ft.ExpansionTile(
                    title=ft.Text("Advanced Options", color=Colors.TEXT_SECONDARY),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text("Temperature:", size=14, color=Colors.TEXT_SECONDARY, width=100),
                                    ft.Slider(min=0, max=1, value=0.2, divisions=10, label="{value}"),
                                ]),
                                ft.Row([
                                    ft.Text("Bilingual:", size=14, color=Colors.TEXT_SECONDARY, width=100),
                                    ft.Switch(value=True),
                                    ft.Text("Keep original + translation", size=12, color=Colors.TEXT_SECONDARY),
                                ]),
                            ]),
                            padding=ft.padding.only(left=16, bottom=16),
                        ),
                    ],
                ),
            ]),
            padding=24,
            bgcolor=Colors.SURFACE,
            border_radius=10,
        )
        
        # Progress Section
        self.progress_bar = ft.ProgressBar(value=0, bgcolor=Colors.BACKGROUND, color=Colors.PRIMARY, bar_height=8)
        self.progress_text = ft.Text("0%", size=16, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)
        self.status_text = ft.Text("Ready to translate", size=14, color=Colors.TEXT_SECONDARY)
        self.chapter_text = ft.Text("", size=12, color=Colors.TEXT_SECONDARY, italic=True)
        
        self.progress_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.DOWNLOADING, color=Colors.TEXT_SECONDARY),
                    ft.Text("Progress", size=16, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                ], spacing=8),
                ft.Container(height=16),
                ft.Row([
                    ft.Container(content=self.progress_bar, expand=True),
                    ft.Container(width=16),
                    self.progress_text,
                ]),
                ft.Container(height=8),
                self.status_text,
                self.chapter_text,
            ]),
            padding=24,
            bgcolor=Colors.SURFACE,
            border_radius=10,
            visible=False,
        )
        
        # Output Section
        self.output_name = ft.Text("", size=16, weight=ft.FontWeight.W_500, color=Colors.TEXT_PRIMARY)
        self.output_path = ft.Text("", size=12, color=Colors.TEXT_SECONDARY)
        
        self.output_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.CHECK_CIRCLE, color=Colors.SUCCESS),
                    ft.Text("Output", size=16, weight=ft.FontWeight.W_600, color=Colors.SUCCESS),
                ], spacing=8),
                ft.Container(height=16),
                ft.Row([
                    ft.Icon(ft.icons.DESCRIPTION, color=Colors.SUCCESS, size=40),
                    ft.Container(width=16),
                    ft.Column([
                        self.output_name,
                        self.output_path,
                    ], spacing=2, expand=True),
                    ft.ElevatedButton("Open File", icon=ft.icons.OPEN_IN_NEW, bgcolor=Colors.PRIMARY, color=Colors.TEXT_PRIMARY),
                    ft.OutlinedButton("Open Folder", icon=ft.icons.FOLDER_OPEN),
                ], spacing=12),
            ]),
            padding=24,
            bgcolor=Colors.SURFACE,
            border_radius=10,
            visible=False,
        )
        
        # Action Buttons
        self.translate_btn = ft.ElevatedButton(
            "🚀 Start Translation",
            bgcolor=Colors.PRIMARY,
            color=Colors.TEXT_PRIMARY,
            height=50,
            width=220,
            disabled=True,
            on_click=self._on_translate,
        )
        
        self.cancel_btn = ft.OutlinedButton(
            "Cancel",
            height=50,
            visible=False,
            on_click=self._on_cancel,
        )
        
        action_section = ft.Row(
            [self.translate_btn, self.cancel_btn],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=16,
        )
        
        # Layout
        self.content = ft.Column([
            file_section,
            ft.Container(height=16),
            settings_section,
            ft.Container(height=24),
            action_section,
            ft.Container(height=16),
            self.progress_section,
            ft.Container(height=16),
            self.output_section,
        ], scroll=ft.ScrollMode.AUTO, expand=True)
        
        self.expand = True

    def _pick_file(self, e):
        """Open file picker."""
        self.file_picker.pick_files(
            allowed_extensions=["epub", "mobi", "docx", "doc", "md"],
            dialog_title="Select file",
        )

    def _on_file_picked(self, e: ft.FilePickerResultEvent):
        """Handle file selection."""
        if e.files and len(e.files) > 0:
            f = e.files[0]
            self._selected_file = f.path
            self._selected_name = f.name
            
            self.file_name.value = f.name
            self.file_name.color = Colors.TEXT_PRIMARY
            self.file_path.value = str(Path(f.path).parent)
            self.translate_btn.disabled = False
            
            self._page.update()

    def _on_provider_change(self, e):
        """Handle provider selection change."""
        provider = e.control.value
        models = PROVIDERS.get(provider, [])
        self.model_dropdown.options = [ft.dropdown.Option(m) for m in models]
        self.model_dropdown.value = models[0] if models else None
        self._page.update()

    def _on_translate(self, e):
        """Start translation."""
        if not self._selected_file or self._is_translating:
            return

        provider_label = self.provider_dropdown.value
        model_name = self.model_dropdown.value
        target_lang = self.language_dropdown.value

        if not provider_label or not model_name or not target_lang:
            self.status_text.value = "Please select provider, model, and language"
            self.status_text.color = Colors.ERROR
            self._page.update()
            return
        
        self._active_job_id += 1
        current_job_id = self._active_job_id
        self._is_translating = True
        self._cancel_requested = False
        self._update_ui_translating(True)
        self.progress_bar.value = None
        self.progress_text.value = "..."
        self.status_text.value = "Starting translation..."
        self.status_text.color = Colors.TEXT_SECONDARY
        self.chapter_text.value = f"{provider_label} • {model_name} • {target_lang}"
        self._page.update()
        
        # Run translation in background.
        threading.Thread(
            target=self._run_translation,
            args=(current_job_id, provider_label, model_name, target_lang),
            daemon=True,
        ).start()

    def _on_cancel(self, e):
        """Cancel translation."""
        if not self._is_translating:
            return

        self._cancel_requested = True
        self.cancel_btn.disabled = True
        self.status_text.value = "Cancel requested..."
        self.status_text.color = Colors.WARNING
        self.chapter_text.value = "Waiting for current provider request to return."
        self._page.update()

    def _update_ui_translating(self, translating: bool):
        """Update UI for translation state."""
        self.translate_btn.disabled = translating
        self.cancel_btn.visible = translating
        self.cancel_btn.disabled = False
        self.progress_section.visible = translating
        self.output_section.visible = False
        self.provider_dropdown.disabled = translating
        self.model_dropdown.disabled = translating
        self.language_dropdown.disabled = translating
        self.select_btn.disabled = translating
        self._page.update()

    def _build_provider(self, provider_label: str, model_name: str):
        canonical_name = UI_PROVIDER_TO_CANONICAL.get(provider_label)
        if not canonical_name:
            raise ValueError(f"Unsupported provider: {provider_label}")

        provider_kwargs: Dict[str, object] = {"debug": False}
        if canonical_name == "azure-openai":
            provider_kwargs["deployment"] = model_name
        else:
            provider_kwargs["model"] = model_name

        provider = create_provider(canonical_name, **provider_kwargs)
        if not provider.is_configured():
            raise ValueError(f"Provider '{provider_label}' is not configured")
        return provider

    def _build_output_path(self, input_file: str, target_lang: str) -> str:
        source = Path(input_file)
        output_dir_env = os.getenv("LEXORA_UI_OUTPUT_DIR")
        output_dir = Path(output_dir_env) if output_dir_env else source.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Keep markdown output as markdown; otherwise output plain text.
        ext = ".md" if source.suffix.lower() == ".md" else ".txt"
        return str(output_dir / f"{source.stem}_{target_lang}{ext}")

    def _run_translation(
        self,
        job_id: int,
        provider_label: str,
        model_name: str,
        target_lang: str,
    ):
        """Run translation with the real Lexora pipeline."""
        try:
            if not self._selected_file:
                raise ValueError("No file selected")

            provider = self._build_provider(provider_label, model_name)
            translator = Translator(provider=provider)
            output_file = self._build_output_path(self._selected_file, target_lang)

            self.status_text.value = "Translating file..."
            self.chapter_text.value = "Reading and translating content"
            self._page.update()

            translator.translate_file(
                input_file=self._selected_file,
                output_file=output_file,
                target_language=target_lang,
            )

            if self._active_job_id != job_id:
                return

            if self._cancel_requested:
                self.status_text.value = "Cancelled"
                self.status_text.color = Colors.WARNING
                self.chapter_text.value = "Current provider request may still complete in background."
                return

            self.progress_bar.value = 1.0
            self.progress_text.value = "100%"
            self.status_text.value = "Translation completed"
            self.status_text.color = Colors.SUCCESS
            self.chapter_text.value = ""

            output_path = Path(output_file)
            self.output_name.value = output_path.name
            self.output_path.value = str(output_path.parent)
            self.output_section.visible = True
        except Exception as exc:
            self.progress_bar.value = 0
            self.progress_text.value = "0%"
            self.status_text.value = f"Failed: {exc}"
            self.status_text.color = Colors.ERROR
            self.chapter_text.value = "Check credentials, model/deployment, and provider configuration."
        finally:
            if self._active_job_id == job_id:
                self._is_translating = False
                self.translate_btn.disabled = False
                self.cancel_btn.visible = False
                self.cancel_btn.disabled = False
                self.provider_dropdown.disabled = False
                self.model_dropdown.disabled = False
                self.language_dropdown.disabled = False
                self.select_btn.disabled = False
                self._page.update()
