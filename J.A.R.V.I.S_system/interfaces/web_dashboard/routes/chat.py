"""
Chat API Route - AI conversation endpoint.

Provides POST /api/chat for sending messages to the J.A.R.V.I.S
orchestrator and receiving AI-generated responses.
Also provides POST /api/chat/stream for Server-Sent Events streaming.
Also provides GET /api/chat/export for exporting conversation history.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel

from core.utils.export import ConversationExporter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    message: str


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""

    response: str
    task_type: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    difficulty: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message through the orchestrator.

    Args:
        request: ChatRequest with the user message.

    Returns:
        ChatResponse with orchestrator result.
    """
    from interfaces.web_dashboard.app import get_orchestrator

    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    orchestrator = get_orchestrator()
    if orchestrator is None:
        raise HTTPException(
            status_code=503,
            detail="Orchestrator not available. Please try again later.",
        )

    try:
        result = orchestrator.process(request.message.strip())
        return ChatResponse(
            response=result.get("response", "No response generated."),
            task_type=result.get("task_type"),
            model=result.get("model"),
            provider=result.get("provider"),
            difficulty=result.get("difficulty"),
        )
    except Exception as e:
        logger.error("Chat processing error: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Error processing message: {}".format(str(e)),
        )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Process a chat message with streaming response via Server-Sent Events.

    Streams tokens from the orchestrator's process_stream() method as SSE
    data events. Each token is sent as 'data: {token}\\n\\n'. The stream
    ends with 'data: [DONE]\\n\\n'.

    Args:
        request: ChatRequest with the user message.

    Returns:
        StreamingResponse with text/event-stream media type.
    """
    from interfaces.web_dashboard.app import get_orchestrator

    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    orchestrator = get_orchestrator()
    if orchestrator is None:
        raise HTTPException(
            status_code=503,
            detail="Orchestrator not available. Please try again later.",
        )

    async def generate():
        """Async generator that wraps the sync process_stream generator."""
        try:
            for token in orchestrator.process_stream(request.message.strip()):
                yield "data: {}\n\n".format(json.dumps(token))
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error("Stream processing error: %s", str(e))
            yield "data: {}\n\n".format(json.dumps("Error: {}".format(str(e))))
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/chat/export")
async def export_chat(format: str = "md"):
    """Export current chat session as downloadable file.

    Args:
        format: Export format - 'md', 'html', or 'txt'. Defaults to 'md'.

    Returns:
        File download response with the exported conversation.
    """
    from interfaces.web_dashboard.app import get_orchestrator

    orchestrator = get_orchestrator()
    if orchestrator is None:
        raise HTTPException(
            status_code=503,
            detail="Orchestrator not available. Please try again later.",
        )

    # Validate format
    valid_formats = ("md", "html", "txt")
    if format not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail="Invalid format: {}. Use 'md', 'html', or 'txt'.".format(format),
        )

    # Get messages from orchestrator memory
    messages = orchestrator.memory.get_messages(include_summary=False)

    # Export even if empty - exporter handles empty gracefully
    exporter = ConversationExporter()

    if format == "md":
        content = exporter.to_markdown(messages)
        media_type = "text/markdown"
        filename = "jarvis_conversation.md"
    elif format == "html":
        content = exporter.to_html(messages)
        media_type = "text/html"
        filename = "jarvis_conversation.html"
    else:
        content = exporter.to_text(messages)
        media_type = "text/plain"
        filename = "jarvis_conversation.txt"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": "attachment; filename={}".format(filename),
        },
    )
