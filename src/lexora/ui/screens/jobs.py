"""
Jobs Screen

View and manage translation jobs:
- Job queue
- Job history
- Status tracking
"""

import flet as ft
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

from lexora.ui.theme import Colors


class JobStatus(Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    """Job data model."""
    id: str
    book_title: str
    provider: str
    model: str
    target_lang: str
    status: JobStatus
    progress: float
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


# Mock data
MOCK_JOBS: List[Job] = [
    Job("1", "Refactoring.epub", "OpenAI", "gpt-4o", "vi", JobStatus.IN_PROGRESS, 0.45, "2024-04-06 10:30"),
    Job("2", "Clean Architecture.epub", "OpenAI", "gpt-4o", "vi", JobStatus.QUEUED, 0.0, "2024-04-06 10:25"),
    Job("3", "Test-Driven Development.epub", "Gemini", "gemini-2.0-flash", "ja", JobStatus.QUEUED, 0.0, "2024-04-06 10:20"),
    Job("4", "Clean Code.epub", "OpenAI", "gpt-4o", "vi", JobStatus.COMPLETED, 1.0, "2024-04-05 14:00", "2024-04-05 15:30"),
    Job("5", "Design Patterns.epub", "OpenAI", "gpt-4", "vi", JobStatus.COMPLETED, 1.0, "2024-04-04 09:00", "2024-04-04 11:00"),
    Job("6", "Microservices.epub", "Azure OpenAI", "gpt-4", "zh", JobStatus.FAILED, 0.32, "2024-04-03 16:00", error="API rate limit exceeded"),
]


class JobsScreen(ft.Container):
    """Jobs screen with queue and history."""

    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self._jobs = MOCK_JOBS.copy()
        self._filter = "all"
        self._build()

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
            ],
            on_change=self._on_tab_change,
        )
        
        # Stats Row
        stats_row = ft.Row([
            self._stat_chip("Queued", self._count_by_status(JobStatus.QUEUED), Colors.TEXT_SECONDARY),
            self._stat_chip("In Progress", self._count_by_status(JobStatus.IN_PROGRESS), Colors.WARNING),
            self._stat_chip("Completed", self._count_by_status(JobStatus.COMPLETED), Colors.SUCCESS),
            self._stat_chip("Failed", self._count_by_status(JobStatus.FAILED), Colors.ERROR),
        ], spacing=12)
        
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
        
        # Layout
        self.content = ft.Column([
            self.tabs,
            ft.Container(height=16),
            stats_row,
            ft.Stack([
                self.jobs_list,
                self.empty_state,
            ], expand=True),
        ], expand=True)
        
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

    def _count_by_status(self, status: JobStatus) -> int:
        """Count jobs by status."""
        return len([j for j in self._jobs if j.status == status])

    def _create_job_card(self, job: Job) -> ft.Container:
        """Create a job card."""
        status_config = {
            JobStatus.QUEUED: (ft.icons.SCHEDULE, Colors.TEXT_SECONDARY, "Queued"),
            JobStatus.IN_PROGRESS: (ft.icons.PENDING, Colors.WARNING, "In Progress"),
            JobStatus.COMPLETED: (ft.icons.CHECK_CIRCLE, Colors.SUCCESS, "Completed"),
            JobStatus.FAILED: (ft.icons.ERROR, Colors.ERROR, "Failed"),
            JobStatus.CANCELLED: (ft.icons.CANCEL, Colors.TEXT_SECONDARY, "Cancelled"),
        }
        
        icon, color, status_text = status_config.get(job.status, (ft.icons.HELP, Colors.TEXT_SECONDARY, "Unknown"))

        menu_items: List[ft.PopupMenuItem] = [
            ft.PopupMenuItem(text="View details", icon=ft.icons.INFO),
        ]
        if job.status in (JobStatus.QUEUED, JobStatus.IN_PROGRESS):
            menu_items.append(ft.PopupMenuItem(text="Cancel", icon=ft.icons.CANCEL))
        if job.status == JobStatus.FAILED:
            menu_items.append(ft.PopupMenuItem(text="Retry", icon=ft.icons.REFRESH))
        menu_items.append(ft.PopupMenuItem(text="Delete", icon=ft.icons.DELETE))

        # Progress bar (only for in-progress jobs)
        progress_row = ft.Container(visible=False)
        if job.status == JobStatus.IN_PROGRESS:
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
        if job.status == JobStatus.FAILED and job.error:
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
                        ft.Text(job.book_title, size=15, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                        ft.Text(f"{job.provider} • {job.model} • {job.target_lang.upper()}", size=12, color=Colors.TEXT_SECONDARY),
                    ], spacing=2, expand=True),
                    ft.Column([
                        ft.Text(status_text, size=12, weight=ft.FontWeight.W_500, color=color),
                        ft.Text(job.created_at, size=11, color=Colors.TEXT_SECONDARY),
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
            filtered_jobs = [j for j in self._jobs if j.status == JobStatus.IN_PROGRESS]
        elif self._filter == "completed":
            filtered_jobs = [j for j in self._jobs if j.status == JobStatus.COMPLETED]
        elif self._filter == "failed":
            filtered_jobs = [j for j in self._jobs if j.status == JobStatus.FAILED]
        
        for job in filtered_jobs:
            self.jobs_list.controls.append(self._create_job_card(job))
        
        # Show/hide empty state
        self.empty_state.visible = len(filtered_jobs) == 0
        self.jobs_list.visible = len(filtered_jobs) > 0

    def _on_tab_change(self, e):
        """Handle tab change."""
        filters = ["all", "in_progress", "completed", "failed"]
        self._filter = filters[e.control.selected_index]
        self._update_list()
        self.page.update()
