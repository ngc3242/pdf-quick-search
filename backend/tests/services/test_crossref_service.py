"""Tests for CrossRef API client service.

TDD RED Phase: Write failing tests first.
"""

import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear CrossRef cache before each test."""
    from app.services.crossref_service import CrossRefService

    CrossRefService.clear_cache()
    yield
    CrossRefService.clear_cache()


class TestCrossRefServiceFetchMetadata:
    """Test cases for fetching metadata from CrossRef API."""

    def test_fetch_metadata_success(self):
        """Test successful metadata fetch from CrossRef API."""
        from app.services.crossref_service import CrossRefService

        # Mock successful API response
        mock_response = {
            "status": "ok",
            "message": {
                "title": ["Test Article Title"],
                "author": [
                    {"given": "John", "family": "Doe"},
                    {"given": "Jane", "family": "Smith"},
                ],
                "container-title": ["Nature"],
                "published-print": {"date-parts": [[2023, 5, 15]]},
                "publisher": "Nature Publishing Group",
            },
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response

            result, error = CrossRefService.fetch_metadata("10.1038/nature12373")

            assert error is None
            assert result is not None
            assert result["title"] == "Test Article Title"
            assert result["authors"] == ["John Doe", "Jane Smith"]
            assert result["journal"] == "Nature"
            assert result["year"] == 2023
            assert result["publisher"] == "Nature Publishing Group"

    def test_fetch_metadata_with_mailto_parameter(self):
        """Test that API request includes mailto parameter for Polite Pool."""
        from app.services.crossref_service import CrossRefService

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "status": "ok",
                "message": {"title": ["Test"]},
            }

            CrossRefService.fetch_metadata("10.1038/nature12373")

            # Check that mailto parameter was included
            call_args = mock_get.call_args
            assert "mailto" in call_args[1].get("params", {})

    def test_fetch_metadata_invalid_doi(self):
        """Test handling of invalid DOI."""
        from app.services.crossref_service import CrossRefService

        result, error = CrossRefService.fetch_metadata("")
        assert result is None
        assert error is not None
        assert "invalid" in error.lower()

    def test_fetch_metadata_none_doi(self):
        """Test handling of None DOI."""
        from app.services.crossref_service import CrossRefService

        result, error = CrossRefService.fetch_metadata(None)
        assert result is None
        assert error is not None

    def test_fetch_metadata_not_found(self):
        """Test handling of 404 response (DOI not found)."""
        from app.services.crossref_service import CrossRefService

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 404

            result, error = CrossRefService.fetch_metadata("10.1038/nonexistent")

            assert result is None
            assert error is not None
            assert "not found" in error.lower()

    def test_fetch_metadata_api_error(self):
        """Test handling of API error responses."""
        from app.services.crossref_service import CrossRefService

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 500

            result, error = CrossRefService.fetch_metadata("10.1038/nature12373")

            assert result is None
            assert error is not None

    def test_fetch_metadata_timeout(self):
        """Test handling of request timeout."""
        from app.services.crossref_service import CrossRefService
        import requests

        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.Timeout("Connection timed out")

            result, error = CrossRefService.fetch_metadata("10.1038/nature12373")

            assert result is None
            assert error is not None
            assert "timeout" in error.lower()

    def test_fetch_metadata_network_error(self):
        """Test handling of network errors."""
        from app.services.crossref_service import CrossRefService
        import requests

        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("Network error")

            result, error = CrossRefService.fetch_metadata("10.1038/nature12373")

            assert result is None
            assert error is not None

    def test_fetch_metadata_timeout_value(self):
        """Test that API request uses correct timeout (2 seconds)."""
        from app.services.crossref_service import CrossRefService

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "status": "ok",
                "message": {"title": ["Test"]},
            }

            CrossRefService.fetch_metadata("10.1038/nature12373")

            # Check timeout parameter
            call_args = mock_get.call_args
            assert call_args[1].get("timeout") == 2


class TestCrossRefServiceParseResponse:
    """Test cases for parsing CrossRef API response."""

    def test_parse_response_full_data(self):
        """Test parsing response with all fields present."""
        from app.services.crossref_service import CrossRefService

        response_data = {
            "title": ["Full Article Title"],
            "author": [
                {"given": "Alice", "family": "Brown"},
                {"given": "Bob", "family": "Green"},
            ],
            "container-title": ["Science"],
            "published-print": {"date-parts": [[2022, 12, 1]]},
            "publisher": "AAAS",
        }

        result = CrossRefService._parse_response(response_data)

        assert result["title"] == "Full Article Title"
        assert result["authors"] == ["Alice Brown", "Bob Green"]
        assert result["journal"] == "Science"
        assert result["year"] == 2022
        assert result["publisher"] == "AAAS"

    def test_parse_response_missing_title(self):
        """Test parsing response with missing title."""
        from app.services.crossref_service import CrossRefService

        response_data = {
            "author": [{"given": "John", "family": "Doe"}],
            "container-title": ["Nature"],
        }

        result = CrossRefService._parse_response(response_data)

        assert result["title"] is None

    def test_parse_response_missing_authors(self):
        """Test parsing response with missing authors."""
        from app.services.crossref_service import CrossRefService

        response_data = {
            "title": ["Test Title"],
            "container-title": ["Nature"],
        }

        result = CrossRefService._parse_response(response_data)

        assert result["authors"] == []

    def test_parse_response_author_without_given_name(self):
        """Test parsing author with only family name."""
        from app.services.crossref_service import CrossRefService

        response_data = {
            "title": ["Test"],
            "author": [{"family": "Institution"}],
        }

        result = CrossRefService._parse_response(response_data)

        assert result["authors"] == ["Institution"]

    def test_parse_response_published_online_fallback(self):
        """Test falling back to published-online when published-print is missing."""
        from app.services.crossref_service import CrossRefService

        response_data = {
            "title": ["Test"],
            "published-online": {"date-parts": [[2021, 6, 15]]},
        }

        result = CrossRefService._parse_response(response_data)

        assert result["year"] == 2021

    def test_parse_response_empty_data(self):
        """Test parsing empty response data."""
        from app.services.crossref_service import CrossRefService

        result = CrossRefService._parse_response({})

        assert result["title"] is None
        assert result["authors"] == []
        assert result["journal"] is None
        assert result["year"] is None
        assert result["publisher"] is None

    def test_parse_response_multiple_container_titles(self):
        """Test parsing response with multiple container titles."""
        from app.services.crossref_service import CrossRefService

        response_data = {
            "title": ["Test"],
            "container-title": ["Short Name", "Full Journal Name"],
        }

        result = CrossRefService._parse_response(response_data)

        # Should use first container title
        assert result["journal"] == "Short Name"


class TestCrossRefServiceAPIEndpoint:
    """Test cases for API endpoint construction."""

    def test_api_endpoint_format(self):
        """Test correct API endpoint URL construction."""
        from app.services.crossref_service import CrossRefService

        doi = "10.1038/nature12373"
        expected_url = f"https://api.crossref.org/works/{doi}"

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "status": "ok",
                "message": {"title": ["Test"]},
            }

            CrossRefService.fetch_metadata(doi)

            # Check URL
            call_args = mock_get.call_args
            assert call_args[0][0] == expected_url


class TestCrossRefServiceReturnTuple:
    """Test cases for consistent tuple return pattern."""

    def test_fetch_metadata_returns_tuple(self):
        """Test that fetch_metadata always returns tuple."""
        from app.services.crossref_service import CrossRefService

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "status": "ok",
                "message": {"title": ["Test"]},
            }

            result = CrossRefService.fetch_metadata("10.1038/nature12373")

            assert isinstance(result, tuple)
            assert len(result) == 2

    def test_fetch_metadata_error_returns_tuple(self):
        """Test that fetch_metadata returns tuple on error."""
        from app.services.crossref_service import CrossRefService

        result = CrossRefService.fetch_metadata(None)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] is None
        assert result[1] is not None


class TestCrossRefServiceEdgeCases:
    """Test cases for edge cases and full coverage."""

    def test_fetch_metadata_invalid_status(self):
        """Test handling of API response with invalid status."""
        from app.services.crossref_service import CrossRefService

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "status": "error",
                "message": {"title": ["Test"]},
            }

            result, error = CrossRefService.fetch_metadata("10.1038/nature12373")

            assert result is None
            assert error is not None
            assert "invalid status" in error.lower()

    def test_fetch_metadata_unexpected_exception(self):
        """Test handling of unexpected exception."""
        from app.services.crossref_service import CrossRefService

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.side_effect = ValueError("Invalid JSON")

            result, error = CrossRefService.fetch_metadata("10.1038/nature12373")

            assert result is None
            assert error is not None
            assert "unexpected" in error.lower()

    def test_parse_response_author_with_only_given_name(self):
        """Test parsing author with only given name (no family name)."""
        from app.services.crossref_service import CrossRefService

        response_data = {
            "title": ["Test"],
            "author": [{"given": "OnlyGivenName"}],
        }

        result = CrossRefService._parse_response(response_data)

        assert result["authors"] == ["OnlyGivenName"]
