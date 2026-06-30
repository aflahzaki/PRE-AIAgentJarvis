#!/usr/bin/env python3
"""
J.A.R.V.I.S - Run All Services.

Starts the Terminal REPL, Web Dashboard, and Proactive Engine together
using threading for concurrent operation. Telegram bot is separate
(use run_telegram.py for that).

Graceful shutdown on Ctrl+C - all services stop cleanly.

Usage:
    python run_all.py

Services Started:
    1. Web Dashboard (FastAPI + Uvicorn) on WEB_HOST:WEB_PORT
    2. Proactive Engine (background scheduler) if PROACTIVE_ENABLED=true
    3. Terminal REPL (interactive, runs on main thread)
"""

import logging
import os
import signal
import sys
import threading

# Ensure core and interfaces modules can be imported from this directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)

# Setup logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global shutdown event
_shutdown_event = threading.Event()


def start_web_dashboard() -> None:
    """Start the web dashboard in a background thread."""
    try:
        import uvicorn
        from interfaces.web_dashboard.app import app
    except ImportError as e:
        logger.warning(
            "Web dashboard not available (missing dependency): %s", str(e)
        )
        print("[run_all] Web dashboard skipped: {}".format(str(e)))
        return

    if app is None:
        logger.warning("Web dashboard app could not be created.")
        return

    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_PORT", "8000"))

    print("[run_all] Starting Web Dashboard on http://{}:{}".format(host, port))

    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="warning",
    )
    server = uvicorn.Server(config)

    # Run the server (blocking within this thread)
    try:
        server.run()
    except Exception as e:
        if not _shutdown_event.is_set():
            logger.error("Web dashboard error: %s", str(e))


def start_proactive_engine():
    """Start the proactive engine (it manages its own thread)."""
    try:
        from interfaces.proactive.proactive_engine import ProactiveEngine
    except ImportError as e:
        logger.warning(
            "Proactive engine not available (missing dependency): %s", str(e)
        )
        print("[run_all] Proactive engine skipped: {}".format(str(e)))
        return None

    engine = ProactiveEngine()
    if engine.enabled:
        started = engine.start()
        if started:
            print(
                "[run_all] Proactive engine started "
                "(interval: {} min).".format(engine.interval_minutes)
            )
        else:
            print("[run_all] Proactive engine failed to start.")
    else:
        print(
            "[run_all] Proactive engine disabled. "
            "Set PROACTIVE_ENABLED=true to enable."
        )

    return engine


def start_terminal_repl() -> None:
    """Start the terminal REPL (runs on main thread)."""
    try:
        from run_jarvis_v2 import main as repl_main
        repl_main()
    except ImportError as e:
        logger.error("Terminal REPL not available: %s", str(e))
        print("[run_all] Terminal REPL failed to start: {}".format(str(e)))
    except (KeyboardInterrupt, EOFError):
        pass


def main() -> None:
    """Main entry point - orchestrates all services."""
    print("\n" + "=" * 55)
    print("  J.A.R.V.I.S - Multi-Service Launcher")
    print("=" * 55)
    print("  Services: Terminal REPL + Web Dashboard + Proactive")
    print("  Press Ctrl+C to stop all services")
    print("=" * 55 + "\n")

    # Start the web dashboard in a background thread
    web_thread = threading.Thread(
        target=start_web_dashboard,
        name="WebDashboard",
        daemon=True,
    )
    web_thread.start()

    # Start proactive engine (manages its own daemon thread)
    proactive_engine = start_proactive_engine()

    # Small delay to let background services initialize
    import time
    time.sleep(1)

    # Run the terminal REPL on the main thread (blocking)
    try:
        start_terminal_repl()
    except KeyboardInterrupt:
        pass
    finally:
        # Graceful shutdown
        _shutdown_event.set()
        print("\n[run_all] Shutting down all services...")

        # Stop proactive engine
        if proactive_engine is not None:
            proactive_engine.stop()

        print("[run_all] All services stopped. Goodbye!")


if __name__ == "__main__":
    main()
