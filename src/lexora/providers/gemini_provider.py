"""
Google Gemini Translation Provider.

Implements BaseTranslator for Google Gemini models.
"""

import os
import time
import hashlib
import logging
from typing import List, Optional, Dict

from lexora.core.base_translator import (
    BaseTranslator,
    TranslationConfig,
    TranslationResult,
    BilingualAST,
    BilingualNode,
)

try:
    from google import genai
    from google.genai import types as genai_types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    genai_types = None


class GeminiProvider(BaseTranslator):
    """
    Google Gemini Translation Provider.
    
    Features:
    - Uses Google Generative AI SDK
    - Supports Gemini Pro, Gemini 1.5
    - Glossary-aware translation
    - Returns Bilingual AST
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-pro",
        temperature: float = 0.2,
        debug: bool = False,
    ):
        """
        Initialize Gemini provider.
        
        Args:
            api_key: Google AI API key (or GOOGLE_API_KEY env var)
            model: Model name (gemini-1.5-pro, gemini-1.5-flash, gemini-pro)
            temperature: Sampling temperature
            debug: Enable debug logging
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-genai package not installed. "
                "Run: pip install google-genai"
            )
        
        self._api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self._model_name = model
        self._temperature = temperature
        self._debug = debug
        self._client = None
        self._logger = logging.getLogger("lexora.providers.gemini")

    @property
    def provider_name(self) -> str:
        return "gemini"

    def is_configured(self) -> bool:
        return bool(self._api_key)

    def _get_client(self):
        if self._client is None:
            if not self.is_configured():
                raise ValueError(
                    "Gemini is not configured. Set GOOGLE_API_KEY environment variable."
                )
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def translate_text(
        self,
        text: str,
        config: TranslationConfig,
    ) -> TranslationResult:
        results = self.translate_batch([text], config)
        return results[0] if results else TranslationResult(
            translated_content=text,
            bilingual_ast=None,
        )

    def translate_batch(
        self,
        texts: List[str],
        config: TranslationConfig,
        retry: int = 3,
        sleep: float = 1.0,
    ) -> List[TranslationResult]:
        client = self._get_client()
        results: List[TranslationResult] = []
        system_instruction = self.get_system_instruction(config)
        
        total_tokens: Dict[str, int] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        
        for idx, text in enumerate(texts):
            prompt = self.build_prompt(text, config)
            full_prompt = f"{system_instruction}\n\n{prompt}"
            
            translated = self._call_api_with_retry(
                client, full_prompt, text, retry, sleep, total_tokens
            )
            
            node = BilingualNode(
                node_id=self._generate_node_id(text, idx),
                source_text=text,
                translated_text=translated,
            )
            
            result = TranslationResult(
                translated_content=translated,
                bilingual_ast=BilingualAST(
                    source_language=config.source_language or "",
                    target_language=config.target_language,
                    nodes=[node],
                ),
                token_usage=dict(total_tokens),
            )
            results.append(result)
        
        return results

    def _call_api_with_retry(
        self,
        client,
        prompt: str,
        text: str,
        retry: int,
        sleep: float,
        total_tokens: Dict[str, int],
    ) -> str:
        for attempt in range(retry):
            try:
                if self._debug:
                    self._logger.debug(
                        "provider.request.started provider=gemini model=%s chars=%s attempt=%s",
                        self._model_name,
                        len(text),
                        attempt + 1,
                    )
                
                t0 = time.time()
                response = client.models.generate_content(
                    model=self._model_name,
                    contents=prompt,
                    config=genai_types.GenerateContentConfig(
                        temperature=self._temperature,
                    ),
                )

                translated = (getattr(response, "text", None) or "").strip()
                if not translated:
                    candidates = getattr(response, "candidates", None) or []
                    first_candidate = candidates[0] if candidates else None
                    content = getattr(first_candidate, "content", None)
                    parts = getattr(content, "parts", None) or []
                    text_parts = [
                        getattr(part, "text", "")
                        for part in parts
                        if getattr(part, "text", None)
                    ]
                    translated = "".join(text_parts).strip()
                if not translated:
                    translated = text
                
                # Track token usage if available
                if hasattr(response, 'usage_metadata'):
                    usage = response.usage_metadata
                    total_tokens["prompt_tokens"] += getattr(usage, 'prompt_token_count', 0)
                    total_tokens["completion_tokens"] += getattr(usage, 'candidates_token_count', 0)
                    total_tokens["total_tokens"] += getattr(usage, 'total_token_count', 0)
                
                if self._debug:
                    self._logger.debug(
                        "provider.request.completed provider=gemini model=%s chars=%s elapsed_ms=%s",
                        self._model_name,
                        len(translated),
                        round((time.time() - t0) * 1000),
                    )
                
                return translated
                
            except Exception as e:
                if self._debug:
                    self._logger.exception(
                        "provider.request.failed provider=gemini model=%s error_type=%s",
                        self._model_name,
                        type(e).__name__,
                    )
                
                # Handle safety blocks
                if "blocked" in str(e).lower() or "safety" in str(e).lower():
                    if self._debug:
                        self._logger.warning(
                            "provider.request.blocked provider=gemini model=%s reason=safety_filter",
                            self._model_name,
                        )
                    return text
                
                time.sleep(sleep * (attempt + 1))
                if attempt == retry - 1:
                    raise
        
        return text

    def _generate_node_id(self, text: str, index: int) -> str:
        content_hash = hashlib.sha256(
            f"{index}:{text[:100]}".encode("utf-8")
        ).hexdigest()[:12]
        return f"node_{index}_{content_hash}"
