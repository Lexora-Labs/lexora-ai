"""Desktop window / browser chrome branding for the Flet UI.

Flet 0.21.x desktop clients ignored ``windowIcon`` entirely (no Flutter hook).
Lexora bundles Flet ≥ 0.23 so ``page.window.icon`` maps to native ``windowIcon``
and replaces the default Flet taskbar/title-bar icon when a ``.ico`` is present.

See upstream ``packages/flet/lib/src/controls/page.dart`` (``windowIcon`` / ``setWindowIcon``).
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, cast

import flet as ft

from lexora.runtime_paths import lexora_repo_root


def branding_root(*, anchor_file: Path | None = None) -> Path:
    return lexora_repo_root(anchor_file=anchor_file or Path(__file__))


def _paths(root: Path) -> tuple[Path, Path, Path]:
    branding = root / "assets" / "branding"
    ico = root / "lexora-ai-icon.ico"
    logo_light = branding / "lexora-ai-logo-light-v2.2.svg"
    logo_fallback = branding / "lexora-ai-logo.svg"
    return ico, logo_light, logo_fallback


def resolve_logo_path(root: Path, theme_mode: ft.ThemeMode) -> Path:
    del theme_mode
    _, light, fallback = _paths(root)
    return light if light.is_file() else fallback


def load_logo_data_uri(logo_path: Path) -> str | None:
    if not logo_path.is_file():
        return None
    encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _posix_path(path: Path) -> str:
    return path.resolve().as_posix()


def apply_desktop_branding(
    page: ft.Page,
    theme_mode: ft.ThemeMode,
    *,
    repo_root: Path | None = None,
    anchor_file: Path | None = None,
) -> None:
    root = repo_root or branding_root(anchor_file=anchor_file)
    ico, _, _ = _paths(root)
    logo_path = resolve_logo_path(root, theme_mode)
    logo_uri = load_logo_data_uri(logo_path)
    has_svg = bool(logo_uri) or logo_path.is_file()
    has_ico = ico.is_file()
    if not has_svg and not has_ico:
        return

    page_any = cast(Any, page)

    if has_ico:
        icon_str = _posix_path(ico)
        window = getattr(page_any, "window", None)
        if window is not None and hasattr(window, "icon"):
            window.icon = icon_str
        else:
            page._set_attr("windowIcon", icon_str)

    if hasattr(page_any, "favicon"):
        if has_svg:
            setattr(page_any, "favicon", logo_uri or logo_path.as_posix())
        elif has_ico:
            setattr(page_any, "favicon", _posix_path(ico))

    try:
        page.update()
    except Exception:
        pass
