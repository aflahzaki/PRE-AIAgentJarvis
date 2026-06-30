"""
Python Executor - Sandboxed Python script execution with timeout.

Executes Python scripts via subprocess with configurable timeout.
Captures stdout/stderr and returns structured results.
Designed for autonomous code execution by J.A.R.V.I.S agents.

Security measures:
- Path restriction: scripts must be within the workspace directory
- Isolated execution: uses -I flag (isolated mode) to prevent import tricks
- Restricted environment: only essential env vars are passed to subprocess
- Timeout enforcement: prevents infinite loops and resource exhaustion
"""

import logging
import os
import subprocess
import sys
import tempfile
from typing import Dict, Optional, Union

logger = logging.getLogger(__name__)

# Default timeout: 30 detik untuk mencegah infinite loops
DEFAULT_TIMEOUT = 30

# Import workspace root from file_tools for consistent path restriction
_WORKSPACE_ROOT = os.path.abspath(
    os.getenv("JARVIS_WORKSPACE", os.getcwd())
)

# Safe environment variables to pass to subprocess
_SAFE_ENV_KEYS = [
    "PATH", "HOME", "USER", "LANG", "LC_ALL", "PYTHONPATH",
    "PYTHONIOENCODING", "TERM", "TMPDIR", "TEMP", "TMP",
]


def _get_restricted_env() -> Dict[str, str]:
    """Build a restricted environment for subprocess execution.

    Only passes essential environment variables to prevent leaking
    sensitive data (API keys, tokens) to executed scripts.

    Returns:
        Dict of environment variables for subprocess.
    """
    env = {}
    for key in _SAFE_ENV_KEYS:
        val = os.environ.get(key)
        if val is not None:
            env[key] = val
    # Ensure UTF-8 encoding
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _validate_script_path(script_path: str) -> tuple:
    """Validate that a script path is within the workspace.

    Args:
        script_path: Path to validate.

    Returns:
        Tuple of (is_valid: bool, abs_path: str, error: str or None).
    """
    abs_path = os.path.abspath(script_path)
    workspace = _WORKSPACE_ROOT

    if not (abs_path == workspace or abs_path.startswith(workspace + os.sep)):
        return (
            False,
            abs_path,
            "Access denied: script '{}' is outside workspace '{}'".format(
                script_path, workspace
            ),
        )
    return (True, abs_path, None)


def execute_python(
    script_path: str,
    timeout: int = DEFAULT_TIMEOUT,
    cwd: Optional[str] = None,
) -> Dict[str, Union[str, int, bool]]:
    """Execute a Python script file with timeout and sandboxing.

    Security: Script must be within the workspace directory. Execution
    uses isolated mode (-I) and a restricted environment that excludes
    sensitive variables like API keys.

    Args:
        script_path: Path to the Python script to execute (must be in workspace).
        timeout: Maximum execution time in seconds (default: 30).
        cwd: Working directory for script execution (must be in workspace).

    Returns:
        Dict with 'success', 'stdout', 'stderr', 'exit_code', or 'error' keys.
    """
    try:
        # Validate script path is within workspace
        is_valid, abs_path, error = _validate_script_path(script_path)
        if not is_valid:
            return {
                "success": False,
                "error": error,
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
            }

        if not os.path.exists(abs_path):
            return {
                "success": False,
                "error": "Script not found: {}".format(script_path),
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
            }

        if not abs_path.endswith(".py"):
            return {
                "success": False,
                "error": "Not a Python file: {}".format(script_path),
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
            }

        # Validate cwd is within workspace if provided
        exec_cwd = cwd or os.path.dirname(abs_path)
        if exec_cwd:
            cwd_abs = os.path.abspath(exec_cwd)
            if not (cwd_abs == _WORKSPACE_ROOT or cwd_abs.startswith(_WORKSPACE_ROOT + os.sep)):
                return {
                    "success": False,
                    "error": "Access denied: cwd '{}' is outside workspace".format(exec_cwd),
                    "stdout": "",
                    "stderr": "",
                    "exit_code": -1,
                }

        # Gunakan interpreter Python yang sama dengan yang menjalankan J.A.R.V.I.S
        # -I flag: isolated mode (no user site-packages, ignores PYTHON* env vars)
        python_exe = sys.executable

        result = subprocess.run(
            [python_exe, "-I", abs_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=exec_cwd,
            env=_get_restricted_env(),
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Script timed out after {} seconds".format(timeout),
            "stdout": "",
            "stderr": "TimeoutError: Execution exceeded {}s limit".format(timeout),
            "exit_code": -1,
        }
    except PermissionError:
        return {
            "success": False,
            "error": "Permission denied: {}".format(script_path),
            "stdout": "",
            "stderr": "",
            "exit_code": -1,
        }
    except Exception as e:
        return {
            "success": False,
            "error": "Execution error: {}".format(str(e)),
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
        }


def execute_python_code(
    code: str,
    timeout: int = DEFAULT_TIMEOUT,
    cwd: Optional[str] = None,
) -> Dict[str, Union[str, int, bool]]:
    """Execute Python code string with timeout.

    Creates a temporary file within the workspace and executes it.
    Useful for running dynamically generated code.

    Args:
        code: Python code string to execute.
        timeout: Maximum execution time in seconds (default: 30).
        cwd: Working directory for code execution (must be in workspace).

    Returns:
        Dict with 'success', 'stdout', 'stderr', 'exit_code', or 'error' keys.
    """
    temp_file_path = None
    try:
        # Create temp file within workspace to pass path validation
        workspace_tmp = os.path.join(_WORKSPACE_ROOT, ".tmp")
        os.makedirs(workspace_tmp, exist_ok=True)

        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            encoding="utf-8",
            dir=workspace_tmp,
        )
        temp_file.write(code)
        temp_file.close()
        temp_file_path = temp_file.name

        # Execute file temporary
        result = execute_python(
            script_path=temp_file_path,
            timeout=timeout,
            cwd=cwd or _WORKSPACE_ROOT,
        )
        return result

    except Exception as e:
        return {
            "success": False,
            "error": "Error executing code: {}".format(str(e)),
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
        }
    finally:
        # Bersihkan file temporary
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass
