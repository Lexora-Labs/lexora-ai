#!/usr/bin/env python3
"""
Lexora AI Desktop UI Launcher (Flet 0.21.x)

Usage:
    python run_ui.py              # Opens browser automatically (default)
    python run_ui.py --no-browser # Desktop app only, no browser
    python run_ui.py -nb          # Same as --no-browser
"""

import sys
import os
import socket
import base64
import asyncio
from pathlib import Path
import threading
from typing import Optional
import argparse
from typing import Any, cast

import flet as ft
from dotenv import load_dotenv

# Allow importing the shared theme module from src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lexora.ui.theme import (
    Colors,
    apply_theme as _apply_theme,
    cycle_theme_mode as _cycle_theme,
    theme_mode_icon as _theme_icon,
)
from lexora.ui.layout.main_layout import MainLayout
from lexora.translator import Translator
from lexora.providers import create_provider


REPO_ROOT = Path(__file__).resolve().parent
BRANDING_DIR = REPO_ROOT / "assets" / "branding"
BRANDING_APP_ICON_ICO = BRANDING_DIR / "lexora-ai-icon.ico"
BRANDING_APP_ICON_ASSET_PATH = "branding/lexora-ai-icon.ico"
BRANDING_LOGO_DARK_SVG = BRANDING_DIR / "lexora-ai-logo-dark-v2.2.svg"
BRANDING_LOGO_LIGHT_SVG = BRANDING_DIR / "lexora-ai-logo-light-v2.2.svg"
BRANDING_LOGO_FALLBACK_SVG = BRANDING_DIR / "lexora-ai-logo.svg"

load_dotenv(REPO_ROOT / ".env")


def _resolve_logo_path(theme_mode: ft.ThemeMode, page: ft.Page | None = None) -> Path:
    """Resolve logo path based on current theme mode."""
    if theme_mode == ft.ThemeMode.LIGHT:
        preferred = BRANDING_LOGO_LIGHT_SVG
    elif theme_mode == ft.ThemeMode.SYSTEM and page is not None and hasattr(page, "platform_brightness"):
        preferred = BRANDING_LOGO_LIGHT_SVG if page.platform_brightness == ft.Brightness.LIGHT else BRANDING_LOGO_DARK_SVG
    else:
        preferred = BRANDING_LOGO_DARK_SVG

    if preferred.exists():
        return preferred
    return BRANDING_LOGO_FALLBACK_SVG


def _load_logo_data_uri(theme_mode: ft.ThemeMode, page: ft.Page | None = None) -> str | None:
    """Return branding SVG as data URI for reliable browser rendering."""
    logo_path = _resolve_logo_path(theme_mode, page)
    if not logo_path.exists():
        return None
    svg_bytes = logo_path.read_bytes()
    encoded = base64.b64encode(svg_bytes).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _set_app_icon(page: ft.Page, theme_mode: ft.ThemeMode) -> None:
    """Set app/window icon and favicon from the branding ICO when available."""
    page_any = cast(Any, page)
    logo_path = _resolve_logo_path(theme_mode, page)
    logo_data_uri = _load_logo_data_uri(theme_mode, page)
    has_svg = bool(logo_data_uri) or logo_path.exists()
    has_ico = BRANDING_APP_ICON_ICO.exists()
    if not has_svg and not has_ico:
        return

    icon_path = str((BRANDING_APP_ICON_ICO if has_ico else logo_path).resolve())
    window_obj = getattr(page_any, "window", None)
    if window_obj is not None and hasattr(window_obj, "icon"):
        setattr(window_obj, "icon", icon_path)
    elif hasattr(page_any, "window_icon"):
        setattr(page_any, "window_icon", icon_path)

    if hasattr(page_any, "favicon"):
        if has_ico:
            setattr(page_any, "favicon", BRANDING_APP_ICON_ASSET_PATH)
        elif has_svg:
            setattr(page_any, "favicon", logo_data_uri or logo_path.as_posix())


