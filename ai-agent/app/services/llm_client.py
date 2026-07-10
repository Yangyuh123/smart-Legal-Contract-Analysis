"""LLM Client - DeepSeek API wrapper using OpenAI SDK.

Provides chat completion, streaming, and embedding capabilities
with built-in error handling, retries, and structured output support.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Optional, List, Dict, Any, Generator, Union

from openai import OpenAI, APIError, RateLimitError, APIConnectionError, APITimeoutError

from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """DeepSeek LLM API client wrapper with error handling and retries."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize the LLM client.

        Args:
            api_key: DeepSeek API key (defaults to settings.DEEPSEEK_API_KEY)
            base_url: API base URL (defaults to settings.DEEPSEEK_BASE_URL)
            model: Model name (defaults to settings.DEEPSEEK_MODEL)
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries (exponential backoff)
        """
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.base_url = base_url or settings.DEEPSEEK_BASE_URL
        self.model = model or settings.DEEPSEEK_MODEL
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self._api_key_valid = bool(self.api_key)
        if not self._api_key_valid:
            logger.warning("DEEPSEEK_API_KEY is not set. LLM calls will fail.")
            # Use a placeholder to avoid OpenAI init error; calls will fail with clear message
            self.api_key = "dummy-key-not-configured"

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=120.0,
            max_retries=0,  # We handle retries ourselves
        )

    def _check_api_key(self):
        """Raise error if API key is not configured."""
        if not self._api_key_valid:
            raise RuntimeError(
                "DeepSeek API密钥未配置。请设置环境变量 DEEPSEEK_API_KEY 或在 .env 文件中配置。"
            )

    def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute a function with exponential backoff retry."""
        self._check_api_key()
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except RateLimitError as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Rate limit hit, retrying in {wait:.1f}s (attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(wait)
            except (APIConnectionError, APITimeoutError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Connection/timeout error, retrying in {wait:.1f}s (attempt {attempt + 1}/{self.max_retries}): {e}"
                    )
                    time.sleep(wait)
            except APIError as e:
                # Non-retryable API errors (e.g., 400 bad request)
                logger.error(f"API error (non-retryable): {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise

        raise last_exception  # type: ignore

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: Optional[Dict[str, str]] = None,
        top_p: float = 0.95,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to DeepSeek.

        Args:
            messages: List of message dicts [{"role": "system/user/assistant", "content": "..."}]
            model: Model override
            temperature: Sampling temperature (0-2), lower = more deterministic
            max_tokens: Maximum tokens in response
            response_format: e.g. {"type": "json_object"} for structured output
            top_p: Nucleus sampling parameter

        Returns:
            API response dict with keys: content, model, usage (prompt_tokens, completion_tokens, total_tokens)

        Raises:
            Exception: On API error after all retries exhausted
        """
        def _call():
            params = {
                "model": model or self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
            }
            if response_format:
                params["response_format"] = response_format

            params.update(kwargs)

            logger.debug(f"Chat completion: model={params['model']}, messages_count={len(messages)}")
            start_time = time.time()

            response = self.client.chat.completions.create(**params)

            elapsed = time.time() - start_time
            choice = response.choices[0]
            content = choice.message.content or ""

            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            logger.debug(
                f"Chat completion done in {elapsed:.2f}s, "
                f"tokens: {usage.get('total_tokens', 'N/A')}, "
                f"finish_reason: {choice.finish_reason}"
            )

            return {
                "content": content,
                "model": response.model,
                "finish_reason": choice.finish_reason,
                "usage": usage,
            }

        return self._retry_with_backoff(_call)

    def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        top_p: float = 0.95,
        **kwargs,
    ):
        """
        Stream a chat completion from DeepSeek.

        Yields content chunks as they arrive.

        Args:
            messages: List of message dicts
            model: Model override
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            top_p: Nucleus sampling parameter

        Yields:
            str chunks of response content
        """
        def _stream():
            params = {
                "model": model or self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
                "stream": True,
            }
            params.update(kwargs)

            logger.debug(f"Streaming chat: model={params['model']}, messages_count={len(messages)}")
            start_time = time.time()

            stream = self.client.chat.completions.create(**params)
            chunk_count = 0

            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        chunk_count += 1
                        yield delta.content

            elapsed = time.time() - start_time
            logger.debug(f"Stream done in {elapsed:.2f}s, chunks={chunk_count}")

        try:
            yield from _stream()
        except RateLimitError as e:
            logger.error(f"Rate limit during streaming: {e}")
            yield f"\n\n[流式输出中断：API速率限制 - {str(e)}]"
        except (APIConnectionError, APITimeoutError) as e:
            logger.error(f"Connection error during streaming: {e}")
            yield f"\n\n[流式输出中断：连接错误 - {str(e)}]"
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"\n\n[流式输出中断：{str(e)}]"

    def chat_completion_structured(
        self,
        messages: List[Dict[str, str]],
        output_schema: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Send a chat completion and parse JSON response.

        Args:
            messages: Message list
            output_schema: Expected JSON schema description (for logging)
            model: Model override
            temperature: Lower temperature for structured output
            max_tokens: Max tokens

        Returns:
            Parsed JSON dict

        Raises:
            ValueError: If response is not valid JSON
        """
        response = self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            **kwargs,
        )

        content = response["content"].strip()

        # DeepSeek sometimes wraps JSON in markdown code blocks
        if content.startswith("```"):
            # Remove ```json ... ``` wrapping
            content = content.split("\n", 1)[-1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

        try:
            parsed = json.loads(content)
            response["parsed"] = parsed
            return response
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw content: {content[:500]}...")
            # Attempt to extract JSON from the content
            extracted = self._extract_json(content)
            if extracted:
                response["parsed"] = extracted
                return response
            raise ValueError(f"Response is not valid JSON: {content[:200]}")

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Attempt to extract a JSON object from text that may contain extra content."""
        # Find the first { and last }
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
        return None

    def get_embeddings(
        self,
        texts: Union[str, List[str]],
        model: Optional[str] = None,
    ) -> List[List[float]]:
        """
        Get embeddings for one or more texts.

        Args:
            texts: Single text string or list of text strings
            model: Embedding model name (default: configured model or fallback)

        Returns:
            List of embedding vectors (each is a list of floats)

        Raises:
            Exception: On API error
        """
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            return []

        embed_model = model or getattr(settings, "DEEPSEEK_EMBEDDING_MODEL", "deepseek-chat")

        def _call():
            logger.debug(f"Getting embeddings for {len(texts)} texts, model={embed_model}")
            start_time = time.time()

            response = self.client.embeddings.create(
                model=embed_model,
                input=texts,
            )

            elapsed = time.time() - start_time
            embeddings = [item.embedding for item in response.data]
            logger.debug(f"Embeddings done in {elapsed:.2f}s, dim={len(embeddings[0]) if embeddings else 0}")
            return embeddings

        return self._retry_with_backoff(_call)

    def get_single_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """
        Get embedding for a single text.

        Args:
            text: Input text
            model: Model override

        Returns:
            Embedding vector
        """
        results = self.get_embeddings(text, model=model)
        return results[0] if results else []


# Module-level singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create the singleton LLMClient instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
