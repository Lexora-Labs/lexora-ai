"""EPUB file reader."""

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from typing import List
from .base_reader import FileReader


class EpubReader(FileReader):
    """Reader for EPUB files."""

    def supports(self, file_path: str) -> bool:
        """Check if file is an EPUB."""
        return file_path.lower().endswith('.epub')

    def read(self, file_path: str) -> str:
        """
        Read EPUB file and extract text content.

        Args:
            file_path: Path to the EPUB file

        Returns:
            str: Extracted text content
        """
        try:
            book = epub.read_epub(file_path)
        except Exception as e:
            raise ValueError(f"Failed to read EPUB file: {str(e)}")

        text_content = []

        # Extract text from all document items
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content()
                # Parse HTML content
                soup = BeautifulSoup(content, 'html.parser')
                text = soup.get_text(separator='\n', strip=True)
                if text:
                    text_content.append(text)

        return '\n\n'.join(text_content)