# ============ Provider Config ============
PROVIDERS = {
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
]

UI_PROVIDER_TO_CANONICAL = {
    "OpenAI": "openai",
    "Azure OpenAI": "azure-openai",
    "Gemini": "gemini",
    "Anthropic": "anthropic",
    "Qwen": "qwen",
}


# ============ Screen Builders ============
def create_dashboard_view(page: ft.Page, navigate_to) -> ft.Control:
    """Dashboard with stats, recent activity, quick actions."""
    
    def stat_card(title, value, icon, color):
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, size=32, color=color),
                    bgcolor=f"{color}20",
                    padding=12,
                    border_radius=8,
                ),
                ft.Container(width=12),
                ft.Column([
                    ft.Text(value, size=28, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                    ft.Text(title, size=12, color=Colors.TEXT_SECONDARY),
                ], spacing=2),
            ]),
            padding=20,
            bgcolor=Colors.SURFACE,
            border_radius=10,
            expand=True,
        )
    
    stats_row = ft.Row([
        stat_card("Books Translated", "12", ft.icons.MENU_BOOK, Colors.PRIMARY),
        stat_card("In Progress", "3", ft.icons.PENDING, Colors.WARNING),
        stat_card("Total Pages", "1,248", ft.icons.DESCRIPTION, Colors.SUCCESS),
        stat_card("This Month", "5", ft.icons.CALENDAR_TODAY, "#8B5CF6"),
    ], spacing=16, wrap=True)
    
    def activity_item(title, subtitle, status):
        icon = ft.icons.CHECK_CIRCLE if status == "done" else ft.icons.PENDING if status == "progress" else ft.icons.SCHEDULE
        color = Colors.SUCCESS if status == "done" else Colors.WARNING if status == "progress" else Colors.TEXT_SECONDARY
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=color, size=24),
                ft.Container(width=12),
                ft.Column([
                    ft.Text(title, size=14, weight=ft.FontWeight.W_500, color=Colors.TEXT_PRIMARY),
                    ft.Text(subtitle, size=12, color=Colors.TEXT_SECONDARY),
                ], spacing=2, expand=True),
            ]),
            padding=ft.padding.symmetric(vertical=8),
        )
    
    recent_section = ft.Container(
        content=ft.Column([
            ft.Text("📋 Recent Activity", size=18, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
            ft.Container(height=12),
            activity_item("Clean Code.epub", "Translated to Vietnamese • 2 hours ago", "done"),
            activity_item("Design Patterns.epub", "Translated to Vietnamese • 1 day ago", "done"),
            activity_item("Refactoring.epub", "In progress • 45% complete", "progress"),
            activity_item("The Pragmatic Programmer.epub", "Queued • Waiting", "queued"),
        ]),
        padding=20,
        bgcolor=Colors.SURFACE,
        border_radius=10,
    )
    
    quick_section = ft.Container(
        content=ft.Column([
            ft.Text("⚡ Quick Actions", size=18, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
            ft.Container(height=12),
            ft.Row([
                ft.ElevatedButton("New Translation", icon=ft.icons.ADD, bgcolor=Colors.PRIMARY, color=Colors.TEXT_PRIMARY, on_click=lambda _: navigate_to(1)),
                ft.OutlinedButton("View Library", icon=ft.icons.LIBRARY_BOOKS, on_click=lambda _: navigate_to(2)),
                ft.OutlinedButton("View Jobs", icon=ft.icons.WORK_HISTORY, on_click=lambda _: navigate_to(3)),
            ], spacing=12, wrap=True),
        ]),
        padding=20,
        bgcolor=Colors.SURFACE,
        border_radius=10,
    )
    
    return ft.Column([
        stats_row,
        ft.Container(height=20),
        recent_section,
        ft.Container(height=20),
        quick_section,
    ], scroll=ft.ScrollMode.AUTO, expand=True)


def create_translate_view(page: ft.Page) -> ft.Control:
    """Translate screen with file picker and progress."""
    
    selected_file: dict[str, Optional[str]] = {"path": None, "name": None}
    output_dir_state: dict[str, Optional[str]] = {"path": os.getenv("LEXORA_UI_OUTPUT_DIR")}
    is_translating = {"value": False}
    active_job_id = {"value": 0}
    cancel_requested = {"value": False}
    
    file_display = ft.Text("No file selected", size=14, color=Colors.TEXT_SECONDARY)
    
    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            f = e.files[0]
            selected_file["path"] = f.path
            selected_file["name"] = f.name
            file_display.value = f"📚 {f.name}"
            file_display.color = Colors.TEXT_PRIMARY
            translate_btn.disabled = False
            page.update()
    
    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)
    
    file_section = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.icons.UPLOAD_FILE, color=Colors.TEXT_SECONDARY),
                ft.Text("File Selection", size=16, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
            ], spacing=8),
            ft.Container(height=16),
            ft.Row([
                ft.ElevatedButton("Select EPUB File", icon=ft.icons.FOLDER_OPEN, bgcolor=Colors.PRIMARY, color=Colors.TEXT_PRIMARY,
                    on_click=lambda _: file_picker.pick_files(allowed_extensions=["epub"])),
                ft.Container(width=16),
                file_display,
            ]),
        ]),
        padding=24,
        bgcolor=Colors.SURFACE,
        border_radius=10,
    )
    
    model_dropdown = ft.Dropdown(
        label="Model",
        options=[ft.dropdown.Option(m) for m in PROVIDERS["OpenAI"]],
        value="gpt-4o",
        width=200,
        bgcolor=Colors.BACKGROUND,
        border_radius=8,
    )
    
    def on_provider_change(e):
        provider = e.control.value
        models = PROVIDERS.get(provider, [])
        model_dropdown.options = [ft.dropdown.Option(m) for m in models]
        model_dropdown.value = models[0] if models else None
        page.update()
    
    provider_dropdown = ft.Dropdown(
        label="AI Provider",
        options=[ft.dropdown.Option(p) for p in PROVIDERS.keys()],
        value="OpenAI",
        width=200,
        bgcolor=Colors.BACKGROUND,
        border_radius=8,
        on_change=on_provider_change,
    )
    
    language_dropdown = ft.Dropdown(
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
            ft.Row([provider_dropdown, model_dropdown, language_dropdown], spacing=16, wrap=True),
        ]),
        padding=24,
        bgcolor=Colors.SURFACE,
        border_radius=10,
    )

    output_dir_text = ft.Text(
        "Default: same folder as input file",
        size=12,
        color=Colors.TEXT_SECONDARY,
    )

    def on_output_dir_picked(e: ft.FilePickerResultEvent):
        if e.path:
            output_dir_state["path"] = e.path
            output_dir_text.value = f"Output folder: {e.path}"
            output_dir_text.color = Colors.TEXT_PRIMARY
            page.update()

    output_dir_picker = ft.FilePicker(on_result=on_output_dir_picked)
    page.overlay.append(output_dir_picker)

    if output_dir_state["path"]:
        output_dir_text.value = f"Output folder: {output_dir_state['path']}"
        output_dir_text.color = Colors.TEXT_PRIMARY

    output_path_section = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.icons.FOLDER, color=Colors.TEXT_SECONDARY),
                ft.Text("Output Location", size=16, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
            ], spacing=8),
            ft.Container(height=16),
            ft.Row([
                ft.OutlinedButton(
                    "Choose Output Folder",
                    icon=ft.icons.CREATE_NEW_FOLDER,
                    on_click=lambda _: output_dir_picker.get_directory_path(dialog_title="Select Output Folder"),
                ),
                ft.OutlinedButton(
                    "Use Input Folder",
                    icon=ft.icons.RESTORE,
                    on_click=lambda _: _clear_output_dir(),
                ),
            ], spacing=12, wrap=True),
            ft.Container(height=8),
            output_dir_text,
        ]),
        padding=24,
        bgcolor=Colors.SURFACE,
        border_radius=10,
    )

    progress_bar = ft.ProgressBar(value=0, bgcolor=Colors.BACKGROUND, color=Colors.PRIMARY, bar_height=8)
    progress_text = ft.Text("0%", size=16, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)
    status_text = ft.Text("Ready to translate", size=14, color=Colors.TEXT_SECONDARY)
    chapter_text = ft.Text("", size=12, color=Colors.TEXT_SECONDARY, italic=True)
    output_text = ft.Text("", size=14, color=Colors.TEXT_PRIMARY)
    
    progress_section = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.icons.DOWNLOADING, color=Colors.TEXT_SECONDARY),
                ft.Text("Progress", size=16, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
            ], spacing=8),
            ft.Container(height=16),
            ft.Row([ft.Container(content=progress_bar, expand=True), ft.Container(width=16), progress_text]),
            ft.Container(height=8),
            status_text,
            chapter_text,
        ]),
        padding=24,
        bgcolor=Colors.SURFACE,
        border_radius=10,
        visible=False,
    )
    
    output_section = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.icons.CHECK_CIRCLE, color=Colors.SUCCESS),
                ft.Text("Output", size=16, weight=ft.FontWeight.W_600, color=Colors.SUCCESS),
            ], spacing=8),
            ft.Container(height=16),
            output_text,
        ]),
        padding=24,
        bgcolor=Colors.SURFACE,
        border_radius=10,
        visible=False,
    )

    def _clear_output_dir() -> None:
        output_dir_state["path"] = None
        output_dir_text.value = "Default: same folder as input file"
        output_dir_text.color = Colors.TEXT_SECONDARY
        page.update()

    def _pick_output_extension(input_path: Path) -> str:
        # Keep markdown output as markdown; other formats default to plain text output.
        return ".md" if input_path.suffix.lower() == ".md" else ".txt"

    def _build_output_path(input_path: str, target_lang: str) -> str:
        source = Path(input_path)
        output_dir = Path(output_dir_state["path"]) if output_dir_state["path"] else source.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        ext = _pick_output_extension(source)
        return str(output_dir / f"{source.stem}_{target_lang}{ext}")

    def _build_provider(provider_label: str, model_name: str):
        canonical_name = UI_PROVIDER_TO_CANONICAL.get(provider_label)
        if not canonical_name:
            raise ValueError(f"Unsupported provider: {provider_label}")

        provider_kwargs: dict[str, object] = {"debug": False}
        if canonical_name == "azure-openai":
            provider_kwargs["deployment"] = model_name
        else:
            provider_kwargs["model"] = model_name

        provider = create_provider(canonical_name, **provider_kwargs)
        if not provider.is_configured():
            raise ValueError(f"Provider '{provider_label}' is not configured. Update API keys in .env/settings.")
        return provider
    
    def on_translate(e):
        if not selected_file["path"] or is_translating["value"]:
            return

        input_path = selected_file["path"]
        provider_label = provider_dropdown.value
        model_name = model_dropdown.value
        target_lang = language_dropdown.value

        if not input_path:
            status_text.value = "Please select an input file."
            status_text.color = Colors.ERROR
            page.update()
            return

        if not provider_label or not model_name or not target_lang:
            status_text.value = "Please select provider, model, and target language."
            status_text.color = Colors.ERROR
            page.update()
            return

        output_path = _build_output_path(input_path, target_lang)

        active_job_id["value"] += 1
        current_job_id = active_job_id["value"]
        
        is_translating["value"] = True
        cancel_requested["value"] = False
        translate_btn.disabled = True
        cancel_btn.visible = True
        cancel_btn.disabled = False
        progress_section.visible = True
        output_section.visible = False
        progress_bar.value = None
        progress_text.value = "..."
        status_text.value = "Starting translation..."
        status_text.color = Colors.TEXT_SECONDARY
        chapter_text.value = f"{provider_label} • {model_name} • {target_lang}"
        page.update()

        def run_translation(job_id: int):
            try:
                if cancel_requested["value"]:
                    return

                provider = _build_provider(provider_label, model_name)
                translator = Translator(provider=provider)

                status_text.value = "Translating file..."
                page.update()

                translator.translate_file(
                    input_file=input_path,
                    output_file=output_path,
                    target_language=target_lang,
                )

                if active_job_id["value"] != job_id:
                    return

                if cancel_requested["value"]:
                    status_text.value = "Cancelled"
                    status_text.color = Colors.WARNING
                    chapter_text.value = "Current provider request may still complete in background."
                    return

                progress_bar.value = 1.0
                progress_text.value = "100%"
                status_text.value = "Completed"
                status_text.color = Colors.SUCCESS
                chapter_text.value = ""
                output_text.value = f"Saved translated output: {output_path}"
                output_section.visible = True
            except Exception as exc:
                progress_bar.value = 0
                progress_text.value = "0%"
                status_text.value = f"Failed: {exc}"
                status_text.color = Colors.ERROR
                chapter_text.value = "Check provider credentials and selected model/deployment."
            finally:
                if active_job_id["value"] == job_id:
                    is_translating["value"] = False
                    translate_btn.disabled = False
                    cancel_btn.visible = False
                    cancel_btn.disabled = False
                    page.update()

        threading.Thread(target=run_translation, args=(current_job_id,), daemon=True).start()
    
    def on_cancel(e):
        if not is_translating["value"]:
            return

        cancel_requested["value"] = True
        cancel_btn.disabled = True
        status_text.value = "Cancel requested..."
        status_text.color = Colors.WARNING
        chapter_text.value = "Waiting for current provider request to return."
        page.update()
    
    translate_btn = ft.ElevatedButton("🚀 Start Translation", bgcolor=Colors.PRIMARY, color=Colors.TEXT_PRIMARY, height=50, width=220, disabled=True, on_click=on_translate)
    cancel_btn = ft.OutlinedButton("Cancel", height=50, visible=False, on_click=on_cancel)
    
    return ft.Column([
        file_section,
        ft.Container(height=16),
        settings_section,
        ft.Container(height=16),
        output_path_section,
        ft.Container(height=24),
        ft.Row([translate_btn, cancel_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=16),
        ft.Container(height=16),
        progress_section,
        ft.Container(height=16),
        output_section,
    ], scroll=ft.ScrollMode.AUTO, expand=True)


def create_library_view(page: ft.Page) -> ft.Control:
    """Library screen with book grid."""
    
    books = [
        {"title": "Clean Code", "author": "Robert C. Martin", "lang": "vi", "date": "2024-04-05"},
        {"title": "Design Patterns", "author": "Gang of Four", "lang": "vi", "date": "2024-04-04"},
        {"title": "The Pragmatic Programmer", "author": "David Thomas", "lang": "vi", "date": "2024-04-03"},
        {"title": "Refactoring", "author": "Martin Fowler", "lang": "vi", "date": "2024-04-02"},
    ]
    
    def book_card(book):
        lang_flag = {"vi": "🇻🇳", "ja": "🇯🇵", "zh": "🇨🇳", "en": "🇺🇸"}.get(book["lang"], "🌐")
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.MENU_BOOK, size=48, color=Colors.PRIMARY),
                        ft.Text(lang_flag, size=24),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                    bgcolor=Colors.BACKGROUND,
                    border_radius=8,
                    height=120,
                    expand=True,
                ),
                ft.Container(height=12),
                ft.Text(book["title"], size=14, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY, max_lines=1),
                ft.Text(book["author"], size=12, color=Colors.TEXT_SECONDARY, max_lines=1),
                ft.Container(height=8),
                ft.Text(book["date"], size=11, color=Colors.TEXT_SECONDARY),
            ]),
            padding=16,
            bgcolor=Colors.SURFACE,
            border_radius=10,
            width=200,
        )
    
    search_field = ft.TextField(hint_text="Search books...", prefix_icon=ft.icons.SEARCH, width=300, height=45, bgcolor=Colors.BACKGROUND, border_radius=8)
    
    header = ft.Row([
        ft.Row([ft.Icon(ft.icons.LIBRARY_BOOKS, color=Colors.TEXT_SECONDARY), ft.Text(f"{len(books)} Books", size=16, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY)], spacing=8),
        ft.Container(expand=True),
        search_field,
    ])
    
    grid = ft.Row([book_card(b) for b in books], spacing=16, wrap=True)
    
    return ft.Column([
        header,
        ft.Container(height=20),
        grid,
    ], scroll=ft.ScrollMode.AUTO, expand=True)


