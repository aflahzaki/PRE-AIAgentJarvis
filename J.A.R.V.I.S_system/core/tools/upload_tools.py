"""
Upload Tools - File upload processing for J.A.R.V.I.S Knowledge Base.

Provides functions to upload files and directories to the knowledge base.
Files are loaded via DocumentLoader, optionally chunked, and stored as
knowledge entries.

Dependencies:
    - core.knowledge.document_loader (DocumentLoader)
    - core.knowledge.knowledge_base (KnowledgeBase)
"""

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Lazy-loaded singletons
_document_loader = None
_knowledge_base = None


def _get_document_loader():
    """Get or create the singleton DocumentLoader instance.

    Returns:
        DocumentLoader instance.
    """
    global _document_loader
    if _document_loader is None:
        from core.knowledge.document_loader import DocumentLoader
        _document_loader = DocumentLoader()
    return _document_loader


def _get_knowledge_base():
    """Get or create the singleton KnowledgeBase instance.

    Returns:
        KnowledgeBase instance, or None if unavailable.
    """
    global _knowledge_base
    if _knowledge_base is None:
        try:
            from core.knowledge.knowledge_base import KnowledgeBase
            _knowledge_base = KnowledgeBase()
        except Exception as e:
            logger.error("Failed to initialize KnowledgeBase: %s", str(e))
            return None
    return _knowledge_base


def upload_to_knowledge_base(
    file_path: str,
    category: str = "uploaded",
    tags: str = "",
    chunk: bool = True,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> Dict[str, Any]:
    """Upload a file to the knowledge base.

    Process:
    1. Load file via DocumentLoader
    2. Chunk if too long (>chunk_size chars) and chunk=True
    3. Store each chunk as knowledge entry
    4. Return summary of entries created

    Args:
        file_path: Path to the file to upload.
        category: Category for the knowledge entries (default: 'uploaded').
        tags: Comma-separated tags for the entries.
        chunk: Whether to chunk long content (default: True).
        chunk_size: Target chunk size in characters (default: 1000).
        chunk_overlap: Overlap between chunks in characters (default: 200).

    Returns:
        Dict with keys:
            - 'success': bool
            - 'entries_created': int
            - 'filename': str
            - 'error': str (only if success is False)
    """
    if not file_path or not file_path.strip():
        return {"success": False, "error": "File path cannot be empty."}

    file_path = file_path.strip()

    # Load file
    loader = _get_document_loader()
    result = loader.load_file(file_path)

    if not result.get("success"):
        return {
            "success": False,
            "error": result.get("error", "Failed to load file."),
            "filename": os.path.basename(file_path),
        }

    content = result["content"]
    metadata = result["metadata"]
    filename = metadata.get("filename", os.path.basename(file_path))

    # Get knowledge base
    kb = _get_knowledge_base()
    if kb is None or not kb.is_available:
        return {
            "success": False,
            "error": "Knowledge base not available.",
            "filename": filename,
        }

    # Prepare tags
    entry_tags = tags.strip() if tags else ""
    format_tag = "format:{}".format(metadata.get("format", "unknown"))
    if entry_tags:
        entry_tags = "{}, {}".format(entry_tags, format_tag)
    else:
        entry_tags = format_tag

    # Chunk if needed
    entries_created = 0

    if chunk and len(content) > chunk_size:
        chunks = loader.chunk_text(content, chunk_size=chunk_size, overlap=chunk_overlap)

        for i, chunk_text in enumerate(chunks, 1):
            title = "{} (part {}/{})".format(filename, i, len(chunks))
            add_result = kb.add(
                title=title,
                content=chunk_text,
                category=category,
                tags=entry_tags,
                source="file:{}".format(file_path),
            )
            if add_result.get("success"):
                entries_created += 1
            else:
                logger.warning(
                    "Failed to add chunk %d of %s: %s",
                    i, filename, add_result.get("error"),
                )
    else:
        # Store as single entry
        title = filename
        add_result = kb.add(
            title=title,
            content=content,
            category=category,
            tags=entry_tags,
            source="file:{}".format(file_path),
        )
        if add_result.get("success"):
            entries_created = 1
        else:
            return {
                "success": False,
                "error": add_result.get("error", "Failed to add to knowledge base."),
                "filename": filename,
            }

    return {
        "success": True,
        "entries_created": entries_created,
        "filename": filename,
        "metadata": metadata,
        "message": "Uploaded '{}' ({} entries created).".format(
            filename, entries_created
        ),
    }


def bulk_upload_directory(
    directory_path: str,
    category: str = "uploaded",
    tags: str = "",
    recursive: bool = False,
    chunk: bool = True,
) -> Dict[str, Any]:
    """Upload all supported files from a directory.

    Scans the directory for files with supported extensions and uploads
    each one to the knowledge base.

    Args:
        directory_path: Path to the directory to scan.
        category: Category for the knowledge entries.
        tags: Comma-separated tags for the entries.
        recursive: Whether to scan subdirectories.
        chunk: Whether to chunk long content.

    Returns:
        Dict with keys:
            - 'success': bool
            - 'files_processed': int
            - 'total_entries_created': int
            - 'errors': list of error messages
            - 'error': str (only if complete failure)
    """
    if not directory_path or not directory_path.strip():
        return {"success": False, "error": "Directory path cannot be empty."}

    directory_path = directory_path.strip()

    if not os.path.exists(directory_path):
        return {
            "success": False,
            "error": "Directory not found: {}".format(directory_path),
        }

    if not os.path.isdir(directory_path):
        return {
            "success": False,
            "error": "Path is not a directory: {}".format(directory_path),
        }

    loader = _get_document_loader()
    supported_ext = set(loader.supported_formats)

    # Collect files to process
    files_to_process = []

    if recursive:
        for root, dirs, files in os.walk(directory_path):
            for fname in files:
                _, ext = os.path.splitext(fname)
                if ext.lower() in supported_ext:
                    files_to_process.append(os.path.join(root, fname))
    else:
        for fname in os.listdir(directory_path):
            fpath = os.path.join(directory_path, fname)
            if os.path.isfile(fpath):
                _, ext = os.path.splitext(fname)
                if ext.lower() in supported_ext:
                    files_to_process.append(fpath)

    if not files_to_process:
        return {
            "success": True,
            "files_processed": 0,
            "total_entries_created": 0,
            "errors": [],
            "message": "No supported files found in directory.",
        }

    # Process each file
    total_entries = 0
    files_processed = 0
    errors = []

    for fpath in files_to_process:
        result = upload_to_knowledge_base(
            file_path=fpath,
            category=category,
            tags=tags,
            chunk=chunk,
        )

        if result.get("success"):
            files_processed += 1
            total_entries += result.get("entries_created", 0)
        else:
            errors.append(
                "{}: {}".format(
                    os.path.basename(fpath),
                    result.get("error", "Unknown error"),
                )
            )

    return {
        "success": True,
        "files_processed": files_processed,
        "total_entries_created": total_entries,
        "errors": errors,
        "message": "Processed {} files, created {} entries.".format(
            files_processed, total_entries
        ),
    }
