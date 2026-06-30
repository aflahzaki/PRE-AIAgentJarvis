"""
Groq Cloud Provider - Fast LLM inference via Groq API.

Uses the OpenAI-compatible API that Groq provides.
Requires GROQ_API_KEY environment variable.
Free tier with rate limits - includes rate limit awareness.
"""

import json
import logging
import os
import time
from typing import Any, Dict, Generator, List, Optional

from openai import OpenAI

from core.providers.base_provider import BaseProvider, ProviderResponse

logger = logging.getLogger(__name__)


class GroqProvider(BaseProvider):
    """Groq cloud LLM provider.

    Connects to Groq's OpenAI-compatible API for fast cloud inference.
    Includes rate limit tracking and graceful handling of missing API keys.
    """

    # Groq free tier limits (approximate)
    # Disesuaikan dengan free tier: ~30 requests/minute, ~6000 tokens/minute
    RATE_LIMIT_REQUESTS_PER_MINUTE = 30
    RATE_LIMIT_COOLDOWN_SECONDS = 60

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        """Initialize Groq provider.

        Args:
            api_key: Groq API key. Defaults to GROQ_API_KEY env var.
            base_url: Groq API base URL. Defaults to standard Groq endpoint.
        """
        super().__init__(name="groq")
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.base_url = base_url or "https://api.groq.com/openai/v1"

        # Rate limiting tracking
        self._request_timestamps = []  # type: List[float]
        self._rate_limited_until = 0.0

        # Hanya buat client jika API key tersedia
        if self.api_key and self.api_key != "your-groq-api-key-here":
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
            )
        else:
            self.client = None

    def is_available(self) -> bool:
        """Check if Groq API is configured and accessible.

        Verifies API key is present, looks valid (not a common placeholder
        or obviously malformed), and we're not rate limited.
        Does NOT make an actual API call to conserve rate limit.

        Returns:
            True if Groq is configured and not rate limited.
        """
        # Cek apakah API key sudah dikonfigurasi
        if not self.client:
            logger.debug("Groq not available: API key not configured")
            return False

        # Additional validation: reject obviously invalid keys
        # Groq API keys typically start with 'gsk_' and have reasonable length
        key = self.api_key.strip()
        if len(key) < 20:
            logger.debug("Groq not available: API key too short (likely invalid)")
            return False

        # Reject common placeholder patterns
        placeholder_patterns = [
            "your-", "insert-", "put-", "enter-", "xxx", "placeholder",
            "example", "test-key", "fake", "dummy", "change-me",
        ]
        key_lower = key.lower()
        for pattern in placeholder_patterns:
            if pattern in key_lower:
                logger.debug("Groq not available: API key appears to be a placeholder")
                return False

        # Cek apakah sedang dalam cooldown karena rate limit
        if time.time() < self._rate_limited_until:
            remaining = int(self._rate_limited_until - time.time())
            logger.debug("Groq rate limited, cooldown: %ds remaining", remaining)
            return False

        return True

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits.

        Returns:
            True if we can make a request, False if rate limited.
        """
        now = time.time()

        # Bersihkan timestamps yang sudah lebih dari 1 menit
        self._request_timestamps = [
            ts for ts in self._request_timestamps
            if now - ts < 60.0
        ]

        # Cek apakah sudah melebihi limit
        if len(self._request_timestamps) >= self.RATE_LIMIT_REQUESTS_PER_MINUTE:
            self._rate_limited_until = now + self.RATE_LIMIT_COOLDOWN_SECONDS
            return False

        return True

    def _record_request(self) -> None:
        """Record a request timestamp for rate limiting."""
        self._request_timestamps.append(time.time())

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ProviderResponse:
        """Send chat completion request to Groq API.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Groq model name (e.g., 'llama-3.3-70b-versatile').
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            ProviderResponse with generated content or error details.
        """
        if not self.client:
            return ProviderResponse(
                content="",
                model=model,
                provider=self.name,
                error="Groq API key not configured. Set GROQ_API_KEY in .env file.",
                success=False,
            )

        # Cek rate limit sebelum mengirim request
        if not self._check_rate_limit():
            return ProviderResponse(
                content="",
                model=model,
                provider=self.name,
                error="Groq rate limit reached. Please wait before retrying.",
                success=False,
            )

        try:
            self._record_request()

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            content = response.choices[0].message.content or ""
            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens or 0,
                    "completion_tokens": response.usage.completion_tokens or 0,
                    "total_tokens": response.usage.total_tokens or 0,
                }

            return ProviderResponse(
                content=content,
                model=model,
                provider=self.name,
                usage=usage,
                success=True,
            )

        except Exception as e:
            error_msg = "Groq error: {}".format(str(e))
            # Deteksi rate limit dari error response
            error_str = str(e).lower()
            if "rate" in error_str and "limit" in error_str:
                self._rate_limited_until = time.time() + self.RATE_LIMIT_COOLDOWN_SECONDS
                error_msg = "Groq rate limit hit. Cooldown active for {}s.".format(
                    self.RATE_LIMIT_COOLDOWN_SECONDS
                )
            logger.error(error_msg)
            return ProviderResponse(
                content="",
                model=model,
                provider=self.name,
                error=error_msg,
                success=False,
            )

    def get_rate_limit_status(self) -> Dict[str, object]:
        """Get current rate limit status.

        Returns:
            Dict with requests_last_minute and is_limited status.
        """
        now = time.time()
        recent = [ts for ts in self._request_timestamps if now - ts < 60.0]
        is_limited = now < self._rate_limited_until

        return {
            "requests_last_minute": len(recent),
            "max_requests_per_minute": self.RATE_LIMIT_REQUESTS_PER_MINUTE,
            "is_rate_limited": is_limited,
            "cooldown_remaining": max(0, int(self._rate_limited_until - now)) if is_limited else 0,
        }

    def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Generator[str, None, None]:
        """Stream chat completion response token by token from Groq.

        Checks rate limits before initiating the stream.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Groq model name (e.g., 'llama-3.3-70b-versatile').
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Yields:
            String tokens as they are generated.
        """
        if not self.client:
            logger.error("Groq streaming failed: API key not configured")
            yield "[Error: Groq API key not configured]"
            return

        if not self._check_rate_limit():
            logger.error("Groq streaming failed: rate limit reached")
            yield "[Error: Groq rate limit reached]"
            return

        try:
            self._record_request()
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str and "limit" in error_str:
                self._rate_limited_until = time.time() + self.RATE_LIMIT_COOLDOWN_SECONDS
            logger.error("Groq streaming error: {}".format(str(e)))
            yield "[Error: Groq streaming failed - {}]".format(str(e))

    def supports_function_calling(self) -> bool:
        """Check if Groq supports native function calling.

        Returns:
            True, as Groq supports function calling via its OpenAI-compatible API.
        """
        return True

    def chat_completion_with_tools(
        self,
        messages: List[Dict[str, str]],
        model: str,
        tools: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ProviderResponse:
        """Send chat completion request with function calling tools to Groq.

        Includes rate limit checking before making the request.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Groq model name (e.g., 'llama-3.3-70b-versatile').
            tools: List of tool definitions in OpenAI function calling format.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            ProviderResponse with generated content and/or tool_calls.
        """
        if not self.client:
            return ProviderResponse(
                content="",
                model=model,
                provider=self.name,
                error="Groq API key not configured. Set GROQ_API_KEY in .env file.",
                success=False,
            )

        if not self._check_rate_limit():
            return ProviderResponse(
                content="",
                model=model,
                provider=self.name,
                error="Groq rate limit reached. Please wait before retrying.",
                success=False,
            )

        try:
            self._record_request()

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
            )

            msg = response.choices[0].message
            content = msg.content or ""
            tool_calls_list = []

            if msg.tool_calls:
                for tc in msg.tool_calls:
                    # Store in OpenAI wire format: nested with arguments as JSON string
                    arguments_str = tc.function.arguments
                    if not isinstance(arguments_str, str):
                        arguments_str = json.dumps(arguments_str, ensure_ascii=False)
                    tool_call_dict = {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": arguments_str,
                        },
                    }
                    tool_calls_list.append(tool_call_dict)

            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens or 0,
                    "completion_tokens": response.usage.completion_tokens or 0,
                    "total_tokens": response.usage.total_tokens or 0,
                }

            return ProviderResponse(
                content=content,
                model=model,
                provider=self.name,
                usage=usage,
                success=True,
                tool_calls=tool_calls_list,
            )

        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str and "limit" in error_str:
                self._rate_limited_until = time.time() + self.RATE_LIMIT_COOLDOWN_SECONDS
            logger.warning(
                "Groq function calling failed, falling back to regular completion: {}".format(
                    str(e)
                )
            )
            return self.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
