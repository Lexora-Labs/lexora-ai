#!/usr/bin/env python3
"""
Lexora AI Desktop UI Launcher (Flet 0.21.x)
"""

import sys
from pathlib import Path
import threading
import time

import flet as ft


# ============ Colors ============
class Colors:
    BACKGROUND = "#0F172A"
    SURFACE = "#1E293B"
    PRIMARY = "#06B6D4"
    TEXT_PRIMARY = "#F8FAFC"
    TEXT_SECONDARY = "#94A3B8"
    ERROR = "#F43F5E"
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"


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
    
    selected_file = {"path": None, "name": None}
    is_translating = {"value": False}
    
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
    
    progress_bar = ft.ProgressBar(value=0, bgcolor=Colors.BACKGROUND, color=Colors.PRIMARY, bar_height=8)
    progress_text = ft.Text("0%", size=16, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)
    status_text = ft.Text("Ready to translate", size=14, color=Colors.TEXT_SECONDARY)
    chapter_text = ft.Text("", size=12, color=Colors.TEXT_SECONDARY, italic=True)
    
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
            ft.Text("", size=14, color=Colors.TEXT_PRIMARY),
        ]),
        padding=24,
        bgcolor=Colors.SURFACE,
        border_radius=10,
        visible=False,
    )
    
    def on_translate(e):
        if not selected_file["path"] or is_translating["value"]:
            return
        
        is_translating["value"] = True
        translate_btn.disabled = True
        cancel_btn.visible = True
        progress_section.visible = True
        output_section.visible = False
        page.update()
        
        def run_mock():
            chapters = ["Chapter 1", "Chapter 2", "Chapter 3", "Chapter 4", "Chapter 5"]
            for i, ch in enumerate(chapters):
                if not is_translating["value"]:
                    return
                progress = (i + 1) / len(chapters)
                progress_bar.value = progress
                progress_text.value = f"{int(progress * 100)}%"
                status_text.value = "Translating..."
                chapter_text.value = ch
                page.update()
                time.sleep(1.0)
            
            if is_translating["value"]:
                is_translating["value"] = False
                status_text.value = "✅ Completed!"
                status_text.color = Colors.SUCCESS
                translate_btn.disabled = False
                cancel_btn.visible = False
                output_section.visible = True
                page.update()
        
        threading.Thread(target=run_mock, daemon=True).start()
    
    def on_cancel(e):
        is_translating["value"] = False
        translate_btn.disabled = False
        cancel_btn.visible = False
        status_text.value = "❌ Cancelled"
        status_text.color = Colors.ERROR
        page.update()
    
    translate_btn = ft.ElevatedButton("🚀 Start Translation", bgcolor=Colors.PRIMARY, color=Colors.TEXT_PRIMARY, height=50, width=220, disabled=True, on_click=on_translate)
    cancel_btn = ft.OutlinedButton("Cancel", height=50, visible=False, on_click=on_cancel)
    
    return ft.Column([
        file_section,
        ft.Container(height=16),
        settings_section,
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
    """Main UI entry point with sidebar layout."""
    
    # Page config
    page.title = "Lexora AI"
    page.window_width = 1100
    page.window_height = 750
    page.bgcolor = Colors.BACKGROUND
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    
    # Current view state
    current_index = {"value": 1}  # Start on Translate page
    
    # Views container
    content_area = ft.Container(expand=True, padding=24)
    
    # Page configs
    PAGE_CONFIG = {
        0: {"title": "Dashboard", "subtitle": "Overview of your translations"},
        1: {"title": "Translate", "subtitle": "Translate eBooks with AI"},
        2: {"title": "Library", "subtitle": "Your translated books"},
        3: {"title": "Jobs", "subtitle": "Translation queue and history"},
        4: {"title": "Settings", "subtitle": "Application preferences"},
    }
    
    # Header
    header_title = ft.Text("Translate", size=24, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)
    header_subtitle = ft.Text("Translate eBooks with AI", size=14, color=Colors.TEXT_SECONDARY)
    
    header = ft.Container(
        content=ft.Row([
            ft.Column([header_title, header_subtitle], spacing=2),
            ft.Container(expand=True),
            ft.IconButton(icon=ft.icons.NOTIFICATIONS_OUTLINED, icon_color=Colors.TEXT_SECONDARY),
            ft.IconButton(icon=ft.icons.ACCOUNT_CIRCLE_OUTLINED, icon_color=Colors.TEXT_SECONDARY),
        ]),
        padding=ft.padding.symmetric(horizontal=24, vertical=16),
        bgcolor=Colors.BACKGROUND,
        border=ft.border.only(bottom=ft.BorderSide(1, Colors.SURFACE)),
    )
    
    # Views cache
    views_cache = {}
    
    def navigate_to(index: int):
        """Navigate to a screen by index."""
        nav_rail.selected_index = index
        on_nav_change_internal(index)
    
    def on_nav_change_internal(index: int):
        """Internal navigation handler."""
        current_index["value"] = index
        config = PAGE_CONFIG.get(index, PAGE_CONFIG[0])
        header_title.value = config["title"]
        header_subtitle.value = config["subtitle"]
        content_area.content = get_view(index)
        page.update()
    
    def get_view(index: int) -> ft.Control:
        if index not in views_cache:
            if index == 0:
                views_cache[index] = create_dashboard_view(page, navigate_to)
            elif index == 1:
                views_cache[index] = create_translate_view(page)
            elif index == 2:
                views_cache[index] = create_library_view(page)
            elif index == 3:
                views_cache[index] = create_jobs_view(page)
            elif index == 4:
                views_cache[index] = create_settings_view(page)
            else:
                views_cache[index] = ft.Text("Page not found", color=Colors.TEXT_PRIMARY)
        return views_cache[index]
    
    def on_nav_change(e):
        index = e.control.selected_index
        on_nav_change_internal(index)
    
    # Sidebar state
    sidebar_expanded = {"value": True}
    
    def toggle_sidebar(e):
        sidebar_expanded["value"] = not sidebar_expanded["value"]
        nav_rail.extended = sidebar_expanded["value"]
        toggle_btn.icon = ft.icons.MENU_OPEN if sidebar_expanded["value"] else ft.icons.MENU
        logo_text.visible = sidebar_expanded["value"]
        page.update()
    
    # Navigation Rail
    nav_rail = ft.NavigationRail(
        selected_index=current_index["value"],
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=80,
        min_extended_width=200,
        extended=True,
        bgcolor=Colors.SURFACE,
        indicator_color=Colors.PRIMARY,
        on_change=on_nav_change,
        destinations=[
            ft.NavigationRailDestination(icon=ft.icons.DASHBOARD_OUTLINED, selected_icon=ft.icons.DASHBOARD, label="Dashboard"),
            ft.NavigationRailDestination(icon=ft.icons.TRANSLATE_OUTLINED, selected_icon=ft.icons.TRANSLATE, label="Translate"),
            ft.NavigationRailDestination(icon=ft.icons.LIBRARY_BOOKS_OUTLINED, selected_icon=ft.icons.LIBRARY_BOOKS, label="Library"),
            ft.NavigationRailDestination(icon=ft.icons.WORK_HISTORY_OUTLINED, selected_icon=ft.icons.WORK_HISTORY, label="Jobs"),
            ft.NavigationRailDestination(icon=ft.icons.SETTINGS_OUTLINED, selected_icon=ft.icons.SETTINGS, label="Settings"),
        ],
    )
    
    # Logo
    logo_text = ft.Text("Lexora", size=20, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)
    logo = ft.Container(
        content=ft.Row([
            ft.Icon(ft.icons.AUTO_STORIES, color=Colors.PRIMARY, size=28),
            logo_text,
        ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
        padding=ft.padding.symmetric(vertical=16),
    )
    
    # Toggle button
    toggle_btn = ft.IconButton(
        icon=ft.icons.MENU_OPEN,
        icon_color=Colors.TEXT_SECONDARY,
        tooltip="Toggle sidebar",
        on_click=toggle_sidebar,
    )
    
    # Sidebar
    sidebar = ft.Container(
        content=ft.Column([
            logo,
            ft.Divider(height=1, color=Colors.BACKGROUND),
            ft.Container(content=nav_rail, expand=True),
            ft.Divider(height=1, color=Colors.BACKGROUND),
            ft.Container(content=toggle_btn, alignment=ft.alignment.center, padding=8),
        ], spacing=0, expand=True),
        bgcolor=Colors.SURFACE,
    )
    
    # Initial content
    content_area.content = get_view(current_index["value"])
    
    # Right panel
    right_panel = ft.Column([
        header,
        content_area,
    ], spacing=0, expand=True)
    
    # Main layout
    page.add(
        ft.Row([
            sidebar,
            ft.VerticalDivider(width=1, color=Colors.SURFACE),
            ft.Container(content=right_panel, expand=True, bgcolor=Colors.BACKGROUND),
        ], spacing=0, expand=True)
    )


if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER, port=8550)
