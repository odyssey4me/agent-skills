"""Tests for shared HTTP utilities."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import responses

from shared.http import APIError, delete, get, make_request, post, put


@pytest.fixture
def _mock_credentials():
    """Mock credentials for testing."""
    with patch("shared.http.get_credentials") as mock:
        creds = MagicMock()
        creds.url = "https://api.example.com"
        creds.email = "test@example.com"
        creds.token = "test-token"
        creds.username = None
        creds.password = None
        creds.is_valid.return_value = True
        mock.return_value = creds
        yield creds


class TestMakeRequest:
    """Tests for make_request function."""

    @responses.activate
    def test_make_request_get_success(self, _mock_credentials):
        """Test successful GET request."""
        responses.add(
            responses.GET,
            "https://api.example.com/api/items",
            json={"items": [{"id": 1}]},
            status=200,
        )

        result = make_request("test-service", "GET", "/api/items")

        assert result == {"items": [{"id": 1}]}
        assert len(responses.calls) == 1

    @responses.activate
    def test_make_request_post_success(self, _mock_credentials):
        """Test successful POST request."""
        responses.add(
            responses.POST,
            "https://api.example.com/api/items",
            json={"id": 1, "name": "New Item"},
            status=201,
        )

        result = make_request("test-service", "POST", "/api/items", json_data={"name": "New Item"})

        assert result == {"id": 1, "name": "New Item"}

    @responses.activate
    def test_make_request_with_params(self, _mock_credentials):
        """Test request with query parameters."""
        responses.add(
            responses.GET,
            "https://api.example.com/api/search",
            json={"results": []},
            status=200,
        )

        make_request("test-service", "GET", "/api/search", params={"q": "test", "limit": 10})

        assert "q=test" in responses.calls[0].request.url
        assert "limit=10" in responses.calls[0].request.url

    @responses.activate
    def test_make_request_404_error(self, _mock_credentials):
        """Test request that returns 404."""
        responses.add(
            responses.GET,
            "https://api.example.com/api/items/999",
            json={"error": "Not found"},
            status=404,
        )

        with pytest.raises(APIError) as exc_info:
            make_request("test-service", "GET", "/api/items/999")

        assert exc_info.value.status_code == 404
        assert "404" in str(exc_info.value)

    @responses.activate
    def test_make_request_204_no_content(self, _mock_credentials):
        """Test request that returns 204 No Content."""
        responses.add(
            responses.DELETE,
            "https://api.example.com/api/items/1",
            status=204,
        )

        result = make_request("test-service", "DELETE", "/api/items/1")

        assert result == {}

    def test_make_request_no_credentials(self):
        """Test request without valid credentials."""
        with patch("shared.http.get_credentials") as mock:
            creds = MagicMock()
            creds.is_valid.return_value = False
            mock.return_value = creds

            with pytest.raises(APIError) as exc_info:
                make_request("test-service", "GET", "/api/items")

            assert "No valid credentials" in str(exc_info.value)

    @responses.activate
    def test_make_request_bearer_auth(self, _mock_credentials):
        """Test request with bearer token auth."""
        _mock_credentials.email = None  # No email = bearer auth

        responses.add(
            responses.GET,
            "https://api.example.com/api/items",
            json={"items": []},
            status=200,
        )

        make_request("test-service", "GET", "/api/items")

        auth_header = responses.calls[0].request.headers.get("Authorization")
        assert auth_header == "Bearer test-token"


class TestConvenienceFunctions:
    """Tests for get, post, put, delete convenience functions."""

    @responses.activate
    def test_get_function(self, _mock_credentials):
        """Test get convenience function."""
        responses.add(
            responses.GET,
            "https://api.example.com/api/items",
            json={"items": []},
            status=200,
        )

        result = get("test-service", "/api/items")

        assert result == {"items": []}

    @responses.activate
    def test_post_function(self, _mock_credentials):
        """Test post convenience function."""
        responses.add(
            responses.POST,
            "https://api.example.com/api/items",
            json={"id": 1},
            status=201,
        )

        result = post("test-service", "/api/items", {"name": "Test"})

        assert result == {"id": 1}

    @responses.activate
    def test_put_function(self, _mock_credentials):
        """Test put convenience function."""
        responses.add(
            responses.PUT,
            "https://api.example.com/api/items/1",
            json={"id": 1, "name": "Updated"},
            status=200,
        )

        result = put("test-service", "/api/items/1", {"name": "Updated"})

        assert result == {"id": 1, "name": "Updated"}

    @responses.activate
    def test_delete_function(self, _mock_credentials):
        """Test delete convenience function."""
        responses.add(
            responses.DELETE,
            "https://api.example.com/api/items/1",
            status=204,
        )

        result = delete("test-service", "/api/items/1")

        assert result == {}
