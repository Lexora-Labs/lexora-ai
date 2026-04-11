"""Main translator module."""

import hashlib
from typing import Optional, List, Dict
from pathlib import Path
from ebooklib import epub

from .core import (
    BaseTranslator,
    TranslationConfig,
    TranslationResult,
    BilingualAST,
    BilingualNode,
    TranslationMode,
)
from .providers import get_default_provider
from .readers import FileReader, EpubReader, MobiReader, WordReader, MarkdownReader


class Translator:
    """Main translator class that coordinates file reading and translation."""

    def __init__(
        self,
        provider: Optional[BaseTranslator] = None,
        service: Optional[BaseTranslator] = None,
    ):
        """
        Initialize translator.

        Args:
            provider: Translation provider to use
            service: Deprecated compatibility alias for provider
        """
        if provider and service:
            raise ValueError("Pass either 'provider' or 'service', not both.")

        selected_provider = provider or service or self._get_default_provider()
        if not isinstance(selected_provider, BaseTranslator):
            raise TypeError(
                "Translator expects a BaseTranslator-compatible provider. "
                "Use lexora.providers.*Provider classes."
            )

        self.provider = selected_provider
        # Backward-compatible alias for older integrations.
        self.service = self.provider
        self.readers: List[FileReader] = [
            EpubReader(),
            MobiReader(),
            WordReader(),
            MarkdownReader(),
        ]

    def _get_default_provider(self) -> BaseTranslator:
        """Get the first configured translation provider."""
        return get_default_provider()

    def _get_reader(self, file_path: str) -> FileReader:
        """Get the appropriate reader for a file."""
        for reader in self.readers:
            if reader.supports(file_path):
                return reader
        
        supported_formats = ['.epub', '.mobi', '.docx', '.doc', '.md']
        raise ValueError(
            f"Unsupported file format. Supported formats: {', '.join(supported_formats)}"
        )

    def translate_file(
        self,
        input_file: str,
        output_file: str,
        target_language: str,
        source_language: Optional[str] = None,
        mode: str = "replace",
        glossary: Optional[Dict[str, str]] = None,
    ) -> TranslationResult:
        """
        Translate a file to the target language.

        Args:
            input_file: Path to input file
            output_file: Path to output file
            target_language: Target language code
            source_language: Source language code (optional)
            mode: Translation output mode: replace or bilingual
            glossary: Optional glossary dictionary {source_term: target_term}
        """
        # Check if input file exists
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        reader = self._get_reader(input_file)
        if isinstance(reader, EpubReader):
            return self._translate_epub_file(
                reader=reader,
                input_file=input_file,
                output_file=output_file,
                target_language=target_language,
                source_language=source_language,
                mode=mode,
                glossary=glossary,
            )

        # Read the file
        print(f"Reading {input_file}...")
        text = reader.read(input_file)

        if not text.strip():
            raise ValueError("No text content found in the file")

        # Translate the text
        print(f"Translating to {target_language} with {self.provider.provider_name}...")
        result = self.translate_text_result(
            text=text,
            target_language=target_language,
            source_language=source_language,
            mode=mode,
            glossary=glossary,
        )

        # Write the translated text
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.translated_content)
        
        print(f"Translation saved to {output_file}")
        return result

    def _translate_epub_file(
        self,
        reader: EpubReader,
        input_file: str,
        output_file: str,
        target_language: str,
        source_language: Optional[str] = None,
        mode: str = "replace",
        glossary: Optional[Dict[str, str]] = None,
    ) -> TranslationResult:
        """Translate EPUB content by replacing DOM text nodes and repacking EPUB."""
        print(f"Reading EPUB {input_file}...")
        book = reader.load_book(input_file)
        config = TranslationConfig(
            source_language=source_language,
            target_language=target_language,
            mode=self._resolve_translation_mode(mode),
            glossary=glossary or {},
        )

        bilingual_nodes: List[BilingualNode] = []
        token_usage: Dict[str, int] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

        print(f"Translating EPUB to {target_language} with {self.provider.provider_name}...")
        for item in reader.iter_document_items(book):
            html = item.get_content().decode("utf-8", errors="ignore")
            soup, text_nodes = reader.extract_translatable_nodes(html)
            if not text_nodes:
                continue

            source_texts = [str(node) for node in text_nodes]
            chunked_texts: List[str] = []
            node_chunk_ranges: List[tuple[int, int]] = []
            for source_text in source_texts:
                node_chunks = self._chunk_text_sentence_aware(source_text)
                start = len(chunked_texts)
                chunked_texts.extend(node_chunks)
                end = len(chunked_texts)
                node_chunk_ranges.append((start, end))

            batch_results = self.provider.translate_batch(chunked_texts, config)
            translated_chunks: List[str] = []
            for index, chunk_text in enumerate(chunked_texts):
                result = batch_results[index] if index < len(batch_results) else None
                translated_chunk = result.translated_content if result else chunk_text
                translated_chunks.append(translated_chunk)
                self._accumulate_token_usage(token_usage, result)

            translated_texts: List[str] = []
            for index, source_text in enumerate(source_texts):
                start, end = node_chunk_ranges[index]
                translated_text = "".join(translated_chunks[start:end]).strip()
                rendered_text = self._render_translated_node_text(
                    source_text=source_text,
                    translated_text=translated_text,
                    mode=config.mode,
                )
                translated_texts.append(rendered_text)

                bilingual_nodes.append(
                    BilingualNode(
                        node_id=self._make_epub_node_id(item.get_name(), index, source_text),
                        source_text=source_text,
                        translated_text=translated_text,
                        tag_name=getattr(text_nodes[index].parent, "name", None),
                    )
                )

            updated_html = reader.replace_translatable_nodes(soup, text_nodes, translated_texts)
            item.set_content(updated_html.encode("utf-8"))

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        epub.write_epub(output_file, book)

        ast = BilingualAST(
            source_language=source_language or "",
            target_language=target_language,
            nodes=bilingual_nodes,
            metadata={
                "provider": self.provider.provider_name,
                "input_file": input_file,
                "output_file": output_file,
            },
        )

        translated_message = (
            f"EPUB translated with {self.provider.provider_name} and saved to {output_file}"
        )
        print(f"Translation saved to {output_file}")
        return TranslationResult(
            translated_content=translated_message,
            bilingual_ast=ast,
            token_usage=token_usage,
        )

    def _make_epub_node_id(self, item_name: str, index: int, text: str) -> str:
        """Create stable node IDs for bilingual AST entries in EPUB workflows."""
        content_hash = hashlib.sha256(
            f"{item_name}:{index}:{text[:120]}".encode("utf-8")
        ).hexdigest()[:12]
        return f"{item_name}:{index}:{content_hash}"

    def _accumulate_token_usage(
        self,
        totals: Dict[str, int],
        result: Optional[TranslationResult],
    ) -> None:
        """Merge token usage reported by provider batch calls."""
        if not result or not result.token_usage:
            return
        for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
            value = result.token_usage.get(key, 0)
            if isinstance(value, int):
                totals[key] += value

    def _resolve_translation_mode(self, mode: str) -> TranslationMode:
        """Resolve string mode values to TranslationMode enum."""
        normalized = (mode or "replace").strip().lower()
        if normalized == "bilingual":
            return TranslationMode.BILINGUAL
        return TranslationMode.REPLACE

    def _render_translated_node_text(
        self,
        source_text: str,
        translated_text: str,
        mode: TranslationMode,
    ) -> str:
        """Render text for EPUB node replacement according to translation mode."""
        if mode == TranslationMode.BILINGUAL:
            return f"{source_text}\n{translated_text}"
        return translated_text

    def _chunk_text_sentence_aware(self, text: str, max_chars: int = 1200) -> List[str]:
        """Split long text into sentence-aware chunks while preserving original order."""
        if len(text) <= max_chars:
            return [text]

        sentence_endings = {".", "!", "?", "。", "！", "？", ";", ":", "\n"}
        chunks: List[str] = []
        buffer = ""
        last_boundary = -1

        for char in text:
            buffer += char
            if char in sentence_endings:
                last_boundary = len(buffer)

            if len(buffer) >= max_chars:
                if last_boundary >= max_chars // 2:
                    chunks.append(buffer[:last_boundary])
                    buffer = buffer[last_boundary:]
                else:
                    chunks.append(buffer[:max_chars])
                    buffer = buffer[max_chars:]

                last_boundary = -1
                for index, buffer_char in enumerate(buffer):
                    if buffer_char in sentence_endings:
                        last_boundary = index + 1

        if buffer:
            chunks.append(buffer)

        return [chunk for chunk in chunks if chunk]

    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> str:
        """
        Translate raw text.

        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (optional)

        Returns:
            str: Translated text
        """
        return self.translate_text_result(
            text=text,
            target_language=target_language,
            source_language=source_language,
        ).translated_content

    def translate_text_result(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None,
        mode: str = "replace",
        glossary: Optional[Dict[str, str]] = None,
    ) -> TranslationResult:
        """Translate raw text and return the provider-native result."""
        config = TranslationConfig(
            source_language=source_language,
            target_language=target_language,
            mode=self._resolve_translation_mode(mode),
            glossary=glossary or {},
        )
        return self.provider.translate_text(text, config)
