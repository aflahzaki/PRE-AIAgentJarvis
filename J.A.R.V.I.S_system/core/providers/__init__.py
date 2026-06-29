"""
LLM Providers - Multi-provider support via OpenAI-compatible API.

Supports:
- Ollama (local, unlimited, offline capable)
- Groq (cloud, free tier, fast inference)
"""

from core.providers.base_provider import BaseProvider, ProviderResponse
from core.providers.ollama_provider import OllamaProvider
from core.providers.groq_provider import GroqProvider

__all__ = [
    "BaseProvider",
    "ProviderResponse",
    "OllamaProvider",
    "GroqProvider",
]
