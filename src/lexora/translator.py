"""Main translator module."""

import hashlib
import logging
import time
from typing import Optional, List, Dict, Any, Tuple, Callable
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
from .readers.epub_reader import restore_xhtml_heads_in_epub
from .core.structured_batch import StructuredBatchItem, pack_items_by_char_budget


class TranslationCancelled(Exception):
    """Raised when a cooperative cancel is requested during ``translate_file``."""

    pass


def _cancel_requested(cancel_fn: Optional[Callable[[], bool]]) -> bool:
    if cancel_fn is None:
        return False
    try:
        return bool(cancel_fn())
    except Exception:
        return False


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

    def _log_event(self, level: int, event: str, **fields: object) -> None:
        """Emit a structured event while keeping text logs readable."""
        compact = " ".join(f"{key}={value}" for key, value in fields.items())
        message = f"{event} | {compact}" if compact else event
        self.logger.log(level, message, extra={"event": event, "fields": fields})

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
        structured_epub_batch: bool = False,
        structured_epub_batch_max_chars: int = 8000,
        on_document_progress: Optional[Callable[[int, int], None]] = None,
        cancel_requested: Optional[Callable[[], bool]] = None,
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
            structured_epub_batch: Use JSON multi-item batches for uncached EPUB chunks (GPT providers)
            structured_epub_batch_max_chars: Approx max source chars per structured batch (EPUB path)
            on_document_progress: Optional ``(docs_completed, docs_total)`` callback after each EPUB
                document is processed (including skipped spine items), or ``(1, 1)`` when a non-EPUB
                file finishes.
            cancel_requested: Optional zero-arg callable; if it returns True, abort with
                :class:`TranslationCancelled` between EPUB documents and before repack / plain-file write.
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
                structured_epub_batch=structured_epub_batch,
                structured_epub_batch_max_chars=structured_epub_batch_max_chars,
                on_document_progress=on_document_progress,
                cancel_requested=cancel_requested,
            )

        # Read the file
        self._log_event(
            logging.INFO,
            "translation.read_input.started",
            input_file=input_file,
            target_language=target_language,
        )
        text = reader.read(input_file)

        if not text.strip():
            raise ValueError("No text content found in the file")

        if on_document_progress:
            try:
                on_document_progress(0, 1)
            except Exception:
                pass

        if _cancel_requested(cancel_requested):
            raise TranslationCancelled("Translation cancelled.")

        # Translate the text
        self._log_event(
            logging.INFO,
            "translation.text.started",
            provider=self.provider.provider_name,
            target_language=target_language,
            source_language=source_language or "auto",
            chunks=1,
        )
        result = self.translate_text_result(
            text=text,
            target_language=target_language,
            source_language=source_language,
            mode=mode,
            glossary=glossary,
        )

        if _cancel_requested(cancel_requested):
            raise TranslationCancelled("Translation cancelled.")

        # Write the translated text
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.translated_content)
        
        self._log_event(
            logging.INFO,
            "translation.text.completed",
            provider=self.provider.provider_name,
            input_file=input_file,
            output_file=output_file,
            elapsed_ms=0,
        )
        if on_document_progress:
            try:
                on_document_progress(1, 1)
            except Exception:
                pass
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
        structured_epub_batch: bool = False,
        structured_epub_batch_max_chars: int = 8000,
        on_document_progress: Optional[Callable[[int, int], None]] = None,
        cancel_requested: Optional[Callable[[], bool]] = None,
    ) -> TranslationResult:
        """Translate EPUB content by replacing DOM text nodes and repacking EPUB."""
        use_structured = (
            structured_epub_batch
            and chunk_context_window <= 0
            and self.provider.supports_structured_batch()
        )
        if structured_epub_batch and chunk_context_window > 0:
            raise ValueError(
                "structured_epub_batch cannot be used with chunk_context_window > 0"
            )
        if structured_epub_batch and not self.provider.supports_structured_batch():
            self._log_event(
                logging.WARNING,
                "translation.epub.structured_batch.unsupported_provider",
                provider=self.provider.provider_name,
            )

        self._log_event(
            logging.INFO,
            "translation.epub.read.started",
            input_file=input_file,
            output_file=output_file,
            target_language=target_language,
            provider=self.provider.provider_name,
        )
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
        cache_fingerprint = self._build_cache_fingerprint(
            config, structured_epub_batch=use_structured
        )
        started_at = time.perf_counter()

        total_nodes = 0
        total_chunks = 0
        total_cache_hits = 0
        total_cache_misses = 0
        translated_docs = 0

        structured_stats: Dict[str, Any] = {
            "structured_batch_enabled": bool(use_structured),
            "structured_batches_total": 0,
            "structured_items_total": 0,
            "structured_validation_failures": 0,
            "structured_fallback_batches": 0,
        }

        # Snapshot the FULL original XHTML for every document item BEFORE
        # we mutate ``set_content`` on it. We read straight from the source
        # EPUB ZIP because ``ebooklib``'s ``EpubHtml.get_content()`` already
        # returns a regenerated document with the ``<head>`` stripped down
        # to the empty ``<head/>`` form (it removes ``<link
        # rel="stylesheet">``, custom ``<meta>``, etc.). We need the
        # untouched bytes from the ZIP so we can splice the real ``<head>``
        # back in after ``epub.write_epub``.
        original_xhtml_by_basename: Dict[str, str] = {}
        if isinstance(reader, EpubReader):
            try:
                import zipfile

                with zipfile.ZipFile(input_file, "r") as src_zip:
                    zip_names = set(src_zip.namelist())
                    for original_item in reader.iter_document_items(book):
                        item_name = original_item.get_name()
                        # ebooklib's ``item_name`` is relative to the OPF.
                        # Different EPUB packagers use different OPF roots
                        # (``OEBPS/``, ``EPUB/``, ``OPS/``, or none), so try
                        # the bare name first then common prefixes.
                        candidates = [
                            item_name,
                            f"OEBPS/{item_name}",
                            f"EPUB/{item_name}",
                            f"OPS/{item_name}",
                        ]
                        chosen = next((c for c in candidates if c in zip_names), None)
                        if chosen is None:
                            # Last-ditch substring match for unusual layouts.
                            chosen = next(
                                (n for n in zip_names if n.endswith("/" + item_name)),
                                None,
                            )
                        if chosen is None:
                            continue
                        try:
                            original_html = src_zip.read(chosen).decode(
                                "utf-8", errors="ignore"
                            )
                        except Exception:
                            continue
                        base = item_name.rsplit("/", 1)[-1]
                        original_xhtml_by_basename[base] = original_html
            except Exception:
                # If the input is not a real ZIP (corrupt or test stub) skip
                # the head-restore feature rather than failing translation.
                original_xhtml_by_basename = {}

        self._log_event(
            logging.INFO,
            "translation.epub.started",
            provider=self.provider.provider_name,
            target_language=target_language,
            source_language=source_language or "auto",
            input_file=input_file,
            output_file=output_file,
            doc_total=len(docs),
        )
        if on_document_progress and docs:
            try:
                on_document_progress(0, len(docs))
            except Exception:
                pass
        for doc_index, item in enumerate(docs, start=1):
            if _cancel_requested(cancel_requested):
                raise TranslationCancelled("Translation cancelled.")
            doc_started_at = time.perf_counter()
            self._log_event(
                logging.INFO,
                "translation.epub.doc.started",
                doc_index=doc_index,
                doc_total=len(docs),
                input_file=input_file,
                output_file=output_file,
                provider=self.provider.provider_name,
                item_name=item.get_name(),
            )

            html = item.get_content().decode("utf-8", errors="ignore")
            soup, text_nodes = reader.extract_translatable_nodes(html)
            if not text_nodes:
                self._log_event(
                    logging.INFO,
                    "translation.epub.doc.skipped",
                    doc_index=doc_index,
                    doc_total=len(docs),
                    item_name=item.get_name(),
                    reason="no_translatable_nodes",
                )
                if on_document_progress:
                    try:
                        on_document_progress(doc_index, len(docs))
                    except Exception:
                        pass
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
                if _cancel_requested(cancel_requested):
                    raise TranslationCancelled("Translation cancelled.")
                self._log_event(
                    logging.INFO,
                    "translation.epub.provider_batch.started",
                    doc_index=doc_index,
                    doc_total=len(docs),
                    provider=self.provider.provider_name,
                    chunks=len(uncached_texts),
                )
                batch_results, batch_token_usage = self._translate_uncached_chunks(
                    chunked_texts=chunked_texts,
                    uncached_indices=uncached_indices,
                    uncached_texts=uncached_texts,
                    config=config,
                    context_window=chunk_context_window,
                    structured_epub_batch=use_structured,
                    structured_epub_batch_max_chars=structured_epub_batch_max_chars,
                    doc_index=doc_index,
                    structured_stats=structured_stats,
                )
                for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                    token_usage[key] += batch_token_usage.get(key, 0)

            for result_index, chunk_index in enumerate(uncached_indices):
                source_chunk = chunked_texts[chunk_index]
                result = batch_results[result_index] if result_index < len(batch_results) else None
                translated_chunk = result.translated_content if result else source_chunk
                translated_chunks[chunk_index] = translated_chunk
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
            self._log_event(
                logging.INFO,
                "translation.epub.doc.completed",
                doc_index=doc_index,
                doc_total=len(docs),
                chunks=len(chunked_texts),
                cache_hit=doc_cache_hits,
                cache_miss=doc_cache_misses,
                elapsed_ms=round(doc_elapsed * 1000),
                provider=self.provider.provider_name,
            )
            if on_document_progress:
                try:
                    on_document_progress(doc_index, len(docs))
                except Exception:
                    pass

        if _cancel_requested(cancel_requested):
            raise TranslationCancelled("Translation cancelled.")

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        epub.write_epub(output_file, book)

        # ebooklib.write_epub strips custom ``<head>`` content (notably
        # ``<link rel="stylesheet">``) from chapter XHTML. Restore each
        # chapter's original head while keeping the translated body.
        if original_xhtml_by_basename:
            try:
                restore_xhtml_heads_in_epub(
                    str(output_path),
                    original_xhtml_by_basename,
                )
                self._log_event(
                    logging.INFO,
                    "translation.epub.head_restored",
                    output_file=output_file,
                    docs_restored=len(original_xhtml_by_basename),
                )
            except Exception as exc:
                self._log_event(
                    logging.WARNING,
                    "translation.epub.head_restore_failed",
                    output_file=output_file,
                    error=str(exc),
                )

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
                **structured_stats,
            },
        )

        translated_message = (
            f"EPUB translated with {self.provider.provider_name} and saved to {output_file}"
        )
        self._log_event(
            logging.INFO,
            "translation.epub.completed",
            provider=self.provider.provider_name,
            input_file=input_file,
            output_file=output_file,
            doc_index=translated_docs,
            doc_total=len(docs),
            chunks=total_chunks,
            cache_hit=total_cache_hits,
            cache_miss=total_cache_misses,
            elapsed_ms=round(total_elapsed * 1000),
            token_total=token_usage.get("total_tokens", 0),
            cache_hit_rate=round(cache_rate, 1),
        )
        self._log_event(
            logging.INFO,
            "translation.output.saved",
            output_file=output_file,
            provider=self.provider.provider_name,
        )
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
        *,
        structured_epub_batch: bool = False,
        structured_epub_batch_max_chars: int = 8000,
        doc_index: int = 0,
        structured_stats: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[TranslationResult], Dict[str, int]]:
        """Translate uncached chunks with optional neighbor context or structured JSON batches."""
        empty_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        if structured_epub_batch and context_window <= 0:
            results, usage = self._translate_uncached_chunks_structured_json(
                chunked_texts=chunked_texts,
                uncached_indices=uncached_indices,
                config=config,
                doc_index=doc_index,
                max_payload_chars=structured_epub_batch_max_chars,
                structured_stats=structured_stats or {},
            )
            return results, usage

        if context_window <= 0:
            results = self.provider.translate_batch(uncached_texts, config)
            usage = dict(empty_usage)
            if results:
                self._accumulate_token_usage(usage, results[-1])
            return results, usage

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
        usage = dict(empty_usage)
        for result in results:
            self._accumulate_token_usage(usage, result)
        return results, usage

    def _chunk_lex_id(self, doc_index: int, chunk_index: int) -> str:
        return f"lx:{doc_index:04d}:{chunk_index:06d}"

    def _translate_uncached_chunks_structured_json(
        self,
        *,
        chunked_texts: List[str],
        uncached_indices: List[int],
        config: TranslationConfig,
        doc_index: int,
        max_payload_chars: int,
        structured_stats: Dict[str, Any],
    ) -> Tuple[List[TranslationResult], Dict[str, int]]:
        """Pack uncached chunks into JSON batches; fallback to translate_batch on failure."""
        items: List[StructuredBatchItem] = []
        for chunk_index in uncached_indices:
            prev_t = chunked_texts[chunk_index - 1] if chunk_index > 0 else ""
            next_t = (
                chunked_texts[chunk_index + 1]
                if chunk_index + 1 < len(chunked_texts)
                else ""
            )
            ctx_before = (prev_t[-120:] if prev_t else "") or None
            ctx_after = (next_t[:120] if next_t else "") or None
            items.append(
                StructuredBatchItem(
                    id=self._chunk_lex_id(doc_index, chunk_index),
                    text=chunked_texts[chunk_index],
                    context_before=ctx_before,
                    context_after=ctx_after,
                )
            )

        batches = pack_items_by_char_budget(items, max_payload_chars)
        merged: Dict[str, str] = {}
        usage_total: Dict[str, int] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        batch_counter = 0

        def _is_non_retryable_provider_error(exc: BaseException) -> bool:
            """Do not split/fallback on quota or transport errors (avoids request amplification)."""
            name = type(exc).__name__
            if name in (
                "RateLimitError",
                "APIConnectionError",
                "APITimeoutError",
                "AuthenticationError",
                "PermissionDeniedError",
            ):
                return True
            msg = str(exc).lower()
            if "insufficient_quota" in msg or "429" in msg:
                return True
            if "quota" in msg and "billing" in msg:
                return True
            return False

        def process_batch(batch: List[StructuredBatchItem]) -> None:
            nonlocal batch_counter
            if not batch:
                return
            bid = f"d{doc_index:04d}b{batch_counter}"
            batch_counter += 1
            try:
                mapping, usage = self.provider.translate_structured_batch(
                    batch,
                    batch_id=bid,
                    config=config,
                )
                merged.update(mapping)
                for key in usage_total:
                    usage_total[key] += usage.get(key, 0)
                structured_stats["structured_batches_total"] = int(
                    structured_stats.get("structured_batches_total", 0) or 0
                ) + 1
                structured_stats["structured_items_total"] = int(
                    structured_stats.get("structured_items_total", 0) or 0
                ) + len(batch)
            except Exception as exc:
                if _is_non_retryable_provider_error(exc):
                    raise
                if len(batch) > 1:
                    mid = len(batch) // 2
                    process_batch(batch[:mid])
                    process_batch(batch[mid:])
                else:
                    structured_stats["structured_fallback_batches"] = int(
                        structured_stats.get("structured_fallback_batches", 0) or 0
                    ) + 1
                    structured_stats["structured_validation_failures"] = int(
                        structured_stats.get("structured_validation_failures", 0) or 0
                    ) + 1
                    one = batch[0]
                    sub = self.provider.translate_batch([one.text], config)
                    merged[one.id] = (
                        sub[0].translated_content if sub else one.text
                    ) or one.text
                    if sub:
                        u: Dict[str, int] = {
                            "prompt_tokens": 0,
                            "completion_tokens": 0,
                            "total_tokens": 0,
                        }
                        self._accumulate_token_usage(u, sub[-1])
                        for key in usage_total:
                            usage_total[key] += u.get(key, 0)

        for batch in batches:
            process_batch(batch)

        results: List[TranslationResult] = []
        for chunk_index in uncached_indices:
            tid = self._chunk_lex_id(doc_index, chunk_index)
            translated = merged.get(tid, chunked_texts[chunk_index])
            results.append(
                TranslationResult(
                    translated_content=translated,
                    bilingual_ast=None,
                    token_usage={},
                )
            )
        return results, usage_total

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

            self._log_event(
                logging.INFO,
                "translation.epub.selection.range",
                start_doc=start_index,
                end_doc=end_index,
                doc_total=len(selected_docs),
            )

        if limit_docs is not None:
            selected_docs = selected_docs[: max(0, limit_docs)]
            self._log_event(
                logging.INFO,
                "translation.epub.selection.limit",
                limit_docs=limit_docs,
                doc_total=len(selected_docs),
            )

        return selected_docs

    def _build_cache_fingerprint(
        self,
        config: TranslationConfig,
        *,
        structured_epub_batch: bool = False,
    ) -> CacheFingerprint:
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
            chunking_version=(
                "sentence-aware-structured-v1"
                if structured_epub_batch
                else "sentence-aware-v1"
            ),
            pipeline_version=(
                "epub-structured-json-v1"
                if structured_epub_batch
                else "epub-node-v1"
            ),
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
