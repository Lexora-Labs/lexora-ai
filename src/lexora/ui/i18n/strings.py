"""Locale packs per flet-ui-desktop-web-plan (fallback: selected -> en -> key)."""

from __future__ import annotations

from typing import Mapping

SUPPORTED_LOCALES = ("en", "vi")

_EN: dict[str, str] = {
    "nav.dashboard": "Dashboard",
    "nav.projects": "Projects",
    "nav.translate": "Translate",
    "nav.glossary": "Glossary",
    "nav.qa_review": "QA / Review",
    "nav.jobs_queue": "Jobs",
    "nav.settings": "Settings",
    "nav.about": "About",
    "nav.library": "Library",
    "app.workspace": "Workspace",
    "header.search_hint": "Search projects and jobs…",
    "common.new_project": "New project",
    "common.new_translation": "New translation",
    "common.save": "Save",
    "common.cancel": "Cancel",
    "common.retry": "Retry",
    "common.delete": "Delete",
    "common.search": "Search",
    "common.filter": "Filter",
    "common.export": "Export",
    "common.import": "Import",
    "page.dashboard.title": "Dashboard",
    "page.dashboard.subtitle": "Overview and quick start",
    "page.projects.title": "Projects",
    "page.projects.subtitle": "Workspaces and translated outputs",
    "page.library.title": "Library",
    "page.library.subtitle": "Translated outputs and source books",
    "page.translate.title": "Translate",
    "page.translate.subtitle": "Run AI translation on your files",
    "page.glossary.title": "Glossary",
    "page.glossary.subtitle": "Terminology and import/export",
    "page.qa_review.title": "QA / Review",
    "page.qa_review.subtitle": "Segment review and approvals",
    "page.jobs.title": "Jobs",
    "page.jobs.subtitle": "Queue, history, and status",
    "page.settings.title": "Settings",
    "page.settings.subtitle": "Appearance, language, and providers",
    "page.about.title": "About",
    "page.about.subtitle": "Version and links",
    "placeholder.soon": "This area is being wired to the translation engine.",
    "placeholder.glossary": "Import/export CSV, term highlighting, and conflicts will live here.",
    "placeholder.qa": "Side-by-side segments, comments, and approve/reject will live here.",
    "placeholder.projects_workspace": "Project folders, metadata, and batch runs will appear here.",
    "settings.ui_language": "App language",
    "about.version": "Lexora-AI desktop shell",
    "about.body": "Blueprint-styled UI for translation workflows. Use the rail to move between sections.",
    "dashboard.recent": "Recent activity",
    "dashboard.quick": "Quick actions",
    "dashboard.view_all": "View all",
    "dashboard.import_books": "Import books",
    "dashboard.view_library": "View library",
    "dashboard.view_jobs": "View jobs",
}

_VI: dict[str, str] = {
    "nav.dashboard": "Tổng quan",
    "nav.projects": "Dự án",
    "nav.translate": "Dịch",
    "nav.glossary": "Thuật ngữ",
    "nav.qa_review": "QA / Rà soát",
    "nav.jobs_queue": "Tác vụ",
    "nav.settings": "Cài đặt",
    "nav.about": "Giới thiệu",
    "nav.library": "Thư viện",
    "app.workspace": "Không gian làm việc",
    "header.search_hint": "Tìm dự án và tác vụ…",
    "common.new_project": "Dự án mới",
    "common.new_translation": "Dịch mới",
    "common.save": "Lưu",
    "common.cancel": "Hủy",
    "common.retry": "Thử lại",
    "common.delete": "Xóa",
    "common.search": "Tìm",
    "common.filter": "Lọc",
    "common.export": "Xuất",
    "common.import": "Nhập",
    "page.dashboard.title": "Tổng quan",
    "page.dashboard.subtitle": "Bắt đầu nhanh và hoạt động gần đây",
    "page.projects.title": "Dự án",
    "page.projects.subtitle": "Không gian làm việc và bản đầu ra đã dịch",
    "page.library.title": "Thư viện",
    "page.library.subtitle": "Bản đầu ra đã dịch và sách nguồn",
    "page.translate.title": "Dịch",
    "page.translate.subtitle": "Chạy dịch AI trên tệp của bạn",
    "page.glossary.title": "Thuật ngữ",
    "page.glossary.subtitle": "Thuật ngữ và nhập/xuất",
    "page.qa_review.title": "QA / Rà soát",
    "page.qa_review.subtitle": "Đoạn song song và phê duyệt",
    "page.jobs.title": "Tác vụ",
    "page.jobs.subtitle": "Hàng đợi, lịch sử và trạng thái",
    "page.settings.title": "Cài đặt",
    "page.settings.subtitle": "Giao diện, ngôn ngữ và nhà cung cấp",
    "page.about.title": "Giới thiệu",
    "page.about.subtitle": "Phiên bản và liên kết",
    "placeholder.soon": "Phần này đang được kết nối với engine dịch.",
    "placeholder.glossary": "Nhập/xuất CSV, làm nổi thuật ngữ và xử lý xung đột sẽ có tại đây.",
    "placeholder.qa": "Đoạn song song, ghi chú và duyệt/từ chối sẽ có tại đây.",
    "placeholder.projects_workspace": "Thư mục dự án, siêu dữ liệu và chạy hàng loạt sẽ xuất hiện tại đây.",
    "settings.ui_language": "Ngôn ngữ ứng dụng",
    "about.version": "Lexora-AI — giao diện desktop",
    "about.body": "Giao diện phong cách Blueprint cho quy trình dịch. Dùng thanh bên để chuyển mục.",
    "dashboard.recent": "Hoạt động gần đây",
    "dashboard.quick": "Thao tác nhanh",
    "dashboard.view_all": "Xem tất cả",
    "dashboard.import_books": "Nhập sách",
    "dashboard.view_library": "Xem thư viện",
    "dashboard.view_jobs": "Xem tác vụ",
}

_PACKS: dict[str, Mapping[str, str]] = {"en": _EN, "vi": _VI}


def merge_missing(locale: str, mapping: Mapping[str, str]) -> dict[str, str]:
    """Return a full map for *locale* with English fallback for missing keys."""
    base = dict(_EN)
    pack = _PACKS.get(locale, _EN)
    base.update(pack)
    base.update(mapping)
    return base


def translate(locale: str, key: str) -> str:
    """Resolve *key* for *locale* with en then key fallback."""
    pack = _PACKS.get(locale) or _EN
    if key in pack:
        return str(pack[key])
    if key in _EN:
        return str(_EN[key])
    return key
