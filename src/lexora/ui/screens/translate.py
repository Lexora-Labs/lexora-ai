"""Translate screen wired to CLI-equivalent translation options."""

from __future__ import annotations

import asyncio
import logging
import os
import threading
import time
from pathlib import Path
from typing import Dict, Optional

import flet as ft
from dotenv import load_dotenv

from lexora.cli import (
    DEFAULT_GLOBAL_CACHE_PATH,
    _clear_cache_file,
    _load_glossary,
    _resolve_cache_path,
    _write_run_report,
)
from lexora.providers import canonical_provider_name, create_provider
from lexora.translator import Translator
from lexora.logging_framework import build_logging_config, configure_logging, get_ui_log_events
from lexora.ui.theme import Colors


PROVIDERS: Dict[str, list[str]] = {
    "OpenAI": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4"],
    "Azure OpenAI": ["gpt-4o", "gpt-4", "gpt-35-turbo"],
    "Azure Foundry": ["gpt-4o-mini", "gpt-4o"],
    "Gemini": ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro"],
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
    "Azure Foundry": "azure-foundry",
    "Gemini": "gemini",
    "Anthropic": "anthropic",
    "Qwen": "qwen",
}

load_dotenv()

UI_CACHE_SCOPE_KEY = "lexora_ui_cache_scope"
UI_CACHE_PATH_KEY = "lexora_ui_cache_path"
UI_NO_CACHE_KEY = "lexora_ui_no_cache"
UI_CLEAR_CACHE_KEY = "lexora_ui_clear_cache"
CONTROL_HEIGHT = 48
CONTROL_TEXT_SIZE = 12
DROPDOWN_HEIGHT = 55


def _ensure_console_logging() -> None:
    """Ensure app logging includes a UI sink for in-app log rendering."""
    current_targets = set(
        token.strip().lower()
        for token in os.getenv("LEXORA_LOG_TARGETS", "console").split(",")
        if token.strip()
    )
    if not current_targets:
        current_targets = {"console"}
    current_targets.add("ui")
    config = build_logging_config(targets=",".join(sorted(current_targets)))
    configure_logging(config)


