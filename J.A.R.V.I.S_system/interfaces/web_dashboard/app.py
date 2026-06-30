"""
J.A.R.V.I.S Web Dashboard - FastAPI Application.

Main application module that sets up the FastAPI app with CORS,
static file serving, and API route mounting. Provides a startup
event to initialize the shared Orchestrator instance.

Usage:
    Run via run_web.py entry point or directly with uvicorn:
        uvicorn interfaces.web_dashboard.app:app --host 0.0.0.0 --port 8000
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logger.warning(
        "FastAPI not installed. Web dashboard is disabled. "
        "Install with: pip install fastapi uvicorn"
    )

if not FASTAPI_AVAILABLE:
    # Provide a dummy app object so imports don't crash
    app = None
else:
    app = FastAPI(
        title="J.A.R.V.I.S Web Dashboard",
        description="AI Assistant Web Interface",
        version="2.0.0",
    )

    # Configure CORS - allow all origins for local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Shared orchestrator instance
    _orchestrator: Optional[object] = None

    def get_orchestrator():
        """Get the shared Orchestrator instance.

        Returns:
            Orchestrator instance, or None if not initialized.
        """
        return _orchestrator

    @app.on_event("startup")
    async def startup_event():
        """Initialize the Orchestrator on application startup."""
        global _orchestrator
        try:
            from core.orchestrator import Orchestrator

            _orchestrator = Orchestrator()
            logger.info("Orchestrator initialized for web dashboard.")
        except Exception as e:
            logger.error(
                "Failed to initialize Orchestrator: %s. "
                "Chat functionality will be limited.",
                str(e),
            )
            _orchestrator = None

    # Import and include route modules
    from interfaces.web_dashboard.routes.chat import router as chat_router
    from interfaces.web_dashboard.routes.tasks import router as tasks_router
    from interfaces.web_dashboard.routes.knowledge import router as knowledge_router
    from interfaces.web_dashboard.routes.journals import router as journals_router
    from interfaces.web_dashboard.routes.habits import router as habits_router
    from interfaces.web_dashboard.routes.status import router as status_router

    app.include_router(chat_router)
    app.include_router(tasks_router)
    app.include_router(knowledge_router)
    app.include_router(journals_router)
    app.include_router(habits_router)
    app.include_router(status_router)

    # Serve static files
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

    if os.path.isdir(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    async def serve_index():
        """Serve the main dashboard HTML page."""
        index_path = os.path.join(static_dir, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        return {"message": "J.A.R.V.I.S Web Dashboard - static files not found"}
