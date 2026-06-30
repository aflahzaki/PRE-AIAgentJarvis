"""
Plugin Loader - Dynamic agent discovery and loading for J.A.R.V.I.S.

Auto-discovers all *_agent.py files in the agents directory, imports
them dynamically using importlib, and extracts agent classes that
inherit from BaseAgent. Supports enable/disable via config.

Features:
- Auto-discovery of agent files matching *_agent.py pattern
- Dynamic import via importlib
- Class extraction (finds classes inheriting BaseAgent)
- Enable/disable agents via config dict
- Get available agents dict (name -> class)
"""

import importlib
import importlib.util
import inspect
import logging
import os
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


class PluginLoader:
    """Dynamic agent plugin loader with auto-discovery.

    Discovers and loads agent classes from Python files matching
    the *_agent.py naming convention. Uses importlib for dynamic
    importing without requiring pre-registration.

    Attributes:
        agents: Dict of agent_type -> agent_class.
        disabled: Set of disabled agent types.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the plugin loader.

        Args:
            config: Optional configuration dict. Supports:
                    'disabled_agents': list of agent type strings to skip.
        """
        self._agents: Dict[str, Type] = {}
        self._modules: Dict[str, Any] = {}
        self._disabled: set = set()

        if config and "disabled_agents" in config:
            self._disabled = set(config["disabled_agents"])

        logger.info("PluginLoader: Initialized")

    def discover_agents(
        self, agents_dir: str = "core/agents"
    ) -> Dict[str, Type]:
        """Auto-discover agent classes from *_agent.py files.

        Scans the specified directory for files matching *_agent.py,
        imports each module, and extracts classes that inherit from BaseAgent.

        Args:
            agents_dir: Path to the agents directory (relative or absolute).

        Returns:
            Dict of agent_type -> agent_class for all discovered agents.
        """
        # Resolve path
        if not os.path.isabs(agents_dir):
            # Try relative to current working directory
            abs_dir = os.path.abspath(agents_dir)
        else:
            abs_dir = agents_dir

        if not os.path.isdir(abs_dir):
            logger.warning(
                "PluginLoader: Agents directory not found: %s", abs_dir
            )
            return {}

        discovered = {}

        # Find all *_agent.py files
        for filename in sorted(os.listdir(abs_dir)):
            if not filename.endswith("_agent.py"):
                continue

            # Skip base_agent.py
            if filename == "base_agent.py":
                continue

            module_name = filename[:-3]  # Remove .py
            file_path = os.path.join(abs_dir, filename)

            try:
                agent_class = self.load_agent(file_path, module_name)
                if agent_class is not None:
                    # Get agent type from a temporary check
                    agent_type = self._get_agent_type_from_class(agent_class)
                    if agent_type:
                        if agent_type in self._disabled:
                            logger.info(
                                "PluginLoader: Agent '%s' is disabled, skipping",
                                agent_type,
                            )
                            continue
                        discovered[agent_type] = agent_class
                        self._agents[agent_type] = agent_class
                        logger.debug(
                            "PluginLoader: Discovered '%s' from %s",
                            agent_type, filename,
                        )
            except Exception as e:
                logger.error(
                    "PluginLoader: Error loading %s: %s", filename, str(e)
                )
                continue

        logger.info(
            "PluginLoader: Discovered %d agents: %s",
            len(discovered), list(discovered.keys()),
        )

        return discovered

    def load_agent(
        self, file_path: str, module_name: Optional[str] = None
    ) -> Optional[Type]:
        """Import and load an agent class from a file.

        Args:
            file_path: Full path to the agent Python file.
            module_name: Optional module name override.

        Returns:
            The agent class (inheriting BaseAgent), or None if not found.
        """
        if not os.path.isfile(file_path):
            logger.warning("PluginLoader: File not found: %s", file_path)
            return None

        if module_name is None:
            module_name = os.path.basename(file_path)[:-3]

        # Construct the import path
        # Convert file path to module dotted path
        dotted_path = self._file_to_module_path(file_path)

        try:
            if dotted_path:
                # Try standard import first
                module = importlib.import_module(dotted_path)
            else:
                # Fallback: use importlib.util for arbitrary paths
                spec = importlib.util.spec_from_file_location(
                    module_name, file_path
                )
                if spec is None or spec.loader is None:
                    logger.warning(
                        "PluginLoader: Could not create spec for %s", file_path
                    )
                    return None
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

            self._modules[module_name] = module

            # Find the agent class in the module
            agent_class = self._find_agent_class(module)
            return agent_class

        except Exception as e:
            logger.error(
                "PluginLoader: Import error for '%s': %s",
                module_name, str(e),
            )
            return None

    def get_available_agents(self) -> Dict[str, Type]:
        """Get all discovered and enabled agent classes.

        Returns:
            Dict of agent_type -> agent_class.
        """
        return dict(self._agents)

    def get_agent_class(self, agent_type: str) -> Optional[Type]:
        """Get a specific agent class by type.

        Args:
            agent_type: Agent type string (e.g., 'coder', 'web_search').

        Returns:
            Agent class, or None if not found.
        """
        return self._agents.get(agent_type)

    def enable_agent(self, agent_type: str) -> None:
        """Enable a previously disabled agent.

        Args:
            agent_type: Agent type to enable.
        """
        self._disabled.discard(agent_type)
        logger.info("PluginLoader: Enabled agent '%s'", agent_type)

    def disable_agent(self, agent_type: str) -> None:
        """Disable an agent (won't be loaded on next discover).

        Args:
            agent_type: Agent type to disable.
        """
        self._disabled.add(agent_type)
        # Remove from loaded agents
        self._agents.pop(agent_type, None)
        logger.info("PluginLoader: Disabled agent '%s'", agent_type)

    def _find_agent_class(self, module: Any) -> Optional[Type]:
        """Find the agent class in a module.

        Looks for classes that inherit from BaseAgent (but are not
        BaseAgent itself).

        Args:
            module: Imported module to search.

        Returns:
            Agent class, or None if not found.
        """
        try:
            from core.agents.base_agent import BaseAgent
        except ImportError:
            logger.error("PluginLoader: Cannot import BaseAgent")
            return None

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, BaseAgent)
                and obj is not BaseAgent
                and obj.__module__ == module.__name__
            ):
                return obj

        return None

    def _get_agent_type_from_class(self, agent_class: Type) -> Optional[str]:
        """Extract agent_type from an agent class without instantiation.

        Checks for get_agent_type method or derives from class name.

        Args:
            agent_class: The agent class to inspect.

        Returns:
            Agent type string, or None.
        """
        # Try to derive from class name
        # e.g., WebSearchAgent -> web_search, CoderAgent -> coder
        class_name = agent_class.__name__

        if class_name.endswith("Agent"):
            # Remove 'Agent' suffix and convert CamelCase to snake_case
            name = class_name[:-5]  # Remove 'Agent'
            # CamelCase to snake_case
            import re
            snake = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
            return snake

        return class_name.lower()

    @staticmethod
    def _file_to_module_path(file_path: str) -> Optional[str]:
        """Convert a file path to a Python module dotted path.

        Args:
            file_path: File path like 'core/agents/web_search_agent.py'.

        Returns:
            Dotted path like 'core.agents.web_search_agent', or None.
        """
        # Normalize path
        file_path = os.path.normpath(file_path)

        # Remove .py extension
        if file_path.endswith(".py"):
            file_path = file_path[:-3]

        # Try to construct dotted path
        # Look for 'core' in the path
        parts = file_path.replace(os.sep, "/").split("/")

        try:
            core_idx = parts.index("core")
            module_parts = parts[core_idx:]
            return ".".join(module_parts)
        except ValueError:
            return None

    def __repr__(self) -> str:
        return "PluginLoader(agents={}, disabled={})".format(
            list(self._agents.keys()),
            list(self._disabled),
        )
