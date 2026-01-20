"""Tests for install script."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.install import (
    SUPPORTED_AGENTS,
    check_agent_config,
    check_location,
    check_skills,
    check_venv,
    get_agent_config_content,
    get_repo_root,
    setup_agent_config,
    setup_path_pointer,
)


class TestGetRepoRoot:
    """Tests for get_repo_root function."""

    def test_returns_path(self):
        """Test that get_repo_root returns a Path."""
        result = get_repo_root()
        assert isinstance(result, Path)
        assert result.exists()

    def test_contains_expected_files(self):
        """Test that repo root contains expected files."""
        result = get_repo_root()
        assert (result / "AGENTS.md").exists()
        assert (result / "scripts" / "install.py").exists()


class TestCheckLocation:
    """Tests for check_location function."""

    def test_returns_tuple(self):
        """Test that check_location returns a tuple."""
        result = check_location()
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_result_structure(self):
        """Test result structure."""
        ok, status, detail = check_location()
        assert isinstance(ok, bool)
        assert isinstance(status, str)
        assert isinstance(detail, str)


class TestCheckVenv:
    """Tests for check_venv function."""

    def test_returns_tuple(self):
        """Test that check_venv returns a tuple."""
        result = check_venv()
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_venv_exists(self):
        """Test that venv is detected when it exists."""
        ok, status, _detail = check_venv()
        # In test environment, venv should exist
        assert ok is True
        assert status == "Found"


class TestCheckSkills:
    """Tests for check_skills function."""

    def test_returns_tuple(self):
        """Test that check_skills returns a tuple."""
        result = check_skills()
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_skills_found(self):
        """Test that skills are detected."""
        ok, status, detail = check_skills()
        assert ok is True
        assert "skill(s)" in status
        assert "jira" in detail


class TestCheckAgentConfig:
    """Tests for check_agent_config function."""

    def test_returns_tuple(self):
        """Test that check_agent_config returns a tuple."""
        result = check_agent_config("claude")
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_unknown_agent(self):
        """Test unknown agent."""
        ok, status, _detail = check_agent_config("unknown_agent")
        assert ok is False
        assert "Unknown" in status or "Not found" in status

    @pytest.mark.parametrize("agent", SUPPORTED_AGENTS)
    def test_supported_agents(self, agent):
        """Test that all supported agents can be checked."""
        ok, status, detail = check_agent_config(agent)
        # Just verify it doesn't crash and returns valid structure
        assert isinstance(ok, bool)
        assert isinstance(status, str)
        assert isinstance(detail, str)


class TestGetAgentConfigContent:
    """Tests for get_agent_config_content function."""

    @pytest.mark.parametrize("agent", SUPPORTED_AGENTS)
    def test_returns_path_and_content(self, agent):
        """Test that config content is returned for all agents."""
        path, content = get_agent_config_content(agent, Path("/test/path"))
        assert isinstance(path, Path)
        assert isinstance(content, str)
        assert len(content) > 0

    def test_content_contains_path(self):
        """Test that content contains the install path."""
        install_path = Path("/custom/install/path")
        _path, content = get_agent_config_content("claude", install_path)
        assert str(install_path) in content

    def test_unknown_agent_returns_empty(self):
        """Test that unknown agent returns empty."""
        path, content = get_agent_config_content("unknown", Path("/test"))
        assert path == Path()
        assert content == ""


class TestSetupPathPointer:
    """Tests for setup_path_pointer function."""

    def test_dry_run_no_changes(self, tmp_path, capsys):
        """Test that dry run doesn't create files."""
        with (
            patch("scripts.install.PATH_POINTER_FILE", tmp_path / "pointer"),
            patch("scripts.install.STANDARD_PATH", Path("/nonexistent")),
        ):
            result = setup_path_pointer(dry_run=True)

        assert result is True
        assert not (tmp_path / "pointer").exists()
        captured = capsys.readouterr()
        assert "Would create" in captured.out


class TestSetupAgentConfig:
    """Tests for setup_agent_config function."""

    def test_dry_run_no_changes(self, tmp_path, capsys):
        """Test that dry run doesn't create files."""
        config_path = tmp_path / "test_config.md"

        with (
            patch(
                "scripts.install.get_agent_config_content",
                return_value=(config_path, "test content"),
            ),
            patch("scripts.install.get_install_path", return_value=tmp_path),
        ):
            result = setup_agent_config("claude", dry_run=True)

        assert result is True
        assert not config_path.exists()
        captured = capsys.readouterr()
        assert "Would create" in captured.out

    def test_creates_config_file(self, tmp_path):
        """Test that config file is created."""
        config_path = tmp_path / "subdir" / "test_config.md"

        with (
            patch(
                "scripts.install.get_agent_config_content",
                return_value=(config_path, "test content"),
            ),
            patch("scripts.install.get_install_path", return_value=tmp_path),
        ):
            result = setup_agent_config("claude", dry_run=False)

        assert result is True
        assert config_path.exists()
        assert config_path.read_text() == "test content"

    def test_skips_existing_file(self, tmp_path, capsys):
        """Test that existing files are skipped."""
        config_path = tmp_path / "existing_config.md"
        config_path.write_text("existing content")

        with (
            patch(
                "scripts.install.get_agent_config_content",
                return_value=(config_path, "new content"),
            ),
            patch("scripts.install.get_install_path", return_value=tmp_path),
        ):
            result = setup_agent_config("claude", dry_run=False)

        assert result is True
        assert config_path.read_text() == "existing content"
        captured = capsys.readouterr()
        assert "already exists" in captured.out

    def test_unknown_agent_fails(self, tmp_path, capsys):
        """Test that unknown agent fails gracefully."""
        with patch("scripts.install.get_install_path", return_value=tmp_path):
            result = setup_agent_config("unknown_agent", dry_run=False)

        assert result is False
        captured = capsys.readouterr()
        assert "Unknown agent" in captured.out
