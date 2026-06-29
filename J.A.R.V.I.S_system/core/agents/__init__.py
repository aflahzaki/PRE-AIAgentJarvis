"""
Agents - Autonomous AI agents for J.A.R.V.I.S system.

Available agents:
- BaseAgent: Abstract base with self-healing loop and tool calling
- CoderAgent: Autonomous coding agent with file and execution tools
- ResearcherAgent: Critical thinking and research analysis agent
"""

from core.agents.base_agent import BaseAgent
from core.agents.coder_agent import CoderAgent
from core.agents.researcher_agent import ResearcherAgent

__all__ = [
    "BaseAgent",
    "CoderAgent",
    "ResearcherAgent",
]
