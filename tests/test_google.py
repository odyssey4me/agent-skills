"""Tests for google.py skill."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from skills.google.scripts.google import (
    LEGACY_CONFIG_FILES,
    _cleanup_legacy,
    cmd_check,
    cmd_cleanup,
    find_gog,
    main,
    run_gog,
)

# ============================================================================
# FIND GOG TESTS
# ============================================================================


class TestFindGog:
    """Tests for gog binary detection."""

    @patch("skills.google.scripts.google.shutil.which", return_value="/usr/local/bin/gog")
    def test_find_gog_found(self, mock_which: Mock) -> None:
        assert find_gog() == "/usr/local/bin/gog"
        mock_which.assert_called_once_with("gog")

    @patch("skills.google.scripts.google.shutil.which", return_value=None)
    def test_find_gog_not_found(self, mock_which: Mock) -> None:
        assert find_gog() is None


# ============================================================================
# RUN GOG TESTS
# ============================================================================


class TestRunGog:
    """Tests for gog command execution."""

    @patch("skills.google.scripts.google.find_gog", return_value="/usr/local/bin/gog")
    @patch("skills.google.scripts.google.subprocess.run")
    def test_run_gog_success(self, mock_run: Mock, mock_find: Mock) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gog", "auth", "status"], returncode=0, stdout="ok\n", stderr=""
        )
        result = run_gog(["auth", "status"])
        assert result.returncode == 0
        mock_run.assert_called_once_with(
            ["/usr/local/bin/gog", "auth", "status"],
            capture_output=True,
            text=True,
        )

    @patch("skills.google.scripts.google.find_gog", return_value=None)
    def test_run_gog_not_found(self, mock_find: Mock) -> None:
        with pytest.raises(SystemExit, match="1"):
            run_gog(["auth", "status"])

    @patch("skills.google.scripts.google.find_gog", return_value="/usr/local/bin/gog")
    @patch("skills.google.scripts.google.subprocess.run")
    def test_run_gog_no_capture(self, mock_run: Mock, mock_find: Mock) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gog", "--version"], returncode=0, stdout="", stderr=""
        )
        run_gog(["--version"], capture=False)
        mock_run.assert_called_once_with(
            ["/usr/local/bin/gog", "--version"],
            text=True,
        )


# ============================================================================
# CMD CHECK TESTS
# ============================================================================


class TestCmdCheck:
    """Tests for check command."""

    @patch("skills.google.scripts.google.run_gog")
    @patch("skills.google.scripts.google.find_gog", return_value="/usr/local/bin/gog")
    def test_check_all_healthy(
        self, mock_find: Mock, mock_run: Mock, capsys: pytest.CaptureFixture
    ) -> None:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout="v0.31.0", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            subprocess.CompletedProcess([], 0, stdout='[{"id":"INBOX"}]', stderr=""),
        ]
        cmd_check(Mock())
        output = capsys.readouterr().out
        assert "gog binary:" in output
        assert "v0.31.0" in output
        assert "auth:** healthy" in output
        assert "API connectivity:** verified" in output
        assert "ready" in output

    @patch("skills.google.scripts.google.find_gog", return_value=None)
    def test_check_gog_missing(self, mock_find: Mock) -> None:
        with pytest.raises(SystemExit, match="1"):
            cmd_check(Mock())

    @patch("skills.google.scripts.google.run_gog")
    @patch("skills.google.scripts.google.find_gog", return_value="/usr/local/bin/gog")
    def test_check_auth_not_configured(self, mock_find: Mock, mock_run: Mock) -> None:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout="v0.31.0", stderr=""),
            subprocess.CompletedProcess([], 4, stdout="", stderr="no accounts"),
        ]
        with pytest.raises(SystemExit, match="4"):
            cmd_check(Mock())

    @patch("skills.google.scripts.google.run_gog")
    @patch("skills.google.scripts.google.find_gog", return_value="/usr/local/bin/gog")
    def test_check_rate_limited(
        self, mock_find: Mock, mock_run: Mock, capsys: pytest.CaptureFixture
    ) -> None:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout="v0.31.0", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            subprocess.CompletedProcess([], 7, stdout="", stderr="rate limited"),
        ]
        cmd_check(Mock())
        output = capsys.readouterr().out
        assert "rate limited" in output


# ============================================================================
# CLEANUP TESTS
# ============================================================================


class TestCleanupLegacy:
    """Tests for legacy artifact cleanup."""

    def test_cleanup_removes_config_files(self, tmp_path: Path) -> None:
        from skills.google.scripts import google

        config_dir = tmp_path / ".config" / "agent-skills"
        config_dir.mkdir(parents=True)
        for name in LEGACY_CONFIG_FILES:
            (config_dir / name).write_text("test")
        google_yaml = config_dir / "google.yaml"
        google_yaml.write_text("oauth_client:\n  client_id: test\n")
        original = google.CONFIG_DIR
        google.CONFIG_DIR = config_dir
        try:
            mock_keyring = MagicMock()
            mock_keyring.get_password.return_value = None
            with patch.dict("sys.modules", {"keyring": mock_keyring}):
                _cleanup_legacy()
            for name in LEGACY_CONFIG_FILES:
                assert not (config_dir / name).exists()
            assert not google_yaml.exists()
        finally:
            google.CONFIG_DIR = original

    def test_cleanup_preserves_other_google_yaml_keys(self, tmp_path: Path) -> None:
        from skills.google.scripts import google

        config_dir = tmp_path / ".config" / "agent-skills"
        config_dir.mkdir(parents=True)
        google_yaml = config_dir / "google.yaml"
        google_yaml.write_text("oauth_client:\n  client_id: test\ngog:\n  account: user@x.com\n")
        original = google.CONFIG_DIR
        google.CONFIG_DIR = config_dir
        try:
            mock_keyring = MagicMock()
            mock_keyring.get_password.return_value = None
            with patch.dict("sys.modules", {"keyring": mock_keyring}):
                _cleanup_legacy()
            assert google_yaml.exists()
            import yaml

            with open(google_yaml) as f:
                data = yaml.safe_load(f)
            assert "oauth_client" not in data
            assert "gog" in data
        finally:
            google.CONFIG_DIR = original

    def test_cleanup_removes_keyring_tokens(self, tmp_path: Path) -> None:
        from skills.google.scripts import google

        original = google.CONFIG_DIR
        google.CONFIG_DIR = tmp_path
        try:
            mock_keyring = MagicMock()
            mock_keyring.get_password.return_value = '{"token": "test"}'
            with patch.dict("sys.modules", {"keyring": mock_keyring}):
                _cleanup_legacy()
            assert mock_keyring.delete_password.call_count == 6
        finally:
            google.CONFIG_DIR = original

    def test_cleanup_nothing_to_clean(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        from skills.google.scripts import google

        original = google.CONFIG_DIR
        google.CONFIG_DIR = tmp_path
        try:
            mock_keyring = MagicMock()
            mock_keyring.get_password.return_value = None
            with patch.dict("sys.modules", {"keyring": mock_keyring}):
                _cleanup_legacy()
            output = capsys.readouterr().out
            assert "No legacy artifacts" in output
        finally:
            google.CONFIG_DIR = original


# ============================================================================
# CMD CLEANUP TESTS
# ============================================================================


class TestCmdCleanup:
    """Tests for cleanup command."""

    @patch("skills.google.scripts.google._cleanup_legacy")
    def test_cleanup_prints_setup_instructions(
        self, mock_cleanup: Mock, capsys: pytest.CaptureFixture
    ) -> None:
        cmd_cleanup(Mock())
        mock_cleanup.assert_called_once()
        output = capsys.readouterr().out
        assert "gog auth credentials set" in output
        assert "gog auth add" in output
        assert "gog auth doctor" in output


# ============================================================================
# MAIN TESTS
# ============================================================================


class TestMain:
    """Tests for argument parsing."""

    @patch("skills.google.scripts.google.cmd_check")
    def test_main_check(self, mock_check: Mock) -> None:
        with patch("sys.argv", ["google.py", "check"]):
            main()
        mock_check.assert_called_once()

    @patch("skills.google.scripts.google.cmd_cleanup")
    def test_main_cleanup(self, mock_cleanup: Mock) -> None:
        with patch("sys.argv", ["google.py", "cleanup"]):
            main()
        mock_cleanup.assert_called_once()

    def test_main_no_command(self) -> None:
        with patch("sys.argv", ["google.py"]), pytest.raises(SystemExit):
            main()
