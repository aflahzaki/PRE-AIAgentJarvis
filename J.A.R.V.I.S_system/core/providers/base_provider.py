"""
Abstract Base Provider for LLM interactions.

All providers (Ollama, Groq, etc.) implement this interface,
ensuring consistent behavior across different backends.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Optional


@dataclass
class ProviderResponse:
    """Structured response from an LLM provider.

    Attributes:
        content: The generated text content.
        model: The model that generated the response.
        provider: Name of the provider (e.g., 'ollama', 'groq').
        usage: Token usage information if available.
        error: Error message if the request failed.
        success: Whether the request completed successfully.
    """

    content: str = ""
    model: str = ""
    provider: str = ""
    usage: Dict[str, int] = field(default_factory=dict)
    error: Optional[str] = None
    success: bool = True
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)


class BaseProvider(ABC):
    """Abstract base class for LLM providers.

    All providers must implement chat_completion() and is_available().
    This ensures a uniform interface regardless of backend (Ollama, Groq, etc.).
    """

    def __init__(self, name: str) -> None:
        """Initialize provider with a name identifier.

        Args:
            name: Human-readable provider name (e.g., 'ollama', 'groq').
        """
        self.name = name

    @abstractmethod
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ProviderResponse:
        """Send a chat completion request to the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Model identifier to use for generation.
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum number of tokens to generate.

        Returns:
            ProviderResponse with the generated content or error details.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is reachable and operational.

        Returns:
            True if the provider can accept requests, False otherwise.
        """
        pass

    @abstractmethod
    def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Generator[str, None, None]:
        """Stream a chat completion response token by token.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Model identifier to use for generation.
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum number of tokens to generate.

        Yields:
            String tokens as they are generated.
        """
        pass

    def supports_function_calling(self) -> bool:
        """Check if the provider supports native function calling.

        Returns:
            True if the provider supports function calling, False otherwise.
        """
        return False

    def chat_completion_with_tools(
        self,
        messages: List[Dict[str, str]],
        model: str,
        tools: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ProviderResponse:
        """Send a chat completion request with function calling tools.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Model identifier to use for generation.
            tools: List of tool definitions in OpenAI function calling format.
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum number of tokens to generate.

        Returns:
            ProviderResponse with generated content and/or tool_calls.
        """
        return self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def __repr__(self) -> str:
        return "{}(name='{}')".format(self.__class__.__name__, self.name)
