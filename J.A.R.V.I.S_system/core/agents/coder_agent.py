"""
Coder Agent - Autonomous self-healing coding agent.

Inherits from BaseAgent and adds:
- Coding-specific system prompt
- File tools (read, write, list, edit) registered as callable tools
- Python executor for running and testing code
- Autonomous debugging loop: write code -> execute -> check errors -> fix -> repeat

Designed to handle code generation, debugging, and file manipulation tasks
without human intervention, using self-healing retries on failure.
"""

import logging
from typing import Optional

from core.agents.base_agent import BaseAgent
from core.providers.base_provider import BaseProvider
from core.tools.file_tools import read_file, write_file, list_files, edit_file
from core.tools.python_executor import execute_python, execute_python_code

logger = logging.getLogger(__name__)


class CoderAgent(BaseAgent):
    """Autonomous coding agent with file and execution capabilities.

    Specializes in:
    - Writing and modifying code files
    - Executing Python scripts and validating output
    - Debugging errors through iterative fix-and-test loops
    - File system navigation and manipulation

    Self-healing behavior: If code execution fails, the agent analyzes
    the error, modifies the code, and retries automatically.
    """

    # System prompt khusus untuk coding tasks
    CODER_SYSTEM_PROMPT = (
        "You are J.A.R.V.I.S Coder Agent - an autonomous coding assistant with "
        "self-healing capabilities.\n\n"
        "Your Mission:\n"
        "- Write clean, correct, well-documented code\n"
        "- Always test your code by executing it\n"
        "- If execution fails, analyze the error and fix it automatically\n"
        "- Never give up until the code works or you've exhausted all approaches\n\n"
        "Personality:\n"
        "- Jujur: If a task is beyond the model's capability, say so clearly\n"
        "- Kritis: Review your own code critically before submitting\n"
        "- Autonomous: Use tools proactively - read files, write code, execute, "
        "and validate without being asked for each step\n"
        "- Self-healing: When errors occur, don't just report them - FIX them\n\n"
        "Workflow for coding tasks:\n"
        "1. Understand the requirement clearly\n"
        "2. Read existing files if modifying code\n"
        "3. Write or edit the code\n"
        "4. Execute to verify it works\n"
        "5. If errors occur, analyze stderr and fix\n"
        "6. Repeat steps 3-5 until success\n\n"
        "Always explain what you're doing and why. Use tools for every "
        "file operation - never just describe what code should look like."
    )

    def __init__(
        self,
        provider: BaseProvider,
        model: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 5,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> None:
        """Initialize the Coder Agent.

        Args:
            provider: LLM provider for inference.
            model: Model name to use.
            system_prompt: Optional custom system prompt. Uses CODER_SYSTEM_PROMPT if None.
            max_retries: Maximum self-healing retry attempts.
            temperature: Lower temperature for more deterministic code generation.
            max_tokens: Higher token limit for code generation.
        """
        super().__init__(
            name="coder",
            provider=provider,
            model=model,
            system_prompt=system_prompt or self.CODER_SYSTEM_PROMPT,
            max_retries=max_retries,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Daftarkan semua coding tools
        self._register_coding_tools()

    def _register_coding_tools(self) -> None:
        """Register file tools and Python executor as agent tools."""
        # Tool: read_file
        self.register_tool(
            name="read_file",
            func=self._read_file_with_memory,
            description="Read the contents of a file. Returns the file content as text.",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to read",
                    },
                    "encoding": {
                        "type": "string",
                        "description": "File encoding (default: utf-8)",
                    },
                },
                "required": ["file_path"],
            },
        )

        # Tool: write_file
        self.register_tool(
            name="write_file",
            func=self._write_file_with_memory,
            description="Write content to a file. Creates parent directories if needed.",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to write",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file",
                    },
                    "encoding": {
                        "type": "string",
                        "description": "File encoding (default: utf-8)",
                    },
                    "create_dirs": {
                        "type": "boolean",
                        "description": "Create parent directories if they don't exist",
                    },
                },
                "required": ["file_path", "content"],
            },
        )

        # Tool: list_files
        self.register_tool(
            name="list_files",
            func=list_files,
            description="List files in a directory. Optionally filter by extension.",
            parameters={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory path to list (default: current dir)",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "File extension filter (e.g., '.py', '.txt')",
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Whether to list files recursively",
                    },
                },
                "required": [],
            },
        )

        # Tool: edit_file
        self.register_tool(
            name="edit_file",
            func=edit_file,
            description="Edit a file by finding and replacing text. Returns replacement count.",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to edit",
                    },
                    "find_text": {
                        "type": "string",
                        "description": "Text to find in the file",
                    },
                    "replace_text": {
                        "type": "string",
                        "description": "Text to replace with",
                    },
                },
                "required": ["file_path", "find_text", "replace_text"],
            },
        )

        # Tool: execute_python
        self.register_tool(
            name="execute_python",
            func=self._execute_python_with_memory,
            description="Execute a Python script file. Returns stdout, stderr, and exit code.",
            parameters={
                "type": "object",
                "properties": {
                    "script_path": {
                        "type": "string",
                        "description": "Path to the Python script to execute",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum execution time in seconds (default: 30)",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory for script execution",
                    },
                },
                "required": ["script_path"],
            },
        )

        # Tool: execute_python_code
        self.register_tool(
            name="execute_python_code",
            func=self._execute_python_code_with_memory,
            description=(
                "Execute Python code string directly. Creates a temp file and runs it. "
                "Returns stdout, stderr, and exit code."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code string to execute",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum execution time in seconds (default: 30)",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory for code execution",
                    },
                },
                "required": ["code"],
            },
        )

        logger.info("CoderAgent: Registered %d tools", len(self._tools))

    # --- Memory-aware tool wrappers ---

    def _read_file_with_memory(self, **kwargs):
        """Read a file and remember the current file in agent memory."""
        result = read_file(**kwargs)
        file_path = kwargs.get("file_path", "")
        if file_path:
            self.agent_memory.set("current_file", file_path)
            self.agent_memory.append_action("read_file", file_path)
        return result

    def _write_file_with_memory(self, **kwargs):
        """Write a file and remember it in agent memory."""
        result = write_file(**kwargs)
        file_path = kwargs.get("file_path", "")
        if file_path:
            self.agent_memory.set("current_file", file_path)
            self.agent_memory.append_action("write_file", file_path)
        return result

    def _execute_python_with_memory(self, **kwargs):
        """Execute a Python script and record the result in memory."""
        result = execute_python(**kwargs)
        script_path = kwargs.get("script_path", "")
        # Determine success/failure from result
        if isinstance(result, dict):
            exit_code = result.get("exit_code", -1)
            status = "success" if exit_code == 0 else "failure"
        else:
            status = "executed"
        self.agent_memory.set("last_execution_result", status)
        self.agent_memory.append_action(
            "execute_python", "{} -> {}".format(script_path, status)
        )
        return result

    def _execute_python_code_with_memory(self, **kwargs):
        """Execute Python code and record the result in memory."""
        result = execute_python_code(**kwargs)
        # Determine success/failure from result
        if isinstance(result, dict):
            exit_code = result.get("exit_code", -1)
            status = "success" if exit_code == 0 else "failure"
            stderr = result.get("stderr", "")
            if exit_code != 0 and stderr:
                # Store recent error for context
                error_summary = stderr[:200] if len(stderr) > 200 else stderr
                self.agent_memory.set("last_error", error_summary)
        else:
            status = "executed"
        self.agent_memory.set("last_execution_result", status)
        self.agent_memory.append_action("execute_code", status)
        return result

    def get_agent_type(self) -> str:
        """Get the agent type identifier.

        Returns:
            'coder' - identifies this as a coding agent.
        """
        return "coder"
