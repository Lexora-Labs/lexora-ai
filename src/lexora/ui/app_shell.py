"""
Lexora-AI Flet app shell — single bootstrap for run_ui and lexora.ui.main.

Implements MVP items from lexora-project/docs/40-planning/flet-ui-desktop-web-plan.md:
Blueprint theme, primary navigation, EN/VI strings, header quick actions.
"""

from __future__ import annotations

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
from lexora.ui.screens.projects import ProjectsScreen
from lexora.ui.screens.translate import TranslateScreen
from lexora.ui.screens.jobs import JobsScreen
from lexora.ui.screens.settings import SettingsScreen
from lexora.ui.screens.about import AboutScreen


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
    projects_ref: dict[str, Optional[ProjectsScreen]] = {"screen": None}

    def _open_workspace_tab() -> None:
        layout = layout_ref["layout"]
        ps = projects_ref["screen"]
        if layout is not None:
            layout.navigate_to(nav_ids.PROJECTS)
        if ps is not None:
            ps.select_workspace_tab()
        page.update()

    def _on_app_language_changed(lang: str) -> None:
        if lang not in ("en", "vi"):
            return
        current_locale["lang"] = lang
        _persist_locale(lang)
        layout = layout_ref["layout"]
        if layout is None:
            return
        ps = projects_ref["screen"]
        if ps is not None:
            ps.relocalize(t)
        layout.relocalize_shell(t, _rebuild_views())

    def _rebuild_views() -> dict[int, ft.Control]:
        ps = ProjectsScreen(page, t)
        projects_ref["screen"] = ps
        views = {
            nav_ids.PROJECTS: ps,
            nav_ids.TRANSLATE: TranslateScreen(page),
            nav_ids.JOBS: JobsScreen(page),
            nav_ids.SETTINGS: SettingsScreen(
                page,
                app_locale=current_locale["lang"],
                on_app_language=_on_app_language_changed,
            ),
            nav_ids.ABOUT: AboutScreen(page, t),
        }
        return views

    def _toggle_theme(_: ft.ControlEvent) -> None:
        next_mode = cycle_theme_mode(current_theme["mode"])
        current_theme["mode"] = next_mode
        apply_theme(page, next_mode)
        if set_app_icon:
            set_app_icon(page, next_mode)

        layout = layout_ref["layout"]
        if layout is not None:
            layout.refresh_theme(theme_icon=theme_mode_icon(next_mode))
            layout.replace_all_views(_rebuild_views())

        page.bgcolor = Colors.BACKGROUND
        page.update()

    def _on_new_translation(_: ft.ControlEvent) -> None:
        if layout_ref["layout"] is not None:
            layout_ref["layout"].navigate_to(nav_ids.TRANSLATE)

    def _on_new_project(_: ft.ControlEvent) -> None:
        _open_workspace_tab()

    main_layout = MainLayout(
        page=page,
        views=_rebuild_views(),
        on_toggle_theme=_toggle_theme,
        theme_icon=theme_mode_icon(current_theme["mode"]),
        get_text=t,
        on_new_translation=_on_new_translation,
        on_new_project=_on_new_project,
    )
    layout_ref["layout"] = main_layout

    page.add(main_layout)
