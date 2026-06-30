"""
Chat API Route - AI conversation endpoint.

Provides POST /api/chat for sending messages to the J.A.R.V.I.S
orchestrator and receiving AI-generated responses.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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
