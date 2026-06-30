"""Analytics API endpoints for the web dashboard.

Provides endpoints for today's stats, weekly stats, and health monitoring data.
"""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/analytics/today")
async def get_today_analytics():
    """Get today's usage statistics.

    Returns:
        Dictionary with today's analytics data.
    """
    try:
        from core.analytics.analytics_tracker import AnalyticsTracker

        tracker = AnalyticsTracker()
        return tracker.get_today_stats()
    except Exception as e:
        logger.error("Error getting today analytics: %s", str(e))
        return {
            "date": None,
            "total_requests": 0,
            "error": str(e),
        }


@router.get("/analytics/weekly")
async def get_weekly_analytics():
    """Get last 7 days statistics.

    Returns:
        Dictionary with weekly aggregated analytics data.
    """
    try:
        from core.analytics.analytics_tracker import AnalyticsTracker

        tracker = AnalyticsTracker()
        return tracker.get_weekly_stats()
    except Exception as e:
        logger.error("Error getting weekly analytics: %s", str(e))
        return {
            "total_requests": 0,
            "error": str(e),
        }


@router.get("/analytics/health")
async def get_health_status():
    """Get provider health monitoring data.

    Returns:
        Dictionary with provider health status and uptime report.
    """
    try:
        from interfaces.web_dashboard.app import get_orchestrator

        orchestrator = get_orchestrator()
        if orchestrator is None:
            return {"providers": {}, "uptime": {}, "error": "Orchestrator not initialized"}

        health_data = {"providers": {}, "uptime": {}}

        # Get health monitor status if available
        if hasattr(orchestrator, "health_monitor") and orchestrator.health_monitor is not None:
            health_data["providers"] = orchestrator.health_monitor.get_status()
            health_data["uptime"] = orchestrator.health_monitor.get_uptime_report()
        else:
            # Fallback: get basic provider status from orchestrator
            try:
                status = orchestrator.get_status()
                providers_info = status.get("providers", {})
                for name, info in providers_info.items():
                    if isinstance(info, dict):
                        available = info.get("available", False)
                    else:
                        available = bool(info)
                    health_data["providers"][name] = {
                        "available": available,
                        "last_check": None,
                    }
            except Exception:
                pass

        return health_data
    except Exception as e:
        logger.error("Error getting health status: %s", str(e))
        return {"providers": {}, "uptime": {}, "error": str(e)}
