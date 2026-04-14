"""
Alibaba Qwen Translation Provider.

Implements BaseTranslator for Alibaba Qwen (Tongyi Qianwen) models.
Uses DashScope API or OpenAI-compatible endpoint.
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
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None


class QwenProvider(BaseTranslator):
    """
    Alibaba Qwen (Tongyi Qianwen) Translation Provider.
    
    Features:
    - Uses DashScope API via OpenAI-compatible interface
    - Supports Qwen-Max, Qwen-Plus, Qwen-Turbo
    - Glossary-aware translation
    - Returns Bilingual AST
    
    API Documentation:
    https://help.aliyun.com/zh/dashscope/developer-reference/compatibility-of-openai-with-dashscope
    """

    # DashScope OpenAI-compatible endpoint
    DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "qwen-max",
        base_url: Optional[str] = None,
        temperature: float = 0.2,
        debug: bool = False,
    ):
        """
        Initialize Qwen provider.
        
        Args:
            api_key: DashScope API key (or DASHSCOPE_API_KEY env var)
            model: Model name (qwen-max, qwen-plus, qwen-turbo, qwen-long)
            base_url: Custom API endpoint (defaults to DashScope)
            temperature: Sampling temperature
            debug: Enable debug logging
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai package not installed. Run: pip install openai"
            )
        
        self._api_key = api_key or os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
        self._model = model
        self._base_url = base_url or self.DASHSCOPE_BASE_URL
        self._temperature = temperature
        self._debug = debug
        self._client: Optional[OpenAI] = None
        self._logger = logging.getLogger("lexora.providers.qwen")

    @property
    def provider_name(self) -> str:
        return "qwen"

    def is_configured(self) -> bool:
        return bool(self._api_key)

    def _get_client(self) -> OpenAI:
        if self._client is None:
            if not self.is_configured():
                raise ValueError(
                    "Qwen is not configured. Set DASHSCOPE_API_KEY or QWEN_API_KEY environment variable."
                )
            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
            )
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
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
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
        client: OpenAI,
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
                    self._logger.debug(
                        "model=%s chars=%s attempt=%s",
                        self._model,
                        len(text),
                        attempt + 1,
                    )
                
                t0 = time.time()
                response = client.chat.completions.create(
                    model=self._model,
                    temperature=self._temperature,
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": prompt},
                    ],
                )
                
                translated = response.choices[0].message.content.strip()
                
                if response.usage:
                    total_tokens["prompt_tokens"] += response.usage.prompt_tokens or 0
                    total_tokens["completion_tokens"] += response.usage.completion_tokens or 0
                    total_tokens["total_tokens"] += response.usage.total_tokens or 0
                
                if self._debug:
                    self._logger.debug(
                        "translated_chars=%s elapsed_s=%.2f",
                        len(translated),
                        time.time() - t0,
                    )
                
                return translated
                
            except Exception as e:
                if self._debug:
                    self._logger.warning("error=%s: %s", type(e).__name__, e)
                
                # Handle content safety
                error_str = str(e).lower()
                if "content" in error_str and ("filter" in error_str or "safety" in error_str):
                    if self._debug:
                        self._logger.warning("content filter triggered; returning original text")
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
