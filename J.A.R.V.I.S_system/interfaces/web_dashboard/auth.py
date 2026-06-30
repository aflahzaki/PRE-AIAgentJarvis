"""Simple authentication middleware for J.A.R.V.I.S web dashboard.

Uses a static token from .env for simplicity.
If WEB_AUTH_ENABLED=false or WEB_AUTH_TOKEN is empty, auth is disabled.
"""

import os

from fastapi import Request, HTTPException

WEB_AUTH_ENABLED = os.getenv("WEB_AUTH_ENABLED", "false").lower() == "true"
WEB_AUTH_TOKEN = os.getenv("WEB_AUTH_TOKEN", "")


async def auth_middleware(request: Request, call_next):
    """Check authentication for API routes.

    Rules:
    - If WEB_AUTH_ENABLED is false, skip auth entirely
    - Static files (/static/*) are always accessible (for login page)
    - API routes (/api/*) require valid token in header: Authorization: Bearer <token>
    - Login endpoint (/api/auth/login) is always accessible
    """
    # Skip auth if disabled
    if not WEB_AUTH_ENABLED:
        return await call_next(request)

    path = request.url.path

    # Allow static files and login endpoint
    if (
        path.startswith("/static")
        or path == "/api/auth/login"
        or path == "/"
        or path == "/favicon.ico"
    ):
        return await call_next(request)

    # Check API auth
    if path.startswith("/api"):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer ") or auth_header[7:] != WEB_AUTH_TOKEN:
            raise HTTPException(status_code=401, detail="Unauthorized")

    return await call_next(request)
