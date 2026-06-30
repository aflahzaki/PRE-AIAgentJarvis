"""Tracks J.A.R.V.I.S usage statistics for analytics dashboard.

Records:
- Requests per day/hour
- Agent usage distribution
- Provider usage distribution
- Model usage distribution
- Average response time
- Token consumption per provider
- Cache hit rate
- Error rate per provider
"""

import json
import os
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AnalyticsTracker:
    """Lightweight analytics tracker with JSON persistence.

    Stores daily stats in data/analytics/ directory.
    Each day gets its own JSON file: analytics_YYYY-MM-DD.json
    """

    def __init__(self, storage_dir: str = "data/analytics"):
        """Initialize the analytics tracker.

        Args:
            storage_dir: Directory to store daily analytics JSON files.
        """
        self.storage_dir = storage_dir
        self._ensure_storage_dir()
        self._today_stats = self._load_today()

    def _ensure_storage_dir(self) -> None:
        """Create the storage directory if it does not exist."""
        try:
            os.makedirs(self.storage_dir, exist_ok=True)
        except OSError as e:
            logger.warning("Could not create analytics dir %s: %s", self.storage_dir, e)

    def record_request(
        self,
        task_type: str,
        agent_used: str,
        provider_used: str,
        model_used: str,
        response_time_ms: int,
        tokens_used: int = 0,
        cache_hit: bool = False,
        success: bool = True,
    ) -> None:
        """Record a single request for analytics.

        Args:
            task_type: Type of task (code, research, simple, etc.).
            agent_used: Agent that handled the request.
            provider_used: LLM provider used.
            model_used: Model name used.
            response_time_ms: Response time in milliseconds.
            tokens_used: Number of tokens consumed.
            cache_hit: Whether the response was served from cache.
            success: Whether the request completed successfully.
        """
        # Ensure we are still tracking for today
        today_str = date.today().isoformat()
        if self._today_stats.get("date") != today_str:
            self._today_stats = self._load_today()

        stats = self._today_stats

        # Increment total requests
        stats["total_requests"] = stats.get("total_requests", 0) + 1

        # Track by hour
        current_hour = str(datetime.now().hour)
        if "requests_by_hour" not in stats:
            stats["requests_by_hour"] = {}
        stats["requests_by_hour"][current_hour] = (
            stats["requests_by_hour"].get(current_hour, 0) + 1
        )

        # Agent usage distribution
        if "agent_usage" not in stats:
            stats["agent_usage"] = {}
        stats["agent_usage"][agent_used] = (
            stats["agent_usage"].get(agent_used, 0) + 1
        )

        # Provider usage distribution
        if "provider_usage" not in stats:
            stats["provider_usage"] = {}
        stats["provider_usage"][provider_used] = (
            stats["provider_usage"].get(provider_used, 0) + 1
        )

        # Model usage distribution
        if "model_usage" not in stats:
            stats["model_usage"] = {}
        stats["model_usage"][model_used] = (
            stats["model_usage"].get(model_used, 0) + 1
        )

        # Response time tracking (for computing average)
        if "response_times" not in stats:
            stats["response_times"] = {"total_ms": 0, "count": 0}
        stats["response_times"]["total_ms"] += response_time_ms
        stats["response_times"]["count"] += 1

        # Token consumption per provider
        if "tokens_by_provider" not in stats:
            stats["tokens_by_provider"] = {}
        stats["tokens_by_provider"][provider_used] = (
            stats["tokens_by_provider"].get(provider_used, 0) + tokens_used
        )

        # Cache hit tracking
        if "cache" not in stats:
            stats["cache"] = {"hits": 0, "misses": 0}
        if cache_hit:
            stats["cache"]["hits"] += 1
        else:
            stats["cache"]["misses"] += 1

        # Error tracking per provider
        if not success:
            if "errors_by_provider" not in stats:
                stats["errors_by_provider"] = {}
            stats["errors_by_provider"][provider_used] = (
                stats["errors_by_provider"].get(provider_used, 0) + 1
            )
        stats["total_errors"] = stats.get("total_errors", 0) + (0 if success else 1)

        # Persist to disk
        self._save_today()

    def get_today_stats(self) -> Dict[str, Any]:
        """Get today's aggregated statistics.

        Returns:
            Dictionary with today's analytics data including computed averages.
        """
        today_str = date.today().isoformat()
        if self._today_stats.get("date") != today_str:
            self._today_stats = self._load_today()

        stats = dict(self._today_stats)

        # Compute average response time
        rt = stats.get("response_times", {"total_ms": 0, "count": 0})
        if rt["count"] > 0:
            stats["avg_response_time_ms"] = round(rt["total_ms"] / rt["count"])
        else:
            stats["avg_response_time_ms"] = 0

        # Compute cache hit rate
        cache = stats.get("cache", {"hits": 0, "misses": 0})
        total_cache = cache["hits"] + cache["misses"]
        if total_cache > 0:
            stats["cache_hit_rate"] = round(
                (cache["hits"] / total_cache) * 100, 1
            )
        else:
            stats["cache_hit_rate"] = 0.0

        # Compute error rate
        total_reqs = stats.get("total_requests", 0)
        total_errs = stats.get("total_errors", 0)
        if total_reqs > 0:
            stats["error_rate"] = round((total_errs / total_reqs) * 100, 1)
        else:
            stats["error_rate"] = 0.0

        return stats

    def get_weekly_stats(self) -> Dict[str, Any]:
        """Get last 7 days aggregated statistics.

        Returns:
            Dictionary with aggregated weekly analytics data.
        """
        weekly = {
            "total_requests": 0,
            "total_errors": 0,
            "agent_usage": {},
            "provider_usage": {},
            "model_usage": {},
            "response_times": {"total_ms": 0, "count": 0},
            "cache": {"hits": 0, "misses": 0},
            "tokens_by_provider": {},
            "daily_requests": {},
        }

        today = date.today()
        for i in range(7):
            day = today - timedelta(days=i)
            day_stats = self._load_day(day.isoformat())

            if not day_stats:
                weekly["daily_requests"][day.isoformat()] = 0
                continue

            weekly["daily_requests"][day.isoformat()] = day_stats.get(
                "total_requests", 0
            )
            weekly["total_requests"] += day_stats.get("total_requests", 0)
            weekly["total_errors"] += day_stats.get("total_errors", 0)

            # Merge agent usage
            for agent, count in day_stats.get("agent_usage", {}).items():
                weekly["agent_usage"][agent] = (
                    weekly["agent_usage"].get(agent, 0) + count
                )

            # Merge provider usage
            for provider, count in day_stats.get("provider_usage", {}).items():
                weekly["provider_usage"][provider] = (
                    weekly["provider_usage"].get(provider, 0) + count
                )

            # Merge model usage
            for model, count in day_stats.get("model_usage", {}).items():
                weekly["model_usage"][model] = (
                    weekly["model_usage"].get(model, 0) + count
                )

            # Merge response times
            rt = day_stats.get("response_times", {"total_ms": 0, "count": 0})
            weekly["response_times"]["total_ms"] += rt.get("total_ms", 0)
            weekly["response_times"]["count"] += rt.get("count", 0)

            # Merge cache stats
            cache = day_stats.get("cache", {"hits": 0, "misses": 0})
            weekly["cache"]["hits"] += cache.get("hits", 0)
            weekly["cache"]["misses"] += cache.get("misses", 0)

            # Merge tokens
            for provider, tokens in day_stats.get("tokens_by_provider", {}).items():
                weekly["tokens_by_provider"][provider] = (
                    weekly["tokens_by_provider"].get(provider, 0) + tokens
                )

        # Compute averages
        rt = weekly["response_times"]
        if rt["count"] > 0:
            weekly["avg_response_time_ms"] = round(rt["total_ms"] / rt["count"])
        else:
            weekly["avg_response_time_ms"] = 0

        cache = weekly["cache"]
        total_cache = cache["hits"] + cache["misses"]
        if total_cache > 0:
            weekly["cache_hit_rate"] = round(
                (cache["hits"] / total_cache) * 100, 1
            )
        else:
            weekly["cache_hit_rate"] = 0.0

        if weekly["total_requests"] > 0:
            weekly["error_rate"] = round(
                (weekly["total_errors"] / weekly["total_requests"]) * 100, 1
            )
        else:
            weekly["error_rate"] = 0.0

        return weekly

    def get_all_time_stats(self) -> Dict[str, Any]:
        """Get all-time stats (aggregate all daily files).

        Returns:
            Dictionary with all-time aggregated analytics data.
        """
        all_time = {
            "total_requests": 0,
            "total_errors": 0,
            "agent_usage": {},
            "provider_usage": {},
            "model_usage": {},
            "response_times": {"total_ms": 0, "count": 0},
            "cache": {"hits": 0, "misses": 0},
            "tokens_by_provider": {},
            "days_tracked": 0,
        }

        if not os.path.isdir(self.storage_dir):
            return all_time

        for filename in os.listdir(self.storage_dir):
            if not filename.startswith("analytics_") or not filename.endswith(".json"):
                continue

            filepath = os.path.join(self.storage_dir, filename)
            try:
                with open(filepath, "r") as f:
                    day_stats = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            all_time["days_tracked"] += 1
            all_time["total_requests"] += day_stats.get("total_requests", 0)
            all_time["total_errors"] += day_stats.get("total_errors", 0)

            for agent, count in day_stats.get("agent_usage", {}).items():
                all_time["agent_usage"][agent] = (
                    all_time["agent_usage"].get(agent, 0) + count
                )

            for provider, count in day_stats.get("provider_usage", {}).items():
                all_time["provider_usage"][provider] = (
                    all_time["provider_usage"].get(provider, 0) + count
                )

            for model, count in day_stats.get("model_usage", {}).items():
                all_time["model_usage"][model] = (
                    all_time["model_usage"].get(model, 0) + count
                )

            rt = day_stats.get("response_times", {"total_ms": 0, "count": 0})
            all_time["response_times"]["total_ms"] += rt.get("total_ms", 0)
            all_time["response_times"]["count"] += rt.get("count", 0)

            cache = day_stats.get("cache", {"hits": 0, "misses": 0})
            all_time["cache"]["hits"] += cache.get("hits", 0)
            all_time["cache"]["misses"] += cache.get("misses", 0)

            for provider, tokens in day_stats.get("tokens_by_provider", {}).items():
                all_time["tokens_by_provider"][provider] = (
                    all_time["tokens_by_provider"].get(provider, 0) + tokens
                )

        # Compute averages
        rt = all_time["response_times"]
        if rt["count"] > 0:
            all_time["avg_response_time_ms"] = round(rt["total_ms"] / rt["count"])
        else:
            all_time["avg_response_time_ms"] = 0

        cache = all_time["cache"]
        total_cache = cache["hits"] + cache["misses"]
        if total_cache > 0:
            all_time["cache_hit_rate"] = round(
                (cache["hits"] / total_cache) * 100, 1
            )
        else:
            all_time["cache_hit_rate"] = 0.0

        if all_time["total_requests"] > 0:
            all_time["error_rate"] = round(
                (all_time["total_errors"] / all_time["total_requests"]) * 100, 1
            )
        else:
            all_time["error_rate"] = 0.0

        return all_time

    def _load_today(self) -> Dict:
        """Load or create today's stats file.

        Returns:
            Dictionary with today's stats data.
        """
        today_str = date.today().isoformat()
        stats = self._load_day(today_str)
        if stats:
            return stats

        # Create fresh stats for today
        return {
            "date": today_str,
            "total_requests": 0,
            "total_errors": 0,
            "requests_by_hour": {},
            "agent_usage": {},
            "provider_usage": {},
            "model_usage": {},
            "response_times": {"total_ms": 0, "count": 0},
            "tokens_by_provider": {},
            "cache": {"hits": 0, "misses": 0},
            "errors_by_provider": {},
        }

    def _load_day(self, date_str: str) -> Dict:
        """Load stats for a specific day.

        Args:
            date_str: Date string in YYYY-MM-DD format.

        Returns:
            Dictionary with day's stats, or empty dict if not found.
        """
        filepath = os.path.join(
            self.storage_dir, "analytics_{}.json".format(date_str)
        )
        if not os.path.isfile(filepath):
            return {}

        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load analytics file %s: %s", filepath, e)
            return {}

    def _save_today(self) -> None:
        """Save today's stats to disk."""
        self._ensure_storage_dir()
        today_str = date.today().isoformat()
        filepath = os.path.join(
            self.storage_dir, "analytics_{}.json".format(today_str)
        )
        try:
            with open(filepath, "w") as f:
                json.dump(self._today_stats, f, indent=2)
        except OSError as e:
            logger.warning("Failed to save analytics file %s: %s", filepath, e)
