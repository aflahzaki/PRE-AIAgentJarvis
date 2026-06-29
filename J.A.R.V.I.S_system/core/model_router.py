"""
Model Router - Smart model selection based on task difficulty.

Analyzes user input and determines the appropriate model/provider
using keyword and heuristic-based detection. No AI needed for routing.

Difficulty Levels:
- EASY: Greetings, simple questions, casual chat
- MEDIUM: Code fixes, file operations, general technical questions
- HARD: Complex reasoning, architecture design, research tasks

Fallback Logic:
- If Ollama unavailable -> use Groq
- If Groq rate limited -> use alternative model
"""

import logging
import os
import re
from enum import Enum
from typing import Optional, Tuple

from core.providers.base_provider import BaseProvider
from core.providers.ollama_provider import OllamaProvider
from core.providers.groq_provider import GroqProvider

logger = logging.getLogger(__name__)


class Difficulty(Enum):
    """Task difficulty levels for model routing."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ModelRoute:
    """Represents a routing decision: which provider and model to use.

    Attributes:
        provider: The provider instance to use.
        model: The model name to use.
        difficulty: The assessed difficulty level.
        reason: Brief explanation of why this route was chosen.
    """

    def __init__(
        self,
        provider: BaseProvider,
        model: str,
        difficulty: Difficulty,
        reason: str = "",
    ) -> None:
        self.provider = provider
        self.model = model
        self.difficulty = difficulty
        self.reason = reason

    def __repr__(self) -> str:
        return "ModelRoute(provider='{}', model='{}', difficulty={})".format(
            self.provider.name, self.model, self.difficulty.value
        )


class ModelRouter:
    """Smart model router with difficulty-based selection and fallback.

    Analyzes user input to determine task difficulty, then selects
    the most appropriate provider and model. Implements fallback
    logic for when preferred providers are unavailable.
    """

    # Keyword patterns untuk klasifikasi difficulty
    # Pattern EASY: sapaan, pertanyaan sederhana, obrolan ringan
    EASY_PATTERNS = [
        r"\b(halo|hai|hello|hi|hey|selamat|good morning|good night)\b",
        r"\b(terima kasih|thanks|thank you|makasih)\b",
        r"\b(apa kabar|how are you|siapa kamu|who are you)\b",
        r"\b(bye|goodbye|sampai jumpa|dadah)\b",
        r"^.{0,20}$",  # Pesan sangat pendek (< 20 karakter)
    ]

    # Pattern HARD: reasoning kompleks, arsitektur, research, analisis mendalam
    HARD_PATTERNS = [
        r"\b(architect|architecture|arsitektur|microservice|distributed)\b",
        r"\b(design pattern|system design|scalab|optimiz)\b",
        r"\b(research|riset|analisis mendalam|deep analysis)\b",
        r"\b(compare|bandingkan|pro.?(?:and|&|dan).?con|trade.?off)\b",
        r"\b(explain in detail|jelaskan detail|comprehensive)\b",
        r"\b(refactor|restructure|redesign|overhaul)\b",
        r"\b(security audit|vulnerability|threat model)\b",
        r"\b(algorithm|complexity|big.?o|mathematical)\b",
        r"\b(machine learning|deep learning|neural network|AI model)\b",
        r"\b(strateg|roadmap|planning|rencana besar)\b",
    ]

    # Pattern MEDIUM: coding, file ops, pertanyaan teknis umum
    MEDIUM_PATTERNS = [
        r"\b(fix|bug|error|perbaiki|debug|repair)\b",
        r"\b(code|kode|script|program|function|fungsi)\b",
        r"\b(file|folder|directory|buat|create|tulis|write)\b",
        r"\b(install|setup|config|setting|configure)\b",
        r"\b(explain|jelaskan|how to|cara|gimana|bagaimana)\b",
        r"\b(test|testing|unit test|validat)\b",
        r"\b(api|database|server|deploy|docker)\b",
        r"\b(python|javascript|java|rust|go|sql)\b",
    ]

    def __init__(self) -> None:
        """Initialize the model router with providers."""
        # Inisialisasi providers
        self.ollama = OllamaProvider()
        self.groq = GroqProvider()

        # Konfigurasi model dari environment variables
        self.ollama_model_small = os.getenv("OLLAMA_MODEL_SMALL", "llama3.2:3b")
        self.ollama_model_medium = os.getenv("OLLAMA_MODEL_MEDIUM", "qwen2.5-coder:7b")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        # Cache status ketersediaan provider
        self._ollama_available = None  # type: Optional[bool]
        self._groq_available = None  # type: Optional[bool]

    def classify_difficulty(self, user_input: str) -> Tuple[Difficulty, str]:
        """Classify the difficulty of a user's request.

        Uses keyword/heuristic-based detection to determine task complexity.
        No AI inference needed for this classification.

        Args:
            user_input: The user's input text.

        Returns:
            Tuple of (Difficulty level, reason string).
        """
        text = user_input.lower().strip()

        # Cek pattern EASY terlebih dahulu
        for pattern in self.EASY_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                # Pastikan bukan false positive - pesan pendek tapi teknis
                is_technical = any(
                    re.search(p, text, re.IGNORECASE)
                    for p in self.MEDIUM_PATTERNS + self.HARD_PATTERNS
                )
                if not is_technical:
                    return Difficulty.EASY, "Simple greeting or short message"

        # Cek pattern HARD
        for pattern in self.HARD_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return Difficulty.HARD, "Complex task requiring advanced reasoning"

        # Cek pattern MEDIUM
        for pattern in self.MEDIUM_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return Difficulty.MEDIUM, "Technical task of moderate complexity"

        # Default: MEDIUM untuk input yang tidak terklasifikasi
        # Lebih baik over-estimate daripada under-estimate
        if len(text) > 100:
            return Difficulty.MEDIUM, "Long input, defaulting to medium complexity"

        return Difficulty.EASY, "Short unclassified input, defaulting to easy"

    def check_providers(self) -> None:
        """Refresh provider availability status."""
        self._ollama_available = self.ollama.is_available()
        self._groq_available = self.groq.is_available()
        logger.info(
            "Provider status - Ollama: %s, Groq: %s",
            "available" if self._ollama_available else "unavailable",
            "available" if self._groq_available else "unavailable",
        )

    def route(self, user_input: str) -> ModelRoute:
        """Route a user request to the appropriate provider and model.

        Analyzes difficulty, selects preferred provider/model, and applies
        fallback logic if the preferred option is unavailable.

        Args:
            user_input: The user's input text.

        Returns:
            ModelRoute with the selected provider, model, and difficulty.
        """
        difficulty, reason = self.classify_difficulty(user_input)

        # Cek ketersediaan provider jika belum dicek
        if self._ollama_available is None:
            self._ollama_available = self.ollama.is_available()
        if self._groq_available is None:
            self._groq_available = self.groq.is_available()

        # Routing berdasarkan difficulty
        if difficulty == Difficulty.EASY:
            return self._route_easy(difficulty, reason)
        elif difficulty == Difficulty.MEDIUM:
            return self._route_medium(difficulty, reason)
        else:
            return self._route_hard(difficulty, reason)

    def _route_easy(self, difficulty: Difficulty, reason: str) -> ModelRoute:
        """Route EASY tasks to small local model.

        Fallback: Ollama medium -> Groq if all local unavailable.
        """
        # Preferensi: Ollama small model (hemat resource)
        if self._ollama_available:
            return ModelRoute(
                provider=self.ollama,
                model=self.ollama_model_small,
                difficulty=difficulty,
                reason=reason,
            )

        # Fallback ke Groq jika Ollama tidak tersedia
        if self._groq_available:
            return ModelRoute(
                provider=self.groq,
                model=self.groq_model,
                difficulty=difficulty,
                reason="{} (fallback: Ollama unavailable)".format(reason),
            )

        # Tidak ada provider yang tersedia
        return self._no_provider_route(difficulty, reason)

    def _route_medium(self, difficulty: Difficulty, reason: str) -> ModelRoute:
        """Route MEDIUM tasks to medium local model.

        Fallback: Groq if local model unavailable.
        """
        # Preferensi: Ollama medium model
        if self._ollama_available:
            return ModelRoute(
                provider=self.ollama,
                model=self.ollama_model_medium,
                difficulty=difficulty,
                reason=reason,
            )

        # Fallback ke Groq
        if self._groq_available:
            return ModelRoute(
                provider=self.groq,
                model=self.groq_model,
                difficulty=difficulty,
                reason="{} (fallback: Ollama unavailable)".format(reason),
            )

        return self._no_provider_route(difficulty, reason)

    def _route_hard(self, difficulty: Difficulty, reason: str) -> ModelRoute:
        """Route HARD tasks to powerful cloud model.

        Fallback: Ollama medium if cloud unavailable.
        """
        # Preferensi: Groq (model besar untuk task kompleks)
        if self._groq_available:
            return ModelRoute(
                provider=self.groq,
                model=self.groq_model,
                difficulty=difficulty,
                reason=reason,
            )

        # Fallback ke Ollama medium (lebih baik daripada tidak ada)
        if self._ollama_available:
            return ModelRoute(
                provider=self.ollama,
                model=self.ollama_model_medium,
                difficulty=difficulty,
                reason="{} (fallback: Groq unavailable, using local model)".format(reason),
            )

        return self._no_provider_route(difficulty, reason)

    def _no_provider_route(self, difficulty: Difficulty, reason: str) -> ModelRoute:
        """Create a route when no providers are available.

        Returns Ollama as default (will fail gracefully at execution time).
        """
        logger.warning("No providers available! Returning Ollama as default.")
        return ModelRoute(
            provider=self.ollama,
            model=self.ollama_model_medium,
            difficulty=difficulty,
            reason="{} (WARNING: No providers available)".format(reason),
        )

    def get_status(self) -> dict:
        """Get current router and provider status.

        Returns:
            Dict with provider availability and configuration info.
        """
        return {
            "ollama": {
                "available": self._ollama_available,
                "base_url": self.ollama.base_url,
                "model_small": self.ollama_model_small,
                "model_medium": self.ollama_model_medium,
            },
            "groq": {
                "available": self._groq_available,
                "model": self.groq_model,
                "rate_limit": self.groq.get_rate_limit_status(),
            },
        }
