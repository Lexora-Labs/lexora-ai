"""
Anthropic Claude Translation Provider.

Implements BaseTranslator for Anthropic Claude models.
"""

import os
import time
import hashlib
from typing import List, Optional, Dict

from lexora.core.base_translator import (
    BaseTranslator,
    TranslationConfig,
    TranslationResult,
    BilingualAST,
    BilingualNode,
)

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None


class AnthropicProvider(BaseTranslator):
    """
    Anthropic Claude Translation Provider.
    
    Features:
    - Uses Anthropic Python SDK
    - Supports Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
    - Glossary-aware translation
    - Returns Bilingual AST
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        temperature: float = 0.2,
        debug: bool = False,
    ):
        """
        Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key (or ANTHROPIC_API_KEY env var)
            model: Model name (claude-sonnet-4-20250514, claude-3-opus-20240229, etc.)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            debug: Enable debug logging
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package not installed. Run: pip install anthropic"
            )
        
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._debug = debug
        self._client = None

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def is_configured(self) -> bool:
        return bool(self._api_key)

    def _get_client(self):
        if self._client is None:
            if not self.is_configured():
                raise ValueError(
                    "Anthropic is not configured. Set ANTHROPIC_API_KEY environment variable."
                )
            self._client = anthropic.Anthropic(api_key=self._api_key)
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
        system_msg = self.get_system_instruction(config)
        
        total_tokens: Dict[str, int] = {
            "input_tokens": 0,
            "output_tokens": 0,
        }
        
        for idx, text in enumerate(texts):
            prompt = self.build_prompt(text, config)
            translated = self._call_api_with_retry(
                client, system_msg, prompt, text, retry, sleep, total_tokens
            )
            
            node = BilingualNode(
                node_id=self._generate_node_id(text, idx),
                source_text=text,
                translated_text=translated,
            )
            
            result = TranslationResult(
                translated_content=translated,
                bilingual_ast=BilingualAST(
                    source_language=config.source_language,
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
        system_msg: str,
        prompt: str,
        text: str,
        retry: int,
        sleep: float,
        total_tokens: Dict[str, int],
    ) -> str:
        for attempt in range(retry):
            try:
                if self._debug:
                    print(f"[anthropic] model={self._model} chars={len(text)} attempt={attempt + 1}")
                
                t0 = time.time()
                response = client.messages.create(
                    model=self._model,
                    max_tokens=self._max_tokens,
                    temperature=self._temperature,
                    system=system_msg,
                    messages=[
                        {"role": "user", "content": prompt},
                    ],
                )
                
                # Extract text from response
                translated = ""
                for block in response.content:
                    if hasattr(block, 'text'):
                        translated += block.text
                translated = translated.strip()
                
                # Track token usage
                if response.usage:
                    total_tokens["input_tokens"] += response.usage.input_tokens or 0
                    total_tokens["output_tokens"] += response.usage.output_tokens or 0
                
                if self._debug:
                    print(f"[anthropic] {len(translated)} chars in {time.time() - t0:.2f}s")
                
                return translated
                
            except Exception as e:
                if self._debug:
                    print(f"[anthropic] error: {type(e).__name__}: {e}")
                
                # Handle content blocks
                if "content" in str(e).lower() and "block" in str(e).lower():
                    if self._debug:
                        print("[anthropic] Content blocked, returning original")
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
