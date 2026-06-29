"""
Orchestrator - The brain of J.A.R.V.I.S system.

Receives user input, classifies the task, routes to the appropriate agent,
and manages the conversation flow. Serves as the single entry point for
all interactions.

Routing Logic:
- Code/file tasks -> CoderAgent
- Research/analysis tasks -> ResearcherAgent
- Simple queries -> Direct LLM response (no agent overhead)

Features:
- Conversation memory across turns
- Intelligent model/provider selection via ModelRouter
- Graceful fallback when providers are unavailable
- JARVIS personality: calm, helpful, honest, never fabricates
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

from core.agents.coder_agent import CoderAgent
from core.agents.researcher_agent import ResearcherAgent
from core.memory.conversation import ConversationMemory
from core.model_router import Difficulty, ModelRoute, ModelRouter
from core.providers.base_provider import BaseProvider, ProviderResponse

logger = logging.getLogger(__name__)


class Orchestrator:
    """Main orchestrator for J.A.R.V.I.S system.

    Coordinates between user input, model routing, agents, and memory.
    Determines the best approach for each request and delegates accordingly.
    """

    # Keyword patterns untuk mendeteksi tipe task
    # Pattern: code/file related tasks
    CODE_PATTERNS = [
        r"\b(code|kode|coding|program|script)\b",
        r"\b(file|buat file|create file|write file|tulis file)\b",
        r"\b(debug|fix bug|perbaiki|error|traceback)\b",
        r"\b(function|fungsi|class|method|module|import)\b",
        r"\b(python|javascript|java|rust|go|sql|html|css)\b",
        r"\b(execute|run|jalankan|eksekusi)\b",
        r"\b(edit|modify|ubah|ganti|replace)\b",
        r"\b(install|pip|npm|package|dependency)\b",
        r"\b(compile|build|deploy)\b",
        r"\b(variable|variabel|loop|if.?else|for|while)\b",
        r"\b(read_file|write_file|list_files)\b",
    ]

    # Pattern: research/analysis tasks
    RESEARCH_PATTERNS = [
        r"\b(research|riset|analisis|analysis|analyze)\b",
        r"\b(compare|bandingkan|versus|vs)\b",
        r"\b(explain in detail|jelaskan detail|comprehensive)\b",
        r"\b(pro.?(?:and|&|dan).?con|trade.?off|kelebihan.?kekurangan)\b",
        r"\b(architect|architecture|arsitektur|design pattern)\b",
        r"\b(strateg|roadmap|planning|rencana)\b",
        r"\b(evaluate|evaluasi|assess|review mendalam)\b",
        r"\b(theory|teori|concept|konsep|principle|prinsip)\b",
        r"\b(security|keamanan|vulnerability|threat)\b",
        r"\b(scalab|optimiz|performance|performa)\b",
        r"\b(machine learning|deep learning|AI|neural)\b",
        r"\b(algorithm|algoritma|complexity|kompleksitas)\b",
    ]

    def __init__(self, memory_size: int = 50) -> None:
        """Initialize the Orchestrator.

        Sets up the model router, conversation memory, and checks
        provider availability.

        Args:
            memory_size: Maximum messages to keep in conversation buffer.
        """
        # Inisialisasi model router (manages providers)
        self.router = ModelRouter()

        # Conversation memory untuk konteks antar-turn
        self.memory = ConversationMemory(max_messages=memory_size)

        # Cache agents - dibuat on-demand saat pertama kali dibutuhkan
        self._coder_agent = None  # type: Optional[CoderAgent]
        self._researcher_agent = None  # type: Optional[ResearcherAgent]

        # Cek ketersediaan provider saat startup
        self.router.check_providers()

        logger.info("Orchestrator initialized. Provider status: %s", self.get_status())

    def classify_task(self, user_input: str) -> str:
        """Classify user input into task type for agent routing.

        Uses a score-based approach that also considers the ModelRouter's
        difficulty classification to avoid disagreement between the two
        classifiers. For example, 'explain python decorators' should not
        go to the coder agent just because it mentions 'python' - if the
        difficulty classifier sees it as a reasoning task, research is
        more appropriate.

        Task types:
        - 'code': Code writing, debugging, file manipulation
        - 'research': Complex analysis, comparison, deep reasoning
        - 'simple': Greetings, simple questions, casual chat

        Args:
            user_input: The user's input text.

        Returns:
            Task type string: 'code', 'research', or 'simple'.
        """
        text = user_input.lower().strip()

        # Hitung score untuk setiap kategori
        code_score = 0
        research_score = 0

        for pattern in self.CODE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                code_score += 1

        for pattern in self.RESEARCH_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                research_score += 1

        # Consult the difficulty classifier for coherence check.
        # If difficulty is HARD and research_score > 0, favor research
        # to avoid sending conceptual questions to the coder agent
        # just because they mention a programming language.
        difficulty, _ = self.router.classify_difficulty(user_input)

        if difficulty == Difficulty.HARD and research_score > 0:
            # HARD + any research signal -> research agent (better reasoning)
            return "research"

        # Strong code signals: action verbs indicating code manipulation
        # These patterns indicate the user wants actual code work, not explanation
        ACTION_CODE_PATTERNS = [
            r"\b(buat file|create file|write file|tulis file)\b",
            r"\b(debug|fix bug|perbaiki|traceback)\b",
            r"\b(execute|run|jalankan|eksekusi)\b",
            r"\b(edit|modify|ubah|ganti|replace)\b",
            r"\b(compile|build|deploy)\b",
            r"\b(install|pip|npm)\b",
            r"\b(read_file|write_file|list_files)\b",
        ]
        strong_code_score = sum(
            1 for p in ACTION_CODE_PATTERNS
            if re.search(p, text, re.IGNORECASE)
        )

        # Routing decision berdasarkan score
        if strong_code_score >= 1:
            # Strong code action verb present -> definitely code
            return "code"
        elif research_score > code_score and research_score >= 1:
            return "research"
        elif code_score > research_score and code_score >= 1:
            return "code"
        elif research_score >= 1:
            return "research"
        elif code_score >= 1:
            return "code"

        # Default: simple task (direct LLM response)
        return "simple"

    def _get_coder_agent(self, route: ModelRoute) -> CoderAgent:
        """Get or create a CoderAgent with the given route's provider/model.

        Args:
            route: ModelRoute with provider and model selection.

        Returns:
            Configured CoderAgent instance.
        """
        # Buat agent baru jika belum ada atau provider/model berubah
        if (
            self._coder_agent is None
            or self._coder_agent.provider != route.provider
            or self._coder_agent.model != route.model
        ):
            self._coder_agent = CoderAgent(
                provider=route.provider,
                model=route.model,
            )
        return self._coder_agent

    def _get_researcher_agent(self, route: ModelRoute) -> ResearcherAgent:
        """Get or create a ResearcherAgent with the given route's provider/model.

        Args:
            route: ModelRoute with provider and model selection.

        Returns:
            Configured ResearcherAgent instance.
        """
        if (
            self._researcher_agent is None
            or self._researcher_agent.provider != route.provider
            or self._researcher_agent.model != route.model
        ):
            self._researcher_agent = ResearcherAgent(
                provider=route.provider,
                model=route.model,
            )
        return self._researcher_agent

    def _direct_llm_response(
        self, user_input: str, route: ModelRoute
    ) -> str:
        """Get a direct LLM response without agent overhead.

        Used for simple queries that don't need tool calling or
        specialized agent logic.

        Args:
            user_input: The user's message.
            route: ModelRoute with provider and model selection.

        Returns:
            LLM response string.
        """
        # Build messages dengan system prompt JARVIS
        system_prompt = (
            "You are J.A.R.V.I.S, a calm, helpful, and honest AI assistant.\n\n"
            "Core traits:\n"
            "- Jujur: Jika tidak tahu, katakan 'Saya tidak yakin' - jangan mengarang\n"
            "- Helpful: Berikan jawaban yang ringkas dan berguna\n"
            "- Humble: Akui keterbatasan dengan jujur\n\n"
            "Respond naturally and concisely. Use Indonesian or English depending "
            "on the user's language."
        )

        messages = [{"role": "system", "content": system_prompt}]

        # Tambahkan context dari memory jika ada
        history = self.memory.get_messages(include_summary=True)
        # Ambil beberapa pesan terakhir untuk context
        recent = history[-6:] if len(history) > 6 else history
        messages.extend(recent)

        # User message saat ini
        messages.append({"role": "user", "content": user_input})

        # Panggil provider
        response = route.provider.chat_completion(
            messages=messages,
            model=route.model,
            temperature=0.7,
            max_tokens=1024,
        )

        if response.success:
            return response.content
        else:
            return (
                "Maaf, saya mengalami kendala teknis: {}. "
                "Pastikan provider LLM tersedia.".format(response.error)
            )

    def process(self, user_input: str) -> Dict[str, str]:
        """Process user input through the full orchestration pipeline.

        Steps:
        1. Classify task type (code/research/simple)
        2. Route to appropriate model via ModelRouter
        3. Execute with the right agent or direct LLM
        4. Store in conversation memory
        5. Return formatted result

        Args:
            user_input: The user's input text.

        Returns:
            Dict with keys: 'response', 'task_type', 'model', 'provider', 'difficulty'.
        """
        # Step 1: Klasifikasi task
        task_type = self.classify_task(user_input)

        # Step 2: Route ke model yang tepat
        route = self.router.route(user_input)

        logger.info(
            "Processing: task_type=%s, difficulty=%s, provider=%s, model=%s",
            task_type, route.difficulty.value, route.provider.name, route.model,
        )

        # Step 3: Execute berdasarkan task type
        response_text = ""

        if task_type == "code":
            agent = self._get_coder_agent(route)
            response_text = agent.run(user_input)
        elif task_type == "research":
            agent = self._get_researcher_agent(route)
            response_text = agent.run(user_input)
        else:
            # Simple task - direct LLM response
            response_text = self._direct_llm_response(user_input, route)

        # Step 4: Simpan ke conversation memory
        self.memory.add_message("user", user_input)
        self.memory.add_message("assistant", response_text)

        # Step 5: Return structured result
        return {
            "response": response_text,
            "task_type": task_type,
            "model": route.model,
            "provider": route.provider.name,
            "difficulty": route.difficulty.value,
        }

    def get_status(self) -> Dict[str, object]:
        """Get current system status including provider availability.

        Returns:
            Dict with provider status, memory info, and configuration.
        """
        router_status = self.router.get_status()
        return {
            "providers": router_status,
            "memory": {
                "messages": self.memory.message_count,
                "has_summary": self.memory.has_summary,
                "max_messages": self.memory.max_messages,
            },
        }

    def refresh_providers(self) -> None:
        """Re-check provider availability.

        Useful when Ollama is started after J.A.R.V.I.S or when
        network connectivity changes.
        """
        self.router.check_providers()
        logger.info("Providers refreshed. Status: %s", self.get_status())

    def clear_memory(self) -> None:
        """Clear conversation memory and reset agent histories."""
        self.memory.clear()
        if self._coder_agent:
            self._coder_agent.clear_history()
        if self._researcher_agent:
            self._researcher_agent.clear_history()
        logger.info("Memory cleared")

    def save_session(self, file_path: str) -> Dict[str, object]:
        """Save the current conversation session to a file.

        Args:
            file_path: Path to save the session JSON.

        Returns:
            Dict with 'success' and 'path' or 'error' keys.
        """
        return self.memory.save_to_file(file_path)

    def load_session(self, file_path: str) -> Dict[str, object]:
        """Load a conversation session from a file.

        Args:
            file_path: Path to the session JSON file.

        Returns:
            Dict with 'success' or 'error' keys.
        """
        return self.memory.load_from_file(file_path)
