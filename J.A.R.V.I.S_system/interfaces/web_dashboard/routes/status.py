"""
Status API Route - System health and status.

Provides GET /api/status endpoint returning orchestrator status
and database health information.
"""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["status"])


@router.get("/status")
async def get_status():
    """Get J.A.R.V.I.S system status.

    Returns system health including orchestrator provider info,
    memory status, and database connectivity.

    Returns:
        Status dictionary with orchestrator and database info.
    """
    from interfaces.web_dashboard.app import get_orchestrator

    status = {
        "system": "J.A.R.V.I.S",
        "version": "2.0.0",
        "orchestrator": None,
        "database": None,
    }

    # Get orchestrator status
    orchestrator = get_orchestrator()
    if orchestrator is not None:
        try:
            orch_status = orchestrator.get_status()
            status["orchestrator"] = orch_status
        except Exception as e:
            logger.error("Error getting orchestrator status: %s", str(e))
            status["orchestrator"] = {"error": str(e)}
    else:
        status["orchestrator"] = {"error": "Orchestrator not initialized"}

    # Get database health
    try:
        from core.database.db_manager import DatabaseManager

        db = DatabaseManager()
        status["database"] = db.health_check()
    except ImportError:
        status["database"] = {"success": False, "error": "Database modules not available"}
    except Exception as e:
        status["database"] = {"success": False, "error": str(e)}

    return status