class TranslateScreen(ft.Container):
    """Translate screen with CLI-equivalent runtime options."""

    def __init__(self, page: ft.Page):
        super().__init__()
        _ensure_console_logging()
        self._logger = logging.getLogger("lexora.ui.translate")
        self._page = page
        self._selected_file: Optional[str] = None
        self._selected_name: Optional[str] = None
        self._selected_glossary: Optional[str] = None
        self._is_translating = False
        self._cancel_requested = False
        self._active_job_id = 0
        self._ui_log_cursor = 0
        self._ui_log_poller_started = False
        self._build()

    def _build(self) -> None:
        self.file_picker = ft.FilePicker(on_result=self._on_file_picked)
        self.glossary_picker = ft.FilePicker(on_result=self._on_glossary_picked)
        self._page.overlay.append(self.file_picker)
        self._page.overlay.append(self.glossary_picker)

        self.file_icon = ft.Icon(ft.icons.MENU_BOOK, color=Colors.PRIMARY, size=40)
        self.file_name = ft.Text("No file selected", size=16, color=Colors.TEXT_SECONDARY)
        self.file_path = ft.Text("", size=12, color=Colors.TEXT_SECONDARY, visible=False)
        self.select_btn = ft.ElevatedButton(
            "Select input file",
            icon=ft.icons.FOLDER_OPEN,
            bgcolor=Colors.PRIMARY,
            color=Colors.TEXT_PRIMARY,
            height=CONTROL_HEIGHT,          
            on_click=self._pick_file,
        )
        file_section = ft.Container(
            padding=8,
            bgcolor=Colors.SURFACE,
            border_radius=10,
            content=ft.Column(
                [
                    ft.Row([ft.Icon(ft.icons.UPLOAD_FILE), ft.Text("File Selection", size=16, weight=ft.FontWeight.W_600)], spacing=8),
                    ft.Container(height=4),
                    ft.Row(
                        [
                            ft.Icon(ft.icons.MENU_BOOK, color=Colors.PRIMARY, size=28),
                            ft.Container(width=12),
                            ft.Container(
                                expand=True,
                                height=CONTROL_HEIGHT,
                                alignment=ft.alignment.center_left,
                                content=ft.Column(
                                    [self.file_name, self.file_path],
                                    spacing=0,
                                    tight=True,
                                    horizontal_alignment=ft.CrossAxisAlignment.START,
                                ),                              
                            ),
                            self.select_btn,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                  
                ]
            ),
        )

        self.provider_dropdown = ft.Dropdown(
            label="Provider",
            options=[ft.dropdown.Option(p) for p in PROVIDERS.keys()],
            value="OpenAI",
            width=180,
            height=DROPDOWN_HEIGHT,
            text_size=CONTROL_TEXT_SIZE,
            on_change=self._on_provider_change,
        )
        self.model_dropdown = ft.Dropdown(
            label="Model",
            options=[ft.dropdown.Option(m) for m in PROVIDERS["OpenAI"]],
            value=PROVIDERS["OpenAI"][0],
            width=220,
            height=DROPDOWN_HEIGHT,
            text_size=CONTROL_TEXT_SIZE,
        )
        self.target_language_dropdown = ft.Dropdown(
            label="Target Language",
            options=[ft.dropdown.Option(key=code, text=name) for code, name in LANGUAGES],
            value="vi",
            width=180,
            height=DROPDOWN_HEIGHT,
            text_size=CONTROL_TEXT_SIZE,
            on_change=self._on_target_language_change,
        )
        self.source_language_dropdown = ft.Dropdown(
            label="Source Language",
            options=[ft.dropdown.Option("auto", "Auto detect")] + [ft.dropdown.Option(key=code, text=name) for code, name in LANGUAGES],
            value="auto",
            width=180,
            height=DROPDOWN_HEIGHT,
            text_size=CONTROL_TEXT_SIZE,
        )
        self.mode_dropdown = ft.Dropdown(
            label="Mode",
            options=[ft.dropdown.Option("replace"), ft.dropdown.Option("bilingual")],
            value="replace",
            width=130,
            height=DROPDOWN_HEIGHT,
            text_size=CONTROL_TEXT_SIZE,
        )
        self.output_file_field = ft.TextField(
            label="Output file",
            value="",
            hint_text="Auto: inputFileName<lang>.ext",
            width=500,
            height=CONTROL_HEIGHT,
            text_size=CONTROL_TEXT_SIZE,
        )
        self.output_reset_btn = ft.OutlinedButton(
            "Reset default",
            icon=ft.icons.RESTART_ALT,
            height=CONTROL_HEIGHT,
            on_click=self._on_reset_output_default,
        )

        self.glossary_path = ft.Text("", size=12, color=Colors.TEXT_SECONDARY)
        glossary_row = ft.Row(
            [
                ft.OutlinedButton("Select glossary JSON", icon=ft.icons.ARTICLE_OUTLINED, on_click=lambda _: self.glossary_picker.pick_files(allowed_extensions=["json"], dialog_title="Select glossary JSON")),
                ft.OutlinedButton("Clear glossary", icon=ft.icons.CLEAR, on_click=self._clear_glossary),
            ],
            spacing=8,
            wrap=True,
        )

        self.limit_docs_field = ft.TextField(label="Limit docs", value="", width=110, height=CONTROL_HEIGHT, text_size=CONTROL_TEXT_SIZE)
        self.start_doc_field = ft.TextField(label="Start doc", value="", width=110, height=CONTROL_HEIGHT, text_size=CONTROL_TEXT_SIZE)
        self.end_doc_field = ft.TextField(label="End doc", value="", width=110, height=CONTROL_HEIGHT, text_size=CONTROL_TEXT_SIZE)
        self.chunk_size_field = ft.TextField(label="Chunk size", value="1200", width=120, height=CONTROL_HEIGHT, text_size=CONTROL_TEXT_SIZE)
        self.chunk_context_field = ft.TextField(label="Context window", value="0", width=130, height=CONTROL_HEIGHT, text_size=CONTROL_TEXT_SIZE)
        self.structured_batch_switch = ft.Switch(value=False)
        self.structured_max_chars_field = ft.TextField(label="Structured max chars", value="8000", width=160, height=CONTROL_HEIGHT, text_size=CONTROL_TEXT_SIZE)
        self.report_path_field = ft.TextField(
            label="Report path (optional)",
            value="",
            height=CONTROL_HEIGHT,
            text_size=CONTROL_TEXT_SIZE,
        )

        settings_section = ft.Container(
            padding=10,
            bgcolor=Colors.SURFACE,
            border_radius=10,
            content=ft.Column(
                [
                    ft.Row([ft.Icon(ft.icons.SETTINGS), ft.Text("Translation Settings", size=16, weight=ft.FontWeight.W_600)], spacing=8),
                    ft.Container(height=6),
                    ft.Row([self.provider_dropdown, self.model_dropdown, self.target_language_dropdown, self.source_language_dropdown, self.mode_dropdown], spacing=12, wrap=True),
                    ft.Row([self.output_file_field, self.output_reset_btn], spacing=8, wrap=True),
                    ft.Container(height=4),
                    glossary_row,
                    self.glossary_path,
                ],
                spacing=4,
            ),
        )

        self._advanced_expanded = False
        self.advanced_toggle_btn = ft.IconButton(
            icon=ft.icons.EXPAND_MORE,
            icon_size=18,
            icon_color=Colors.TEXT_SECONDARY,
            tooltip="Expand advanced config",
            width=CONTROL_HEIGHT,
            height=CONTROL_HEIGHT,
            style=ft.ButtonStyle(padding=0),
            on_click=self._toggle_advanced_config,
        )
        self.advanced_controls = ft.Container(
            visible=False,
            padding=ft.padding.only(top=4),
            content=ft.Column(
                [
                    ft.Container(
                        alignment=ft.alignment.center_left,
                        content=ft.Row(
                            [self.limit_docs_field, self.start_doc_field, self.end_doc_field, self.chunk_size_field, self.chunk_context_field],
                            spacing=8,
                            wrap=True,
                            alignment=ft.MainAxisAlignment.START,
                        ),
                    ),
                    ft.Container(
                        alignment=ft.alignment.center_left,
                        content=ft.Row(
                            [
                                ft.Text("Structured EPUB batch"),
                                self.structured_batch_switch,
                                self.structured_max_chars_field,
                            ],
                            spacing=8,
                            wrap=True,
                            alignment=ft.MainAxisAlignment.START,
                        ),
                    ),
                    ft.Container(
                        alignment=ft.alignment.center_left,
                        content=ft.Row(
                            [ft.Container(content=self.report_path_field, expand=True)],
                            spacing=8,
                            wrap=False,
                            alignment=ft.MainAxisAlignment.START,
                        ),
                    ),
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
        )
        advanced_section = ft.Container(
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            bgcolor=Colors.SURFACE,
            border_radius=10,
            content=ft.Column(
                [
                    ft.Container(
                        height=CONTROL_HEIGHT,
                        alignment=ft.alignment.center_left,
                        content=ft.Row(
                            [
                                ft.Row(
                                    [ft.Icon(ft.icons.TUNE), ft.Text("Advanced config", size=16, weight=ft.FontWeight.W_600)],
                                    spacing=8,
                                    alignment=ft.MainAxisAlignment.START,
                                ),
                                ft.Container(expand=True),
                                self.advanced_toggle_btn,
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ),
                    self.advanced_controls,
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
        )

        self.progress_bar = ft.ProgressBar(value=0, bgcolor=Colors.BACKGROUND, color=Colors.PRIMARY, bar_height=8)
        self.progress_text = ft.Text("0%", size=16, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)
        self.status_text = ft.Text("Ready to translate", size=14, color=Colors.TEXT_SECONDARY)
        self.chapter_text = ft.Text("", size=12, color=Colors.TEXT_SECONDARY, italic=True)
        self.progress_section = ft.Container(
            padding=10,
            bgcolor=Colors.SURFACE,
            border_radius=10,
            visible=False,
            content=ft.Column(
                [
                    ft.Row([ft.Icon(ft.icons.DOWNLOADING), ft.Text("Progress", size=16, weight=ft.FontWeight.W_600)], spacing=8),
                    ft.Container(height=12),
                    ft.Row([ft.Container(content=self.progress_bar, expand=True), ft.Container(width=16), self.progress_text]),
                    ft.Container(height=8),
                    self.status_text,
                    self.chapter_text,
                ]
            ),
        )

        self.output_name = ft.Text("", size=16, weight=ft.FontWeight.W_500, color=Colors.TEXT_PRIMARY)
        self.output_path = ft.Text("", size=12, color=Colors.TEXT_SECONDARY)
        self.output_section = ft.Container(
            padding=10,
            bgcolor=Colors.SURFACE,
            border_radius=10,
            visible=False,
            content=ft.Column(
                [
                    ft.Row([ft.Icon(ft.icons.CHECK_CIRCLE, color=Colors.SUCCESS), ft.Text("Output", size=16, weight=ft.FontWeight.W_600, color=Colors.SUCCESS)], spacing=8),
                    ft.Container(height=12),
                    ft.Row([ft.Icon(ft.icons.DESCRIPTION, color=Colors.SUCCESS, size=40), ft.Container(width=16), ft.Column([self.output_name, self.output_path], spacing=2, expand=True)]),
                ]
            ),
        )
        self.translation_log_list = ft.ListView(
            expand=False,
            height=160,
            spacing=4,
            auto_scroll=True,
        )
        self.translation_log_section = ft.Container(
            padding=10,
            bgcolor=Colors.SURFACE,
            border_radius=10,
            content=ft.Column(
                [
                    ft.Row([ft.Icon(ft.icons.LIST_ALT), ft.Text("Translation Log", size=15, weight=ft.FontWeight.W_600)], spacing=8),
                    self.translation_log_list,
                ],
                spacing=8,
            ),
        )

        self.translate_btn = ft.ElevatedButton(
            "Start Translation",
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
        action_section = ft.Row([self.translate_btn, self.cancel_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=16)

        self.content = ft.Column(
            [
                file_section,
                ft.Container(height=16),
                settings_section,
                ft.Container(height=16),
                advanced_section,
                ft.Container(height=24),
                action_section,
                ft.Container(height=16),
                self.progress_section,
                ft.Container(height=16),
                self.output_section,
                ft.Container(height=16),
                self.translation_log_section,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.expand = True
        self._ui_log_cursor = len(get_ui_log_events())
        self._start_ui_log_poller()
        self._log_ui_action("Translate screen ready")

    def _log_ui_action(self, message: str, level: int = logging.INFO) -> None:
        self._logger.log(level, message)
        self._flush_ui_log_events()

    def _start_ui_log_poller(self) -> None:
        if self._ui_log_poller_started:
            return
        self._ui_log_poller_started = True
        self._page.run_task(self._poll_ui_logs)

    async def _poll_ui_logs(self) -> None:
        while True:
            self._flush_ui_log_events()
            await asyncio.sleep(0.8)

    def _flush_ui_log_events(self) -> None:
        events = get_ui_log_events()
        if self._ui_log_cursor >= len(events):
            return
        new_events = events[self._ui_log_cursor :]
        self._ui_log_cursor = len(events)
        for event in new_events:
            level_name = str(event.get("level") or "INFO")
            timestamp = str(event.get("timestamp") or time.strftime("%H:%M:%S"))
            message = str(event.get("message") or "")
            color = (
                Colors.ERROR if level_name in {"ERROR", "CRITICAL"} else
                Colors.WARNING if level_name == "WARNING" else
                Colors.TEXT_SECONDARY
            )
            self.translation_log_list.controls.append(
                ft.Text(f"[{timestamp}] {level_name}: {message}", size=12, color=color)
            )
        if len(self.translation_log_list.controls) > 400:
            self.translation_log_list.controls = self.translation_log_list.controls[-400:]
        try:
            self.translation_log_list.update()
        except Exception:
            pass

    def _pick_file(self, _: ft.ControlEvent) -> None:
        self._log_ui_action("Open file picker")
        self.file_picker.pick_files(
            allowed_extensions=["epub", "mobi", "docx", "doc", "md"],
            dialog_title="Select file",
        )

    def _on_file_picked(self, e: ft.FilePickerResultEvent) -> None:
        if e.files and len(e.files) > 0:
            f = e.files[0]
            picked_path = getattr(f, "path", None)
            self._selected_file = picked_path
            self._selected_name = f.name
            self.file_name.value = f.name
            self.file_name.color = Colors.TEXT_PRIMARY
            if picked_path:
                self.file_path.value = str(Path(picked_path).parent)
                self.file_path.visible = True
                self._refresh_output_file_default(force=True)
                self.translate_btn.disabled = False
                self._log_ui_action(f"Selected file: {f.name}")
            else:
                self.file_path.value = "No local file path available in browser mode."
                self.file_path.visible = True
                self.status_text.value = "Cannot access local path in browser mode; use desktop mode to translate local files."
                self.status_text.color = Colors.WARNING
                self.translate_btn.disabled = True
                self._log_ui_action("File selected without local path (browser mode)", logging.WARNING)
            self._page.update()

    def _on_target_language_change(self, _: ft.ControlEvent) -> None:
        """Keep output-file default synced with selected target language."""
        self._refresh_output_file_default()
        self._page.update()

    def _toggle_advanced_config(self, _: ft.ControlEvent) -> None:
        self._advanced_expanded = not self._advanced_expanded
        self.advanced_controls.visible = self._advanced_expanded
        self.advanced_toggle_btn.icon = (
            ft.icons.EXPAND_LESS if self._advanced_expanded else ft.icons.EXPAND_MORE
        )
        self.advanced_toggle_btn.tooltip = (
            "Collapse advanced config" if self._advanced_expanded else "Expand advanced config"
        )
        self._page.update()

    def _on_glossary_picked(self, e: ft.FilePickerResultEvent) -> None:
        if e.files and len(e.files) > 0:
            self._selected_glossary = e.files[0].path
            self.glossary_path.value = self._selected_glossary or ""
            self._page.update()

    def _clear_glossary(self, _: ft.ControlEvent) -> None:
        self._selected_glossary = None
        self.glossary_path.value = ""
        self._page.update()

    def _on_provider_change(self, e: ft.ControlEvent) -> None:
        provider = e.control.value
        models = PROVIDERS.get(provider, [])
        self.model_dropdown.options = [ft.dropdown.Option(m) for m in models]
        self.model_dropdown.value = models[0] if models else None
        self._page.update()

    def _build_default_output_path(self, input_file: str, target_lang: str) -> str:
        source = Path(input_file)
        # Keep source extension and output in the same folder by default.
        return str(source.parent / f"{source.stem}-{target_lang}{source.suffix}")

    def _refresh_output_file_default(self, *, force: bool = False) -> None:
        if not self._selected_file:
            return
        current_value = (self.output_file_field.value or "").strip()
        if force or not current_value:
            target_lang = self.target_language_dropdown.value or "vi"
            self.output_file_field.value = self._build_default_output_path(self._selected_file, target_lang)

    def _on_reset_output_default(self, _: ft.ControlEvent) -> None:
        self._refresh_output_file_default(force=True)
        self._page.update()

    def _parse_optional_int(self, value: str, field_name: str) -> Optional[int]:
        if not value.strip():
            return None
        try:
            return int(value.strip())
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an integer") from exc

    def _load_cache_settings(self) -> dict[str, object]:
        """Load cache-related runtime options from Settings (client storage)."""
        cache_scope = "global"
        cache_path = DEFAULT_GLOBAL_CACHE_PATH
        no_cache = False
        clear_cache = False
        try:
            scope_stored = self._page.client_storage.get(UI_CACHE_SCOPE_KEY)
            path_stored = self._page.client_storage.get(UI_CACHE_PATH_KEY)
            no_cache_stored = self._page.client_storage.get(UI_NO_CACHE_KEY)
            clear_cache_stored = self._page.client_storage.get(UI_CLEAR_CACHE_KEY)
            if scope_stored in ("global", "per-ebook", "disabled"):
                cache_scope = str(scope_stored)
            if isinstance(path_stored, str) and path_stored.strip():
                cache_path = path_stored.strip()
            if isinstance(no_cache_stored, bool):
                no_cache = no_cache_stored
            if isinstance(clear_cache_stored, bool):
                clear_cache = clear_cache_stored
        except Exception:
            pass
        return {
            "cache_scope": cache_scope,
            "cache_path": cache_path,
            "no_cache": no_cache,
            "clear_cache": clear_cache,
        }

    def _on_translate(self, _: ft.ControlEvent) -> None:
        if not self._selected_file or self._is_translating:
            return
        provider_label = self.provider_dropdown.value
        model_name = self.model_dropdown.value
        target_lang = self.target_language_dropdown.value
        if not provider_label or not model_name or not target_lang:
            self.status_text.value = "Please select provider, model, and target language."
            self.status_text.color = Colors.ERROR
            self._log_ui_action("Validation failed: missing provider/model/target", logging.ERROR)
            self._page.update()
            return

        self._log_ui_action("Starting translation run")
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

        threading.Thread(
            target=self._run_translation,
            args=(current_job_id, provider_label, model_name, target_lang),
            daemon=True,
        ).start()

    def _on_cancel(self, _: ft.ControlEvent) -> None:
        if not self._is_translating:
            return
        self._cancel_requested = True
        self.cancel_btn.disabled = True
        self.status_text.value = "Cancel requested..."
        self.status_text.color = Colors.WARNING
        self.chapter_text.value = "Waiting for current provider request to return."
        self._log_ui_action("Cancel requested by user", logging.WARNING)
        self._page.update()

    def _update_ui_translating(self, translating: bool) -> None:
        self.translate_btn.disabled = translating
        self.cancel_btn.visible = translating
        self.cancel_btn.disabled = False
        self.progress_section.visible = translating
        self.output_section.visible = False
        self.provider_dropdown.disabled = translating
        self.model_dropdown.disabled = translating
        self.target_language_dropdown.disabled = translating
        self.source_language_dropdown.disabled = translating
        self.mode_dropdown.disabled = translating
        self.output_file_field.disabled = translating
        self.output_reset_btn.disabled = translating
        self.select_btn.disabled = translating
        self.report_path_field.disabled = translating
        self._page.update()

    def _build_provider(self, provider_label: str, model_name: str):
        canonical_name = UI_PROVIDER_TO_CANONICAL.get(provider_label)
        if not canonical_name:
            raise ValueError(f"Unsupported provider: {provider_label}")
        provider_kwargs: Dict[str, object] = {"debug": False}
        if canonical_name == "azure-openai":
            provider_kwargs["deployment"] = model_name
        elif canonical_name == "azure-foundry":
            provider_kwargs["model"] = model_name
        else:
            provider_kwargs["model"] = model_name
        provider = create_provider(canonical_name, **provider_kwargs)
        if not provider.is_configured():
            raise ValueError(f"Provider '{provider_label}' is not configured")
        return provider

    def _build_output_path(self, input_file: str, target_lang: str) -> str:
        override = (self.output_file_field.value or "").strip()
        if override:
            output_path = Path(override)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            return str(output_path)
        default_path = Path(self._build_default_output_path(input_file, target_lang))
        default_path.parent.mkdir(parents=True, exist_ok=True)
        return str(default_path)

    def _run_translation(self, job_id: int, provider_label: str, model_name: str, target_lang: str) -> None:
        started_at = time.perf_counter()
        report_payload = {
            "command": "translate",
            "input_file": self._selected_file,
            "output_file": None,
            "target_language": target_lang,
            "source_language": None if self.source_language_dropdown.value == "auto" else self.source_language_dropdown.value,
            "mode": self.mode_dropdown.value,
            "cache_scope": "global",
            "dry_run": False,
        }
        try:
            if not self._selected_file:
                raise ValueError("No file selected")

            limit_docs = self._parse_optional_int(self.limit_docs_field.value, "limit-docs")
            start_doc = self._parse_optional_int(self.start_doc_field.value, "start-doc")
            end_doc = self._parse_optional_int(self.end_doc_field.value, "end-doc")
            chunk_size = self._parse_optional_int(self.chunk_size_field.value, "chunk-size")
            chunk_context_window = self._parse_optional_int(self.chunk_context_field.value, "chunk-context-window")
            structured_max_chars = self._parse_optional_int(self.structured_max_chars_field.value, "structured-epub-batch-max-chars")

            if limit_docs is not None and limit_docs < 0:
                raise ValueError("--limit-docs must be >= 0")
            if start_doc is not None and start_doc < 1:
                raise ValueError("--start-doc must be >= 1")
            if end_doc is not None and end_doc < 1:
                raise ValueError("--end-doc must be >= 1")
            if start_doc is not None and end_doc is not None and start_doc > end_doc:
                raise ValueError("--start-doc cannot be greater than --end-doc")
            if chunk_size is None:
                chunk_size = 1200
            if chunk_size < 200:
                raise ValueError("--chunk-size must be >= 200")
            if chunk_context_window is None:
                chunk_context_window = 0
            if chunk_context_window < 0:
                raise ValueError("--chunk-context-window must be >= 0")
            structured_epub_batch = bool(self.structured_batch_switch.value)
            if structured_epub_batch and chunk_context_window > 0:
                raise ValueError("Cannot use structured EPUB batch with context window > 0")
            if structured_max_chars is None:
                structured_max_chars = 8000
            if structured_max_chars < 2000:
                raise ValueError("--structured-epub-batch-max-chars must be >= 2000")

            cache_settings = self._load_cache_settings()
            cache_scope = str(cache_settings["cache_scope"])
            cache_path_value = str(cache_settings["cache_path"])
            no_cache = bool(cache_settings["no_cache"])
            clear_cache = bool(cache_settings["clear_cache"])
            report_payload["cache_scope"] = cache_scope

            run_params = {
                "input_file": self._selected_file,
                "provider_label": provider_label,
                "model": model_name,
                "target_language": target_lang,
                "source_language": None if self.source_language_dropdown.value == "auto" else self.source_language_dropdown.value,
                "mode": self.mode_dropdown.value or "replace",
                "glossary_path": self._selected_glossary or "",
                "cache_scope": cache_scope,
                "cache_path": cache_path_value,
                "no_cache": no_cache,
                "clear_cache": clear_cache,
                "limit_docs": limit_docs,
                "start_doc": start_doc,
                "end_doc": end_doc,
                "chunk_size": chunk_size,
                "chunk_context_window": chunk_context_window,
                "structured_epub_batch": structured_epub_batch,
                "structured_epub_batch_max_chars": structured_max_chars,
                "report_path": (self.report_path_field.value or "").strip(),
            }
            self._logger.info("translation.run.parameters | %s", run_params)
            self._log_ui_action("Parameters logged to terminal")

            glossary = _load_glossary(self._selected_glossary or "")
            cache_path = _resolve_cache_path(
                input_file=self._selected_file,
                cache_scope=cache_scope,
                cache_path=cache_path_value,
                no_cache=no_cache,
            )
            if clear_cache:
                self.status_text.value = _clear_cache_file(cache_path)
                self.status_text.color = Colors.WARNING
                self._log_ui_action(self.status_text.value, logging.WARNING)
                self._page.update()
                try:
                    self._page.client_storage.set(UI_CLEAR_CACHE_KEY, False)
                except Exception:
                    pass

            provider = self._build_provider(provider_label, model_name)
            translator = Translator(provider=provider)
            selected_provider = canonical_provider_name(translator.provider.provider_name)
            output_file = self._build_output_path(self._selected_file, target_lang)
            report_payload.update(
                {
                    "provider": selected_provider,
                    "output_file": output_file,
                    "glossary_terms": len(glossary),
                    "cache_path": cache_path,
                    "structured_epub_batch": structured_epub_batch,
                    "structured_epub_batch_max_chars": structured_max_chars,
                }
            )

            self.status_text.value = "Translating file..."
            self.chapter_text.value = "Reading and translating content"
            self._log_ui_action("Translator started")
            self._page.update()

            result = translator.translate_file(
                input_file=self._selected_file,
                output_file=output_file,
                target_language=target_lang,
                source_language=None if self.source_language_dropdown.value == "auto" else self.source_language_dropdown.value,
                mode=self.mode_dropdown.value or "replace",
                glossary=glossary,
                cache_path=cache_path,
                limit_docs=limit_docs,
                start_doc=start_doc,
                end_doc=end_doc,
                chunk_size=chunk_size,
                chunk_context_window=chunk_context_window,
                structured_epub_batch=structured_epub_batch,
                structured_epub_batch_max_chars=structured_max_chars,
            )

            if self._active_job_id != job_id:
                return
            if self._cancel_requested:
                self.status_text.value = "Cancelled"
                self.status_text.color = Colors.WARNING
                self.chapter_text.value = "Current provider request may still complete in background."
                self._log_ui_action("Run cancelled", logging.WARNING)
                return

            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
            report_payload.update({"status": "success", "elapsed_ms": elapsed_ms, "token_usage": result.token_usage or {}})
            if result.bilingual_ast and result.bilingual_ast.metadata:
                report_payload["translation_summary"] = result.bilingual_ast.metadata
            report_path = (self.report_path_field.value or "").strip()
            if report_path:
                _write_run_report(report_path, report_payload)
                self._log_ui_action(f"Run report written: {report_path}")

            self.progress_bar.value = 1.0
            self.progress_text.value = "100%"
            self.status_text.value = "Translation completed"
            self.status_text.color = Colors.SUCCESS
            self.chapter_text.value = ""
            output_path = Path(output_file)
            self.output_name.value = output_path.name
            self.output_path.value = str(output_path.parent)
            self.output_section.visible = True
            self._log_ui_action(f"Completed: {output_path.name}")

        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
            report_payload.update({"status": "failed", "elapsed_ms": elapsed_ms, "error": str(exc)})
            report_path = (self.report_path_field.value or "").strip()
            if report_path:
                _write_run_report(report_path, report_payload)
            self.progress_bar.value = 0
            self.progress_text.value = "0%"
            self.status_text.value = f"Failed: {exc}"
            self.status_text.color = Colors.ERROR
            self.chapter_text.value = "Check provider credentials and selected options."
            self._logger.exception("translation.run.failed")
            self._log_ui_action(f"Failed: {exc}", logging.ERROR)
        finally:
            if self._active_job_id == job_id:
                self._is_translating = False
                self.translate_btn.disabled = False
                self.cancel_btn.visible = False
                self.cancel_btn.disabled = False
                self.provider_dropdown.disabled = False
                self.model_dropdown.disabled = False
                self.target_language_dropdown.disabled = False
                self.source_language_dropdown.disabled = False
                self.mode_dropdown.disabled = False
                self.output_file_field.disabled = False
                self.output_reset_btn.disabled = False
                self.select_btn.disabled = False
                self.report_path_field.disabled = False
                self._page.update()
