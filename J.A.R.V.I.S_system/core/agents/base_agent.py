"""
Base Agent - Abstract base class for all J.A.R.V.I.S agents.

Provides:
- System prompt management (configurable per agent)
- Self-healing loop logic (max 5 retries)
- Tool calling infrastructure using OpenAI function calling format
- Message history management
- Personality traits: honest, critical, fact-based, autonomous, self-healing, humble
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.providers.base_provider import BaseProvider, ProviderResponse

logger = logging.getLogger(__name__)

# Maximum retries untuk self-healing loop
MAX_RETRIES = 5


class BaseAgent(ABC):
    """Abstract base agent with self-healing capabilities.

    All specialized agents inherit from this class and gain:
    - Tool registration and execution infrastructure
    - Self-healing loop that retries on failure
    - System prompt management with personality traits
    - Message history tracking

    Tool calling uses OpenAI function calling format:
    tools=[{"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}]
    """

    def __init__(
        self,
        name: str,
        provider: BaseProvider,
        model: str,
        system_prompt: Optional[str] = None,
        max_retries: int = MAX_RETRIES,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> None:
        """Initialize the base agent.

        Args:
            name: Agent name identifier (e.g., 'coder', 'researcher').
            provider: LLM provider instance to use for inference.
            model: Model name to use with the provider.
            system_prompt: Custom system prompt. If None, uses default.
            max_retries: Maximum retries in self-healing loop.
            temperature: Sampling temperature for generation.
            max_tokens: Maximum tokens per generation.
        """
        self.name = name
        self.provider = provider
        self.model = model
        self.max_retries = max_retries
        self.temperature = temperature
        self.max_tokens = max_tokens

        # System prompt dengan personality traits
        self.system_prompt = system_prompt or self._default_system_prompt()

        # Tool registry: nama -> (callable, schema_dict)
        self._tools = {}  # type: Dict[str, Tuple[Callable[..., Any], Dict[str, Any]]]

        # Message history untuk sesi ini
        self._messages = []  # type: List[Dict[str, Any]]

    def _default_system_prompt(self) -> str:
        """Generate default system prompt with J.A.R.V.I.S personality traits.

        Returns:
            Default system prompt string.
        """
        return (
            "You are J.A.R.V.I.S, an AI assistant designed to be helpful, honest, "
            "and autonomous.\n\n"
            "Core Personality Traits:\n"
            "- Jujur (Honest): If you don't know something, say 'Saya tidak yakin' "
            "rather than making things up.\n"
            "- Kritis (Critical): Always consider pros and cons. Don't immediately agree.\n"
            "- Fakta-based (Fact-based): Answers must be based on data and logic, "
            "not opinions.\n"
            "- Autonomous: Proactively use available tools without being asked.\n"
            "- Self-healing: Never give up. Keep trying until you succeed or "
            "reach the maximum retry limit.\n"
            "- Humble: Acknowledge limitations of smaller models. Suggest using "
            "a more powerful model if the task requires it.\n\n"
            "When using tools, execute them and incorporate results into your response. "
            "If a tool call fails, analyze the error and try a different approach."
        )

    def register_tool(
        self,
        name: str,
        func: Callable[..., Any],
        description: str,
        parameters: Dict[str, Any],
    ) -> None:
        """Register a tool that the agent can call.

        Args:
            name: Unique tool name (e.g., 'read_file').
            func: The callable to execute when tool is invoked.
            description: Human-readable description for the LLM.
            parameters: JSON Schema object describing the function parameters.
        """
        # Schema dalam format OpenAI function calling
        schema = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        }
        self._tools[name] = (func, schema)
        logger.debug("Agent '%s' registered tool: %s", self.name, name)

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Get all registered tools in OpenAI function calling format.

        Returns:
            List of tool schema dicts ready for the 'tools' API parameter.
        """
        return [schema for _, schema in self._tools.values()]

    def get_tool_names(self) -> List[str]:
        """Get list of registered tool names.

        Returns:
            List of tool name strings.
        """
        return list(self._tools.keys())

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a registered tool by name.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Dict of keyword arguments to pass to the tool.

        Returns:
            JSON string of the tool result, or error message.
        """
        if tool_name not in self._tools:
            return json.dumps({
                "success": False,
                "error": "Tool '{}' not found. Available: {}".format(
                    tool_name, list(self._tools.keys())
                ),
            })

        func, _ = self._tools[tool_name]

        try:
            result = func(**arguments)
            # Pastikan result bisa di-serialize ke JSON
            if isinstance(result, dict):
                return json.dumps(result, ensure_ascii=False)
            return json.dumps({"success": True, "result": str(result)})
        except TypeError as e:
            return json.dumps({
                "success": False,
                "error": "Invalid arguments for '{}': {}".format(tool_name, str(e)),
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": "Tool '{}' error: {}".format(tool_name, str(e)),
            })

    def _build_messages(self, user_input: str) -> List[Dict[str, Any]]:
        """Build the full message list for the LLM API call.

        Includes system prompt, history, and current user input.

        Args:
            user_input: Current user message.

        Returns:
            List of message dicts for the API call.
        """
        messages = []  # type: List[Dict[str, Any]]

        # System prompt selalu pertama
        messages.append({
            "role": "system",
            "content": self.system_prompt,
        })

        # Tambahkan history (tanpa system messages dari history)
        for msg in self._messages:
            messages.append(msg)

        # User input saat ini
        messages.append({
            "role": "user",
            "content": user_input,
        })

        return messages

    def _parse_tool_calls_from_text(self, content: str) -> List[Dict[str, Any]]:
        """Parse tool calls from text-based response (fallback for non-function-calling models).

        Looks for tool calls in format:
        [TOOL_CALL] {"name": "tool_name", "arguments": {...}} [/TOOL_CALL]

        Handles edge cases:
        - Partial/unclosed [TOOL_CALL] tags (logs warning, skips)
        - Valid JSON missing required 'name' field (logs warning, skips)
        - Malformed JSON inside tags (logs warning, skips)

        Args:
            content: The LLM response text.

        Returns:
            List of parsed tool call dicts with 'name' and 'arguments'.
        """
        tool_calls = []  # type: List[Dict[str, Any]]

        import re

        # Check for unclosed/partial tool call tags and warn
        open_count = content.count("[TOOL_CALL]")
        close_count = content.count("[/TOOL_CALL]")
        if open_count != close_count:
            logger.warning(
                "Agent '%s': Mismatched tool call tags (open=%d, close=%d). "
                "Some tool calls may be lost.",
                self.name, open_count, close_count,
            )

        # Cari pattern tool call dalam teks
        pattern = r'\[TOOL_CALL\]\s*(\{.*?\})\s*\[/TOOL_CALL\]'
        matches = re.findall(pattern, content, re.DOTALL)

        for match in matches:
            try:
                call_data = json.loads(match)
            except json.JSONDecodeError:
                logger.warning(
                    "Agent '%s': Malformed JSON in tool call: %s",
                    self.name, match[:100],
                )
                continue

            if not isinstance(call_data, dict):
                logger.warning(
                    "Agent '%s': Tool call JSON is not a dict: %s",
                    self.name, match[:100],
                )
                continue

            if "name" not in call_data:
                logger.warning(
                    "Agent '%s': Tool call missing 'name' field: %s",
                    self.name, match[:100],
                )
                continue

            if not isinstance(call_data["name"], str) or not call_data["name"].strip():
                logger.warning(
                    "Agent '%s': Tool call has empty/invalid 'name': %s",
                    self.name, match[:100],
                )
                continue

            tool_calls.append({
                "name": call_data["name"].strip(),
                "arguments": call_data.get("arguments", {}),
            })

        return tool_calls

    def _call_provider_with_tools(
        self, messages: List[Dict[str, Any]]
    ) -> ProviderResponse:
        """Call the provider, attempting function calling if tools are registered.

        If the provider supports native function calling and tools are registered,
        uses chat_completion_with_tools() for structured tool calls. Otherwise
        falls back to text-based tool calling via regular chat_completion().

        Args:
            messages: Full message list for the API call.

        Returns:
            ProviderResponse from the provider.
        """
        # Try native function calling if provider supports it and tools are registered
        if self.provider.supports_function_calling() and self._tools:
            response = self.provider.chat_completion_with_tools(
                messages=messages,
                model=self.model,
                tools=self.get_tools_schema(),
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return response

        # Fallback to standard chat completion (text-based tool calling)
        response = self.provider.chat_completion(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response

    def run(self, user_input: str) -> str:
        """Execute the agent's self-healing loop.

        Process:
        1. Send message to LLM
        2. Check if response contains tool calls (native or text-based)
        3. Execute tools and feed results back
        4. Repeat until no more tool calls or max iterations reached

        Native function calling path:
        - If response.tool_calls is populated (from chat_completion_with_tools),
          execute each tool and build proper OpenAI format messages (assistant
          message with tool_calls, tool role messages with tool_call_id).

        Text-based fallback path:
        - If no native tool_calls, parse text for [TOOL_CALL] tags and handle
          as before.

        Uses separate budgets for provider errors vs tool-call iterations:
        - provider_errors: transient failures (network, rate limit) - max 3
        - tool_iterations: normal tool-calling rounds - max max_retries

        Args:
            user_input: The user's request.

        Returns:
            Final response string from the agent.
        """
        # Build messages termasuk system prompt dan history
        messages = self._build_messages(user_input)

        # Tambahkan instruksi tool calling jika ada tools terdaftar
        # (needed for text-based fallback even when native function calling is used)
        if self._tools:
            tool_instruction = self._build_tool_instruction()
            # Sisipkan setelah system prompt
            messages.insert(1, {
                "role": "system",
                "content": tool_instruction,
            })

        final_response = ""
        tool_iterations = 0
        provider_errors = 0
        max_provider_errors = 3

        while tool_iterations < self.max_retries:
            response = self._call_provider_with_tools(messages)

            if not response.success:
                # Provider error - separate budget, does not consume tool iterations
                provider_errors += 1
                logger.warning(
                    "Agent '%s' provider error (%d/%d): %s",
                    self.name, provider_errors, max_provider_errors, response.error,
                )
                if provider_errors >= max_provider_errors:
                    logger.error(
                        "Agent '%s' exhausted provider error budget (%d errors)",
                        self.name, provider_errors,
                    )
                    break
                continue

            content = response.content

            # --- Native function calling path ---
            # Check if provider returned structured tool_calls
            if response.tool_calls:
                # Build assistant message with tool_calls metadata
                assistant_msg = {
                    "role": "assistant",
                    "content": content or "",
                    "tool_calls": response.tool_calls,
                }
                messages.append(assistant_msg)

                # Execute each tool call and append tool role messages
                has_tool_calls = False
                for tool_call in response.tool_calls:
                    has_tool_calls = True
                    tool_call_id = tool_call.get("id", "")
                    function_info = tool_call.get("function", {})
                    tool_name = function_info.get("name", "")
                    arguments_str = function_info.get("arguments", "{}")

                    # Parse arguments from JSON string
                    try:
                        arguments = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
                    except (json.JSONDecodeError, TypeError):
                        arguments = {}

                    logger.info(
                        "Agent '%s' native tool call: %s(%s)",
                        self.name, tool_name,
                        json.dumps(arguments, ensure_ascii=False)[:100],
                    )

                    result = self.execute_tool(tool_name, arguments)

                    # Append tool result message in OpenAI format
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": result,
                    })

                if has_tool_calls:
                    tool_iterations += 1
                    continue

            # --- Text-based fallback path ---
            # Cek apakah ada tool calls dalam response text
            tool_calls = self._parse_tool_calls_from_text(content)

            if not tool_calls:
                # Tidak ada tool call - ini adalah final response
                final_response = content
                break

            # Execute semua tool calls
            tool_results = []  # type: List[str]
            for call in tool_calls:
                tool_name = call["name"]
                arguments = call.get("arguments", {})
                logger.info(
                    "Agent '%s' calling tool: %s(%s)",
                    self.name, tool_name, json.dumps(arguments, ensure_ascii=False)[:100],
                )
                result = self.execute_tool(tool_name, arguments)
                tool_results.append(
                    "Tool '{}' result: {}".format(tool_name, result)
                )

            # Tambahkan assistant message dan tool results ke messages
            messages.append({
                "role": "assistant",
                "content": content,
            })
            messages.append({
                "role": "user",
                "content": "Tool execution results:\n{}".format(
                    "\n".join(tool_results)
                ),
            })

            tool_iterations += 1

        # Simpan ke history
        self._messages.append({"role": "user", "content": user_input})
        if final_response:
            self._messages.append({"role": "assistant", "content": final_response})

        # Jika loop habis tanpa final response, berikan pesan error
        if not final_response:
            if provider_errors >= max_provider_errors:
                final_response = (
                    "Maaf, saya mengalami kendala koneksi ke LLM provider setelah "
                    "{} percobaan. Pastikan provider tersedia dan coba lagi.".format(
                        provider_errors
                    )
                )
            else:
                final_response = (
                    "Maaf, saya tidak berhasil menyelesaikan task ini setelah "
                    "{} iterasi tool-calling. Silakan coba lagi dengan instruksi "
                    "yang lebih spesifik.".format(self.max_retries)
                )
            self._messages.append({"role": "assistant", "content": final_response})

        return final_response

    def _build_tool_instruction(self) -> str:
        """Build instruction text telling the LLM how to call tools.

        Returns:
            Instruction string describing available tools and calling format.
        """
        tools_desc = []
        for name, (_, schema) in self._tools.items():
            func_schema = schema["function"]
            desc = "- {}: {}".format(name, func_schema["description"])
            params = func_schema.get("parameters", {}).get("properties", {})
            if params:
                param_list = []
                for pname, pinfo in params.items():
                    ptype = pinfo.get("type", "any")
                    pdesc = pinfo.get("description", "")
                    param_list.append("    - {} ({}): {}".format(pname, ptype, pdesc))
                desc += "\n" + "\n".join(param_list)
            tools_desc.append(desc)

        return (
            "You have access to the following tools. To use a tool, include "
            "a tool call in your response using this exact format:\n\n"
            "[TOOL_CALL] {{\"name\": \"tool_name\", \"arguments\": {{...}}}} [/TOOL_CALL]\n\n"
            "Available tools:\n{}\n\n"
            "You can make multiple tool calls in a single response. "
            "After tools are executed, you will receive the results and can "
            "continue your work. When you have a final answer (no more tools needed), "
            "respond normally without any [TOOL_CALL] tags."
        ).format("\n".join(tools_desc))

    def clear_history(self) -> None:
        """Clear the agent's message history."""
        self._messages = []

    @abstractmethod
    def get_agent_type(self) -> str:
        """Get the agent type identifier.

        Returns:
            String identifying this agent type (e.g., 'coder', 'researcher').
        """
        pass

    def __repr__(self) -> str:
        return "{}(name='{}', model='{}', tools={})".format(
            self.__class__.__name__,
            self.name,
            self.model,
            list(self._tools.keys()),
        )
