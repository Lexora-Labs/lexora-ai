"""
Azure OpenAI Translation Provider.

Implements BaseTranslator for Azure OpenAI GPT models.
Extracted and refactored from azure_epub_gpt_translator.py.
"""

import os
import time
import hashlib
from typing import List, Optional, Dict, Any

from openai import AzureOpenAI

from lexora.core.base_translator import (
    BaseTranslator,
    TranslationConfig,
    TranslationResult,
    BilingualAST,
    BilingualNode,
)


class AzureOpenAIProvider(BaseTranslator):
    """
    Azure OpenAI GPT Translation Provider.
    
    Features:
    - Uses Azure OpenAI SDK
    - Supports glossary-aware translation
    - Returns both translated content and Bilingual AST
    - Retry logic with exponential backoff
    - Content filter handling
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment: Optional[str] = None,
        api_version: str = "2024-02-01",
        temperature: float = 0.2,
        debug: bool = False,
    ):
        """
        Initialize Azure OpenAI provider.
        
        Args:
            endpoint: Azure OpenAI endpoint (or AZURE_OPENAI_ENDPOINT env var)
            api_key: API key (or AZURE_OPENAI_KEY env var)
            deployment: Model deployment name (or AZURE_OPENAI_DEPLOYMENT env var)
            api_version: API version
            temperature: Sampling temperature
            debug: Enable debug logging
        """
        self._endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self._api_key = api_key or os.getenv("AZURE_OPENAI_KEY")
        self._deployment = deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
        self._api_version = api_version
        self._temperature = temperature
        self._debug = debug
        self._client: Optional[AzureOpenAI] = None

    @property
    def provider_name(self) -> str:
        return "azure_openai"

    def is_configured(self) -> bool:
        """Check if all required Azure credentials are set."""
        return bool(
            self._endpoint
            and self._api_key
            and self._deployment
        )

    def _get_client(self) -> AzureOpenAI:
        """Lazy initialization of Azure OpenAI client."""
        if self._client is None:
            if not self.is_configured():
                raise ValueError(
                    "Azure OpenAI is not configured. Set AZURE_OPENAI_ENDPOINT, "
                    "AZURE_OPENAI_KEY, and AZURE_OPENAI_DEPLOYMENT environment variables."
                )
            
            # Normalize endpoint (remove trailing /openai/v1)
            endpoint = self._normalize_endpoint(self._endpoint)
            
            self._client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=self._api_key,
                api_version=self._api_version,
            )
        return self._client

    def _normalize_endpoint(self, url: Optional[str]) -> Optional[str]:
        """Strip any trailing /openai/v1 from Azure endpoint URLs."""
        if not url:
            return url
        lowered = url.lower()
        for suffix in ("/openai/v1/", "/openai/v1"):
            if lowered.endswith(suffix):
                return url[:-len(suffix)]
        return url

    def translate_text(
        self,
        text: str,
        config: TranslationConfig,
    ) -> TranslationResult:
        """
        Translate a single text string using Azure OpenAI.
        
        Returns TranslationResult with:
        - translated_content: The translated text
        - bilingual_ast: BilingualAST with source and translation
        """
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
        """
        Translate a batch of texts using Azure OpenAI.
        
        Args:
            texts: List of source texts
            config: Translation configuration
            retry: Number of retry attempts
            sleep: Base sleep time between retries
            
        Returns:
            List of TranslationResult objects
        """
        client = self._get_client()
        results: List[TranslationResult] = []
        
        system_msg = self.get_system_instruction(config)
        
        # Prepare AST structure
        ast = BilingualAST(
            source_language=config.source_language,
            target_language=config.target_language,
            metadata={
                "provider": self.provider_name,
                "deployment": self._deployment,
                "temperature": self._temperature,
            }
        )
        
        total_tokens: Dict[str, int] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        
        for idx, text in enumerate(texts):
            prompt = self.build_prompt(text, config)
            translated = self._call_api_with_retry(
                client=client,
                system_msg=system_msg,
                prompt=prompt,
                text=text,
                retry=retry,
                sleep=sleep,
                total_tokens=total_tokens,
            )
            
            # Generate node ID
            node_id = self._generate_node_id(text, idx)
            
            # Create bilingual node
            node = BilingualNode(
                node_id=node_id,
                source_text=text,
                translated_text=translated,
            )
            ast.nodes.append(node)
            
            # Create individual result
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
        client: AzureOpenAI,
        system_msg: str,
        prompt: str,
        text: str,
        retry: int,
        sleep: float,
        total_tokens: Dict[str, int],
    ) -> str:
        """Call Azure OpenAI API with retry logic."""
        for attempt in range(retry):
            try:
                if self._debug:
                    print(
                        f"[azure_openai] chat.completions.create "
                        f"deployment={self._deployment} chars={len(text)} "
                        f"attempt={attempt + 1}"
                    )
                
                t0 = time.time()
                
                response = client.chat.completions.create(
                    model=self._deployment,
                    temperature=self._temperature,
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": prompt},
                    ],
                )
                
                translated = response.choices[0].message.content.strip()
                
                # Track token usage
                if response.usage:
                    total_tokens["prompt_tokens"] += response.usage.prompt_tokens or 0
                    total_tokens["completion_tokens"] += response.usage.completion_tokens or 0
                    total_tokens["total_tokens"] += response.usage.total_tokens or 0
                
                if self._debug:
                    dt = time.time() - t0
                    preview = translated[:160].replace("\n", " ")
                    print(
                        f"[azure_openai] response {len(translated)} chars "
                        f"in {dt:.2f}s: {preview}..."
                    )
                
                return translated
                
            except Exception as e:
                if self._debug:
                    print(f"[azure_openai] error: {type(e).__name__}: {e}")
                
                # Handle content filter errors gracefully
                error_str = str(e)
                if "content_filter" in error_str or "ResponsibleAIPolicyViolation" in error_str:
                    if self._debug:
                        print(
                            "[azure_openai] Content filter triggered, "
                            "returning original text"
                        )
                    return text
                
                # Exponential backoff
                time.sleep(sleep * (attempt + 1))
                
                if attempt == retry - 1:
                    raise
        
        return text  # Fallback

    def _generate_node_id(self, text: str, index: int) -> str:
        """Generate a unique node ID for the AST."""
        # Use hash of text content + index for reproducibility
        content_hash = hashlib.sha256(
            f"{index}:{text[:100]}".encode("utf-8")
        ).hexdigest()[:12]
        return f"node_{index}_{content_hash}"
