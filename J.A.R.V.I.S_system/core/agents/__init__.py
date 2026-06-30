"""
Agents - Autonomous AI agents for J.A.R.V.I.S system.

Available agents:
- BaseAgent: Abstract base with self-healing loop and tool calling
- CoderAgent: Autonomous coding agent with file and execution tools
- ResearcherAgent: Critical thinking and research analysis agent
- WebSearchAgent: Internet research and fact-finding agent
- DataAnalystAgent: Data analysis and insight generation agent
- SchedulerAgent: Time management and task scheduling agent
- WriterAgent: Multi-purpose writing assistant agent
- LifeAssistantAgent: Personal life helper and wellness agent
"""

from core.agents.base_agent import BaseAgent
from core.agents.coder_agent import CoderAgent
from core.agents.researcher_agent import ResearcherAgent
from core.agents.web_search_agent import WebSearchAgent
from core.agents.data_analyst_agent import DataAnalystAgent
from core.agents.scheduler_agent import SchedulerAgent
from core.agents.writer_agent import WriterAgent
from core.agents.life_assistant_agent import LifeAssistantAgent

__all__ = [
    "BaseAgent",
    "CoderAgent",
    "ResearcherAgent",
    "WebSearchAgent",
    "DataAnalystAgent",
    "SchedulerAgent",
    "WriterAgent",
    "LifeAssistantAgent",
]
