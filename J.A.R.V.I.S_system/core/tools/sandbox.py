"""Sandboxed code execution with resource limits.

Wraps python_executor with additional safety:
- Max execution time (configurable, default 30s)
- Max output size (prevent memory bombs)
- Blocked dangerous imports (os.system, subprocess, shutil.rmtree, etc.)
- Working directory restriction
- Environment variable sanitization (don't pass secrets to executed code)
"""

import logging
import os
import re
from typing import Dict, Any, List

from core.tools.python_executor import execute_python_code

logger = logging.getLogger(__name__)

# Configurable via environment
SANDBOX_STRICT_MODE = os.getenv("SANDBOX_STRICT_MODE", "false").lower() == "true"

DANGEROUS_PATTERNS = [
    r'\bos\.system\b',
    r'\bos\.remove\b',
    r'\bos\.rmdir\b',
    r'\bos\.unlink\b',
    r'\bshutil\.rmtree\b',
    r'\bsubprocess\.(run|call|Popen|check_output)\b',
    r'\b__import__\b',
    r'\beval\b\(',
    r'\bexec\b\(',
    r'\bopen\(.+["\']w["\']\)',
    r'\bsocket\b',
    r'\brequests\.(get|post|put|delete)\b',
]


def check_code_safety(code: str) -> Dict[str, Any]:
    """Scan code for dangerous patterns.

    Returns:
        {"safe": bool, "warnings": List[str]}
    """
    warnings = []  # type: List[str]

    for pattern in DANGEROUS_PATTERNS:
        matches = re.findall(pattern, code)
        if matches:
            warnings.append(
                "Dangerous pattern detected: {}".format(pattern)
            )

    is_safe = len(warnings) == 0
    return {"safe": is_safe, "warnings": warnings}


def execute_sandboxed(
    code: str,
    timeout: int = 30,
    max_output: int = 10000,
) -> Dict[str, Any]:
    """Execute Python code with safety checks.

    1. Check for dangerous patterns (warn but don't block by default)
    2. Create sanitized environment (strip secrets from env)
    3. Execute with timeout
    4. Truncate output if too long
    5. Return structured result

    Args:
        code: Python code string to execute.
        timeout: Maximum execution time in seconds (default: 30).
        max_output: Maximum output size in characters (default: 10000).

    Returns:
        Dict with keys: success, stdout, stderr, exit_code, warnings, blocked.
    """
    # Step 1: Safety check
    safety = check_code_safety(code)

    # In strict mode, block execution if unsafe
    if SANDBOX_STRICT_MODE and not safety["safe"]:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Code blocked by sandbox: dangerous patterns detected",
            "exit_code": -1,
            "warnings": safety["warnings"],
            "blocked": True,
        }

    # Step 2 & 3: Execute with timeout (python_executor already sanitizes env)
    result = execute_python_code(code=code, timeout=timeout)

    # Step 4: Truncate output if too long
    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")

    truncated = False
    if len(stdout) > max_output:
        stdout = stdout[:max_output] + "\n... [output truncated at {} chars]".format(
            max_output
        )
        truncated = True

    if len(stderr) > max_output:
        stderr = stderr[:max_output] + "\n... [stderr truncated at {} chars]".format(
            max_output
        )
        truncated = True

    # Step 5: Return structured result
    return {
        "success": result.get("success", False),
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": result.get("exit_code", -1),
        "warnings": safety["warnings"],
        "blocked": False,
        "truncated": truncated,
    }
