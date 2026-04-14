"""Main translator module."""

import hashlib
import logging
import time
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
    CacheFingerprint,
    TranslationCache,
    hash_glossary,
)
from .providers import canonical_provider_name, get_default_provider
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
        self.logger = logging.getLogger("lexora.translator")
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
        cache_path: Optional[str] = None,
        limit_docs: Optional[int] = None,
        start_doc: Optional[int] = None,
        end_doc: Optional[int] = None,
        chunk_size: int = 1200,
        chunk_context_window: int = 0,
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
            cache_path: Optional global translation cache path (JSONL)
            limit_docs: Optional number of EPUB documents to translate from selection start
            start_doc: Optional 1-based start index of EPUB document selection
            end_doc: Optional 1-based end index (inclusive) of EPUB document selection
            chunk_size: Max chars for sentence-aware chunking (EPUB path)
            chunk_context_window: Number of neighbor chunks on each side for context
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
                cache_path=cache_path,
                limit_docs=limit_docs,
                start_doc=start_doc,
                end_doc=end_doc,
                chunk_size=chunk_size,
                chunk_context_window=chunk_context_window,
            )

        # Read the file
        self.logger.info("Reading %s...", input_file)
        text = reader.read(input_file)

        if not text.strip():
            raise ValueError("No text content found in the file")

        # Translate the text
        self.logger.info(
            "Translating to %s with %s...",
            target_language,
            self.provider.provider_name,
        )
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
        
        self.logger.info("Translation saved to %s", output_file)
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
        cache_path: Optional[str] = None,
        limit_docs: Optional[int] = None,
        start_doc: Optional[int] = None,
        end_doc: Optional[int] = None,
        chunk_size: int = 1200,
        chunk_context_window: int = 0,
    ) -> TranslationResult:
        """Translate EPUB content by replacing DOM text nodes and repacking EPUB."""
        self.logger.info("Reading EPUB %s...", input_file)
        book = reader.load_book(input_file)
        docs = list(reader.iter_document_items(book))
        docs = self._select_epub_docs(
            docs=docs,
            limit_docs=limit_docs,
            start_doc=start_doc,
            end_doc=end_doc,
        )
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

        cache = TranslationCache(cache_path) if cache_path else None
        cache_stats_before = cache.stats() if cache else None
        cache_fingerprint = self._build_cache_fingerprint(config)
        started_at = time.perf_counter()

        total_nodes = 0
        total_chunks = 0
        total_cache_hits = 0
        total_cache_misses = 0
        translated_docs = 0

        self.logger.info(
            "[epub] Starting translation: docs=%s target=%s provider=%s",
            len(docs),
            target_language,
            self.provider.provider_name,
        )
        for doc_index, item in enumerate(docs, start=1):
            doc_started_at = time.perf_counter()
            self.logger.info(
                "[epub] [%s/%s] Translating %s...",
                doc_index,
                len(docs),
                item.get_name(),
            )

            html = item.get_content().decode("utf-8", errors="ignore")
            soup, text_nodes = reader.extract_translatable_nodes(html)
            if not text_nodes:
                self.logger.info(
                    "[epub] [%s/%s] No translatable nodes, skipped",
                    doc_index,
                    len(docs),
                )
                continue

            source_texts = [str(node) for node in text_nodes]
            chunked_texts: List[str] = []
            node_chunk_ranges: List[tuple[int, int]] = []
            for source_text in source_texts:
                node_chunks = self._chunk_text_sentence_aware(
                    source_text,
                    max_chars=chunk_size,
                )
                start = len(chunked_texts)
                chunked_texts.extend(node_chunks)
                end = len(chunked_texts)
                node_chunk_ranges.append((start, end))

            doc_cache_hits = 0
            doc_cache_misses = 0

            translated_chunks: List[str] = [""] * len(chunked_texts)
            uncached_indices: List[int] = []
            uncached_texts: List[str] = []
            for index, chunk_text in enumerate(chunked_texts):
                if cache is None:
                    uncached_indices.append(index)
                    uncached_texts.append(chunk_text)
                    doc_cache_misses += 1
                    continue

                cached_text = cache.get(chunk_text, cache_fingerprint)
                if cached_text is None:
                    uncached_indices.append(index)
                    uncached_texts.append(chunk_text)
                    doc_cache_misses += 1
                else:
                    translated_chunks[index] = cached_text
                    doc_cache_hits += 1

            batch_results: List[TranslationResult] = []
            if uncached_texts:
                self.logger.info(
                    "[epub] [%s/%s] Provider translating %s chunk(s) context_window=%s...",
                    doc_index,
                    len(docs),
                    len(uncached_texts),
                    chunk_context_window,
                )
                batch_results = self._translate_uncached_chunks(
                    chunked_texts=chunked_texts,
                    uncached_indices=uncached_indices,
                    uncached_texts=uncached_texts,
                    config=config,
                    context_window=chunk_context_window,
                )

            for result_index, chunk_index in enumerate(uncached_indices):
                source_chunk = chunked_texts[chunk_index]
                result = batch_results[result_index] if result_index < len(batch_results) else None
                translated_chunk = result.translated_content if result else source_chunk
                translated_chunks[chunk_index] = translated_chunk
                self._accumulate_token_usage(token_usage, result)
                if cache is not None:
                    cache.put(source_chunk, cache_fingerprint, translated_chunk)

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

            translated_docs += 1
            total_nodes += len(text_nodes)
            total_chunks += len(chunked_texts)
            total_cache_hits += doc_cache_hits
            total_cache_misses += doc_cache_misses

            doc_elapsed = time.perf_counter() - doc_started_at
            self.logger.info(
                "[epub] [%s/%s] Done nodes=%s chunks=%s cache_hit=%s cache_miss=%s time=%.1fs",
                doc_index,
                len(docs),
                len(text_nodes),
                len(chunked_texts),
                doc_cache_hits,
                doc_cache_misses,
                doc_elapsed,
            )

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        epub.write_epub(output_file, book)

        total_elapsed = time.perf_counter() - started_at
        cache_rate = (total_cache_hits / total_chunks * 100.0) if total_chunks else 0.0

        ast = BilingualAST(
            source_language=source_language or "",
            target_language=target_language,
            nodes=bilingual_nodes,
            metadata={
                "provider": canonical_provider_name(self.provider.provider_name),
                "input_file": input_file,
                "output_file": output_file,
                "docs_total": len(docs),
                "docs_translated": translated_docs,
                "nodes_total": total_nodes,
                "chunks_total": total_chunks,
                "cache_hits": total_cache_hits,
                "cache_misses": total_cache_misses,
                "cache_hit_rate": round(cache_rate, 2),
                "cache_entries_before": cache_stats_before["entries"] if cache_stats_before else 0,
                "chunk_size": chunk_size,
                "chunk_context_window": chunk_context_window,
                "elapsed_ms": int(total_elapsed * 1000),
            },
        )

        translated_message = (
            f"EPUB translated with {self.provider.provider_name} and saved to {output_file}"
        )
        self.logger.info(
            "[epub] Summary docs=%s/%s nodes=%s chunks=%s cache_hit=%s cache_miss=%s cache_hit_rate=%.1f%% tokens=%s time=%.1fs",
            translated_docs,
            len(docs),
            total_nodes,
            total_chunks,
            total_cache_hits,
            total_cache_misses,
            cache_rate,
            token_usage.get("total_tokens", 0),
            total_elapsed,
        )
        self.logger.info("Translation saved to %s", output_file)
        return TranslationResult(
            translated_content=translated_message,
            bilingual_ast=ast,
            token_usage=token_usage,
        )

    def _translate_uncached_chunks(
        self,
        chunked_texts: List[str],
        uncached_indices: List[int],
        uncached_texts: List[str],
        config: TranslationConfig,
        context_window: int,
    ) -> List[TranslationResult]:
        """Translate uncached chunks with optional neighbor context windows."""
        if context_window <= 0:
            return self.provider.translate_batch(uncached_texts, config)

        results: List[TranslationResult] = []
        for index, chunk_index in enumerate(uncached_indices):
            source_chunk = chunked_texts[chunk_index]
            left = max(0, chunk_index - context_window)
            right = min(len(chunked_texts), chunk_index + context_window + 1)
            neighbors = chunked_texts[left:right]

            contextual_text = "\n".join(
                [
                    "CONTEXT_NEIGHBORS_START",
                    *neighbors,
                    "CONTEXT_NEIGHBORS_END",
                    "TARGET_CHUNK_START",
                    source_chunk,
                    "TARGET_CHUNK_END",
                ]
            )
            contextual_instruction = (
                "Translate only the text between TARGET_CHUNK_START and TARGET_CHUNK_END. "
                "Use neighbor context for coherence but output only the translated target chunk. "
                "Do not include labels or any extra commentary."
            )
            contextual_config = TranslationConfig(
                source_language=config.source_language,
                target_language=config.target_language,
                mode=config.mode,
                glossary=config.glossary,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                custom_instruction=contextual_instruction,
            )
            result = self.provider.translate_text(contextual_text, contextual_config)
            translated = (result.translated_content or "").strip()
            if not translated:
                translated = source_chunk
            # Normalize to target-only output if provider echoed delimiters.
            if "TARGET_CHUNK_START" in translated and "TARGET_CHUNK_END" in translated:
                translated = translated.split("TARGET_CHUNK_START", 1)[1]
                translated = translated.split("TARGET_CHUNK_END", 1)[0].strip()
            results.append(
                TranslationResult(
                    translated_content=translated,
                    bilingual_ast=result.bilingual_ast,
                    token_usage=result.token_usage,
                    cost_estimate=result.cost_estimate,
                )
            )
            if (index + 1) % 50 == 0:
                self.logger.debug(
                    "[epub] Context chunk progress %s/%s",
                    index + 1,
                    len(uncached_indices),
                )
        return results

    def _select_epub_docs(
        self,
        docs: List,
        limit_docs: Optional[int],
        start_doc: Optional[int],
        end_doc: Optional[int],
    ) -> List:
        """Select EPUB docs for scoped test runs using 1-based inclusive range."""
        selected_docs = docs

        if start_doc is not None or end_doc is not None:
            start_index = max(1, start_doc or 1)
            end_index = end_doc if end_doc is not None else len(selected_docs)
            end_index = max(start_index, end_index)

            zero_based_start = start_index - 1
            zero_based_end_exclusive = min(len(selected_docs), end_index)
            selected_docs = selected_docs[zero_based_start:zero_based_end_exclusive]

            self.logger.info(
                "[epub] Doc range selection start=%s end=%s selected=%s",
                start_index,
                end_index,
                len(selected_docs),
            )

        if limit_docs is not None:
            selected_docs = selected_docs[: max(0, limit_docs)]
            self.logger.info(
                "[epub] Limit selection limit_docs=%s selected=%s",
                limit_docs,
                len(selected_docs),
            )

        return selected_docs

    def _build_cache_fingerprint(self, config: TranslationConfig) -> CacheFingerprint:
        """Build a robust cache fingerprint for translation behavior."""
        model = (
            getattr(self.provider, "_model", None)
            or getattr(self.provider, "_deployment", None)
            or getattr(self.provider, "model", None)
            or getattr(self.provider, "deployment", None)
            or "unknown"
        )
        custom_instruction = config.custom_instruction or ""
        instruction_hash = hashlib.sha256(custom_instruction.encode("utf-8")).hexdigest()
        return CacheFingerprint(
            source_language=config.source_language or "auto",
            target_language=config.target_language,
            provider_name=self.provider.provider_name,
            provider_model=str(model),
            glossary_hash=hash_glossary(config.glossary),
            instruction_hash=instruction_hash,
            chunking_version="sentence-aware-v1",
            pipeline_version="epub-node-v1",
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
