"""
Library Screen

View and manage translated books:
- List all translated books
- Search and filter
- Open/delete books
"""

import flet as ft
from typing import Optional, List, Dict
from dataclasses import dataclass
from datetime import datetime


class Colors:
    BACKGROUND = "#0F172A"
    SURFACE = "#1E293B"
    PRIMARY = "#06B6D4"
    TEXT_PRIMARY = "#F8FAFC"
    TEXT_SECONDARY = "#94A3B8"
    ERROR = "#F43F5E"
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"


@dataclass
class Book:
    """Book data model."""
    id: str
    title: str
    author: str
    source_lang: str
    target_lang: str
    pages: int
    translated_at: str
    file_path: str
    status: str = "completed"


# Mock data
MOCK_BOOKS: List[Book] = [
    Book("1", "Clean Code", "Robert C. Martin", "en", "vi", 464, "2024-04-05", "/books/clean_code_vi.epub"),
    Book("2", "Design Patterns", "Gang of Four", "en", "vi", 395, "2024-04-04", "/books/design_patterns_vi.epub"),
    Book("3", "The Pragmatic Programmer", "David Thomas", "en", "vi", 352, "2024-04-03", "/books/pragmatic_vi.epub"),
    Book("4", "Refactoring", "Martin Fowler", "en", "vi", 448, "2024-04-02", "/books/refactoring_vi.epub"),
    Book("5", "Domain-Driven Design", "Eric Evans", "en", "ja", 560, "2024-04-01", "/books/ddd_ja.epub"),
]


class LibraryScreen(ft.Container):
    """Library screen with book list and management."""

    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self._books = MOCK_BOOKS.copy()
        self._filtered_books = self._books.copy()
        self._search_query = ""
        self._filter_lang = "all"
        self._build()

    def _build(self):
        """Build the library UI."""
        
        # Search Bar
        self.search_field = ft.TextField(
            hint_text="Search books...",
            prefix_icon=ft.icons.SEARCH,
            width=300,
            height=45,
            bgcolor=Colors.BACKGROUND,
            border_radius=8,
            on_change=self._on_search,
        )
        
        # Filter Dropdown
        self.filter_dropdown = ft.Dropdown(
            label="Language",
            options=[
                ft.dropdown.Option("all", "All Languages"),
                ft.dropdown.Option("vi", "Vietnamese"),
                ft.dropdown.Option("ja", "Japanese"),
                ft.dropdown.Option("zh", "Chinese"),
                ft.dropdown.Option("en", "English"),
            ],
            value="all",
            width=180,
            bgcolor=Colors.BACKGROUND,
            border_radius=8,
            on_change=self._on_filter,
        )
        
        # Header Row
        header_row = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.icons.LIBRARY_BOOKS, color=Colors.TEXT_SECONDARY),
                    ft.Text(f"{len(self._books)} Books", size=16, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                ], spacing=8),
                ft.Container(expand=True),
                self.search_field,
                ft.Container(width=16),
                self.filter_dropdown,
            ]),
            padding=ft.padding.only(bottom=16),
        )
        
        # Books Grid
        self.books_grid = ft.GridView(
            expand=True,
            runs_count=3,
            max_extent=320,
            child_aspect_ratio=0.85,
            spacing=16,
            run_spacing=16,
        )
        
        self._update_grid()
        
        # Empty State
        self.empty_state = ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.LIBRARY_BOOKS_OUTLINED, size=64, color=Colors.TEXT_SECONDARY),
                ft.Container(height=16),
                ft.Text("No books found", size=18, weight=ft.FontWeight.W_500, color=Colors.TEXT_PRIMARY),
                ft.Text("Try adjusting your search or filters", size=14, color=Colors.TEXT_SECONDARY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
            expand=True,
            visible=False,
        )
        
        # Layout
        self.content = ft.Column([
            header_row,
            ft.Stack([
                self.books_grid,
                self.empty_state,
            ], expand=True),
        ], expand=True)
        
        self.expand = True

    def _create_book_card(self, book: Book) -> ft.Container:
        """Create a book card."""
        lang_flag = {
            "vi": "🇻🇳",
            "ja": "🇯🇵",
            "zh": "🇨🇳",
            "en": "🇺🇸",
            "ko": "🇰🇷",
        }.get(book.target_lang, "🌐")
        
        return ft.Container(
            content=ft.Column([
                # Book cover placeholder
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
                # Book info
                ft.Text(
                    book.title,
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=Colors.TEXT_PRIMARY,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Text(
                    book.author,
                    size=12,
                    color=Colors.TEXT_SECONDARY,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Container(height=8),
                ft.Row([
                    ft.Text(f"{book.pages} pages", size=11, color=Colors.TEXT_SECONDARY),
                    ft.Container(expand=True),
                    ft.Text(book.translated_at, size=11, color=Colors.TEXT_SECONDARY),
                ]),
                ft.Container(height=8),
                # Actions
                ft.Row([
                    ft.IconButton(
                        icon=ft.icons.OPEN_IN_NEW,
                        icon_color=Colors.PRIMARY,
                        icon_size=18,
                        tooltip="Open",
                    ),
                    ft.IconButton(
                        icon=ft.icons.FOLDER_OPEN,
                        icon_color=Colors.TEXT_SECONDARY,
                        icon_size=18,
                        tooltip="Show in folder",
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.icons.DELETE_OUTLINE,
                        icon_color=Colors.ERROR,
                        icon_size=18,
                        tooltip="Delete",
                        on_click=lambda e, b=book: self._delete_book(b),
                    ),
                ], spacing=0),
            ]),
            padding=16,
            bgcolor=Colors.SURFACE,
            border_radius=10,
        )

    def _update_grid(self):
        """Update the books grid."""
        self.books_grid.controls.clear()
        
        for book in self._filtered_books:
            self.books_grid.controls.append(self._create_book_card(book))
        
        # Show/hide empty state
        self.empty_state.visible = len(self._filtered_books) == 0
        self.books_grid.visible = len(self._filtered_books) > 0

    def _on_search(self, e):
        """Handle search input."""
        self._search_query = e.control.value.lower()
        self._apply_filters()

    def _on_filter(self, e):
        """Handle filter change."""
        self._filter_lang = e.control.value
        self._apply_filters()

    def _apply_filters(self):
        """Apply search and filter."""
        self._filtered_books = []
        
        for book in self._books:
            # Search filter
            if self._search_query:
                if (self._search_query not in book.title.lower() and 
                    self._search_query not in book.author.lower()):
                    continue
            
            # Language filter
            if self._filter_lang != "all" and book.target_lang != self._filter_lang:
                continue
            
            self._filtered_books.append(book)
        
        self._update_grid()
        self.page.update()

    def _delete_book(self, book: Book):
        """Delete a book."""
        # Show confirmation dialog
        def close_dialog(e):
            dialog.open = False
            self.page.update()
        
        def confirm_delete(e):
            self._books = [b for b in self._books if b.id != book.id]
            self._apply_filters()
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Delete Book"),
            content=ft.Text(f"Are you sure you want to delete '{book.title}'?"),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.TextButton("Delete", on_click=confirm_delete),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
