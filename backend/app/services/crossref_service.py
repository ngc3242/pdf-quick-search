"""CrossRef API client service.

Fetches metadata for academic papers using DOIs from the CrossRef API.
Uses the Polite Pool with mailto parameter for better rate limits.
Includes in-memory caching with 7-day TTL.
"""

import threading
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import requests


class CrossRefService:
    """Service class for CrossRef API operations with caching."""

    # CrossRef API base URL
    API_BASE_URL = "https://api.crossref.org/works"

    # Request timeout in seconds
    TIMEOUT = 2

    # Contact email for Polite Pool access
    MAILTO = "pdf-search@example.com"

    # Cache TTL in days
    CACHE_TTL_DAYS = 7

    # In-memory cache storage
    _cache: Dict[str, Dict[str, Any]] = {}
    _cache_lock = threading.Lock()

    # Cache statistics
    _cache_hits = 0
    _cache_misses = 0

    @classmethod
    def fetch_metadata(
        cls, doi: Optional[str]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Fetch metadata for a DOI from CrossRef API with caching.

        Uses the Polite Pool by including mailto parameter.
        Returns tuple following the (result, error) pattern.
        Caches successful results for 7 days.

        Args:
            doi: DOI string to look up

        Returns:
            Tuple of (metadata dict or None, error message or None)
        """
        if not doi:
            return None, "Invalid DOI: DOI cannot be empty"

        # Check cache first
        cached = cls._get_cache_entry(doi)
        if cached is not None:
            with cls._cache_lock:
                cls._cache_hits += 1
            return cached, None

        with cls._cache_lock:
            cls._cache_misses += 1

        # Fetch from API
        result, error = cls._fetch_from_api(doi)

        # Cache successful results only
        if result is not None and error is None:
            cls._set_cache_entry(doi, result)

        return result, error

    @classmethod
    def _fetch_from_api(
        cls, doi: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Fetch metadata directly from CrossRef API.

        Args:
            doi: DOI string to look up

        Returns:
            Tuple of (metadata dict or None, error message or None)
        """
        url = f"{cls.API_BASE_URL}/{doi}"
        params = {"mailto": cls.MAILTO}

        try:
            response = requests.get(url, params=params, timeout=cls.TIMEOUT)

            if response.status_code == 404:
                return None, f"DOI not found: {doi}"

            if response.status_code != 200:
                return None, f"API error: HTTP {response.status_code}"

            data = response.json()
            if data.get("status") != "ok":
                return None, "API returned invalid status"

            message = data.get("message", {})
            metadata = cls._parse_response(message)

            return metadata, None

        except requests.Timeout:
            return None, "Request timeout: CrossRef API did not respond in time"

        except requests.RequestException as e:
            return None, f"Network error: {str(e)}"

        except Exception as e:
            return None, f"Unexpected error: {str(e)}"

    @classmethod
    def _get_cache_entry(cls, doi: str) -> Optional[Dict[str, Any]]:
        """Get cache entry if exists and not expired.

        Args:
            doi: DOI string as cache key

        Returns:
            Cached metadata or None if not found/expired
        """
        with cls._cache_lock:
            entry = cls._cache.get(doi)

            if entry is None:
                return None

            # Check expiration
            if datetime.now() > entry["expires_at"]:
                # Remove expired entry
                del cls._cache[doi]
                return None

            return entry["data"]

    @classmethod
    def _set_cache_entry(cls, doi: str, data: Dict[str, Any]) -> None:
        """Store data in cache with TTL.

        Args:
            doi: DOI string as cache key
            data: Metadata to cache
        """
        expires_at = datetime.now() + timedelta(days=cls.CACHE_TTL_DAYS)

        with cls._cache_lock:
            cls._cache[doi] = {
                "data": data,
                "expires_at": expires_at,
            }

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached entries."""
        with cls._cache_lock:
            cls._cache.clear()
            cls._cache_hits = 0
            cls._cache_misses = 0

    @classmethod
    def remove_from_cache(cls, doi: str) -> bool:
        """Remove specific DOI from cache.

        Args:
            doi: DOI string to remove

        Returns:
            True if removed, False if not found
        """
        with cls._cache_lock:
            if doi in cls._cache:
                del cls._cache[doi]
                return True
            return False

    @classmethod
    def get_cache_stats(cls) -> Dict[str, int]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with cls._cache_lock:
            return {
                "size": len(cls._cache),
                "hits": cls._cache_hits,
                "misses": cls._cache_misses,
            }

    @staticmethod
    def _parse_response(data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse CrossRef API response into structured metadata.

        Args:
            data: Raw message data from CrossRef API response

        Returns:
            Parsed metadata dictionary
        """
        # Extract title
        titles = data.get("title", [])
        title = titles[0] if titles else None

        # Extract authors
        authors = []
        for author in data.get("author", []):
            given = author.get("given", "")
            family = author.get("family", "")
            if given and family:
                authors.append(f"{given} {family}")
            elif family:
                authors.append(family)
            elif given:
                authors.append(given)

        # Extract journal (container-title)
        container_titles = data.get("container-title", [])
        journal = container_titles[0] if container_titles else None

        # Extract publication year
        year = None
        published = data.get("published-print") or data.get("published-online")
        if published:
            date_parts = published.get("date-parts", [[]])
            if date_parts and date_parts[0]:
                year = date_parts[0][0]

        # Extract publisher
        publisher = data.get("publisher")

        return {
            "title": title,
            "authors": authors,
            "journal": journal,
            "year": year,
            "publisher": publisher,
        }
