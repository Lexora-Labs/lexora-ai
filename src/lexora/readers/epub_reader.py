"""EPUB reader built on DOM parsing.

This reader extracts readable text from EPUB XHTML documents without using
regex-based parsing. It is intentionally conservative and returns plain text
for the current translator contract, while preserving a clean DOM-driven
foundation for future node-level translation and EPUB repacking.
"""

from html import unescape
from typing import List, Tuple

import ebooklib
from bs4 import BeautifulSoup, NavigableString
from ebooklib import epub

from .base_reader import FileReader


class EpubReader(FileReader):
    """Reader for EPUB files."""

    _PARAGRAPH_TAGS = (
        "p",
        "li",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "blockquote",
        "div",
        "section",
    )

    _SKIP_TAGS = {"script", "style", "code", "pre"}

    def supports(self, file_path: str) -> bool:
        """Check if file is an EPUB."""
        return file_path.lower().endswith(".epub")

    def read(self, file_path: str) -> str:
        """Read EPUB and extract text from document items."""
        try:
            book = epub.read_epub(file_path)
            text_blocks: List[str] = []

            for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                html = item.get_content().decode("utf-8", errors="ignore")
                text_blocks.extend(self._extract_blocks_from_html(html))

            return "\n\n".join(block for block in text_blocks if block.strip())
        except Exception as e:
            raise ValueError(f"Failed to read EPUB file: {str(e)}") from e

    def load_book(self, file_path: str):
        """Load an EPUB book object for translation/repack workflows."""
        return epub.read_epub(file_path)

    def iter_document_items(self, book):
        """Yield document items (XHTML/HTML) from the EPUB."""
        return book.get_items_of_type(ebooklib.ITEM_DOCUMENT)

    def extract_translatable_nodes(self, html: str) -> Tuple[BeautifulSoup, List[NavigableString]]:
        """Parse HTML/XHTML and return translatable text nodes."""
        soup = BeautifulSoup(html, "lxml-xml")
        nodes: List[NavigableString] = []

        for text_node in soup.find_all(string=True):
            if not isinstance(text_node, NavigableString):
                continue
            if not text_node.strip():
                continue
            # lxml-xml can surface a spurious document-level string (e.g. "html") whose
            # parent is the BeautifulSoup root; translating/replacing it corrupts XHTML.
            if text_node.parent is soup:
                continue
            if self._is_in_skipped_context(text_node):
                continue
            nodes.append(text_node)

        return soup, nodes

    def replace_translatable_nodes(
        self,
        soup: BeautifulSoup,
        nodes: List[NavigableString],
        translated_texts: List[str],
    ) -> str:
        """Replace collected text nodes with translated content and render HTML."""
        for node, translated in zip(nodes, translated_texts):
            node.replace_with(self.normalize_node_text(translated))
        return str(soup)

    def normalize_node_text(self, translated_text: str) -> str:
        """Normalize provider text for safe text-node replacement.

        Providers may occasionally return HTML fragments. For DOM text-node
        replacement we always want plain text content, otherwise tags like
        `<p>...</p>` will appear as raw text inside EPUB readers.
        """
        if translated_text is None:
            return ""

        normalized = str(translated_text)
        if "<" in normalized and ">" in normalized:
            fragment = BeautifulSoup(normalized, "lxml")
            normalized = fragment.get_text(separator=" ", strip=False)

        return unescape(normalized)

    def _extract_blocks_from_html(self, html: str) -> List[str]:
        """Extract text blocks from one XHTML/HTML document using DOM traversal."""
        soup = BeautifulSoup(html, "lxml-xml")
        blocks: List[str] = []

        for tag_name in self._PARAGRAPH_TAGS:
            for node in soup.find_all(tag_name):
                if self._should_skip_node(node):
                    continue
                text = node.get_text(separator=" ", strip=True)
                if text:
                    blocks.append(text)

        if blocks:
            return blocks

        # Fallback for documents that do not use common paragraph tags.
        fallback = soup.get_text(separator="\n", strip=True)
        return [fallback] if fallback else []

    def _should_skip_node(self, node) -> bool:
        """Skip nodes that are inside tags we should not translate as prose."""
        for parent in [node, *node.parents]:
            name = getattr(parent, "name", None)
            if name and name.lower() in self._SKIP_TAGS:
                return True
        return False

    def _is_in_skipped_context(self, node: NavigableString) -> bool:
        """Return True when a text node is under script/style/code/pre tags."""
        parent = node.parent
        while parent is not None:
            name = getattr(parent, "name", None)
            if name and name.lower() in self._SKIP_TAGS:
                return True
            parent = parent.parent
        return False