"""
Document Loader - Multi-format file parser for J.A.R.V.I.S Knowledge Base.

Loads and parses various document formats into text content suitable
for storage in the knowledge base. Supports chunking for long documents.

Supported formats:
- .txt - Plain text
- .md - Markdown
- .pdf - PDF (via PyPDF2, graceful if not installed)
- .docx - Word documents (via python-docx, graceful if not installed)
- .csv - CSV (extract headers + sample rows as context)
- .json - JSON (pretty-print structure)
- .py / .js / .html / .css - Source code (preserve formatting)

Dependencies (all optional):
    - PyPDF2>=3.0.0 (for PDF support)
    - python-docx>=0.8.11 (for DOCX support)
"""

import csv
import io
import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Maximum file size: 10MB
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    ".txt", ".md", ".pdf", ".docx", ".csv", ".json",
    ".py", ".js", ".html", ".css", ".ts", ".jsx", ".tsx",
}

# Source code extensions (preserve formatting)
CODE_EXTENSIONS = {
    ".py", ".js", ".html", ".css", ".ts", ".jsx", ".tsx",
}

# Optional dependency: PyPDF2
try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    logger.debug("PyPDF2 not installed. PDF support disabled.")

# Optional dependency: python-docx
try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.debug("python-docx not installed. DOCX support disabled.")