def create_jobs_view(page: ft.Page) -> ft.Control:
    """Jobs screen with queue."""
    
    jobs = [
        {"title": "Refactoring.epub", "provider": "OpenAI", "status": "progress", "progress": 0.45},
        {"title": "Clean Architecture.epub", "provider": "OpenAI", "status": "queued", "progress": 0},
        {"title": "Clean Code.epub", "provider": "OpenAI", "status": "done", "progress": 1.0},
        {"title": "Design Patterns.epub", "provider": "Gemini", "status": "done", "progress": 1.0},
        {"title": "Microservices.epub", "provider": "Azure", "status": "failed", "progress": 0.32},
    ]
    
    def job_card(job):
        status_config = {
            "queued": (ft.icons.SCHEDULE, Colors.TEXT_SECONDARY, "Queued"),
            "progress": (ft.icons.PENDING, Colors.WARNING, "In Progress"),
            "done": (ft.icons.CHECK_CIRCLE, Colors.SUCCESS, "Completed"),
            "failed": (ft.icons.ERROR, Colors.ERROR, "Failed"),
        }
        icon, color, status_text = status_config.get(job["status"], (ft.icons.HELP, Colors.TEXT_SECONDARY, "Unknown"))
        
        progress_row = ft.Container(visible=False)
        if job["status"] == "progress":
            progress_row = ft.Container(
                content=ft.Row([
                    ft.ProgressBar(value=job["progress"], bgcolor=Colors.BACKGROUND, color=Colors.PRIMARY, bar_height=6, expand=True),
                    ft.Container(width=8),
                    ft.Text(f"{int(job['progress'] * 100)}%", size=12, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                ]),
                padding=ft.padding.only(top=12),
                visible=True,
            )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, color=color, size=24),
                    ft.Container(width=12),
                    ft.Column([
                        ft.Text(job["title"], size=15, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                        ft.Text(job["provider"], size=12, color=Colors.TEXT_SECONDARY),
                    ], spacing=2, expand=True),
                    ft.Text(status_text, size=12, weight=ft.FontWeight.W_500, color=color),
                ]),
                progress_row,
            ]),
            padding=16,
            bgcolor=Colors.SURFACE,
            border_radius=10,
        )
    
    stats = ft.Row([
        ft.Container(content=ft.Row([ft.Container(width=8, height=8, bgcolor=Colors.TEXT_SECONDARY, border_radius=4), ft.Text(f"Queued: 1", size=13, color=Colors.TEXT_PRIMARY)], spacing=8), padding=ft.padding.symmetric(horizontal=12, vertical=6), bgcolor=Colors.SURFACE, border_radius=16),
        ft.Container(content=ft.Row([ft.Container(width=8, height=8, bgcolor=Colors.WARNING, border_radius=4), ft.Text(f"In Progress: 1", size=13, color=Colors.TEXT_PRIMARY)], spacing=8), padding=ft.padding.symmetric(horizontal=12, vertical=6), bgcolor=Colors.SURFACE, border_radius=16),
        ft.Container(content=ft.Row([ft.Container(width=8, height=8, bgcolor=Colors.SUCCESS, border_radius=4), ft.Text(f"Completed: 2", size=13, color=Colors.TEXT_PRIMARY)], spacing=8), padding=ft.padding.symmetric(horizontal=12, vertical=6), bgcolor=Colors.SURFACE, border_radius=16),
        ft.Container(content=ft.Row([ft.Container(width=8, height=8, bgcolor=Colors.ERROR, border_radius=4), ft.Text(f"Failed: 1", size=13, color=Colors.TEXT_PRIMARY)], spacing=8), padding=ft.padding.symmetric(horizontal=12, vertical=6), bgcolor=Colors.SURFACE, border_radius=16),
    ], spacing=12)
    
    job_list = ft.Column([job_card(j) for j in jobs], spacing=8)
    
    return ft.Column([
        ft.Text("Translation Jobs", size=20, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
        ft.Container(height=16),
        stats,
        ft.Container(height=20),
        job_list,
    ], scroll=ft.ScrollMode.AUTO, expand=True)


def create_settings_view(page: ft.Page) -> ft.Control:
    """Settings screen."""
    
    providers_config = [
        ("OpenAI", "OPENAI_API_KEY", False),
        ("Azure OpenAI", "AZURE_OPENAI_KEY", False),
        ("Gemini", "GOOGLE_API_KEY", True),
        ("Anthropic", "ANTHROPIC_API_KEY", False),
        ("Qwen", "DASHSCOPE_API_KEY", False),
    ]
    
    def provider_card(name, env_var, configured):
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.CHECK_CIRCLE if configured else ft.icons.ERROR_OUTLINE, color=Colors.SUCCESS if configured else Colors.TEXT_SECONDARY, size=24),
                ft.Container(width=12),
                ft.Column([
                    ft.Text(name, size=15, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                    ft.Text("Configured" if configured else "Not configured", size=12, color=Colors.SUCCESS if configured else Colors.TEXT_SECONDARY),
                ], spacing=2, width=140),
                ft.TextField(label=env_var, hint_text="Enter API key...", password=True, can_reveal_password=True, width=300, height=45, bgcolor=Colors.BACKGROUND, border_radius=8),
                ft.IconButton(icon=ft.icons.SAVE, icon_color=Colors.PRIMARY, tooltip="Save"),
            ], spacing=12),
            padding=16,
            bgcolor=Colors.BACKGROUND,
            border_radius=8,
        )
    
    providers_section = ft.Container(
        content=ft.Column([
            ft.Row([ft.Icon(ft.icons.KEY, color=Colors.TEXT_SECONDARY), ft.Text("API Providers", size=18, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY)], spacing=8),
            ft.Container(height=8),
            ft.Text("Configure your AI provider API keys.", size=13, color=Colors.TEXT_SECONDARY),
            ft.Container(height=16),
            ft.Column([provider_card(n, e, c) for n, e, c in providers_config], spacing=12),
        ]),
        padding=24,
        bgcolor=Colors.SURFACE,
        border_radius=10,
    )
    
    defaults_section = ft.Container(
        content=ft.Column([
            ft.Row([ft.Icon(ft.icons.TUNE, color=Colors.TEXT_SECONDARY), ft.Text("Default Settings", size=18, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY)], spacing=8),
            ft.Container(height=16),
            ft.Row([
                ft.Dropdown(label="Default Provider", options=[ft.dropdown.Option(p) for p in PROVIDERS.keys()], value="OpenAI", width=200, bgcolor=Colors.BACKGROUND, border_radius=8),
                ft.Dropdown(label="Default Language", options=[ft.dropdown.Option(key=c, text=n) for c, n in LANGUAGES], value="vi", width=200, bgcolor=Colors.BACKGROUND, border_radius=8),
            ], spacing=16),
        ]),
        padding=24,
        bgcolor=Colors.SURFACE,
        border_radius=10,
    )
    
    save_section = ft.Row([
        ft.ElevatedButton("Save Settings", icon=ft.icons.SAVE, bgcolor=Colors.PRIMARY, color=Colors.TEXT_PRIMARY, height=45),
        ft.OutlinedButton("Reset to Defaults", icon=ft.icons.RESTORE, height=45),
    ], spacing=16)
    
    return ft.Column([
        providers_section,
        ft.Container(height=20),
        defaults_section,
        ft.Container(height=24),
        save_section,
    ], scroll=ft.ScrollMode.AUTO, expand=True)


