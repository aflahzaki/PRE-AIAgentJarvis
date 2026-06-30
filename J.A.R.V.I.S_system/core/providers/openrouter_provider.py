"""
OpenRouter Provider - Multi-model LLM inference via OpenRouter API.

Uses the OpenAI-compatible endpoint that OpenRouter provides at
https://openrouter.ai/api/v1
Requires OPENROUTER_API_KEY environment variable.
Free models available including meta-llama/llama-3.3-70b-instruct:free.
"""

import json
import logging
import os
import time
from typing import Any, Dict, Generator, List, Optional

from openai import OpenAI

from core.providers.base_provider import BaseProvider, ProviderResponse

logger = logging.getLogger(__name__)


class OpenRouterProvider(BaseProvider):
    """OpenRouter LLM provider via OpenAI-compatible API.

    Connects to OpenRouter's API using the OpenAI SDK.
    Includes HTTP-Referer and X-Title headers as required by OpenRouter.
    Rate limit tracking included for responsible usage.
    """

    # OpenRouter free tier limits (conservative estimate)
    RATE_LIMIT_REQUESTS_PER_MINUTE = 20
    RATE_LIMIT_COOLDOWN_SECONDS = 60

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        """Initialize OpenRouter provider.

        Args:
            api_key: OpenRouter API key. Defaults to OPENROUTER_API_KEY env var.
            base_url: OpenRouter API base URL. Defaults to https://openrouter.ai/api/v1.
        """
        super().__init__(name="openrouter")
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = base_url or "https://openrouter.ai/api/v1"

        # Rate limiting tracking
        self._request_timestamps = []  # type: List[float]
        self._rate_limited_until = 0.0

        # OpenRouter requires additional headers
        self._extra_headers = {
            "HTTP-Referer": "https://github.com/aflahzaki/PRE-AIAgentJarvis",
            "X-Title": "J.A.R.V.I.S AI Assistant",
        }

        # Hanya buat client jika API key tersedia dan bukan placeholder
        if self.api_key and self.api_key != "your-openrouter-api-key-here":
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                default_headers=self._extra_headers,
            )
        else:
            self.client = None

    def is_available(self) -> bool:
        """Check if OpenRouter API is configured and accessible.

        Verifies API key is present, looks valid (not a common placeholder
        or obviously malformed), and we're not rate limited.
        Does NOT make an actual API call to conserve rate limit.

        Returns:
            True if OpenRouter is configured and not rate limited.
        """
        if not self.client:
            logger.debug("OpenRouter not available: API key not configured")
            return False

        # Validate key length
        key = self.api_key.strip()
        if len(key) < 20:
            logger.debug("OpenRouter not available: API key too short (likely invalid)")
            return False

        # Reject common placeholder patterns
        placeholder_patterns = [
            "your-", "insert-", "put-", "enter-", "xxx", "placeholder",
            "example", "test-key", "fake", "dummy", "change-me",
        ]
        key_lower = key.lower()
        for pattern in placeholder_patterns:
            if pattern in key_lower:
                logger.debug("OpenRouter not available: API key appears to be a placeholder")
                return False

        # Cek apakah sedang dalam cooldown karena rate limit
        if time.time() < self._rate_limited_until:
            remaining = int(self._rate_limited_until - time.time())
            logger.debug("OpenRouter rate limited, cooldown: %ds remaining", remaining)
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
        """Send chat completion request to OpenRouter API.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: OpenRouter model name (e.g., 'meta-llama/llama-3.3-70b-instruct:free').
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
                error="OpenRouter API key not configured. Set OPENROUTER_API_KEY in .env file.",
                success=False,
            )

        if not self._check_rate_limit():
            return ProviderResponse(
                content="",
                model=model,
                provider=self.name,
                error="OpenRouter rate limit reached. Please wait before retrying.",
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
            error_msg = "OpenRouter error: {}".format(str(e))
            error_str = str(e).lower()
            if "rate" in error_str and "limit" in error_str:
                self._rate_limited_until = time.time() + self.RATE_LIMIT_COOLDOWN_SECONDS
                error_msg = "OpenRouter rate limit hit. Cooldown active for {}s.".format(
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

    def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Generator[str, None, None]:
        """Stream chat completion response token by token from OpenRouter.

        Checks rate limits before initiating the stream.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: OpenRouter model name.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Yields:
            String tokens as they are generated.
        """
        if not self.client:
            logger.error("OpenRouter streaming failed: API key not configured")
            yield "[Error: OpenRouter API key not configured]"
            return

        if not self._check_rate_limit():
            logger.error("OpenRouter streaming failed: rate limit reached")
            yield "[Error: OpenRouter rate limit reached]"
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
            logger.error("OpenRouter streaming error: {}".format(str(e)))
            yield "[Error: OpenRouter streaming failed - {}]".format(str(e))

    def supports_function_calling(self) -> bool:
        """Check if OpenRouter supports native function calling.

        Returns:
            True, as OpenRouter supports function calling via its OpenAI-compatible API.
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
        """Send chat completion request with function calling tools to OpenRouter.

        Includes rate limit checking before making the request.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: OpenRouter model name.
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
                error="OpenRouter API key not configured. Set OPENROUTER_API_KEY in .env file.",
                success=False,
            )

        if not self._check_rate_limit():
            return ProviderResponse(
                content="",
                model=model,
                provider=self.name,
                error="OpenRouter rate limit reached. Please wait before retrying.",
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
                "OpenRouter function calling failed, falling back to regular completion: {}".format(
                    str(e)
                )
            )
            return self.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
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
