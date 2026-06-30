"""
Response Cache - LRU cache for LLM responses to avoid redundant API calls.

Features:
- Hash-based key (message content hash)
- TTL (time-to-live) per entry (default 1 hour)
- Max size limit (default 100 entries)
- Persistence to JSON (survives restarts)
- Skip caching for tool-calling responses
- Configurable via environment variables
"""

import hashlib
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_MAX_SIZE = 100
DEFAULT_TTL_SECONDS = 3600  # 1 hour
DEFAULT_CACHE_FILE = "data/cache/response_cache.json"


class ResponseCache:
    """LRU cache for LLM responses with TTL-based expiration.

    Stores responses keyed by a hash of the input messages and model.
    Entries expire after TTL seconds and are evicted LRU-style when
    the cache reaches max_size.
    """

    def __init__(
        self,
        max_size: int = DEFAULT_MAX_SIZE,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        cache_file: str = DEFAULT_CACHE_FILE,
    ) -> None:
        """Initialize the response cache.

        Args:
            max_size: Maximum number of cached entries.
            ttl_seconds: Time-to-live in seconds for each entry.
            cache_file: Path to the JSON file for persistence.
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache_file = cache_file
        self._cache = {}  # type: Dict[str, Dict[str, Any]]
        self._hits = 0
        self._misses = 0
        self._load()

    def get(self, messages: List[Dict[str, str]], model: str) -> Optional[str]:
        """Check cache for a matching response.

        Returns cached response if found and not expired, None otherwise.
        Increments hit/miss counters for statistics.

        Args:
            messages: The message list sent to the LLM.
            model: The model name used.

        Returns:
            Cached response string if found and valid, None otherwise.
        """
        key = self._make_key(messages, model)

        if key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[key]

        # Check TTL expiration
        if time.time() - entry["timestamp"] > self.ttl_seconds:
            # Expired - remove it
            del self._cache[key]
            self._misses += 1
            return None

        # Cache hit - update access time for LRU and increment hits
        entry["last_access"] = time.time()
        entry["hits"] = entry.get("hits", 0) + 1
        self._hits += 1
        return entry["response"]

    def put(
        self,
        messages: List[Dict[str, str]],
        model: str,
        response: str,
    ) -> None:
        """Cache a response. Evicts oldest entry if at max_size.

        Args:
            messages: The message list sent to the LLM.
            model: The model name used.
            response: The LLM response to cache.
        """
        # Evict expired entries first
        self._evict_expired()

        # Evict LRU if still over limit
        if len(self._cache) >= self.max_size:
            self._evict_lru()

        key = self._make_key(messages, model)
        self._cache[key] = {
            "response": response,
            "timestamp": time.time(),
            "last_access": time.time(),
            "hits": 0,
            "model": model,
        }

        self._save()

    def _make_key(self, messages: List[Dict[str, str]], model: str) -> str:
        """Create hash key from messages + model.

        Args:
            messages: The message list to hash.
            model: The model name to include in the hash.

        Returns:
            A 16-character hex hash string.
        """
        content = json.dumps(messages, sort_keys=True) + "|" + model
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _evict_expired(self) -> None:
        """Remove all entries whose TTL has expired."""
        now = time.time()
        expired_keys = [
            k for k, v in self._cache.items()
            if now - v["timestamp"] > self.ttl_seconds
        ]
        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug("Cache: evicted %d expired entries", len(expired_keys))

    def _evict_lru(self) -> None:
        """Remove least recently used entries until under max_size."""
        while len(self._cache) >= self.max_size:
            # Find entry with oldest last_access time
            lru_key = min(
                self._cache.keys(),
                key=lambda k: self._cache[k].get("last_access", 0),
            )
            del self._cache[lru_key]
            logger.debug("Cache: evicted LRU entry %s", lru_key)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache hit/miss statistics.

        Returns:
            Dict with cache statistics including size, hits, misses, hit rate.
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 1),
            "ttl_seconds": self.ttl_seconds,
        }

    def clear(self) -> None:
        """Clear entire cache and reset statistics."""
        self._cache = {}
        self._hits = 0
        self._misses = 0
        self._save()
        logger.info("Response cache cleared")

    def _save(self) -> None:
        """Persist cache to disk as JSON.

        Creates the cache directory if it does not exist.
        """
        try:
            cache_dir = os.path.dirname(self.cache_file)
            if cache_dir:
                os.makedirs(cache_dir, exist_ok=True)

            data = {
                "cache": self._cache,
                "stats": {
                    "hits": self._hits,
                    "misses": self._misses,
                },
            }

            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.warning("ResponseCache: Failed to save: %s", str(e))

    def _load(self) -> None:
        """Load cache from disk if the file exists.

        If the file is missing or invalid, starts with an empty cache.
        """
        if not os.path.exists(self.cache_file):
            return

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._cache = data.get("cache", {})
            stats = data.get("stats", {})
            self._hits = stats.get("hits", 0)
            self._misses = stats.get("misses", 0)

            # Evict any expired entries on load
            self._evict_expired()

            logger.debug(
                "ResponseCache: Loaded %d entries from %s",
                len(self._cache), self.cache_file,
            )

        except (json.JSONDecodeError, IOError) as e:
            logger.warning(
                "ResponseCache: Failed to load from %s: %s. Starting fresh.",
                self.cache_file, str(e),
            )
            self._cache = {}

    def __repr__(self) -> str:
        return "ResponseCache(size={}, max={}, ttl={}s)".format(
            len(self._cache), self.max_size, self.ttl_seconds,
        )
