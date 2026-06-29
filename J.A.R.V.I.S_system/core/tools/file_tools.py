"""
File Tools - Pure Python file operations for J.A.R.V.I.S agents.

Provides read, write, list, and edit (find & replace) capabilities.
All functions return structured dict results with success/error status.
No external dependencies required.
"""

import logging
import os
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def read_file(file_path: str, encoding: str = "utf-8") -> Dict[str, Union[str, bool]]:
    """Read content from a file.

    Args:
        file_path: Path to the file to read.
        encoding: File encoding (default: utf-8).

    Returns:
        Dict with 'success', 'content' or 'error' keys.
    """
    try:
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            return {
                "success": False,
                "error": "File not found: {}".format(file_path),
            }

        if not os.path.isfile(abs_path):
            return {
                "success": False,
                "error": "Path is not a file: {}".format(file_path),
            }

        with open(abs_path, "r", encoding=encoding) as f:
            content = f.read()

        return {
            "success": True,
            "content": content,
            "path": abs_path,
            "size": len(content),
        }

    except PermissionError:
        return {
            "success": False,
            "error": "Permission denied: {}".format(file_path),
        }
    except UnicodeDecodeError as e:
        return {
            "success": False,
            "error": "Encoding error reading {}: {}".format(file_path, str(e)),
        }
    except Exception as e:
        return {
            "success": False,
            "error": "Error reading file: {}".format(str(e)),
        }


def write_file(
    file_path: str,
    content: str,
    encoding: str = "utf-8",
    create_dirs: bool = True,
) -> Dict[str, Union[str, bool]]:
    """Write content to a file.

    Args:
        file_path: Path to the file to write.
        content: Content to write.
        encoding: File encoding (default: utf-8).
        create_dirs: Whether to create parent directories if they don't exist.

    Returns:
        Dict with 'success' and 'path' or 'error' keys.
    """
    try:
        abs_path = os.path.abspath(file_path)

        # Buat direktori parent jika diperlukan
        if create_dirs:
            dir_path = os.path.dirname(abs_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)

        with open(abs_path, "w", encoding=encoding) as f:
            f.write(content)

        return {
            "success": True,
            "path": abs_path,
            "size": len(content),
        }

    except PermissionError:
        return {
            "success": False,
            "error": "Permission denied: {}".format(file_path),
        }
    except Exception as e:
        return {
            "success": False,
            "error": "Error writing file: {}".format(str(e)),
        }


def list_files(
    directory: str = ".",
    pattern: Optional[str] = None,
    recursive: bool = False,
) -> Dict[str, Union[List[str], bool, str]]:
    """List files in a directory.

    Args:
        directory: Directory path to list.
        pattern: Optional file extension filter (e.g., '.py', '.txt').
        recursive: Whether to list files recursively.

    Returns:
        Dict with 'success', 'files' list or 'error' keys.
    """
    try:
        abs_dir = os.path.abspath(directory)
        if not os.path.exists(abs_dir):
            return {
                "success": False,
                "error": "Directory not found: {}".format(directory),
            }

        if not os.path.isdir(abs_dir):
            return {
                "success": False,
                "error": "Path is not a directory: {}".format(directory),
            }

        files = []  # type: List[str]

        if recursive:
            for root, dirs, filenames in os.walk(abs_dir):
                for filename in filenames:
                    if pattern is None or filename.endswith(pattern):
                        rel_path = os.path.relpath(
                            os.path.join(root, filename), abs_dir
                        )
                        files.append(rel_path)
        else:
            for item in os.listdir(abs_dir):
                item_path = os.path.join(abs_dir, item)
                if os.path.isfile(item_path):
                    if pattern is None or item.endswith(pattern):
                        files.append(item)

        files.sort()
        return {
            "success": True,
            "files": files,
            "directory": abs_dir,
            "count": len(files),
        }

    except PermissionError:
        return {
            "success": False,
            "error": "Permission denied: {}".format(directory),
        }
    except Exception as e:
        return {
            "success": False,
            "error": "Error listing files: {}".format(str(e)),
        }


def edit_file(
    file_path: str,
    find_text: str,
    replace_text: str,
    encoding: str = "utf-8",
) -> Dict[str, Union[str, bool, int]]:
    """Edit a file by finding and replacing text.

    Args:
        file_path: Path to the file to edit.
        find_text: Text to find.
        replace_text: Text to replace with.
        encoding: File encoding (default: utf-8).

    Returns:
        Dict with 'success', 'replacements' count or 'error' keys.
    """
    try:
        # Pertama baca file
        read_result = read_file(file_path, encoding)
        if not read_result["success"]:
            return read_result

        content = read_result["content"]
        assert isinstance(content, str)

        # Hitung jumlah penggantian
        count = content.count(find_text)
        if count == 0:
            return {
                "success": False,
                "error": "Text not found in file: '{}'".format(
                    find_text[:50] + "..." if len(find_text) > 50 else find_text
                ),
            }

        # Lakukan penggantian
        new_content = content.replace(find_text, replace_text)

        # Tulis kembali
        write_result = write_file(file_path, new_content, encoding, create_dirs=False)
        if not write_result["success"]:
            return write_result

        return {
            "success": True,
            "path": os.path.abspath(file_path),
            "replacements": count,
        }

    except Exception as e:
        return {
            "success": False,
            "error": "Error editing file: {}".format(str(e)),
        }
