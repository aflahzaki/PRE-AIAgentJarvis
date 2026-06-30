"""Background health monitoring for all providers.

Checks provider availability every 5 minutes and:
- Logs status changes
- Records uptime/downtime
- Triggers notifications when provider goes down/comes back
"""

import threading
import time
import logging
from datetime import datetime
from typing import Dict, Any, Callable, List, Optional

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Background health monitor for LLM providers.

    Periodically checks provider availability and records status changes.
    Runs in a daemon thread so it does not prevent program exit.
    """

    def __init__(self, check_interval_seconds: int = 300):
        """Initialize the health monitor.

        Args:
            check_interval_seconds: Seconds between health checks (default 300 = 5 min).
        """
        self.interval = check_interval_seconds
        self._running = False
        self._thread = None  # type: Optional[threading.Thread]
        self._provider_status = {}  # type: Dict[str, Dict[str, Any]]
        self._status_change_callbacks = []  # type: List[Callable]
        self._providers = {}  # type: Dict[str, Any]
        self._lock = threading.Lock()

    def start(self, providers: Dict[str, Any]) -> None:
        """Start monitoring providers in background thread.

        Args:
            providers: Dictionary of provider_name -> provider instance.
                       Each provider should have a check_health() or similar method.
        """
        if self._running:
            logger.warning("HealthMonitor is already running.")
            return

        self._providers = providers
        self._running = True

        # Initialize status for all providers
        with self._lock:
            for name in providers:
                self._provider_status[name] = {
                    "available": None,
                    "last_check": None,
                    "uptime_start": None,
                    "downtime_start": None,
                    "total_checks": 0,
                    "successful_checks": 0,
                }

        self._thread = threading.Thread(
            target=self._monitor_loop,
            name="HealthMonitor",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            "HealthMonitor started. Checking %d providers every %ds.",
            len(providers),
            self.interval,
        )

    def stop(self) -> None:
        """Stop the monitoring thread."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("HealthMonitor stopped.")

    def on_status_change(self, callback: Callable) -> None:
        """Register callback for provider status changes.

        The callback receives: (provider_name, new_status: bool, old_status: bool)

        Args:
            callback: Function to call when a provider status changes.
        """
        self._status_change_callbacks.append(callback)

    def get_status(self) -> Dict[str, Any]:
        """Get current health status of all providers.

        Returns:
            Dictionary mapping provider names to their status info.
        """
        with self._lock:
            result = {}
            for name, status in self._provider_status.items():
                result[name] = {
                    "available": status["available"],
                    "last_check": status["last_check"],
                    "uptime_start": status.get("uptime_start"),
                    "downtime_start": status.get("downtime_start"),
                }
            return result

    def get_uptime_report(self) -> Dict[str, Any]:
        """Get uptime percentage per provider.

        Returns:
            Dictionary mapping provider names to uptime stats.
        """
        with self._lock:
            report = {}
            for name, status in self._provider_status.items():
                total = status.get("total_checks", 0)
                successful = status.get("successful_checks", 0)
                if total > 0:
                    uptime_pct = round((successful / total) * 100, 1)
                else:
                    uptime_pct = 0.0
                report[name] = {
                    "uptime_percent": uptime_pct,
                    "total_checks": total,
                    "successful_checks": successful,
                    "currently_available": status.get("available"),
                }
            return report

    def _monitor_loop(self) -> None:
        """Main monitoring loop that runs in the background thread."""
        # Do an initial check immediately
        self._check_all_providers()

        while self._running:
            time.sleep(self.interval)
            if not self._running:
                break
            self._check_all_providers()

    def _check_all_providers(self) -> None:
        """Check health of all registered providers."""
        for name, provider in self._providers.items():
            try:
                available = self._check_provider(provider)
            except Exception as e:
                logger.debug("Health check failed for %s: %s", name, e)
                available = False

            now = datetime.now().isoformat()

            with self._lock:
                old_status = self._provider_status[name].get("available")
                self._provider_status[name]["last_check"] = now
                self._provider_status[name]["total_checks"] = (
                    self._provider_status[name].get("total_checks", 0) + 1
                )

                if available:
                    self._provider_status[name]["successful_checks"] = (
                        self._provider_status[name].get("successful_checks", 0) + 1
                    )

                # Detect status change
                if old_status is not None and old_status != available:
                    if available:
                        self._provider_status[name]["uptime_start"] = now
                        self._provider_status[name]["downtime_start"] = None
                        logger.info("Provider %s is back ONLINE.", name)
                    else:
                        self._provider_status[name]["downtime_start"] = now
                        self._provider_status[name]["uptime_start"] = None
                        logger.warning("Provider %s went OFFLINE.", name)

                    # Fire callbacks
                    for callback in self._status_change_callbacks:
                        try:
                            callback(name, available, old_status)
                        except Exception as cb_err:
                            logger.debug(
                                "Status change callback error: %s", cb_err
                            )
                elif old_status is None:
                    # First check
                    if available:
                        self._provider_status[name]["uptime_start"] = now
                    else:
                        self._provider_status[name]["downtime_start"] = now

                self._provider_status[name]["available"] = available

    def _check_provider(self, provider: Any) -> bool:
        """Check if a single provider is available.

        Tries multiple methods that providers might implement.

        Args:
            provider: Provider instance to check.

        Returns:
            True if provider is available, False otherwise.
        """
        # Try common health check methods
        if hasattr(provider, "check_health"):
            return bool(provider.check_health())
        if hasattr(provider, "is_available"):
            return bool(provider.is_available())
        if hasattr(provider, "health_check"):
            result = provider.health_check()
            if isinstance(result, dict):
                return result.get("available", False)
            return bool(result)
        # If no health check method, assume available
        return True
