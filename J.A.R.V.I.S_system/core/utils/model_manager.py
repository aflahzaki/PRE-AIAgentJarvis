"""Model Manager - Auto-detect and suggest Ollama model downloads.

On startup, checks which recommended models are available locally
and suggests downloading missing ones.
"""

import subprocess
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

RECOMMENDED_MODELS = {
    "small": {
        "name": "llama3.2:3b",
        "size": "~2GB",
        "use": "Simple tasks, greetings, quick answers",
    },
    "medium": {
        "name": "qwen2.5-coder:7b",
        "size": "~4.7GB",
        "use": "Coding, general tasks, tool calling",
    },
    "alternative": {
        "name": "mistral:7b",
        "size": "~4.1GB",
        "use": "General purpose, good reasoning",
    },
}


class ModelManager:
    """Manage local Ollama models."""

    def check_ollama_installed(self) -> bool:
        """Check if Ollama CLI is available."""
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def check_ollama_running(self) -> bool:
        """Check if Ollama server is running."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_installed_models(self) -> List[str]:
        """Get list of locally installed Ollama models."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return []
            lines = result.stdout.strip().split("\n")[1:]  # skip header
            return [line.split()[0] for line in lines if line.strip()]
        except Exception:
            return []

    def get_missing_models(self) -> List[Dict[str, str]]:
        """Check which recommended models are not installed."""
        installed = self.get_installed_models()
        missing = []
        for tier, info in RECOMMENDED_MODELS.items():
            if info["name"] not in installed:
                missing.append({**info, "tier": tier})
        return missing

    def pull_model(self, model_name: str) -> bool:
        """Download/pull a model via Ollama CLI.
        Shows progress via subprocess.
        """
        try:
            result = subprocess.run(
                ["ollama", "pull", model_name],
                timeout=600,  # 10 min timeout for large models
            )
            return result.returncode == 0
        except Exception:
            return False

    def suggest_downloads(self) -> str:
        """Generate suggestion text for missing models."""
        missing = self.get_missing_models()
        if not missing:
            return ""
        lines = ["Recommended models not yet installed:"]
        for m in missing:
            lines.append("  - {} ({}) - {}".format(m["name"], m["size"], m["use"]))
        lines.append("\nDownload with: ollama pull <model_name>")
        return "\n".join(lines)

    def get_model_status(self) -> Dict[str, List[Dict[str, str]]]:
        """Get full model status: installed and missing models.

        Returns:
            Dict with 'installed' and 'missing' keys.
        """
        installed = self.get_installed_models()
        missing = self.get_missing_models()
        return {
            "installed": [{"name": m} for m in installed],
            "missing": missing,
        }
