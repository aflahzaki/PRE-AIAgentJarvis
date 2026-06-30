"""
Protocols - Inter-agent communication and task management for J.A.R.V.I.S.

Available modules:
- AgentProtocol: Standard message format and delegation between agents
- AgentMessage: Dataclass for agent-to-agent messages
- AgentResponse: Dataclass for agent responses
- TaskQueue: Priority queue for task scheduling and tracking
"""

from core.protocols.agent_protocol import AgentMessage, AgentResponse, AgentProtocol
from core.protocols.task_queue import TaskQueue

__all__ = [
    "AgentMessage",
    "AgentResponse",
    "AgentProtocol",
    "TaskQueue",
]
