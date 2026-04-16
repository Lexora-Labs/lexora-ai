"""Jobs screen showing live Translate job lifecycle."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import flet as ft

from lexora.logging_framework import get_ui_log_events
from lexora.ui.desktop_open import open_file, reveal_in_file_manager
from lexora.ui.job_store import JobStore, TranslationJob
from lexora.ui.theme import Colors


def _format_duration_ms(ms: Optional[int]) -> str:
    if ms is None:
        return "—"
    if ms < 1000:
        return f"{ms} ms"
    sec = ms / 1000.0
    if sec < 60:
        return f"{sec:.1f} s"
    minutes, sec_rem = divmod(int(sec), 60)
    if minutes < 60:
        return f"{minutes}m {sec_rem}s"
    hours, minutes_rem = divmod(minutes, 60)
    return f"{hours}h {minutes_rem}m"


def _job_card_title(job: TranslationJob) -> str:
    """Primary card title: original → output basename (``book_title`` stays the original name)."""
    if job.output_path:
        return f"{job.book_title} → {Path(job.output_path).name}"
    return job.book_title


def _format_doc_summary(job: TranslationJob) -> str:
    if job.total_docs is None:
        return "Docs: —"
    if job.docs_translated is not None:
        return f"Docs: {job.docs_translated}/{job.total_docs}"
    return f"Docs: {job.total_docs}"


class JobsScreen(ft.Container):
    """Jobs screen with queue and history."""

    def __init__(
        self,
        page: ft.Page,
        job_store: JobStore,
        *,
        on_cancel_job: Optional[Callable[[str], bool]] = None,
        on_retry_job: Optional[Callable[[str], bool]] = None,
        on_delete_job: Optional[Callable[[str], bool]] = None,
    ):
        super().__init__()
        self.page = page
        self._job_store = job_store
        self._on_cancel_job = on_cancel_job
        self._on_retry_job = on_retry_job
        self._on_delete_job = on_delete_job
        self._jobs = self._job_store.snapshot()
        self._filter = "all"
        self._run_log_tab_index = 4
        self._run_log_visible = False
        self._log_poller_started = False
        self._unsubscribe = self._job_store.subscribe(self._on_jobs_updated)
        self._build()
        self._start_log_poller()

    def _build(self):
        """Build the jobs UI."""
        
        # Filter Tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="All Jobs", icon=ft.icons.LIST),
                ft.Tab(text="In Progress", icon=ft.icons.PENDING),
                ft.Tab(text="Completed", icon=ft.icons.CHECK_CIRCLE),
                ft.Tab(text="Failed", icon=ft.icons.ERROR),
                ft.Tab(text="Run log", icon=ft.icons.ARTICLE),
            ],
            on_change=self._on_tab_change,
        )

        # Stats Row
        self.stats_row = ft.Row(
            [
                self._stat_chip("Queued", self._count_by_status("queued"), Colors.TEXT_SECONDARY),
                self._stat_chip("In Progress", self._count_by_status("in_progress"), Colors.WARNING),
                self._stat_chip("Completed", self._count_by_status("completed"), Colors.SUCCESS),
                self._stat_chip("Failed", self._count_by_status("failed"), Colors.ERROR),
            ],
            spacing=12,
        )
        
        # Jobs List
        self.jobs_list = ft.ListView(
            expand=True,
            spacing=8,
            padding=ft.padding.only(top=16),
        )
        
        # Empty State
        self.empty_state = ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.WORK_HISTORY_OUTLINED, size=64, color=Colors.TEXT_SECONDARY),
                ft.Container(height=16),
                ft.Text("No jobs found", size=18, weight=ft.FontWeight.W_500, color=Colors.TEXT_PRIMARY),
                ft.Text("Start a translation to see jobs here", size=14, color=Colors.TEXT_SECONDARY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
            expand=True,
            visible=False,
        )
        self._update_list()

        self.run_log_hint = ft.Text("", size=13, color=Colors.TEXT_SECONDARY)
        self.run_log_list = ft.ListView(
            expand=True,
            spacing=4,
            auto_scroll=True,
            padding=ft.padding.only(top=8),
        )
        self._run_log_panel = ft.Container(
            padding=ft.padding.only(top=8),
            visible=False,
            expand=True,
            content=ft.Column(
                [
                    ft.Text("Run log", size=16, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                    self.run_log_hint,
                    ft.Container(
                        expand=True,
                        border=ft.border.all(1, Colors.TEXT_SECONDARY),
                        border_radius=8,
                        padding=8,
                        content=self.run_log_list,
                    ),
                ],
                expand=True,
                spacing=8,
            ),
        )

        self._jobs_panel = ft.Column(
            [
                ft.Container(height=16),
                self.stats_row,
                ft.Stack(
                    [
                        self.jobs_list,
                        self.empty_state,
                    ],
                    expand=True,
                ),
            ],
            expand=True,
        )

        self._body = ft.Column([self.tabs, self._jobs_panel, self._run_log_panel], expand=True)

        self.content = self._body
        self.expand = True

    def _stat_chip(self, label: str, count: int, color: str) -> ft.Container:
        """Create a stat chip."""
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    width=8,
                    height=8,
                    bgcolor=color,
                    border_radius=4,
                ),
                ft.Text(f"{label}: {count}", size=13, color=Colors.TEXT_PRIMARY),
            ], spacing=8),
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            bgcolor=Colors.SURFACE,
            border_radius=16,
        )

    def _count_by_status(self, status: str) -> int:
        """Count jobs by status."""
        return len([j for j in self._jobs if j.status == status])

    def _create_job_card(self, job: TranslationJob) -> ft.Container:
        """Create a job card."""
        status_config = {
            "queued": (ft.icons.SCHEDULE, Colors.TEXT_SECONDARY, "Queued"),
            "in_progress": (ft.icons.PENDING, Colors.WARNING, "In Progress"),
            "completed": (ft.icons.CHECK_CIRCLE, Colors.SUCCESS, "Completed"),
            "failed": (ft.icons.ERROR, Colors.ERROR, "Failed"),
            "cancelled": (ft.icons.CANCEL, Colors.TEXT_SECONDARY, "Cancelled"),
        }
        
        icon, color, status_text = status_config.get(job.status, (ft.icons.HELP, Colors.TEXT_SECONDARY, "Unknown"))

        menu_items: List[ft.PopupMenuItem] = [
            ft.PopupMenuItem(
                text="View details",
                icon=ft.icons.INFO,
                on_click=lambda e, j=job: self._show_job_details(j),
            ),
        ]
        if job.log_cursor_start is not None:
            menu_items.append(
                ft.PopupMenuItem(
                    text="View run log",
                    icon=ft.icons.ARTICLE_OUTLINED,
                    on_click=lambda e, j=job: self._show_job_log_dialog(j),
                )
            )
        if job.status == "completed" and job.output_path:
            outp = job.output_path
            menu_items.append(
                ft.PopupMenuItem(
                    text="Open translated file",
                    icon=ft.icons.OPEN_IN_NEW,
                    on_click=lambda _e, p=outp: self._menu_open_translated(p),
                )
            )
            menu_items.append(
                ft.PopupMenuItem(
                    text="Open file location",
                    icon=ft.icons.FOLDER_OPEN,
                    on_click=lambda _e, p=outp: self._menu_open_location(p),
                )
            )
        if job.status in ("queued", "in_progress"):
            menu_items.append(ft.PopupMenuItem(text="Cancel", icon=ft.icons.CANCEL, on_click=lambda _: self._cancel_job(job.id)))
        if job.status == "failed":
            menu_items.append(
                ft.PopupMenuItem(text="Re-run", icon=ft.icons.REFRESH, on_click=lambda _: self._retry_job(job.id))
            )
        menu_items.append(ft.PopupMenuItem(text="Delete", icon=ft.icons.DELETE, on_click=lambda _: self._delete_job(job.id)))

        # Progress bar (only for in-progress jobs)
        progress_row = ft.Container(visible=False)
        if job.status == "in_progress":
            progress_row = ft.Container(
                content=ft.Row([
                    ft.ProgressBar(value=job.progress, bgcolor=Colors.BACKGROUND, color=Colors.PRIMARY, bar_height=6, expand=True),
                    ft.Container(width=8),
                    ft.Text(f"{int(job.progress * 100)}%", size=12, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                ]),
                padding=ft.padding.only(top=12),
                visible=True,
            )
        
        # Error message (only for failed jobs)
        error_row = ft.Container(visible=False)
        if job.status == "failed" and job.error:
            error_row = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.WARNING, color=Colors.ERROR, size=16),
                    ft.Text(job.error, size=12, color=Colors.ERROR),
                ], spacing=8),
                padding=ft.padding.only(top=8),
                visible=True,
            )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, color=color, size=24),
                    ft.Container(width=12),
                    ft.Column([
                        ft.Text(_job_card_title(job), size=15, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                        ft.Text(f"{job.provider} • {job.model} • {job.target_lang.upper()}", size=12, color=Colors.TEXT_SECONDARY),
                        ft.Text(
                            f"Run ID: {job.run_id}  •  {_format_doc_summary(job)}  •  {_format_duration_ms(job.duration_ms)}",
                            size=11,
                            color=Colors.TEXT_SECONDARY,
                        ),
                    ], spacing=2, expand=True),
                    ft.Column([
                        ft.Text(status_text, size=12, weight=ft.FontWeight.W_500, color=color),
                    ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2),
                    ft.Container(width=8),
                    ft.PopupMenuButton(
                        icon=ft.icons.MORE_VERT,
                        items=menu_items,
                    ),
                ]),
                progress_row,
                error_row,
            ]),
            padding=16,
            bgcolor=Colors.SURFACE,
            border_radius=10,
        )

    def _update_list(self):
        """Update the jobs list."""
        self.jobs_list.controls.clear()
        
        filtered_jobs = self._jobs
        if self._filter == "in_progress":
            filtered_jobs = [j for j in self._jobs if j.status == "in_progress"]
        elif self._filter == "completed":
            filtered_jobs = [j for j in self._jobs if j.status == "completed"]
        elif self._filter == "failed":
            filtered_jobs = [j for j in self._jobs if j.status == "failed"]
        
        for job in filtered_jobs:
            self.jobs_list.controls.append(self._create_job_card(job))
        
        # Show/hide empty state
        self.empty_state.visible = len(filtered_jobs) == 0
        self.jobs_list.visible = len(filtered_jobs) > 0

    def _on_tab_change(self, e):
        """Handle tab change."""
        idx = e.control.selected_index
        if idx == self._run_log_tab_index:
            self._run_log_visible = True
            self._jobs_panel.visible = False
            self._run_log_panel.visible = True
            self._refresh_run_log_content()
        else:
            self._run_log_visible = False
            self._jobs_panel.visible = True
            self._run_log_panel.visible = False
            filters = ["all", "in_progress", "completed", "failed"]
            self._filter = filters[idx]
            self._update_list()
        self.page.update()

    def _on_jobs_updated(self) -> None:
        self._jobs = self._job_store.snapshot()
        self._update_list()
        if self._run_log_visible:
            self._refresh_run_log_content()
        try:
            self.page.update()
        except Exception:
            pass

    def _start_log_poller(self) -> None:
        if self._log_poller_started:
            return
        self._log_poller_started = True
        self.page.run_task(self._poll_run_log)

    async def _poll_run_log(self) -> None:
        while True:
            if self._run_log_visible:
                self._refresh_run_log_content()
                try:
                    self.run_log_list.update()
                except Exception:
                    try:
                        self.page.update()
                    except Exception:
                        pass
            await asyncio.sleep(0.8)

    def _active_in_progress_job(self) -> Optional[TranslationJob]:
        for j in self._jobs:
            if j.status == "in_progress":
                return j
        return None

    def _slice_log_events(self, job: TranslationJob) -> List[Dict[str, Any]]:
        events = get_ui_log_events()
        start = job.log_cursor_start or 0
        start = max(0, min(start, len(events)))
        if job.status != "in_progress" and job.log_cursor_end is not None:
            end = max(start, min(int(job.log_cursor_end), len(events)))
        else:
            end = len(events)
        return list(events[start:end])

    def _refresh_run_log_content(self) -> None:
        job = self._active_in_progress_job()
        if not job:
            self.run_log_hint.value = "No translation is running. Start a job from Translate, then watch the log here."
            self.run_log_list.controls.clear()
            return
        self.run_log_hint.value = f"Live log for: {job.book_title}  ({job.run_id})"
        events = self._slice_log_events(job)
        self.run_log_list.controls.clear()
        for event in events[-500:]:
            level_name = str(event.get("level") or "INFO")
            timestamp = str(event.get("timestamp") or time.strftime("%H:%M:%S"))
            message = str(event.get("message") or "")
            color = (
                Colors.ERROR
                if level_name in {"ERROR", "CRITICAL"}
                else Colors.WARNING
                if level_name == "WARNING"
                else Colors.TEXT_SECONDARY
            )
            self.run_log_list.controls.append(
                ft.Text(f"[{timestamp}] {level_name}: {message}", size=12, color=color)
            )

    def _show_job_log_dialog(self, job: TranslationJob) -> None:
        events = self._slice_log_events(job)
        if not events:
            self._show_message("No log lines were captured for this job.")
            return
        lines = []
        for event in events[-800:]:
            level_name = str(event.get("level") or "INFO")
            timestamp = str(event.get("timestamp") or "")
            message = str(event.get("message") or "")
            lines.append(f"[{timestamp}] {level_name}: {message}")
        body = ft.Column(
            [ft.Text(line, size=12, selectable=True) for line in lines],
            scroll=ft.ScrollMode.AUTO,
            tight=True,
        )
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Run log — {job.book_title}", weight=ft.FontWeight.W_600),
            content=ft.Container(width=560, height=440, padding=ft.padding.only(top=8), content=body),
            actions=[ft.TextButton("Close", on_click=self._close_dialog)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def _menu_open_translated(self, path: str) -> None:
        ok, msg = open_file(path)
        self._show_message(msg if ok else msg)

    def _menu_open_location(self, path: str) -> None:
        ok, msg = reveal_in_file_manager(path)
        self._show_message(msg if ok else msg)

    def _cancel_job(self, job_id: str) -> None:
        success = self._on_cancel_job(job_id) if self._on_cancel_job else False
        if not success:
            # Fallback for queued jobs if no callback is wired.
            self._job_store.set_status(job_id, status="cancelled", progress=0.0)
            self._show_message("Job cancelled.")
        else:
            self._show_message("Cancel requested.")

    def _retry_job(self, job_id: str) -> None:
        success = self._on_retry_job(job_id) if self._on_retry_job else False
        if success:
            self._show_message("Re-run queued.")
            return
        self._show_message("Re-run is not available for this job.")

    def _delete_job(self, job_id: str) -> None:
        if self._on_delete_job:
            self._on_delete_job(job_id)
        ok, message = self._job_store.delete_job(job_id)
        self._show_message(message if ok else f"Delete blocked: {message}")

    def _show_message(self, message: str) -> None:
        self.page.snack_bar = ft.SnackBar(content=ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()

    def _close_dialog(self, _: Optional[ft.ControlEvent] = None) -> None:
        if self.page.dialog:
            self.page.dialog.open = False
        self.page.update()

    def _show_job_details(self, job: TranslationJob) -> None:
        lines = [
            f"Run ID: {job.run_id}",
            f"Job name: {job.book_title}",
            f"Output: {job.output_path or '—'}",
            f"Status: {job.status}",
            f"Created: {job.created_at}",
            f"Started: {job.started_at or '—'}",
            f"Ended: {job.completed_at or '—'}",
            f"Duration: {_format_duration_ms(job.duration_ms)}",
            f"{_format_doc_summary(job)}",
            "",
            "Parameters:",
        ]
        for key in sorted(job.parameters.keys()):
            lines.append(f"  {key}: {job.parameters[key]}")

        scroll_col = ft.Column(
            [ft.Text(line, size=12, selectable=True) for line in lines],
            scroll=ft.ScrollMode.AUTO,
            tight=True,
        )
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Job details", weight=ft.FontWeight.W_600),
            content=ft.Container(width=520, height=420, padding=ft.padding.only(top=8), content=scroll_col),
            actions=[ft.TextButton("Close", on_click=self._close_dialog)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