# ============ Main Layout ============
def main(page: ft.Page):
    """Main UI entry point using shared MainLayout + Sidebar components."""
    page_any = cast(Any, page)

    current_theme = {"mode": ft.ThemeMode.SYSTEM}

    page.title = "Lexora AI"
    _set_app_icon(page, current_theme["mode"])
    window_obj = getattr(page_any, "window", None)
    if window_obj is not None:
        setattr(window_obj, "width", 1100)
        setattr(window_obj, "height", 750)
        setattr(window_obj, "min_width", 800)
        setattr(window_obj, "min_height", 600)
    else:
        setattr(page_any, "window_width", 1100)
        setattr(page_any, "window_height", 750)
        setattr(page_any, "window_min_width", 800)
        setattr(page_any, "window_min_height", 600)
    page.padding = 0

    _apply_theme(page, current_theme["mode"])
    page.bgcolor = Colors.BACKGROUND

    layout_ref: dict[str, Optional[MainLayout]] = {"layout": None}

    view_builders = {
        0: lambda: create_translate_view(page),
        1: lambda: create_library_view(page),
        2: lambda: create_jobs_view(page),
        3: lambda: create_settings_view(page),
    }

    def _build_views() -> dict[int, ft.Control]:
        return {idx: build() for idx, build in view_builders.items()}

    def _toggle_theme(e: ft.ControlEvent) -> None:
        next_mode = _cycle_theme(current_theme["mode"])
        current_theme["mode"] = next_mode
        _apply_theme(page, next_mode)
        _set_app_icon(page, next_mode)

        layout = layout_ref["layout"]
        if layout is not None:
            layout.refresh_theme(theme_icon=_theme_icon(next_mode))
            for idx, build in view_builders.items():
                layout.set_view(idx, build())

        page.bgcolor = Colors.BACKGROUND
        page.update()

    main_layout = MainLayout(
        page=page,
        views=_build_views(),
        on_toggle_theme=_toggle_theme,
        theme_icon=_theme_icon(current_theme["mode"]),
    )
    layout_ref["layout"] = main_layout

    page.add(main_layout)


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Lexora AI Desktop UI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_ui.py     # Open in browser automatically (default)
  python run_ui.py -nb # Skip browser, run server only on localhost
        """,
    )
    parser.add_argument(
        "--no-browser", "-nb",
        action="store_true",
        help="Skip auto-opening browser (server runs on localhost only)",
    )
    args = parser.parse_args()

    if sys.platform.startswith("win") and not args.no_browser:
        # Avoid Proactor transport shutdown races on Windows (WinError 10054).
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    def _is_port_available(port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False

    def _pick_port(default: int = 8550) -> int:
        env_port = os.getenv("LEXORA_UI_PORT")
        if env_port:
            try:
                requested = int(env_port)
                if _is_port_available(requested):
                    return requested
            except ValueError:
                pass

        # Use OS-assigned ephemeral port to avoid stale/default-port collisions.
        return 0

    port = _pick_port()
    
    # Determine view mode
    # Default: WEB_BROWSER (auto-opens browser)
    # With --no-browser: FLET_APP_HIDDEN (runs without opening browser window)
    view_mode = ft.AppView.FLET_APP_HIDDEN if args.no_browser else ft.AppView.WEB_BROWSER
    
    print(f"Starting Lexora UI on port {port if port else 'auto'}")
    print(f"View mode: {'No browser auto-open (hidden app)' if args.no_browser else 'Web Browser (auto-open)'}")
    
    ft.app(target=main, view=view_mode, port=port, assets_dir=str(REPO_ROOT / "assets"))
