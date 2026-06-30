"""Export conversations to readable formats (Markdown, HTML, plain text).

Supports exporting from:
- Current session memory
- Saved conversation JSON files
- Database conversation logs
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


class ConversationExporter:
    """Export conversations to various formats."""

    def to_markdown(self, messages: List[Dict[str, str]], title: Optional[str] = None) -> str:
        """Convert conversation messages to Markdown format.

        Format:
        # J.A.R.V.I.S Conversation - {date}

        ## User
        {message}

        ## J.A.R.V.I.S
        {response}

        ---

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            title: Optional title for the document.

        Returns:
            Markdown-formatted string.
        """
        if not title:
            title = "J.A.R.V.I.S Conversation - {}".format(
                datetime.now().strftime("%Y-%m-%d %H:%M")
            )

        lines = ["# {}\n".format(title)]

        if not messages:
            lines.append("*No messages in this conversation.*\n")
            return "\n".join(lines)

        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            if role == "system":
                lines.append("> **System**: {}\n".format(content))
            elif role == "user":
                lines.append("## User\n")
                lines.append("{}\n".format(content))
            elif role == "assistant":
                lines.append("## J.A.R.V.I.S\n")
                lines.append("{}\n".format(content))
            else:
                lines.append("## {}\n".format(role.capitalize()))
                lines.append("{}\n".format(content))

            lines.append("---\n")

        # Footer
        lines.append("\n*Exported on {}*\n".format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        return "\n".join(lines)

    def to_html(self, messages: List[Dict[str, str]], title: Optional[str] = None) -> str:
        """Convert conversation to styled HTML page.
        Dark theme matching JARVIS aesthetic.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            title: Optional title for the document.

        Returns:
            Self-contained HTML string with inline CSS.
        """
        if not title:
            title = "J.A.R.V.I.S Conversation - {}".format(
                datetime.now().strftime("%Y-%m-%d %H:%M")
            )

        html_parts = []
        html_parts.append("<!DOCTYPE html>")
        html_parts.append("<html lang=\"en\">")
        html_parts.append("<head>")
        html_parts.append("<meta charset=\"UTF-8\">")
        html_parts.append("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">")
        html_parts.append("<title>{}</title>".format(self._escape_html(title)))
        html_parts.append("<style>")
        html_parts.append(self._get_html_styles())
        html_parts.append("</style>")
        html_parts.append("</head>")
        html_parts.append("<body>")
        html_parts.append("<div class=\"container\">")
        html_parts.append("<h1>{}</h1>".format(self._escape_html(title)))

        if not messages:
            html_parts.append("<p class=\"empty\">No messages in this conversation.</p>")
        else:
            for msg in messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")

                if role == "system":
                    html_parts.append(
                        "<div class=\"message system\"><div class=\"role\">System</div>"
                        "<div class=\"content\">{}</div></div>".format(
                            self._escape_html(content)
                        )
                    )
                elif role == "user":
                    html_parts.append(
                        "<div class=\"message user\"><div class=\"role\">User</div>"
                        "<div class=\"content\">{}</div></div>".format(
                            self._escape_html(content)
                        )
                    )
                elif role == "assistant":
                    html_parts.append(
                        "<div class=\"message assistant\"><div class=\"role\">J.A.R.V.I.S</div>"
                        "<div class=\"content\">{}</div></div>".format(
                            self._escape_html(content)
                        )
                    )
                else:
                    html_parts.append(
                        "<div class=\"message other\"><div class=\"role\">{}</div>"
                        "<div class=\"content\">{}</div></div>".format(
                            self._escape_html(role.capitalize()),
                            self._escape_html(content),
                        )
                    )

        html_parts.append("<div class=\"footer\">Exported on {}</div>".format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        html_parts.append("</div>")
        html_parts.append("</body>")
        html_parts.append("</html>")

        return "\n".join(html_parts)

    def to_text(self, messages: List[Dict[str, str]], title: Optional[str] = None) -> str:
        """Convert to plain text.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            title: Optional title for the document.

        Returns:
            Plain text string.
        """
        if not title:
            title = "J.A.R.V.I.S Conversation - {}".format(
                datetime.now().strftime("%Y-%m-%d %H:%M")
            )

        lines = [title, "=" * len(title), ""]

        if not messages:
            lines.append("(No messages in this conversation)")
            return "\n".join(lines)

        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            if role == "system":
                lines.append("[System]: {}".format(content))
            elif role == "user":
                lines.append("[User]: {}".format(content))
            elif role == "assistant":
                lines.append("[J.A.R.V.I.S]: {}".format(content))
            else:
                lines.append("[{}]: {}".format(role.capitalize(), content))

            lines.append("")

        lines.append("-" * 40)
        lines.append("Exported on {}".format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        return "\n".join(lines)

    def export_to_file(
        self,
        messages: List[Dict[str, str]],
        output_path: str,
        format: str = "md",
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Export conversation to file.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            output_path: Path where the file will be saved.
            format: Export format - 'md', 'html', or 'txt'.
            title: Optional title for the export.

        Returns:
            Dict with 'success', 'path', and 'format' keys.
        """
        try:
            if format == "md":
                content = self.to_markdown(messages, title)
            elif format == "html":
                content = self.to_html(messages, title)
            elif format == "txt":
                content = self.to_text(messages, title)
            else:
                return {
                    "success": False,
                    "error": "Unsupported format: {}. Use 'md', 'html', or 'txt'.".format(format),
                }

            abs_path = os.path.abspath(output_path)
            dir_path = os.path.dirname(abs_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)

            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)

            return {
                "success": True,
                "path": abs_path,
                "format": format,
            }

        except Exception as e:
            return {
                "success": False,
                "error": "Export failed: {}".format(str(e)),
            }

    def export_session(
        self,
        session_json_path: str,
        output_path: str,
        format: str = "md",
    ) -> Dict[str, Any]:
        """Export a saved session JSON to readable format.

        Args:
            session_json_path: Path to the session JSON file.
            output_path: Path where the exported file will be saved.
            format: Export format - 'md', 'html', or 'txt'.

        Returns:
            Dict with 'success', 'path', and 'format' keys.
        """
        try:
            if not os.path.exists(session_json_path):
                return {
                    "success": False,
                    "error": "Session file not found: {}".format(session_json_path),
                }

            with open(session_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            messages = data.get("messages", [])
            title = "J.A.R.V.I.S Session - {}".format(
                os.path.basename(session_json_path)
            )

            return self.export_to_file(messages, output_path, format, title)

        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": "Invalid JSON in session file: {}".format(str(e)),
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Export failed: {}".format(str(e)),
            }

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters.

        Args:
            text: Raw text to escape.

        Returns:
            HTML-safe string.
        """
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\"", "&quot;")
            .replace("'", "&#x27;")
        )

    def _get_html_styles(self) -> str:
        """Get inline CSS styles for HTML export.

        Returns:
            CSS string for dark theme JARVIS aesthetic.
        """
        return """
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #1a1a2e;
                color: #e0e0e0;
                line-height: 1.6;
                padding: 2rem;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
            }
            h1 {
                color: #00bcd4;
                margin-bottom: 2rem;
                padding-bottom: 1rem;
                border-bottom: 1px solid #333;
            }
            .message {
                margin-bottom: 1.5rem;
                padding: 1rem 1.5rem;
                border-radius: 8px;
                border-left: 4px solid #333;
            }
            .message.user {
                background: #16213e;
                border-left-color: #4caf50;
            }
            .message.assistant {
                background: #0f3460;
                border-left-color: #00bcd4;
            }
            .message.system {
                background: #1a1a2e;
                border-left-color: #ff9800;
                font-style: italic;
                opacity: 0.8;
            }
            .message.other {
                background: #1a1a2e;
                border-left-color: #9c27b0;
            }
            .role {
                font-weight: bold;
                font-size: 0.85rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 0.5rem;
                color: #aaa;
            }
            .message.user .role { color: #4caf50; }
            .message.assistant .role { color: #00bcd4; }
            .message.system .role { color: #ff9800; }
            .content {
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            .footer {
                margin-top: 3rem;
                padding-top: 1rem;
                border-top: 1px solid #333;
                color: #666;
                font-size: 0.85rem;
                text-align: center;
            }
            .empty {
                color: #666;
                font-style: italic;
                text-align: center;
                padding: 3rem;
            }
        """
