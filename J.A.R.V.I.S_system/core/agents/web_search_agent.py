"""
Web Search Agent - Internet research and fact-finding agent.

Inherits from BaseAgent and specializes in:
- Web search using DuckDuckGo (via web_search tools)
- News search for current events
- Page summarization for deep-dive on specific URLs
- Fact verification and source cross-referencing

System prompt focuses on accuracy, source verification, and
structured presentation of search results.
"""

import logging
from typing import Optional

from core.agents.base_agent import BaseAgent
from core.providers.base_provider import BaseProvider
from core.tools.web_search import search_web, search_news, get_page_summary

logger = logging.getLogger(__name__)


# System prompt for web search agent - fact-finding focused
WEB_SEARCH_SYSTEM_PROMPT = (
    "Kamu adalah J.A.R.V.I.S Web Search Agent - agen riset internet yang "
    "mengutamakan akurasi dan verifikasi fakta.\n\n"
    "Misi Utama:\n"
    "- Mencari informasi terkini dari internet menggunakan DuckDuckGo\n"
    "- Memverifikasi fakta dari multiple sources sebelum memberikan jawaban\n"
    "- Menyajikan hasil pencarian secara terstruktur dan mudah dipahami\n"
    "- Selalu mencantumkan sumber informasi\n\n"
    "Personality:\n"
    "- Jujur: Jika tidak menemukan informasi yang reliable, katakan dengan jelas\n"
    "- Kritis: Cross-reference informasi dari beberapa sumber\n"
    "- Fakta-based: Prioritaskan data dan fakta, bukan opini\n"
    "- Teliti: Periksa tanggal dan relevansi informasi\n\n"
    "Workflow:\n"
    "1. Analisis pertanyaan user - tentukan search query terbaik\n"
    "2. Lakukan pencarian web (atau news jika tentang berita terkini)\n"
    "3. Jika perlu detail lebih, gunakan get_page_summary untuk halaman tertentu\n"
    "4. Rangkum hasil dalam format yang jelas:\n"
    "   - Jawaban utama\n"
    "   - Sumber-sumber yang digunakan\n"
    "   - Catatan jika ada informasi yang kontradiktif\n\n"
    "Format jawaban:\n"
    "- Gunakan bullet points untuk poin-poin penting\n"
    "- Sertakan URL sumber\n"
    "- Tandai jika informasi belum terverifikasi\n"
    "- Bahasa Indonesia sebagai default, kecuali diminta lain"
)


class WebSearchAgent(BaseAgent):
    """Internet research agent with web search capabilities.

    Specializes in:
    - Finding current information via web search
    - News search for recent events
    - Summarizing web pages
    - Fact verification from multiple sources
    """

    def __init__(
        self,
        provider: BaseProvider,
        model: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 5,
        temperature: float = 0.4,
        max_tokens: int = 3072,
    ) -> None:
        """Initialize the Web Search Agent.

        Args:
            provider: LLM provider for inference.
            model: Model name to use.
            system_prompt: Optional custom system prompt.
            max_retries: Maximum self-healing retry attempts.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens per generation.
        """
        super().__init__(
            name="web_search",
            provider=provider,
            model=model,
            system_prompt=system_prompt or WEB_SEARCH_SYSTEM_PROMPT,
            max_retries=max_retries,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        self._register_web_tools()

    def _register_web_tools(self) -> None:
        """Register web search tools."""
        # Tool: search_web
        self.register_tool(
            name="search_web",
            func=search_web,
            description=(
                "Search the web using DuckDuckGo. Returns a list of results "
                "with title, URL, and snippet for each."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 5)",
                    },
                },
                "required": ["query"],
            },
        )

        # Tool: search_news
        self.register_tool(
            name="search_news",
            func=search_news,
            description=(
                "Search news articles using DuckDuckGo. Returns recent news "
                "with title, URL, snippet, date, and source."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "News search query string",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 5)",
                    },
                },
                "required": ["query"],
            },
        )

        # Tool: get_page_summary
        self.register_tool(
            name="get_page_summary",
            func=get_page_summary,
            description=(
                "Get a text summary of a web page. Fetches the URL and "
                "extracts readable text content (truncated to ~3000 chars)."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of the page to summarize (must start with http:// or https://)",
                    },
                },
                "required": ["url"],
            },
        )

        logger.info("WebSearchAgent: Registered %d tools", len(self._tools))

    def get_agent_type(self) -> str:
        """Get the agent type identifier.

        Returns:
            'web_search' - identifies this as a web search agent.
        """
        return "web_search"
