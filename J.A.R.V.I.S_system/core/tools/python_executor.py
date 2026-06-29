"""
Python Executor - Safe Python script execution with timeout.

Executes Python scripts via subprocess with configurable timeout.
Captures stdout/stderr and returns structured results.
Designed for autonomous code execution by J.A.R.V.I.S agents.
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


def execute_python(
    script_path: str,
    timeout: int = DEFAULT_TIMEOUT,
    cwd: Optional[str] = None,
) -> Dict[str, Union[str, int, bool]]:
    """Execute a Python script file with timeout.

    Args:
        script_path: Path to the Python script to execute.
        timeout: Maximum execution time in seconds (default: 30).
        cwd: Working directory for script execution.

    Returns:
        Dict with 'success', 'stdout', 'stderr', 'exit_code', or 'error' keys.
    """
    try:
        abs_path = os.path.abspath(script_path)
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

        # Gunakan interpreter Python yang sama dengan yang menjalankan J.A.R.V.I.S
        python_exe = sys.executable

        result = subprocess.run(
            [python_exe, abs_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or os.path.dirname(abs_path),
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

    Creates a temporary file and executes it. Useful for running
    dynamically generated code.

    Args:
        code: Python code string to execute.
        timeout: Maximum execution time in seconds (default: 30).
        cwd: Working directory for code execution.

    Returns:
        Dict with 'success', 'stdout', 'stderr', 'exit_code', or 'error' keys.
    """
    temp_file = None
    try:
        # Buat file temporary untuk code
        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            encoding="utf-8",
        )
        temp_file.write(code)
        temp_file.close()

        # Execute file temporary
        result = execute_python(
            script_path=temp_file.name,
            timeout=timeout,
            cwd=cwd,
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
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except OSError:
                pass
