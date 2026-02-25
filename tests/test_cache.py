"""Tests for the cache manager system."""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from cache import CacheManager


@pytest.fixture
def temp_cache_db():
    """Create a temporary cache database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_cache.db"
        yield str(db_path)


class TestCacheManager:
    """Test suite for CacheManager."""

    def test_init_creates_database(self, temp_cache_db):
        """Test that CacheManager initializes database."""
        manager = CacheManager(temp_cache_db)
        assert Path(temp_cache_db).exists()

    def test_set_and_get(self, temp_cache_db):
        """Test basic set/get operations."""
        manager = CacheManager(temp_cache_db)
        test_data = {"results": ["incident1", "incident2"], "count": 2}

        # Store data
        manager.set("google_docs", "test_query", test_data, ttl_hours=1)

        # Retrieve data
        cached = manager.get("google_docs", "test_query")
        assert cached is not None
        assert cached["data"] == test_data
        assert cached["cache_hit"] is True

    def test_cache_miss(self, temp_cache_db):
        """Test cache miss for non-existent entry."""
        manager = CacheManager(temp_cache_db)

        # Try to get non-existent entry
        cached = manager.get("nonexistent", "query")
        assert cached is None

    def test_cache_expiration(self, temp_cache_db):
        """Test that expired entries are not returned."""
        manager = CacheManager(temp_cache_db)
        test_data = {"result": "test"}

        # Store with very short TTL (already expired)
        manager.set("test_source", "query", test_data, ttl_hours=-1)

        # Should be expired
        cached = manager.get("test_source", "query")
        assert cached is None

    def test_list_cached(self, temp_cache_db):
        """Test listing cached entries."""
        manager = CacheManager(temp_cache_db)

        # Add multiple entries
        manager.set("google_docs", "query1", {"data": 1}, ttl_hours=1)
        manager.set("slack", "query2", {"data": 2}, ttl_hours=1)
        manager.set("slack", "query3", {"data": 3}, ttl_hours=1)

        # List all entries
        entries = manager.list_cached()
        assert len(entries) == 3
        assert all(e["source"] in ["google_docs", "slack"] for e in entries)

    def test_cache_status(self, temp_cache_db):
        """Test cache status by source."""
        manager = CacheManager(temp_cache_db)

        # Add entries to different sources
        manager.set("google_docs", "q1", {"data": 1}, ttl_hours=1)
        manager.set("google_docs", "q2", {"data": 2}, ttl_hours=1)
        manager.set("slack", "q3", {"data": 3}, ttl_hours=1)

        # Check status
        status = manager.cache_status()
        assert status["google_docs"] == 2
        assert status["slack"] == 1

    def test_clear_expired(self, temp_cache_db):
        """Test clearing expired entries."""
        manager = CacheManager(temp_cache_db)

        # Add mix of fresh and expired
        manager.set("test", "fresh", {"data": "fresh"}, ttl_hours=24)
        manager.set("test", "expired", {"data": "expired"}, ttl_hours=-1)

        # Clear expired
        deleted = manager.clear_expired()
        assert deleted == 1

        # Verify fresh remains, expired removed
        assert manager.get("test", "fresh") is not None
        assert manager.get("test", "expired") is None

    def test_delete_by_source(self, temp_cache_db):
        """Test deleting all entries for a source."""
        manager = CacheManager(temp_cache_db)

        # Add entries to multiple sources
        manager.set("source1", "q1", {"data": 1}, ttl_hours=1)
        manager.set("source1", "q2", {"data": 2}, ttl_hours=1)
        manager.set("source2", "q3", {"data": 3}, ttl_hours=1)

        # Delete source1
        deleted = manager.delete_by_source("source1")
        assert deleted == 2

        # Verify source1 deleted, source2 remains
        status = manager.cache_status()
        assert "source1" not in status
        assert status.get("source2", 0) == 1

    def test_clear_all(self, temp_cache_db):
        """Test clearing entire cache."""
        manager = CacheManager(temp_cache_db)

        # Add entries
        manager.set("source1", "q1", {"data": 1}, ttl_hours=1)
        manager.set("source2", "q2", {"data": 2}, ttl_hours=1)

        # Clear all
        deleted = manager.clear_all()
        assert deleted == 2

        # Verify empty
        assert len(manager.list_cached()) == 0

    def test_export_json(self, temp_cache_db):
        """Test exporting cache as JSON."""
        manager = CacheManager(temp_cache_db)

        manager.set("test", "q1", {"result": "data"}, ttl_hours=1)

        exported = manager.export_cache(format="json")
        data = json.loads(exported)

        assert len(data) == 1
        assert data[0]["source"] == "test"

    def test_export_csv(self, temp_cache_db):
        """Test exporting cache as CSV."""
        manager = CacheManager(temp_cache_db)

        manager.set("test", "q1", {"result": "data"}, ttl_hours=1)

        exported = manager.export_cache(format="csv")

        # Should have header and one entry
        lines = exported.strip().split("\n")
        assert len(lines) >= 2  # Header + at least 1 entry
        assert "id,source,cached_at" in lines[0]

    def test_hash_query(self, temp_cache_db):
        """Test query hashing."""
        manager = CacheManager(temp_cache_db)

        # Same query should produce same hash
        hash1 = manager._hash_query("test query")
        hash2 = manager._hash_query("test query")
        assert hash1 == hash2

        # Different queries should produce different hashes
        hash3 = manager._hash_query("different query")
        assert hash1 != hash3

    def test_is_expired(self, temp_cache_db):
        """Test expiration checking."""
        manager = CacheManager(temp_cache_db)

        now = datetime.now(timezone.utc)

        # Should not be expired (just cached)
        assert not manager.is_expired(now, ttl_hours=1)

        # Should be expired (cached in past)
        past = now - timedelta(hours=2)
        assert manager.is_expired(past, ttl_hours=1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
