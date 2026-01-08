"""Tests for CrossRef API caching functionality.

TDD RED Phase: Write failing tests first.
In-memory cache with 7-day TTL for CrossRef metadata.
"""

from unittest.mock import patch
from datetime import datetime, timedelta


class TestCrossRefCache:
    """Test cases for CrossRef API caching."""

    def test_cache_stores_result(self):
        """Test that successful API results are cached."""
        from app.services.crossref_service import CrossRefService

        mock_response = {
            "status": "ok",
            "message": {
                "title": ["Test Article"],
                "author": [{"given": "John", "family": "Doe"}],
            },
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response

            # First call - should hit API
            result1, _ = CrossRefService.fetch_metadata("10.1038/test123")
            assert mock_get.call_count == 1

            # Second call - should use cache
            result2, _ = CrossRefService.fetch_metadata("10.1038/test123")
            assert mock_get.call_count == 1  # No additional API call

            # Results should be identical
            assert result1 == result2

    def test_cache_key_is_doi(self):
        """Test that cache uses DOI as key."""
        from app.services.crossref_service import CrossRefService

        mock_response = {
            "status": "ok",
            "message": {"title": ["Test"]},
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response

            # Different DOIs should make different API calls
            CrossRefService.fetch_metadata("10.1038/first")
            CrossRefService.fetch_metadata("10.1038/second")
            assert mock_get.call_count == 2

            # Same DOI should use cache
            CrossRefService.fetch_metadata("10.1038/first")
            assert mock_get.call_count == 2

    def test_cache_does_not_store_errors(self):
        """Test that API errors are not cached."""
        from app.services.crossref_service import CrossRefService

        with patch("requests.get") as mock_get:
            # First call returns error
            mock_get.return_value.status_code = 500

            result1, error1 = CrossRefService.fetch_metadata("10.1038/error")
            assert error1 is not None
            assert mock_get.call_count == 1

            # Second call should retry API (not use cached error)
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "status": "ok",
                "message": {"title": ["Recovered"]},
            }

            result2, error2 = CrossRefService.fetch_metadata("10.1038/error")
            assert mock_get.call_count == 2
            assert error2 is None
            assert result2["title"] == "Recovered"

    def test_cache_does_not_store_not_found(self):
        """Test that 404 errors are not cached."""
        from app.services.crossref_service import CrossRefService

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 404

            result1, error1 = CrossRefService.fetch_metadata("10.1038/notfound")
            assert mock_get.call_count == 1

            # Should retry
            result2, error2 = CrossRefService.fetch_metadata("10.1038/notfound")
            assert mock_get.call_count == 2


class TestCrossRefCacheTTL:
    """Test cases for cache TTL (Time To Live)."""

    def test_cache_expires_after_ttl(self):
        """Test that cache entries expire after 7 days."""
        from app.services.crossref_service import CrossRefService

        # Clear cache to start fresh
        CrossRefService.clear_cache()

        mock_response = {
            "status": "ok",
            "message": {"title": ["Test"]},
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response

            # First call - populates cache
            CrossRefService.fetch_metadata("10.1038/ttl-test")
            assert mock_get.call_count == 1

            # Manually expire the cache entry
            with CrossRefService._cache_lock:
                if "10.1038/ttl-test" in CrossRefService._cache:
                    CrossRefService._cache["10.1038/ttl-test"]["expires_at"] = (
                        datetime.now() - timedelta(seconds=1)
                    )

            # Second call - cache should be expired, new API call
            CrossRefService.fetch_metadata("10.1038/ttl-test")
            assert mock_get.call_count == 2

    def test_cache_ttl_is_7_days(self):
        """Test that cache TTL is configured to 7 days."""
        from app.services.crossref_service import CrossRefService

        # Check TTL configuration
        assert CrossRefService.CACHE_TTL_DAYS == 7


class TestCrossRefCacheManagement:
    """Test cases for cache management operations."""

    def test_clear_cache(self):
        """Test clearing the entire cache."""
        from app.services.crossref_service import CrossRefService

        mock_response = {
            "status": "ok",
            "message": {"title": ["Test"]},
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response

            # Populate cache
            CrossRefService.fetch_metadata("10.1038/cache1")
            CrossRefService.fetch_metadata("10.1038/cache2")
            assert mock_get.call_count == 2

            # Clear cache
            CrossRefService.clear_cache()

            # Should make new API calls
            CrossRefService.fetch_metadata("10.1038/cache1")
            CrossRefService.fetch_metadata("10.1038/cache2")
            assert mock_get.call_count == 4

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        from app.services.crossref_service import CrossRefService

        # Clear cache first
        CrossRefService.clear_cache()

        mock_response = {
            "status": "ok",
            "message": {"title": ["Test"]},
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response

            # Make some calls
            CrossRefService.fetch_metadata("10.1038/stat1")
            CrossRefService.fetch_metadata("10.1038/stat2")
            CrossRefService.fetch_metadata("10.1038/stat1")  # Cache hit

            stats = CrossRefService.get_cache_stats()

            assert stats["size"] == 2  # Two unique DOIs
            assert stats["hits"] >= 1  # At least one cache hit
            assert stats["misses"] >= 2  # At least two cache misses

    def test_remove_from_cache(self):
        """Test removing specific DOI from cache."""
        from app.services.crossref_service import CrossRefService

        mock_response = {
            "status": "ok",
            "message": {"title": ["Test"]},
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response

            # Populate cache
            CrossRefService.fetch_metadata("10.1038/remove-me")
            assert mock_get.call_count == 1

            # Remove from cache
            CrossRefService.remove_from_cache("10.1038/remove-me")

            # Should make new API call
            CrossRefService.fetch_metadata("10.1038/remove-me")
            assert mock_get.call_count == 2


class TestCrossRefCacheThreadSafety:
    """Test cases for thread-safe cache operations."""

    def test_cache_is_thread_safe(self):
        """Test that cache operations are thread-safe."""
        import threading
        from app.services.crossref_service import CrossRefService

        mock_response = {
            "status": "ok",
            "message": {"title": ["Test"]},
        }

        errors = []
        lock = threading.Lock()

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response

            def worker(doi_suffix):
                try:
                    CrossRefService.fetch_metadata(f"10.1038/thread{doi_suffix}")
                except Exception as e:
                    with lock:
                        errors.append(str(e))

            # Create multiple threads accessing cache
            threads = [
                threading.Thread(target=worker, args=(i % 10,)) for i in range(50)
            ]

            for t in threads:
                t.start()

            for t in threads:
                t.join()

            # No errors should occur
            assert len(errors) == 0
