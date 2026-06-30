"""
J.A.R.V.I.S Web Dashboard Interface.

A FastAPI-powered web dashboard providing a beautiful dark-themed UI
for interacting with J.A.R.V.I.S through a browser. Includes chat,
task management, knowledge base, journals, habits, and system status.
"""

try:
    from interfaces.web_dashboard.app import app

    WEB_DASHBOARD_AVAILABLE = True
except ImportError:
    WEB_DASHBOARD_AVAILABLE = False
    app = None

__all__ = ["app", "WEB_DASHBOARD_AVAILABLE"]
