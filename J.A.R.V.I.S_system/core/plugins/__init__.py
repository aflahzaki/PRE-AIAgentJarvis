"""
Plugins - Dynamic agent discovery and loading for J.A.R.V.I.S system.

Available modules:
- PluginLoader: Auto-discovers and loads agent classes from *_agent.py files
"""

from core.plugins.plugin_loader import PluginLoader

__all__ = [
    "PluginLoader",
]
