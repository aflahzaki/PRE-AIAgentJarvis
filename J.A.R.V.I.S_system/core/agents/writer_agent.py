"""
Writer Agent - Multi-purpose writing assistant agent.

Inherits from BaseAgent and specializes in:
- Email drafting (formal, casual, professional)
- Proposal and document writing
- Social media caption generation
- Academic and casual text formatting
- Tone adjustment and style switching

System prompt focuses on clarity, creativity, and adaptable communication.
"""

import logging
from typing import Optional

from core.agents.base_agent import BaseAgent
from core.providers.base_provider import BaseProvider
from core.tools.writing_tools import (
    email_template,
    proposal_template,
    caption_template,
    format_academic,
    format_casual,
)

logger = logging.getLogger(__name__)


WRITER_SYSTEM_PROMPT = (
    "Kamu adalah J.A.R.V.I.S Writer Agent - agen penulisan serbaguna yang "
    "membantu user menghasilkan konten berkualitas tinggi.\n\n"
    "Misi Utama:\n"
    "- Menulis email dengan tone yang tepat (formal/casual/professional)\n"
    "- Membuat proposal dan dokumen terstruktur\n"
    "- Generate caption social media yang engaging\n"
    "- Menyesuaikan tone dan style sesuai kebutuhan\n"
    "- Format teks untuk berbagai keperluan (akademik, casual, kreatif)\n\n"
    "Personality:\n"
    "- Kreatif: Gunakan bahasa yang menarik dan engaging\n"
    "- Adaptif: Bisa switch antara formal dan casual dengan mudah\n"
    "- Detail-oriented: Perhatikan grammar, struktur, dan flow\n"
    "- Empathetic: Pahami konteks dan audience dari tulisan\n\n"
    "Kemampuan Penulisan:\n"
    "- Email: formal, casual, friendly, professional\n"
    "- Proposal: executive summary, objectives, timeline, budget\n"
    "- Caption: Instagram, Twitter, LinkedIn, TikTok, Facebook\n"
    "- Essay, surat, script video, creative writing\n"
    "- Format: academic (passive voice, citations) atau casual (conversational)\n\n"
    "Workflow:\n"
    "1. Pahami jenis konten yang dibutuhkan user\n"
    "2. Tentukan tone dan audience\n"
    "3. Gunakan template tools sebagai starting point\n"
    "4. Customize dan sempurnakan sesuai kebutuhan spesifik\n"
    "5. Review dan polish hasil akhir\n\n"
    "Tips:\n"
    "- Selalu tanya audience jika belum jelas\n"
    "- Bahasa Indonesia sebagai default, bisa switch ke English\n"
    "- Berikan beberapa opsi jika user belum yakin style-nya"
)


class WriterAgent(BaseAgent):
    """Multi-purpose writing agent with template and formatting tools.

    Specializes in:
    - Email drafting with tone selection
    - Proposal document generation
    - Social media caption creation
    - Text formatting (academic, casual)
    - Style and tone adaptation
    """

    def __init__(
        self,
        provider: BaseProvider,
        model: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 5,
        temperature: float = 0.7,
        max_tokens: int = 3072,
    ) -> None:
        """Initialize the Writer Agent.

        Args:
            provider: LLM provider for inference.
            model: Model name to use.
            system_prompt: Optional custom system prompt.
            max_retries: Maximum self-healing retry attempts.
            temperature: Higher temperature for creative writing.
            max_tokens: Higher limit for longer content.
        """
        super().__init__(
            name="writer",
            provider=provider,
            model=model,
            system_prompt=system_prompt or WRITER_SYSTEM_PROMPT,
            max_retries=max_retries,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        self._register_writing_tools()

    def _register_writing_tools(self) -> None:
        """Register writing and formatting tools."""
        # Tool: email_template
        self.register_tool(
            name="email_template",
            func=email_template,
            description=(
                "Generate an email template with specified tone. "
                "Returns a formatted email structure ready for customization."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "tone": {
                        "type": "string",
                        "description": "Email tone: formal, casual, friendly, professional",
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line",
                    },
                    "recipient": {
                        "type": "string",
                        "description": "Recipient name (optional)",
                    },
                },
                "required": ["tone", "subject"],
            },
        )

        # Tool: proposal_template
        self.register_tool(
            name="proposal_template",
            func=proposal_template,
            description=(
                "Generate a structured proposal document template with "
                "sections for executive summary, objectives, approach, budget, etc."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Proposal title",
                    },
                    "context": {
                        "type": "string",
                        "description": "Brief context or background for the proposal",
                    },
                },
                "required": ["title"],
            },
        )

        # Tool: caption_template
        self.register_tool(
            name="caption_template",
            func=caption_template,
            description=(
                "Generate a social media caption template optimized for "
                "the specified platform (Instagram, Twitter, LinkedIn, TikTok, Facebook)."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "platform": {
                        "type": "string",
                        "description": "Platform: instagram, twitter, linkedin, tiktok, facebook",
                    },
                    "topic": {
                        "type": "string",
                        "description": "Topic or subject of the caption",
                    },
                },
                "required": ["platform", "topic"],
            },
        )

        # Tool: format_academic
        self.register_tool(
            name="format_academic",
            func=format_academic,
            description=(
                "Format text in academic/formal style. Applies proper "
                "capitalization, structure suggestions, and academic conventions."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to format in academic style",
                    },
                },
                "required": ["text"],
            },
        )

        # Tool: format_casual
        self.register_tool(
            name="format_casual",
            func=format_casual,
            description=(
                "Format text in casual/conversational style. Replaces "
                "formal phrases with casual equivalents and adds style tips."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to format in casual style",
                    },
                },
                "required": ["text"],
            },
        )

        logger.info("WriterAgent: Registered %d tools", len(self._tools))

    def get_agent_type(self) -> str:
        """Get the agent type identifier.

        Returns:
            'writer' - identifies this as a writing agent.
        """
        return "writer"
