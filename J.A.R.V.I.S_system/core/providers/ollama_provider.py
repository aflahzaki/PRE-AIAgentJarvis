"""
Ollama Provider - Local LLM inference via Ollama.

Uses the OpenAI-compatible API that Ollama exposes at /v1.
No API key needed. Supports unlimited requests, works offline.
Ideal for CPU-only inference on local hardware.
"""

import json
import logging
import os
from typing import Any, Dict, Generator, List, Optional

from openai import OpenAI

from core.providers.base_provider import BaseProvider, ProviderResponse

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    """Ollama local LLM provider.

    Connects to a local Ollama instance via its OpenAI-compatible API.
    Gracefully handles cases where Ollama is not installed or running.
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        """Initialize Ollama provider.

        Args:
            base_url: Ollama API base URL. Defaults to OLLAMA_BASE_URL env var
                      or http://localhost:11434/v1.
        """
        super().__init__(name="ollama")
        self.base_url = base_url or os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434/v1"
        )
        # Ollama tidak memerlukan API key, tapi OpenAI SDK butuh value non-empty
        self.client = OpenAI(
            base_url=self.base_url,
            api_key="ollama",  # Dummy key, Ollama tidak memvalidasi ini
        )
        self._available = None  # Cache status, None = belum dicek

    def is_available(self) -> bool:
        """Check if Ollama server is running and reachable.

        Attempts to list models from the Ollama server.
        Returns False gracefully if server is unreachable.

        Returns:
            True if Ollama server responds, False otherwise.
        """
        try:
            # Coba list models sebagai health check
            self.client.models.list()
            self._available = True
            return True
        except Exception as e:
            logger.debug("Ollama not available: %s", str(e))
            self._available = False
            return False

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ProviderResponse:
        """Send chat completion request to local Ollama instance.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Ollama model name (e.g., 'llama3.2:3b', 'qwen2.5-coder:7b').
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            ProviderResponse with generated content or error details.
        """
        try:
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
            error_msg = "Ollama error: {}".format(str(e))
            logger.error(error_msg)
            return ProviderResponse(
                content="",
                model=model,
                provider=self.name,
                error=error_msg,
                success=False,
            )

    def list_models(self) -> List[str]:
        """List available models on the local Ollama instance.

        Returns:
            List of model names, or empty list if unavailable.
        """
        try:
            models = self.client.models.list()
            return [m.id for m in models.data]
        except Exception as e:
            logger.debug("Cannot list Ollama models: %s", str(e))
            return []

    def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Generator[str, None, None]:
        """Stream chat completion response token by token from Ollama.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Ollama model name (e.g., 'llama3.2:3b', 'qwen2.5-coder:7b').
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Yields:
            String tokens as they are generated.
        """
        try:
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
            logger.error("Ollama streaming error: {}".format(str(e)))
            yield "[Error: Ollama streaming failed - {}]".format(str(e))

    def supports_function_calling(self) -> bool:
        """Check if Ollama supports native function calling.

        Returns:
            True, as Ollama supports function calling via its OpenAI-compatible API.
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
        """Send chat completion request with function calling tools to Ollama.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Ollama model name (e.g., 'llama3.2:3b', 'qwen2.5-coder:7b').
            tools: List of tool definitions in OpenAI function calling format.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            ProviderResponse with generated content and/or tool_calls.
        """
        try:
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
            logger.warning(
                "Ollama function calling failed, falling back to regular completion: {}".format(
                    str(e)
                )
            )
            return self.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
