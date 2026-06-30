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
from typing import Dict, Generator, List, Optional, Tuple

from core.agents.coder_agent import CoderAgent
from core.agents.researcher_agent import ResearcherAgent
from core.agents.web_search_agent import WebSearchAgent
from core.agents.data_analyst_agent import DataAnalystAgent
from core.agents.scheduler_agent import SchedulerAgent
from core.agents.writer_agent import WriterAgent
from core.agents.life_assistant_agent import LifeAssistantAgent
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

    # Pattern: web search tasks
    SEARCH_PATTERNS = [
        r"\b(cari|search|searching|googling)\b",
        r"\b(berita|news|kabar terbaru)\b",
        r"\b(info terbaru|informasi terbaru|latest info)\b",
        r"\b(latest|terbaru|update terkini)\b",
        r"\b(link|url|website|situs)\b",
        r"\b(browse|lookup|look up|find online)\b",
        r"\b(trending|viral|populer saat ini)\b",
        r"\b(apa yang terjadi|what happened|what's new)\b",
    ]

    # Pattern: data analysis tasks
    DATA_PATTERNS = [
        r"\b(data|dataset|dataframe)\b",
        r"\b(csv|excel|spreadsheet|tabel)\b",
        r"\b(statistik|statistics|rata.?rata|mean|median)\b",
        r"\b(analisis data|data analysis|analyze data)\b",
        r"\b(grafik|chart|graph|plot|visualisasi|visualization)\b",
        r"\b(korelasi|correlation|regresi|regression)\b",
        r"\b(pivot|aggregate|group by|filter data)\b",
        r"\b(insight|pattern|tren data|trend)\b",
    ]

    # Pattern: scheduling/task management tasks
    SCHEDULE_PATTERNS = [
        r"\b(deadline|tenggat|due date)\b",
        r"\b(jadwal|schedule|agenda|calendar)\b",
        r"\b(reminder|ingatkan|pengingat)\b",
        r"\b(task|tugas|todo|to.?do)\b",
        r"\b(planning|perencanaan|rencana harian)\b",
        r"\b(besok|tomorrow|minggu depan|next week)\b",
        r"\b(prioritas|priority|urgent|penting)\b",
        r"\b(meeting|rapat|janji|appointment)\b",
    ]

    # Pattern: writing/content creation tasks
    WRITE_PATTERNS = [
        r"\b(tulis|tuliskan|write|compose)\b",
        r"\b(buat email|write email|email formal|email template)\b",
        r"\b(draft|draf|rangkuman|summary)\b",
        r"\b(proposal|laporan|report)\b",
        r"\b(caption|copywriting|konten|content)\b",
        r"\b(essay|esai|artikel|article)\b",
        r"\b(surat|letter|memo|dokumen)\b",
        r"\b(puisi|poem|cerpen|cerita|story)\b",
    ]

    # Pattern: life assistant/wellness tasks
    LIFE_PATTERNS = [
        r"\b(mood|perasaan|feeling|emosi)\b",
        r"\b(jurnal|journal|diary|catatan harian)\b",
        r"\b(habit|kebiasaan|rutinitas|routine)\b",
        r"\b(motivasi|motivation|semangat|inspirasi)\b",
        r"\b(saran|advice|rekomendasi|suggestion)\b",
        r"\b(bingung|confused|galau|dilema)\b",
        r"\b(pilihan|pilih|choice|choose|keputusan|decision)\b",
        r"\b(self.?care|kesehatan mental|wellness|well.?being)\b",
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
        self._web_search_agent = None  # type: Optional[WebSearchAgent]
        self._data_analyst_agent = None  # type: Optional[DataAnalystAgent]
        self._scheduler_agent = None  # type: Optional[SchedulerAgent]
        self._writer_agent = None  # type: Optional[WriterAgent]
        self._life_assistant_agent = None  # type: Optional[LifeAssistantAgent]

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
        - 'search': Web searching, news, latest info retrieval
        - 'data': Data analysis, CSV processing, visualizations
        - 'schedule': Reminders, deadlines, task management
        - 'write': Email drafts, articles, proposals, content creation
        - 'life': Personal advice, wellness, decision help
        - 'code': Code writing, debugging, file manipulation
        - 'research': Complex analysis, comparison, deep reasoning
        - 'simple': Greetings, simple questions, casual chat

        Args:
            user_input: The user's input text.

        Returns:
            Task type string: 'search', 'data', 'schedule', 'write',
            'life', 'code', 'research', or 'simple'.
        """
        text = user_input.lower().strip()

        # --- Phase 3: Check new specific patterns first ---
        # These are more specific task types that should be checked before
        # the broader code/research patterns to avoid misclassification.

        search_score = sum(
            1 for p in self.SEARCH_PATTERNS
            if re.search(p, text, re.IGNORECASE)
        )
        data_score = sum(
            1 for p in self.DATA_PATTERNS
            if re.search(p, text, re.IGNORECASE)
        )
        schedule_score = sum(
            1 for p in self.SCHEDULE_PATTERNS
            if re.search(p, text, re.IGNORECASE)
        )
        write_score = sum(
            1 for p in self.WRITE_PATTERNS
            if re.search(p, text, re.IGNORECASE)
        )
        life_score = sum(
            1 for p in self.LIFE_PATTERNS
            if re.search(p, text, re.IGNORECASE)
        )

        # Determine if any new pattern has a strong match (>= 1)
        new_scores = {
            "search": search_score,
            "data": data_score,
            "schedule": schedule_score,
            "write": write_score,
            "life": life_score,
        }

        # Find the best new-pattern match
        best_new_type = max(new_scores, key=new_scores.get)
        best_new_score = new_scores[best_new_type]

        # If we have a strong new-pattern match, use it
        # (threshold >= 2 means multiple keywords matched for high confidence,
        #  or >= 1 with no competing code/research signals)
        if best_new_score >= 2:
            return best_new_type

        # --- Original code/research classification logic ---
        # Hitung score untuk setiap kategori
        code_score = 0
        research_score = 0

        for pattern in self.CODE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                code_score += 1

        for pattern in self.RESEARCH_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                research_score += 1

        # If best_new_score is 1 and code/research scores are 0,
        # route to the new agent type
        if best_new_score >= 1 and code_score == 0 and research_score == 0:
            return best_new_type

        # If best_new_score is 1 and it strictly beats code/research, route to new agent
        if best_new_score >= 1 and best_new_score > code_score and best_new_score > research_score:
            return best_new_type

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

    def _get_web_search_agent(self, route: ModelRoute) -> WebSearchAgent:
        """Get or create a WebSearchAgent with the given route's provider/model.

        Args:
            route: ModelRoute with provider and model selection.

        Returns:
            Configured WebSearchAgent instance.
        """
        if (
            self._web_search_agent is None
            or self._web_search_agent.provider != route.provider
            or self._web_search_agent.model != route.model
        ):
            self._web_search_agent = WebSearchAgent(
                provider=route.provider,
                model=route.model,
            )
        return self._web_search_agent

    def _get_data_analyst_agent(self, route: ModelRoute) -> DataAnalystAgent:
        """Get or create a DataAnalystAgent with the given route's provider/model.

        Args:
            route: ModelRoute with provider and model selection.

        Returns:
            Configured DataAnalystAgent instance.
        """
        if (
            self._data_analyst_agent is None
            or self._data_analyst_agent.provider != route.provider
            or self._data_analyst_agent.model != route.model
        ):
            self._data_analyst_agent = DataAnalystAgent(
                provider=route.provider,
                model=route.model,
            )
        return self._data_analyst_agent

    def _get_scheduler_agent(self, route: ModelRoute) -> SchedulerAgent:
        """Get or create a SchedulerAgent with the given route's provider/model.

        Args:
            route: ModelRoute with provider and model selection.

        Returns:
            Configured SchedulerAgent instance.
        """
        if (
            self._scheduler_agent is None
            or self._scheduler_agent.provider != route.provider
            or self._scheduler_agent.model != route.model
        ):
            self._scheduler_agent = SchedulerAgent(
                provider=route.provider,
                model=route.model,
            )
        return self._scheduler_agent

    def _get_writer_agent(self, route: ModelRoute) -> WriterAgent:
        """Get or create a WriterAgent with the given route's provider/model.

        Args:
            route: ModelRoute with provider and model selection.

        Returns:
            Configured WriterAgent instance.
        """
        if (
            self._writer_agent is None
            or self._writer_agent.provider != route.provider
            or self._writer_agent.model != route.model
        ):
            self._writer_agent = WriterAgent(
                provider=route.provider,
                model=route.model,
            )
        return self._writer_agent

    def _get_life_assistant_agent(self, route: ModelRoute) -> LifeAssistantAgent:
        """Get or create a LifeAssistantAgent with the given route's provider/model.

        Args:
            route: ModelRoute with provider and model selection.

        Returns:
            Configured LifeAssistantAgent instance.
        """
        if (
            self._life_assistant_agent is None
            or self._life_assistant_agent.provider != route.provider
            or self._life_assistant_agent.model != route.model
        ):
            self._life_assistant_agent = LifeAssistantAgent(
                provider=route.provider,
                model=route.model,
            )
        return self._life_assistant_agent

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

        if task_type == "search":
            agent = self._get_web_search_agent(route)
            response_text = agent.run(user_input)
        elif task_type == "data":
            agent = self._get_data_analyst_agent(route)
            response_text = agent.run(user_input)
        elif task_type == "schedule":
            agent = self._get_scheduler_agent(route)
            response_text = agent.run(user_input)
        elif task_type == "write":
            agent = self._get_writer_agent(route)
            response_text = agent.run(user_input)
        elif task_type == "life":
            agent = self._get_life_assistant_agent(route)
            response_text = agent.run(user_input)
        elif task_type == "code":
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

    def process_stream(self, user_input: str) -> Generator[str, None, None]:
        """Process user input with streaming token output.

        For simple tasks, streams tokens directly from the provider using
        stream_chat_completion(). For agent-based tasks (code, research, etc.),
        falls back to the non-streaming process() method and yields the full
        response as a single chunk.

        Includes error handling that falls back to non-streaming process()
        if streaming fails for any reason.

        Args:
            user_input: The user's input text.

        Yields:
            String tokens as they are generated.
        """
        try:
            # Step 1: Classify task
            task_type = self.classify_task(user_input)

            # Step 2: Route to appropriate model
            route = self.router.route(user_input)

            logger.info(
                "Streaming: task_type=%s, difficulty=%s, provider=%s, model=%s",
                task_type, route.difficulty.value, route.provider.name, route.model,
            )

            if task_type == "simple":
                # Stream directly from provider for simple tasks
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

                # Add context from memory
                history = self.memory.get_messages(include_summary=True)
                recent = history[-6:] if len(history) > 6 else history
                messages.extend(recent)

                # Current user message
                messages.append({"role": "user", "content": user_input})

                # Stream tokens from provider
                full_response = ""
                for token in route.provider.stream_chat_completion(
                    messages=messages,
                    model=route.model,
                    temperature=0.7,
                    max_tokens=1024,
                ):
                    full_response += token
                    yield token

                # Add to memory after streaming completes
                self.memory.add_message("user", user_input)
                self.memory.add_message("assistant", full_response)
            else:
                # Agent-based tasks: use non-streaming process and yield full response
                result = self.process(user_input)
                yield result["response"]

        except Exception as e:
            logger.warning(
                "Streaming failed, falling back to non-streaming: %s", str(e)
            )
            # Fallback to non-streaming process
            try:
                result = self.process(user_input)
                yield result["response"]
            except Exception as fallback_error:
                yield "Maaf, terjadi kesalahan: {}".format(str(fallback_error))

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
        if self._web_search_agent:
            self._web_search_agent.clear_history()
        if self._data_analyst_agent:
            self._data_analyst_agent.clear_history()
        if self._scheduler_agent:
            self._scheduler_agent.clear_history()
        if self._writer_agent:
            self._writer_agent.clear_history()
        if self._life_assistant_agent:
            self._life_assistant_agent.clear_history()
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
