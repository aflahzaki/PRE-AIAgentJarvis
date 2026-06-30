#!/usr/bin/env python3
"""
J.A.R.V.I.S Web Dashboard - Entry Point.

Starts the FastAPI web dashboard for J.A.R.V.I.S.
Loads environment variables and runs uvicorn on the configured host/port.

Usage:
    python run_web.py

Environment Variables:
    WEB_HOST: Host to bind (default: 0.0.0.0)
    WEB_PORT: Port to listen on (default: 8000)
"""

import logging
import os
import sys

# Ensure core and interfaces modules can be imported from this directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for the web dashboard."""
    try:
        import uvicorn
    except ImportError:
        logger.error(
            "uvicorn not installed. "
            "Install with: pip install uvicorn"
        )
        print("\nError: uvicorn is required to run the web dashboard.")
        print("Install with: pip install fastapi uvicorn")
        sys.exit(1)

    try:
        from interfaces.web_dashboard.app import app
    except ImportError as e:
        logger.error(
            "Failed to import web dashboard app. "
            "Ensure fastapi is installed: pip install fastapi"
        )
        logger.error("Import error: %s", str(e))
        sys.exit(1)

    if app is None:
        logger.error("FastAPI app could not be created. Check dependencies.")
        sys.exit(1)

    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_PORT", "8000"))

    print("\n" + "=" * 50)
    print("  J.A.R.V.I.S Web Dashboard")
    print("=" * 50)
    print("  URL: http://{}:{}".format(host, port))
    print("  Press Ctrl+C to stop")
    print("=" * 50 + "\n")

    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
        )
    except KeyboardInterrupt:
        logger.info("Web dashboard stopped by user.")
        print("\nJ.A.R.V.I.S Web Dashboard stopped.")
    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        print("\nUnexpected error: {}".format(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
