"""EPUB reader built on DOM parsing.

This reader extracts readable text from EPUB XHTML documents without using
regex-based parsing. It is intentionally conservative and returns plain text
for the current translator contract, while preserving a clean DOM-driven
foundation for future node-level translation and EPUB repacking.
"""

import io
import logging
import re
import zipfile
from html import unescape
from typing import Dict, List, Tuple

import ebooklib
from bs4 import BeautifulSoup, NavigableString
from ebooklib import epub

from .base_reader import FileReader

_logger = logging.getLogger(__name__)


# File extensions inside an EPUB whose XHTML <head> we want to preserve
# verbatim (because EPUB readers depend on <link rel="stylesheet"/>, charset
# meta, etc.).
_HEAD_PRESERVE_EXTS = (".xhtml", ".html", ".htm")


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
            # Preserve leading/trailing whitespace from the original text
            # node so we don't accidentally glue words to following tags,
            # e.g. "... link " + "<a href=...>" becoming "... link<a ...>".
            original_text = str(node)
            leading_ws = re.match(r"^\s*", original_text)
            trailing_ws = re.search(r"\s*$", original_text)
            before = leading_ws.group(0) if leading_ws else ""
            after = trailing_ws.group(0) if trailing_ws else ""

            normalized = self.normalize_node_text(translated)

            # If the provider already included boundary whitespace,
            # don't duplicate it; otherwise re-apply the structural
            # boundary whitespace from the original XHTML.
            normalized_before = re.match(r"^\s+", normalized)
            normalized_after = re.search(r"\s+$", normalized)

            prefix = before if not normalized_before else ""
            suffix = after if not normalized_after else ""

            node.replace_with(f"{prefix}{normalized}{suffix}")
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


def splice_translated_body(
    original_xhtml: str,
    translated_xhtml: str,
) -> str:
    """Merge an original XHTML's ``<head>`` with a translated XHTML's ``<body>``.

    Background
    ----------
    ``ebooklib.epub.write_epub`` regenerates each chapter's ``<head>`` from
    the ``EpubHtml`` Python attributes (``title``, ``lang`` and items
    declared via ``add_link``) instead of preserving the source bytes.
    Stylesheet links, charset declarations and custom meta tags written via
    ``EpubItem.set_content`` are silently dropped, which leaves the saved
    ebook unstyled.

    This helper is the core of the post-processing fix: re-attach the
    *original* ``<head>`` (full fidelity, including ``<link
    rel="stylesheet">``) to the *translated* ``<body>`` produced by the
    translator. It also copies the translated ``<title>`` over the original
    one so the chapter title in head still reflects the target language.

    Parameters
    ----------
    original_xhtml:
        Bytes/text of the chapter as it existed in the source EPUB
        (i.e. before any mutation, before ``epub.write_epub``).
    translated_xhtml:
        Bytes/text of the chapter as ``ebooklib`` wrote it - this is what
        contains the translated ``<body>`` but a stripped-down ``<head>``.

    Returns
    -------
    str
        XHTML where the head is the original head, the body is the
        translated body, and the ``<title>`` (if both files have one) is
        taken from the translated copy.
    """
    if not original_xhtml or not translated_xhtml:
        return translated_xhtml or original_xhtml or ""

    def _parse(xhtml: str) -> BeautifulSoup:
        # Try lxml-xml first (preserves self-closing tags and XML decl).
        # If lxml chokes on namespace prefix issues that are common in EPUB
        # (e.g. ``epub:prefix`` written by ebooklib without a fully-namespaced
        # declaration), fall back to the lenient HTML parser, then to the
        # built-in html.parser as a last resort.
        for parser in ("lxml-xml", "lxml", "html.parser"):
            try:
                return BeautifulSoup(xhtml, parser)
            except Exception:
                continue
        return BeautifulSoup(xhtml, "html.parser")

    orig_soup = _parse(original_xhtml)
    new_soup = _parse(translated_xhtml)

    orig_body = orig_soup.find("body")
    new_body = new_soup.find("body")
    if orig_body is not None and new_body is not None:
        orig_body.replace_with(new_body)
    elif new_body is not None:
        return translated_xhtml

    # If the translated head still has a (translated) <title>, prefer it
    # over the original-language one.
    new_head = new_soup.find("head")
    new_title = new_head.find("title") if new_head is not None else None
    if new_title is not None and orig_soup.find("head") is not None:
        orig_head = orig_soup.find("head")
        existing_title = orig_head.find("title") if orig_head is not None else None
        if existing_title is not None:
            existing_title.replace_with(new_title)
        elif orig_head is not None:
            orig_head.append(new_title)

    return str(orig_soup)


def restore_xhtml_heads_in_epub(
    epub_path: str,
    original_xhtml_by_basename: Dict[str, str],
) -> None:
    """Rewrite chapter XHTML in an already-written EPUB to restore ``<head>``.

    Walks every entry in ``epub_path``; for any XHTML whose basename matches
    a key in ``original_xhtml_by_basename`` the entry is replaced with the
    output of :func:`splice_translated_body`. Other entries (mimetype, OPF,
    NCX, nav, CSS, fonts, images) are passed through byte-for-byte.

    The ``mimetype`` entry is special-cased to remain stored (uncompressed)
    and ordered first - that's an EPUB OCF requirement.

    Parameters
    ----------
    epub_path:
        Path to the EPUB to rewrite in place.
    original_xhtml_by_basename:
        Mapping of ``<chapter file basename>`` -> original XHTML content as
        captured before mutation. Basename match (rather than full path)
        keeps us robust to ebooklib renaming the OPF root from ``OEBPS/`` to
        ``EPUB/`` and similar.
    """
    if not original_xhtml_by_basename:
        return

    buf = io.BytesIO()
    with zipfile.ZipFile(epub_path, "r") as src_zip:
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out_zip:
            for info in src_zip.infolist():
                data = src_zip.read(info.filename)
                lower = info.filename.lower()
                if lower.endswith(_HEAD_PRESERVE_EXTS):
                    base = info.filename.rsplit("/", 1)[-1]
                    original = original_xhtml_by_basename.get(base)
                    if original:
                        try:
                            spliced = splice_translated_body(
                                original,
                                data.decode("utf-8", errors="ignore"),
                            )
                            data = spliced.encode("utf-8")
                        except Exception:
                            # Don't corrupt the chapter on splice failure -
                            # keep ebooklib's output but log so the cause is
                            # visible in production rather than silently
                            # losing the stylesheet link.
                            _logger.exception(
                                "splice_translated_body failed for %s; "
                                "falling back to ebooklib output",
                                info.filename,
                            )

                if info.filename == "mimetype":
                    out_zip.writestr(
                        "mimetype",
                        data,
                        compress_type=zipfile.ZIP_STORED,
                    )
                else:
                    out_zip.writestr(info, data)

    with open(epub_path, "wb") as fh:
        fh.write(buf.getvalue())