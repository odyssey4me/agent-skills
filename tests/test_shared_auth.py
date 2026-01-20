"""Tests for shared authentication utilities."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

from shared.auth.keyring_store import delete_credential, get_credential, set_credential
from shared.auth.token import Credentials, get_credentials, load_config, save_config


class TestKeyringStore:
    """Tests for keyring_store module."""

    def test_get_credential(self):
        """Test getting a credential from keyring."""
        with patch("shared.auth.keyring_store.keyring") as mock_keyring:
            mock_keyring.get_password.return_value = "test-value"

            result = get_credential("test-key")

            assert result == "test-value"
            mock_keyring.get_password.assert_called_once_with("agent-skills", "test-key")

    def test_get_credential_not_found(self):
        """Test getting a non-existent credential."""
        with patch("shared.auth.keyring_store.keyring") as mock_keyring:
            mock_keyring.get_password.return_value = None

            result = get_credential("nonexistent-key")

            assert result is None

    def test_set_credential(self):
        """Test setting a credential in keyring."""
        with patch("shared.auth.keyring_store.keyring") as mock_keyring:
            set_credential("test-key", "test-value")

            mock_keyring.set_password.assert_called_once_with(
                "agent-skills", "test-key", "test-value"
            )

    def test_delete_credential(self):
        """Test deleting a credential from keyring."""
        with patch("shared.auth.keyring_store.keyring") as mock_keyring:
            delete_credential("test-key")

            mock_keyring.delete_password.assert_called_once_with("agent-skills", "test-key")

    def test_delete_credential_not_found(self):
        """Test deleting a non-existent credential."""
        with patch("shared.auth.keyring_store.keyring") as mock_keyring:
            mock_keyring.delete_password.side_effect = Exception("Not found")
            mock_keyring.errors = MagicMock()
            mock_keyring.errors.PasswordDeleteError = Exception

            # Should not raise
            delete_credential("nonexistent-key")


class TestCredentials:
    """Tests for Credentials dataclass."""

    def test_credentials_valid_with_token(self):
        """Test credentials are valid with token and URL."""
        creds = Credentials(url="https://example.com", token="abc123")
        assert creds.is_valid() is True

    def test_credentials_valid_with_username_password(self):
        """Test credentials are valid with username/password."""
        creds = Credentials(url="https://example.com", username="user", password="pass")
        assert creds.is_valid() is True

    def test_credentials_invalid_without_url(self):
        """Test credentials are invalid without URL."""
        creds = Credentials(token="abc123")
        assert creds.is_valid() is False

    def test_credentials_invalid_empty(self):
        """Test empty credentials are invalid."""
        creds = Credentials()
        assert creds.is_valid() is False


class TestGetCredentials:
    """Tests for get_credentials function."""

    def test_get_credentials_from_keyring(self):
        """Test getting credentials from keyring."""
        with patch("shared.auth.token.get_credential") as mock_get:
            mock_get.side_effect = lambda key: {
                "jira-url": "https://test.atlassian.net",
                "jira-email": "test@example.com",
                "jira-token": "abc123",
            }.get(key)

            creds = get_credentials("jira")

            assert creds.url == "https://test.atlassian.net"
            assert creds.email == "test@example.com"
            assert creds.token == "abc123"
            assert creds.is_valid() is True

    def test_get_credentials_from_env(self):
        """Test getting credentials from environment variables."""
        with (
            patch("shared.auth.token.get_credential", return_value=None),
            patch.dict(
                os.environ,
                {
                    "JIRA_URL": "https://env.atlassian.net",
                    "JIRA_EMAIL": "env@example.com",
                    "JIRA_TOKEN": "env-token",
                },
            ),
        ):
            creds = get_credentials("jira")

            assert creds.url == "https://env.atlassian.net"
            assert creds.email == "env@example.com"
            assert creds.token == "env-token"

    def test_get_credentials_priority_keyring_over_env(self):
        """Test keyring takes priority over environment variables."""
        with patch("shared.auth.token.get_credential") as mock_get:
            mock_get.side_effect = lambda key: {
                "jira-url": "https://keyring.atlassian.net",
            }.get(key)

            with patch.dict(os.environ, {"JIRA_URL": "https://env.atlassian.net"}):
                creds = get_credentials("jira")

                assert creds.url == "https://keyring.atlassian.net"


class TestConfig:
    """Tests for config file operations."""

    def test_load_config_not_found(self, tmp_path):
        """Test loading config when file doesn't exist."""
        with patch("shared.auth.token.CONFIG_DIR", tmp_path):
            result = load_config("nonexistent")
            assert result is None

    def test_save_and_load_config(self, tmp_path):
        """Test saving and loading config."""
        with patch("shared.auth.token.CONFIG_DIR", tmp_path):
            config = {"url": "https://example.com", "token": "abc123"}
            save_config("test-service", config)

            loaded = load_config("test-service")
            assert loaded == config

    def test_save_config_creates_directory(self, tmp_path):
        """Test save_config creates the config directory."""
        config_dir = tmp_path / "subdir"
        with patch("shared.auth.token.CONFIG_DIR", config_dir):
            save_config("test", {"key": "value"})
            assert config_dir.exists()
