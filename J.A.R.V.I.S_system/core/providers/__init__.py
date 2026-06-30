"""
LLM Providers - Multi-provider support via OpenAI-compatible API.

Supports:
- Ollama (local, unlimited, offline capable)
- Groq (cloud, free tier, fast inference)
- Gemini (Google, free tier, 60 req/min)
- OpenRouter (multi-model, free models available)
"""

from core.providers.base_provider import BaseProvider, ProviderResponse
from core.providers.ollama_provider import OllamaProvider
from core.providers.groq_provider import GroqProvider
from core.providers.gemini_provider import GeminiProvider
from core.providers.openrouter_provider import OpenRouterProvider

__all__ = [
    "BaseProvider",
    "ProviderResponse",
    "OllamaProvider",
    "GroqProvider",
    "GeminiProvider",
    "OpenRouterProvider",
]
