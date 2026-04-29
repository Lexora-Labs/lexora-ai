"""
Lexora-AI Flet app shell — single bootstrap for run_ui and lexora.ui.main.

Implements MVP items from lexora-project/docs/40-planning/flet-ui-desktop-web-plan.md:
Blueprint theme, primary navigation, EN/VI strings, header quick actions.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Optional, cast

import flet as ft

from lexora.ui.i18n import translate
from lexora.ui.layout.main_layout import MainLayout
from lexora.ui import nav as nav_ids
from lexora.ui.theme import (
    Colors,
    apply_theme,
    cycle_theme_mode,
    theme_mode_icon,
)

THEME_STORAGE_KEY = "lexora_ui_theme_mode"
_THEME_FROM_STORAGE = {
    "dark": ft.ThemeMode.DARK,
    "light": ft.ThemeMode.LIGHT,
    "system": ft.ThemeMode.SYSTEM,
}
_THEME_TO_STORAGE = {
    ft.ThemeMode.DARK: "dark",
    ft.ThemeMode.LIGHT: "light",
    ft.ThemeMode.SYSTEM: "system",
}
README_HELP_URL = "https://github.com/Lexora-Labs/lexora-ai/blob/main/README.md"
from lexora.ui.screens.library import LibraryScreen
from lexora.ui.screens.translate import TranslateScreen
from lexora.ui.screens.jobs import JobsScreen
from lexora.ui.screens.settings import SettingsScreen
from lexora.ui.screens.about import AboutScreen
from lexora.ui.job_store import JobStore
from lexora.runtime_paths import lexora_data_file


def _resolve_jobs_db_path() -> str:
    configured = (os.getenv("LEXORA_UI_JOBS_DB") or "").strip()
    if configured:
        return configured
    return str(lexora_data_file("jobs.sqlite3"))


def attach_lexora_shell(
    page: ft.Page,
    *,
    set_app_icon: Optional[Callable[[ft.Page, ft.ThemeMode], None]] = None,
) -> None:
    """Configure *page* and add the main shell (navigation + views)."""
    page_any = cast(Any, page)

    current_theme: dict[str, ft.ThemeMode] = {"mode": ft.ThemeMode.SYSTEM}
    current_locale: dict[str, str] = {"lang": "en"}

    def _persist_locale(lang: str) -> None:
        try:
            page.client_storage.set("lexora_ui_locale", lang)
        except Exception:
            pass

    def _load_locale() -> None:
        try:
            stored = page.client_storage.get("lexora_ui_locale")
            if stored in ("en", "vi"):
                current_locale["lang"] = stored
        except Exception:
            pass

    _load_locale()

    def t(key: str) -> str:
        return translate(current_locale["lang"], key)

    page.title = "Lexora AI"
    if set_app_icon:
        set_app_icon(page, current_theme["mode"])

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

    apply_theme(page, current_theme["mode"])
    page.bgcolor = Colors.BACKGROUND

    layout_ref: dict[str, Optional[MainLayout]] = {"layout": None}
    translate_ref: dict[str, Optional[TranslateScreen]] = {"screen": None}
    job_store = JobStore(db_path=_resolve_jobs_db_path())

    def _on_app_language_changed(lang: str) -> None:
        if lang not in ("en", "vi"):
            return
        current_locale["lang"] = lang
        _persist_locale(lang)
        layout = layout_ref["layout"]
        if layout is None:
            return
        layout.relocalize_shell(t, _rebuild_views(), current_language=current_locale["lang"])

    def _cancel_job(job_id: str) -> bool:
        ts = translate_ref["screen"]
        return ts.cancel_job(job_id) if ts is not None else False

    def _retry_job(job_id: str) -> bool:
        ts = translate_ref["screen"]
        return ts.retry_job(job_id) if ts is not None else False

    def _delete_job(job_id: str) -> bool:
        ts = translate_ref["screen"]
        return ts.drop_queued_job(job_id) if ts is not None else False

    def _apply_theme_mode(mode: ft.ThemeMode) -> None:
        """Apply theme, persist choice, refresh chrome, and rebuild views (matches header toggle)."""
        current_theme["mode"] = mode
        apply_theme(page, mode)
        if set_app_icon:
            set_app_icon(page, mode)
        layout = layout_ref["layout"]
        if layout is not None:
            layout.refresh_theme(theme_icon=theme_mode_icon(mode))
            layout.replace_all_views(_rebuild_views())
        page.bgcolor = Colors.BACKGROUND
        try:
            page.client_storage.set(THEME_STORAGE_KEY, _THEME_TO_STORAGE.get(mode, "system"))
        except Exception:
            pass
        page.update()

    def _rebuild_views() -> dict[int, ft.Control]:
        library = LibraryScreen(page, get_text=t)
        ts = TranslateScreen(page, job_store=job_store, get_text=t)
        translate_ref["screen"] = ts
        views = {
            nav_ids.TRANSLATE: ts,
            nav_ids.JOBS: JobsScreen(
                page,
                job_store=job_store,
                on_cancel_job=_cancel_job,
                on_retry_job=_retry_job,
                on_delete_job=_delete_job,
                get_text=t,
            ),
            nav_ids.LIBRARY: library,
            nav_ids.SETTINGS: SettingsScreen(
                page,
                app_locale=current_locale["lang"],
                on_app_language=_on_app_language_changed,
                get_theme_mode=lambda: current_theme["mode"],
                on_theme_mode=_apply_theme_mode,
            ),
            nav_ids.ABOUT: AboutScreen(page, t),
        }
        return views

    def _toggle_theme(_: ft.ControlEvent) -> None:
        _apply_theme_mode(cycle_theme_mode(current_theme["mode"]))

    def _on_new_translation(_: ft.ControlEvent) -> None:
        if layout_ref["layout"] is not None:
            layout_ref["layout"].navigate_to(nav_ids.TRANSLATE)

    def _on_new_project(_: ft.ControlEvent) -> None:
        if layout_ref["layout"] is not None:
            layout_ref["layout"].navigate_to(nav_ids.LIBRARY)

    def _open_readme_help(_: ft.ControlEvent) -> None:
        try:
            page.launch_url(README_HELP_URL)
        except Exception:
            page.snack_bar = ft.SnackBar(content=ft.Text("Unable to open README help link."))
            page.snack_bar.open = True
            page.update()

    main_layout = MainLayout(
        page=page,
        views=_rebuild_views(),
        on_toggle_theme=_toggle_theme,
        on_open_help=_open_readme_help,
        on_change_language=_on_app_language_changed,
        current_language=current_locale["lang"],
        theme_icon=theme_mode_icon(current_theme["mode"]),
        get_text=t,
        on_new_translation=_on_new_translation,
        on_new_project=_on_new_project,
    )
    layout_ref["layout"] = main_layout

    page.add(main_layout)