class DocumentLoader:
    """Load and parse documents into text for knowledge base.

    Provides multi-format document loading with automatic format
    detection based on file extension. Includes text chunking for
    long documents to improve retrieval quality.
    """

    def __init__(self) -> None:
        """Initialize the DocumentLoader."""
        self._supported_formats = list(SUPPORTED_EXTENSIONS)
        logger.info(
            "DocumentLoader initialized. PDF=%s, DOCX=%s",
            PYPDF2_AVAILABLE, DOCX_AVAILABLE,
        )

    @property
    def supported_formats(self) -> List[str]:
        """Get list of supported file extensions."""
        return self._supported_formats

    def load_file(self, file_path: str) -> Dict[str, Any]:
        """Load file and extract text content.

        Args:
            file_path: Path to the file to load.

        Returns:
            Dict with keys:
                - 'success': bool
                - 'content': str (extracted text)
                - 'metadata': dict with filename, format, size_kb, etc.
                - 'error': str (only if success is False)
        """
        if not file_path or not file_path.strip():
            return {"success": False, "error": "File path cannot be empty."}

        file_path = file_path.strip()

        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": "File not found: {}".format(file_path),
            }

        if not os.path.isfile(file_path):
            return {
                "success": False,
                "error": "Path is not a file: {}".format(file_path),
            }

        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE_BYTES:
            return {
                "success": False,
                "error": "File too large: {:.1f}MB (max 10MB).".format(
                    file_size / (1024 * 1024)
                ),
            }

        # Get extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext not in SUPPORTED_EXTENSIONS:
            return {
                "success": False,
                "error": "Unsupported format '{}'. Supported: {}".format(
                    ext, ", ".join(sorted(SUPPORTED_EXTENSIONS))
                ),
            }

        # Extract content based on format
        try:
            if ext == ".pdf":
                content, pages = self._load_pdf(file_path)
            elif ext == ".docx":
                content, pages = self._load_docx(file_path)
            elif ext == ".csv":
                content, pages = self._load_csv(file_path)
            elif ext == ".json":
                content, pages = self._load_json(file_path)
            elif ext in CODE_EXTENSIONS:
                content, pages = self._load_code(file_path, ext)
            else:
                # .txt, .md - plain text
                content, pages = self._load_text(file_path)

            metadata = self.extract_metadata(file_path)
            if pages is not None:
                metadata["pages"] = pages

            return {
                "success": True,
                "content": content,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error("Error loading file %s: %s", file_path, str(e))
            return {
                "success": False,
                "error": "Failed to load file: {}".format(str(e)),
            }

    def chunk_text(
        self, text: str, chunk_size: int = 1000, overlap: int = 200
    ) -> List[str]:
        """Split long text into overlapping chunks for better retrieval.

        Uses sentence-boundary splitting to avoid cutting mid-word
        or mid-sentence. Each chunk overlaps with the previous one
        by the specified number of characters for context continuity.

        Args:
            text: Text to split into chunks.
            chunk_size: Target size for each chunk in characters.
            overlap: Number of characters to overlap between chunks.

        Returns:
            List of text chunks.
        """
        if not text or not text.strip():
            return []

        text = text.strip()

        # If text is short enough, return as single chunk
        if len(text) <= chunk_size:
            return [text]

        # Split into sentences
        sentences = self._split_sentences(text)

        chunks = []
        current_chunk = ""
        current_length = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            # If single sentence exceeds chunk_size, split by words
            if sentence_len > chunk_size:
                # Flush current chunk first
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                    current_length = 0

                # Split long sentence by words
                words = sentence.split()
                for word in words:
                    if current_length + len(word) + 1 > chunk_size:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        # Start new chunk with overlap
                        overlap_text = current_chunk[-overlap:] if overlap > 0 else ""
                        current_chunk = overlap_text + " " + word
                        current_length = len(current_chunk)
                    else:
                        current_chunk += " " + word if current_chunk else word
                        current_length = len(current_chunk)
                continue

            # Check if adding this sentence exceeds chunk_size
            if current_length + sentence_len > chunk_size:
                # Save current chunk
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())

                # Start new chunk with overlap from previous
                if overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-overlap:]
                    current_chunk = overlap_text + " " + sentence
                else:
                    current_chunk = sentence
                current_length = len(current_chunk)
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                current_length = len(current_chunk)

        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract file metadata (size, creation date, type).

        Args:
            file_path: Path to the file.

        Returns:
            Dict with filename, format, size_kb, created_at keys.
        """
        stat = os.stat(file_path)
        _, ext = os.path.splitext(file_path)

        return {
            "filename": os.path.basename(file_path),
            "format": ext.lower().lstrip("."),
            "size_kb": round(stat.st_size / 1024, 2),
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        }

    # ============================================
    # Private format-specific loaders
    # ============================================

    def _load_text(self, file_path: str) -> tuple:
        """Load plain text or markdown file.

        Returns:
            Tuple of (content, pages). Pages is None for text files.
        """
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return content, None

    def _load_pdf(self, file_path: str) -> tuple:
        """Load PDF file using PyPDF2.

        Returns:
            Tuple of (content, page_count).

        Raises:
            ImportError: If PyPDF2 is not installed.
        """
        if not PYPDF2_AVAILABLE:
            raise ImportError(
                "PyPDF2 is required for PDF support. "
                "Install with: pip install PyPDF2"
            )

        reader = PdfReader(file_path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)

        content = "\n\n".join(pages)
        return content, len(reader.pages)

    def _load_docx(self, file_path: str) -> tuple:
        """Load DOCX file using python-docx.

        Returns:
            Tuple of (content, paragraph_count).

        Raises:
            ImportError: If python-docx is not installed.
        """
        if not DOCX_AVAILABLE:
            raise ImportError(
                "python-docx is required for DOCX support. "
                "Install with: pip install python-docx"
            )

        doc = DocxDocument(file_path)
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text)

        content = "\n\n".join(paragraphs)
        return content, len(paragraphs)

    def _load_csv(self, file_path: str) -> tuple:
        """Load CSV file, extracting headers and sample rows.

        Returns:
            Tuple of (content, row_count).
        """
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            # Read first portion to detect dialect
            sample = f.read(8192)
            f.seek(0)

            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                dialect = csv.excel

            reader = csv.reader(f, dialect)
            rows = list(reader)

        if not rows:
            return "Empty CSV file.", 0

        headers = rows[0]
        data_rows = rows[1:]

        # Build content: headers + sample rows (max 50)
        content_parts = []
        content_parts.append("CSV Headers: {}".format(", ".join(headers)))
        content_parts.append("Total rows: {}".format(len(data_rows)))
        content_parts.append("")
        content_parts.append("Sample data (first 50 rows):")

        for i, row in enumerate(data_rows[:50]):
            row_str = " | ".join(
                "{}: {}".format(h, v) for h, v in zip(headers, row)
            )
            content_parts.append("Row {}: {}".format(i + 1, row_str))

        if len(data_rows) > 50:
            content_parts.append("... ({} more rows)".format(len(data_rows) - 50))

        content = "\n".join(content_parts)
        return content, len(rows)

    def _load_json(self, file_path: str) -> tuple:
        """Load JSON file, pretty-printing the structure.

        Returns:
            Tuple of (content, None).
        """
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)

        content = json.dumps(data, indent=2, ensure_ascii=False)

        # If too long, truncate with structure summary
        if len(content) > 50000:
            # Provide structure overview instead
            structure = self._json_structure_summary(data)
            content = "JSON Structure (large file, summarized):\n\n{}".format(
                structure
            )

        return content, None

    def _load_code(self, file_path: str, ext: str) -> tuple:
        """Load source code file, preserving formatting.

        Returns:
            Tuple of (content, line_count).
        """
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        line_count = content.count("\n") + 1
        language = ext.lstrip(".")

        # Wrap in code block indicator for context
        formatted = "Language: {}\nLines: {}\n\n{}".format(
            language, line_count, content
        )
        return formatted, line_count

    # ============================================
    # Utility methods
    # ============================================

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """Split text into sentences using regex.

        Handles common sentence endings (. ! ?) while avoiding
        splits on abbreviations and decimal numbers.

        Args:
            text: Text to split.

        Returns:
            List of sentences.
        """
        # Split on sentence-ending punctuation followed by space + uppercase
        # or newlines (paragraph breaks)
        sentences = re.split(
            r"(?<=[.!?])\s+(?=[A-Z\u0400-\u04FF])|(?:\n\s*\n)",
            text,
        )
        # Filter empty strings
        return [s.strip() for s in sentences if s and s.strip()]

    @staticmethod
    def _json_structure_summary(data: Any, depth: int = 0, max_depth: int = 3) -> str:
        """Generate a structural summary of a JSON object.

        Args:
            data: JSON data to summarize.
            depth: Current depth level.
            max_depth: Maximum depth to recurse.

        Returns:
            String representation of the structure.
        """
        indent = "  " * depth

        if depth >= max_depth:
            return "{}...".format(indent)

        if isinstance(data, dict):
            if not data:
                return "{}{{}}".format(indent)
            lines = ["{}{{".format(indent)]
            for key in list(data.keys())[:20]:
                val_summary = DocumentLoader._json_structure_summary(
                    data[key], depth + 1, max_depth
                )
                lines.append('{}  "{}": {}'.format(indent, key, val_summary.strip()))
            if len(data) > 20:
                lines.append("{}  ... ({} more keys)".format(indent, len(data) - 20))
            lines.append("{}}}".format(indent))
            return "\n".join(lines)
        elif isinstance(data, list):
            if not data:
                return "{}[]".format(indent)
            item_summary = DocumentLoader._json_structure_summary(
                data[0], depth + 1, max_depth
            )
            return "{}[Array of {} items, first: {}]".format(
                indent, len(data), item_summary.strip()
            )
        else:
            return "{}{}".format(indent, type(data).__name__)

    def __repr__(self) -> str:
        return "DocumentLoader(pdf={}, docx={}, formats={})".format(
            PYPDF2_AVAILABLE, DOCX_AVAILABLE, len(self._supported_formats)
        )
