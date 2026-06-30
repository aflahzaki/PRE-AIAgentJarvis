"""
Agent Protocol - Standardized inter-agent communication for J.A.R.V.I.S.

Defines the message format, response format, and communication primitives
for agent-to-agent interaction. Supports delegation (agent A asks agent B
to perform a task) and result aggregation (combining outputs from multiple agents).

Dataclasses:
    - AgentMessage: Request/task message between agents
    - AgentResponse: Agent's response to a message

Class:
    - AgentProtocol: Communication manager with send, delegate, aggregate
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentMessage:
    """Standardized message format for inter-agent communication.

    Attributes:
        sender: Name/ID of the sending agent.
        receiver: Name/ID of the target agent.
        task: Task description or instruction.
        context: Additional context or metadata for the task.
        priority: Message priority ('low', 'medium', 'high', 'urgent').
        timestamp: When the message was created.
        message_id: Unique identifier for this message.
    """

    sender: str
    receiver: str
    task: str
    context: Optional[Dict[str, Any]] = None
    priority: str = "medium"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary representation.

        Returns:
            Dict with all message fields.
        """
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "task": self.task,
            "context": self.context,
            "priority": self.priority,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AgentResponse:
    """Standardized response format from an agent.

    Attributes:
        sender: Name/ID of the responding agent.
        content: Response content/output.
        success: Whether the task was completed successfully.
        metadata: Additional response metadata (timing, tools used, etc).
        message_id: ID of the original message being responded to.
        timestamp: When the response was created.
    """

    sender: str
    content: str
    success: bool = True
    metadata: Optional[Dict[str, Any]] = None
    message_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary representation.

        Returns:
            Dict with all response fields.
        """
        return {
            "sender": self.sender,
            "content": self.content,
            "success": self.success,
            "metadata": self.metadata,
            "message_id": self.message_id,
            "timestamp": self.timestamp.isoformat(),
        }


class AgentProtocol:
    """Manages inter-agent communication, delegation, and result aggregation.

    Provides a centralized protocol for agents to send messages, delegate
    tasks to other agents, and aggregate results from multiple agents.

    Attributes:
        message_log: History of all messages sent through the protocol.
        response_log: History of all responses received.
    """

    def __init__(self) -> None:
        """Initialize the agent protocol manager."""
        self.message_log: List[AgentMessage] = []
        self.response_log: List[AgentResponse] = []
        self._agents: Dict[str, Any] = {}
        logger.info("AgentProtocol: Initialized")

    def register_agent(self, name: str, agent: Any) -> None:
        """Register an agent with the protocol.

        Args:
            name: Agent name/identifier.
            agent: Agent instance (must have a 'run' method).
        """
        self._agents[name] = agent
        logger.debug("AgentProtocol: Registered agent '%s'", name)

    def get_registered_agents(self) -> List[str]:
        """Get list of registered agent names.

        Returns:
            List of agent name strings.
        """
        return list(self._agents.keys())

    def send_message(self, message: AgentMessage) -> Optional[AgentResponse]:
        """Send a message to a target agent and get response.

        Args:
            message: AgentMessage to send.

        Returns:
            AgentResponse from the target agent, or None if agent not found.
        """
        self.message_log.append(message)
        logger.info(
            "AgentProtocol: Message from '%s' to '%s': %s",
            message.sender,
            message.receiver,
            message.task[:100],
        )

        # Find the target agent
        target_agent = self._agents.get(message.receiver)
        if target_agent is None:
            logger.warning(
                "AgentProtocol: Agent '%s' not registered", message.receiver
            )
            response = AgentResponse(
                sender="protocol",
                content="Agent '{}' not found. Available: {}".format(
                    message.receiver, list(self._agents.keys())
                ),
                success=False,
                message_id=message.message_id,
            )
            self.response_log.append(response)
            return response

        # Execute the task on the target agent
        try:
            # Build context-enriched prompt
            prompt = message.task
            if message.context:
                context_str = "\n".join(
                    "{}: {}".format(k, v) for k, v in message.context.items()
                )
                prompt = "Context:\n{}\n\nTask: {}".format(
                    context_str, message.task
                )

            result = target_agent.run(prompt)

            response = AgentResponse(
                sender=message.receiver,
                content=result,
                success=True,
                metadata={
                    "delegated_by": message.sender,
                    "priority": message.priority,
                },
                message_id=message.message_id,
            )

        except Exception as e:
            logger.error(
                "AgentProtocol: Error executing on '%s': %s",
                message.receiver, str(e),
            )
            response = AgentResponse(
                sender=message.receiver,
                content="Error: {}".format(str(e)),
                success=False,
                metadata={"error_type": type(e).__name__},
                message_id=message.message_id,
            )

        self.response_log.append(response)
        return response

    def delegate_task(
        self,
        from_agent: str,
        to_agent: str,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        priority: str = "medium",
    ) -> Optional[AgentResponse]:
        """Delegate a task from one agent to another.

        Convenience method that creates an AgentMessage and sends it.

        Args:
            from_agent: Sender agent name.
            to_agent: Target agent name.
            task: Task description.
            context: Additional context.
            priority: Task priority level.

        Returns:
            AgentResponse from the target agent.
        """
        message = AgentMessage(
            sender=from_agent,
            receiver=to_agent,
            task=task,
            context=context,
            priority=priority,
        )
        return self.send_message(message)

    def aggregate_results(
        self, responses: List[AgentResponse]
    ) -> Dict[str, Any]:
        """Aggregate results from multiple agent responses.

        Combines outputs, tracks success/failure counts, and produces
        a unified summary.

        Args:
            responses: List of AgentResponse objects to aggregate.

        Returns:
            Dict with aggregated results including 'combined_content',
            'success_count', 'failure_count', and individual 'responses'.
        """
        if not responses:
            return {
                "success": True,
                "combined_content": "",
                "success_count": 0,
                "failure_count": 0,
                "responses": [],
            }

        success_count = sum(1 for r in responses if r.success)
        failure_count = len(responses) - success_count

        # Combine successful responses
        combined_parts = []
        for resp in responses:
            if resp.success:
                combined_parts.append(
                    "[{}]: {}".format(resp.sender, resp.content)
                )
            else:
                combined_parts.append(
                    "[{} - FAILED]: {}".format(resp.sender, resp.content)
                )

        return {
            "success": failure_count == 0,
            "combined_content": "\n\n".join(combined_parts),
            "success_count": success_count,
            "failure_count": failure_count,
            "total": len(responses),
            "responses": [r.to_dict() for r in responses],
        }

    def get_message_history(
        self, agent_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get message history, optionally filtered by agent.

        Args:
            agent_name: Filter by sender or receiver name.

        Returns:
            List of message dicts.
        """
        if agent_name:
            filtered = [
                m for m in self.message_log
                if m.sender == agent_name or m.receiver == agent_name
            ]
            return [m.to_dict() for m in filtered]

        return [m.to_dict() for m in self.message_log]

    def clear_history(self) -> None:
        """Clear all message and response logs."""
        self.message_log.clear()
        self.response_log.clear()
        logger.info("AgentProtocol: History cleared")

    def __repr__(self) -> str:
        return "AgentProtocol(agents={}, messages={}, responses={})".format(
            len(self._agents),
            len(self.message_log),
            len(self.response_log),
        )
