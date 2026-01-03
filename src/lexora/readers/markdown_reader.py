"""Markdown file reader."""

import markdown
from .base_reader import FileReader


class MarkdownReader(FileReader):
    """Reader for Markdown files."""

    def supports(self, file_path: str) -> bool:
        """Check if file is a Markdown file."""
        return file_path.lower().endswith('.md')

    def read(self, file_path: str) -> str:
        """
        Read Markdown file and extract text content.

        Args:
            file_path: Path to the Markdown file

        Returns:
            str: Text content (markdown format is preserved)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            raise ValueError(f"Failed to read Markdown file: {str(e)}")
