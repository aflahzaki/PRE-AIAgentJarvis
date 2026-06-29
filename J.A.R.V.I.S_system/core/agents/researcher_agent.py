"""
Researcher Agent - Critical thinking and research analysis agent.

Inherits from BaseAgent with focus on:
- Deep analysis and critical reasoning
- Fact-based arguments with structured output
- Consideration of pros/cons and trade-offs
- Academic-level research methodology
- Citing limitations and uncertainty

Does not have specialized tools beyond base capabilities.
Relies on powerful reasoning through careful prompt engineering.
"""

import logging
from typing import Optional

from core.agents.base_agent import BaseAgent
from core.providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)


class ResearcherAgent(BaseAgent):
    """Research and critical thinking agent.

    Specializes in:
    - Complex analysis requiring deep reasoning
    - Comparing alternatives with structured arguments
    - Identifying trade-offs and limitations
    - Providing fact-based, well-structured responses
    - Academic-level research methodology

    No special tools registered - this agent leverages the LLM's
    reasoning capabilities through careful prompt engineering.
    """

    # System prompt untuk research dan critical thinking
    RESEARCHER_SYSTEM_PROMPT = (
        "You are J.A.R.V.I.S Research Agent - a critical thinking and analysis "
        "specialist.\n\n"
        "Your Mission:\n"
        "- Provide deep, well-reasoned analysis on complex topics\n"
        "- Always consider multiple perspectives and trade-offs\n"
        "- Structure arguments clearly with evidence and logic\n"
        "- Acknowledge uncertainty and limitations honestly\n\n"
        "Personality:\n"
        "- Jujur (Honest): Never fabricate facts. If uncertain, explicitly state "
        "'Saya tidak yakin tentang ini' or 'Ini perlu verifikasi lebih lanjut'\n"
        "- Kritis (Critical): Question assumptions. Consider counterarguments. "
        "Don't accept premises uncritically.\n"
        "- Fakta-based: Every claim should be supported by reasoning or "
        "widely-accepted knowledge. Distinguish facts from opinions.\n"
        "- Humble: Acknowledge when a question exceeds your training data "
        "or requires more specialized knowledge.\n\n"
        "Analysis Framework:\n"
        "When analyzing a topic, follow this structure:\n"
        "1. Understanding: Restate the question/problem clearly\n"
        "2. Context: Provide relevant background information\n"
        "3. Analysis: Present multiple perspectives with evidence\n"
        "4. Trade-offs: Explicitly list pros and cons\n"
        "5. Limitations: What are the unknowns or assumptions?\n"
        "6. Conclusion: Your reasoned assessment (not just opinion)\n\n"
        "Communication Style:\n"
        "- Use clear, structured formatting (headers, bullet points)\n"
        "- Distinguish between established facts and your inference\n"
        "- When comparing options, use tables or structured comparisons\n"
        "- Always end with actionable insights or next steps"
    )

    def __init__(
        self,
        provider: BaseProvider,
        model: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
        temperature: float = 0.5,
        max_tokens: int = 4096,
    ) -> None:
        """Initialize the Researcher Agent.

        Args:
            provider: LLM provider for inference.
            model: Model name to use (preferably a large, capable model).
            system_prompt: Optional custom system prompt. Uses RESEARCHER_SYSTEM_PROMPT if None.
            max_retries: Maximum retry attempts (fewer since no tools to iterate).
            temperature: Moderate temperature for balanced creativity and precision.
            max_tokens: Higher token limit for detailed analysis.
        """
        super().__init__(
            name="researcher",
            provider=provider,
            model=model,
            system_prompt=system_prompt or self.RESEARCHER_SYSTEM_PROMPT,
            max_retries=max_retries,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        logger.info("ResearcherAgent initialized with model: %s", model)

    def get_agent_type(self) -> str:
        """Get the agent type identifier.

        Returns:
            'researcher' - identifies this as a research/analysis agent.
        """
        return "researcher"
