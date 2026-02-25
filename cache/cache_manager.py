"""Cache manager for DOE_METRICS_REPORTER - handles local SQLite caching with TTL."""

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages local SQLite cache with configurable TTL per source."""

    def __init__(self, db_path: str = "./cache/cache.db"):
        """Initialize cache manager and create database if needed.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """Initialize SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    query_hash TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    cached_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    ttl_hours INTEGER NOT NULL,
                    UNIQUE(source, query_hash)
                )
            """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_source_hash ON cache_entries(source, query_hash)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON cache_entries(expires_at)")
            conn.commit()

    def _hash_query(self, query: str) -> str:
        """Generate hash for query string for cache key."""
        return hashlib.sha256(query.encode()).hexdigest()[:16]

    def get(self, source: str, query: str) -> Optional[dict]:
        """Retrieve cached data if fresh (not expired).

        Args:
            source: Source identifier (e.g., 'google_docs', 'slack')
            query: Query string to hash for cache key

        Returns:
            Cached data dict if found and not expired, None otherwise
        """
        query_hash = self._hash_query(query)
        now = datetime.now(timezone.utc)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT data_json, cached_at FROM cache_entries
                WHERE source = ? AND query_hash = ? AND expires_at > ?
            """,
                (source, query_hash, now),
            )
            row = cursor.fetchone()

        if row:
            data_json, cached_at = row
            logger.debug(
                f"Cache hit: {source}:{query_hash[:8]}... (cached at {cached_at})"
            )
            return {
                "data": json.loads(data_json),
                "cached_at": cached_at,
                "cache_hit": True,
            }

        logger.debug(f"Cache miss: {source}:{query_hash[:8]}...")
        return None

    def set(
        self,
        source: str,
        query: str,
        data: dict,
        ttl_hours: int = 24,
    ) -> None:
        """Store data in cache with TTL.

        Args:
            source: Source identifier (e.g., 'google_docs', 'slack')
            query: Query string to hash for cache key
            data: Data dict to cache
            ttl_hours: Time-to-live in hours (default 24)
        """
        query_hash = self._hash_query(query)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=ttl_hours)
        cache_id = f"{source}:{query_hash}"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache_entries
                (id, source, query_hash, data_json, cached_at, expires_at, ttl_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    cache_id,
                    source,
                    query_hash,
                    json.dumps(data),
                    now.isoformat(),
                    expires_at.isoformat(),
                    ttl_hours,
                ),
            )
            conn.commit()

        logger.debug(
            f"Cached {source}:{query_hash[:8]}... (TTL: {ttl_hours}h, expires: {expires_at})"
        )

    def is_expired(self, cached_at: datetime, ttl_hours: int) -> bool:
        """Check if cache entry has expired.

        Args:
            cached_at: Datetime when cached
            ttl_hours: TTL in hours

        Returns:
            True if expired, False if still fresh
        """
        expires_at = cached_at + timedelta(hours=ttl_hours)
        return datetime.now(timezone.utc) > expires_at

    def clear_expired(self) -> int:
        """Remove all expired entries from cache.

        Returns:
            Number of entries deleted
        """
        now = datetime.now(timezone.utc)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM cache_entries WHERE expires_at <= ?",
                (now,),
            )
            deleted = cursor.rowcount
            conn.commit()

        if deleted > 0:
            logger.info(f"Cleared {deleted} expired cache entries")
        return deleted

    def list_cached(self) -> list[dict]:
        """List all current cache entries (not expired).

        Returns:
            List of cache entry dicts with metadata
        """
        now = datetime.now(timezone.utc)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, source, cached_at, expires_at, ttl_hours
                FROM cache_entries
                WHERE expires_at > ?
                ORDER BY cached_at DESC
            """,
                (now,),
            )
            rows = cursor.fetchall()

        entries = []
        for cache_id, source, cached_at, expires_at, ttl_hours in rows:
            expires_dt = datetime.fromisoformat(expires_at)
            time_remaining = expires_dt - datetime.now(timezone.utc)
            hours_left = max(0, time_remaining.total_seconds() / 3600)

            entries.append(
                {
                    "id": cache_id,
                    "source": source,
                    "cached_at": cached_at,
                    "ttl_hours": ttl_hours,
                    "expires_in_hours": round(hours_left, 2),
                }
            )

        return entries

    def cache_status(self) -> dict:
        """Get cache statistics by source.

        Returns:
            Dict with counts per source
        """
        now = datetime.now(timezone.utc)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT source, COUNT(*) as count
                FROM cache_entries
                WHERE expires_at > ?
                GROUP BY source
                ORDER BY source
            """,
                (now,),
            )
            rows = cursor.fetchall()

        status = {source: count for source, count in rows}
        return status

    def export_cache(self, format: str = "json") -> str:
        """Export cache contents to string.

        Args:
            format: Export format ('json' or 'csv')

        Returns:
            Formatted string of cache contents
        """
        entries = self.list_cached()

        if format == "json":
            return json.dumps(entries, indent=2)
        elif format == "csv":
            if not entries:
                return "id,source,cached_at,ttl_hours,expires_in_hours\n"

            lines = ["id,source,cached_at,ttl_hours,expires_in_hours"]
            for entry in entries:
                lines.append(
                    f"{entry['id']},{entry['source']},{entry['cached_at']},"
                    f"{entry['ttl_hours']},{entry['expires_in_hours']}"
                )
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def clear_all(self) -> int:
        """Clear entire cache (use with caution).

        Returns:
            Number of entries deleted
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM cache_entries")
            deleted = cursor.rowcount
            conn.commit()

        logger.warning(f"Cleared entire cache ({deleted} entries)")
        return deleted

    def delete_by_source(self, source: str) -> int:
        """Delete all cache entries for a specific source.

        Args:
            source: Source identifier

        Returns:
            Number of entries deleted
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM cache_entries WHERE source = ?",
                (source,),
            )
            deleted = cursor.rowcount
            conn.commit()

        logger.info(f"Cleared cache for source '{source}' ({deleted} entries)")
        return deleted
