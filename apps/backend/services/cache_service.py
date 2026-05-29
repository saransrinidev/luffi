import hashlib
import time
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """In-memory LRU cache for LLM responses. Avoids re-querying same text."""

    def __init__(self, max_size: int = 200, ttl: int = 3600):
        self.cache: dict[str, dict] = {}
        self.max_size = max_size
        self.ttl = ttl
        self.hits = 0
        self.misses = 0

    def _make_key(self, text: str, mode: str) -> str:
        """Hash the input for cache key."""
        content = f"{mode}:{text.strip().lower()}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, text: str, mode: str) -> dict | None:
        """Get cached response if exists and not expired."""
        key = self._make_key(text, mode)
        entry = self.cache.get(key)

        if entry is None:
            self.misses += 1
            return None

        if time.time() - entry["timestamp"] > self.ttl:
            del self.cache[key]
            self.misses += 1
            return None

        self.hits += 1
        logger.info(f"Cache HIT (hits={self.hits}, misses={self.misses})")
        return entry["data"]

    def set(self, text: str, mode: str, data: dict):
        """Store response in cache."""
        if len(self.cache) >= self.max_size:
            # Evict oldest entry
            oldest_key = min(self.cache, key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]

        key = self._make_key(text, mode)
        self.cache[key] = {"data": data, "timestamp": time.time()}

    def clear(self):
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    @property
    def stats(self) -> dict:
        total = self.hits + self.misses
        rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{rate:.1f}%",
        }
