"""Tests for google-slides.py skill."""

from __future__ import annotations

# Import from skills module - use importlib to handle hyphenated module name
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Load the module with hyphenated name
spec = importlib.util.spec_from_file_location(
    "google_slides",
    Path(__file__).parent.parent / "skills" / "google-slides" / "scripts" / "google-slides.py",
)
google_slides = importlib.util.module_from_spec(spec)
sys.modules["google_slides"] = google_slides
spec.loader.exec_module(google_slides)

# Now import from the loaded module
AuthenticationError = google_slides.AuthenticationError
SlidesAPIError = google_slides.SlidesAPIError
SLIDES_SCOPES = google_slides.SLIDES_SCOPES
SLIDES_SCOPES_DEFAULT = google_slides.SLIDES_SCOPES_DEFAULT
DRIVE_SCOPES_READONLY = google_slides.DRIVE_SCOPES_READONLY
build_drive_service = google_slides.build_drive_service
export_presentation_as_pdf = google_slides.export_presentation_as_pdf
build_parser = google_slides.build_parser
build_slides_service = google_slides.build_slides_service
check_slides_connectivity = google_slides.check_slides_connectivity
cmd_auth_setup = google_slides.cmd_auth_setup
cmd_auth_reset = google_slides.cmd_auth_reset
cmd_auth_status = google_slides.cmd_auth_status
cmd_check = google_slides.cmd_check
cmd_images_create = google_slides.cmd_images_create
cmd_presentations_create = google_slides.cmd_presentations_create
cmd_presentations_get = google_slides.cmd_presentations_get
cmd_presentations_read = google_slides.cmd_presentations_read
cmd_shapes_create = google_slides.cmd_shapes_create
cmd_slides_create = google_slides.cmd_slides_create
cmd_slides_delete = google_slides.cmd_slides_delete
cmd_text_insert = google_slides.cmd_text_insert
create_image = google_slides.create_image
create_presentation = google_slides.create_presentation
create_shape = google_slides.create_shape
create_slide = google_slides.create_slide
delete_credential = google_slides.delete_credential
delete_slide = google_slides.delete_slide
format_presentation_summary = google_slides.format_presentation_summary
format_slide_info = google_slides.format_slide_info
get_credential = google_slides.get_credential
get_google_credentials = google_slides.get_google_credentials
_run_oauth_flow = google_slides._run_oauth_flow
get_oauth_client_config = google_slides.get_oauth_client_config
get_presentation = google_slides.get_presentation
handle_api_error = google_slides.handle_api_error
insert_text = google_slides.insert_text
read_presentation_content = google_slides.read_presentation_content
_extract_slide_text = google_slides._extract_slide_text
_extract_table_text = google_slides._extract_table_text
_extract_text_from_text_content = google_slides._extract_text_from_text_content
load_config = google_slides.load_config
save_config = google_slides.save_config
set_credential = google_slides.set_credential

# ============================================================================
# KEYRING CREDENTIAL TESTS
# ============================================================================


class TestKeyringFunctions:
    """Tests for keyring credential functions."""

    @patch("google_slides.keyring")
    def test_get_credential(self, mock_keyring):
        """Test getting credential from keyring."""
        mock_keyring.get_password.return_value = "secret"
        result = get_credential("test-key")
        assert result == "secret"
        mock_keyring.get_password.assert_called_once_with("agent-skills", "test-key")

    @patch("google_slides.keyring")
    def test_get_credential_not_found(self, mock_keyring):
        """Test getting non-existent credential."""
        mock_keyring.get_password.return_value = None
        result = get_credential("nonexistent")
        assert result is None

    @patch("google_slides.keyring")
    def test_set_credential(self, mock_keyring):
        """Test setting credential in keyring."""
        set_credential("test-key", "secret")
        mock_keyring.set_password.assert_called_once_with("agent-skills", "test-key", "secret")

    @patch("google_slides.keyring")
    def test_delete_credential(self, mock_keyring):
        """Test deleting credential from keyring."""
        delete_credential("test-key")
        mock_keyring.delete_password.assert_called_once_with("agent-skills", "test-key")

    @patch("google_slides.keyring")
    def test_delete_credential_not_exists(self, mock_keyring):
        """Test deleting non-existent credential doesn't raise error."""
        import keyring.errors

        mock_keyring.errors.PasswordDeleteError = keyring.errors.PasswordDeleteError
        mock_keyring.delete_password.side_effect = keyring.errors.PasswordDeleteError("Not found")
        # Should not raise
        delete_credential("test-key")


# ============================================================================
# CONFIG MANAGEMENT TESTS
# ============================================================================


class TestConfigManagement:
    """Tests for config file management."""

    def test_load_config_nonexistent(self, tmp_path, monkeypatch):
        """Test loading config when file doesn't exist."""
        monkeypatch.setattr("google_slides.CONFIG_DIR", tmp_path / "nonexistent")
        config = load_config("google-slides")
        assert config is None

    def test_save_and_load_config(self, tmp_path, monkeypatch):
        """Test saving and loading config."""
        config_dir = tmp_path / "config"
        monkeypatch.setattr("google_slides.CONFIG_DIR", config_dir)

        test_config = {
            "oauth_client": {
                "client_id": "test-client-id",
                "client_secret": "test-client-secret",
            }
        }

        save_config("google-slides", test_config)
        loaded = load_config("google-slides")

        assert loaded == test_config


# ============================================================================
# OAUTH CLIENT CONFIG TESTS
# ============================================================================


class TestOAuthClientConfig:
    """Tests for OAuth client configuration."""

    @patch("google_slides.load_config")
    def test_get_oauth_client_config_from_service_file(self, mock_load_config):
        """Test getting OAuth config from service-specific file."""
        mock_load_config.return_value = {
            "oauth_client": {
                "client_id": "file-client-id",
                "client_secret": "file-client-secret",
            }
        }

        config = get_oauth_client_config("google-slides")

        assert config["installed"]["client_id"] == "file-client-id"
        assert config["installed"]["client_secret"] == "file-client-secret"

    @patch("google_slides.load_config")
    def test_get_oauth_client_config_from_service_env(self, mock_load_config, monkeypatch):
        """Test getting OAuth config from service-specific environment."""
        mock_load_config.return_value = None
        monkeypatch.setenv("GOOGLE_SLIDES_CLIENT_ID", "env-client-id")
        monkeypatch.setenv("GOOGLE_SLIDES_CLIENT_SECRET", "env-client-secret")

        config = get_oauth_client_config("google-slides")

        assert config["installed"]["client_id"] == "env-client-id"
        assert config["installed"]["client_secret"] == "env-client-secret"

    @patch("google_slides.load_config")
    def test_get_oauth_client_config_from_shared_file(self, mock_load_config, monkeypatch):
        """Test getting OAuth config from shared google.yaml file."""
        # No service-specific config or env vars
        monkeypatch.delenv("GOOGLE_SLIDES_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_SLIDES_CLIENT_SECRET", raising=False)

        def side_effect(service):
            if service == "google":
                return {
                    "oauth_client": {
                        "client_id": "shared-file-client-id",
                        "client_secret": "shared-file-client-secret",
                    }
                }
            return None

        mock_load_config.side_effect = side_effect

        config = get_oauth_client_config("google-slides")

        assert config["installed"]["client_id"] == "shared-file-client-id"
        assert config["installed"]["client_secret"] == "shared-file-client-secret"

    @patch("google_slides.load_config")
    def test_get_oauth_client_config_from_shared_env(self, mock_load_config, monkeypatch):
        """Test getting OAuth config from shared environment variables."""
        mock_load_config.return_value = None
        monkeypatch.delenv("GOOGLE_SLIDES_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_SLIDES_CLIENT_SECRET", raising=False)
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "shared-env-client-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "shared-env-client-secret")

        config = get_oauth_client_config("google-slides")

        assert config["installed"]["client_id"] == "shared-env-client-id"
        assert config["installed"]["client_secret"] == "shared-env-client-secret"

    @patch("google_slides.load_config")
    def test_get_oauth_client_config_not_found(self, mock_load_config, monkeypatch):
        """Test error when OAuth config not found anywhere."""
        mock_load_config.return_value = None
        monkeypatch.delenv("GOOGLE_SLIDES_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_SLIDES_CLIENT_SECRET", raising=False)
        monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)

        with pytest.raises(AuthenticationError, match="OAuth client credentials not found"):
            get_oauth_client_config("google-slides")


# ============================================================================
# PRESENTATION OPERATION TESTS
# ============================================================================


class TestPresentationOperations:
    """Tests for presentation operations."""

    def test_create_presentation(self):
        """Test creating a presentation."""
        mock_service = Mock()
        mock_service.presentations().create().execute.return_value = {
            "presentationId": "test-pres-id",
            "title": "Test Presentation",
            "slides": [{"objectId": "slide1"}],
        }

        result = create_presentation(mock_service, "Test Presentation")

        assert result["presentationId"] == "test-pres-id"
        assert result["title"] == "Test Presentation"

    def test_get_presentation(self):
        """Test getting a presentation."""
        mock_service = Mock()
        mock_service.presentations().get().execute.return_value = {
            "presentationId": "test-pres-id",
            "title": "Test Presentation",
            "slides": [{"objectId": "slide1"}],
        }

        result = get_presentation(mock_service, "test-pres-id")

        assert result["presentationId"] == "test-pres-id"

    def test_read_presentation_content(self):
        """Test reading presentation content from all slides."""
        mock_service = Mock()
        mock_service.presentations().get().execute.return_value = {
            "presentationId": "test-pres-id",
            "title": "Test Presentation",
            "slides": [
                {
                    "objectId": "slide1",
                    "pageElements": [
                        {
                            "shape": {
                                "shapeType": "TEXT_BOX",
                                "text": {
                                    "textElements": [{"textRun": {"content": "Title Slide\n"}}]
                                },
                            }
                        }
                    ],
                },
                {
                    "objectId": "slide2",
                    "pageElements": [
                        {
                            "shape": {
                                "shapeType": "TEXT_BOX",
                                "text": {
                                    "textElements": [{"textRun": {"content": "Content Slide\n"}}]
                                },
                            }
                        }
                    ],
                },
            ],
        }

        result = read_presentation_content(mock_service, "test-pres-id")

        assert "--- Slide 1 ---" in result
        assert "Title Slide" in result
        assert "--- Slide 2 ---" in result
        assert "Content Slide" in result

    def test_extract_slide_text_with_shapes(self):
        """Test extracting text from slide with multiple shapes."""
        slide = {
            "objectId": "slide1",
            "pageElements": [
                {
                    "shape": {
                        "shapeType": "TEXT_BOX",
                        "text": {
                            "textElements": [
                                {"textRun": {"content": "Heading\n"}},
                                {"textRun": {"content": "Subheading\n"}},
                            ]
                        },
                    }
                },
                {
                    "shape": {
                        "shapeType": "RECTANGLE",
                        "text": {"textElements": [{"textRun": {"content": "Box text\n"}}]},
                    }
                },
            ],
        }

        result = _extract_slide_text(slide)

        assert "Heading" in result
        assert "Subheading" in result
        assert "Box text" in result

    def test_extract_table_text(self):
        """Test extracting text from a table element."""
        table = {
            "tableRows": [
                {
                    "tableCells": [
                        {"text": {"textElements": [{"textRun": {"content": "Header 1\n"}}]}},
                        {"text": {"textElements": [{"textRun": {"content": "Header 2\n"}}]}},
                    ]
                },
                {
                    "tableCells": [
                        {"text": {"textElements": [{"textRun": {"content": "Value 1\n"}}]}},
                        {"text": {"textElements": [{"textRun": {"content": "Value 2\n"}}]}},
                    ]
                },
            ]
        }

        result = _extract_table_text(table)

        assert "| Header 1 | Header 2 |" in result
        assert "| --- | --- |" in result
        assert "| Value 1 | Value 2 |" in result

    @patch("google_slides.build_drive_service")
    def test_export_presentation_as_pdf(self, mock_build_drive):
        """Test exporting presentation as PDF."""
        mock_service = Mock()
        mock_build_drive.return_value = mock_service
        mock_service.files().export().execute.return_value = b"%PDF-1.4 mock content"

        result = export_presentation_as_pdf("pres-123")

        assert result == b"%PDF-1.4 mock content"
        call_args = mock_service.files().export.call_args
        assert call_args[1]["fileId"] == "pres-123"
        assert call_args[1]["mimeType"] == "application/pdf"


# ============================================================================
# SLIDE OPERATION TESTS
# ============================================================================


class TestSlideOperations:
    """Tests for slide operations."""

    def test_create_slide_blank(self):
        """Test creating a blank slide."""
        mock_service = Mock()
        mock_service.presentations().batchUpdate().execute.return_value = {
            "replies": [
                {
                    "createSlide": {
                        "objectId": "slide_abc123",
                    }
                }
            ]
        }

        result = create_slide(mock_service, "test-pres-id", "BLANK")

        assert "replies" in result
        call_args = mock_service.presentations().batchUpdate.call_args
        assert (
            call_args[1]["body"]["requests"][0]["createSlide"]["slideLayoutReference"][
                "predefinedLayout"
            ]
            == "BLANK"
        )

    def test_create_slide_with_layout(self):
        """Test creating slide with specific layout."""
        mock_service = Mock()
        mock_service.presentations().batchUpdate().execute.return_value = {
            "replies": [
                {
                    "createSlide": {
                        "objectId": "slide_abc123",
                    }
                }
            ]
        }

        result = create_slide(mock_service, "test-pres-id", "TITLE_AND_BODY")

        assert "replies" in result
        call_args = mock_service.presentations().batchUpdate.call_args
        assert (
            call_args[1]["body"]["requests"][0]["createSlide"]["slideLayoutReference"][
                "predefinedLayout"
            ]
            == "TITLE_AND_BODY"
        )

    def test_create_slide_with_index(self):
        """Test creating slide at specific index."""
        mock_service = Mock()
        mock_service.presentations().batchUpdate().execute.return_value = {
            "replies": [
                {
                    "createSlide": {
                        "objectId": "slide_abc123",
                    }
                }
            ]
        }

        result = create_slide(mock_service, "test-pres-id", "BLANK", insert_index=2)

        assert "replies" in result
        call_args = mock_service.presentations().batchUpdate.call_args
        assert call_args[1]["body"]["requests"][0]["createSlide"]["insertionIndex"] == 2

    def test_delete_slide(self):
        """Test deleting a slide."""
        mock_service = Mock()
        mock_service.presentations().batchUpdate().execute.return_value = {}

        result = delete_slide(mock_service, "test-pres-id", "slide_abc123")

        assert result == {}
        call_args = mock_service.presentations().batchUpdate.call_args
        assert call_args[1]["body"]["requests"][0]["deleteObject"]["objectId"] == "slide_abc123"


# ============================================================================
# TEXT OPERATION TESTS
# ============================================================================


class TestTextOperations:
    """Tests for text operations."""

    def test_insert_text_default_position(self):
        """Test inserting text with default position."""
        mock_service = Mock()
        mock_service.presentations().batchUpdate().execute.return_value = {}

        result = insert_text(mock_service, "test-pres-id", "slide_abc123", "Hello World")

        assert result == {}
        call_args = mock_service.presentations().batchUpdate.call_args
        requests = call_args[1]["body"]["requests"]

        # Check createShape request
        assert "createShape" in requests[0]
        assert requests[0]["createShape"]["shapeType"] == "TEXT_BOX"

        # Check insertText request
        assert "insertText" in requests[1]
        assert requests[1]["insertText"]["text"] == "Hello World"

    def test_insert_text_custom_position(self):
        """Test inserting text with custom position and size."""
        mock_service = Mock()
        mock_service.presentations().batchUpdate().execute.return_value = {}

        result = insert_text(
            mock_service,
            "test-pres-id",
            "slide_abc123",
            "Custom Text",
            x=200,
            y=150,
            width=500,
            height=120,
        )

        assert result == {}
        call_args = mock_service.presentations().batchUpdate.call_args
        requests = call_args[1]["body"]["requests"]

        # Verify transform coordinates (points to EMUs conversion)
        transform = requests[0]["createShape"]["elementProperties"]["transform"]
        # 200 points * 12700 EMU/point = 2540000 EMU
        assert transform["translateX"] == 200 * 12700
        assert transform["translateY"] == 150 * 12700


# ============================================================================
# SHAPE OPERATION TESTS
# ============================================================================


class TestShapeOperations:
    """Tests for shape operations."""

    def test_create_shape_rectangle(self):
        """Test creating a rectangle shape."""
        mock_service = Mock()
        mock_service.presentations().batchUpdate().execute.return_value = {}

        result = create_shape(mock_service, "test-pres-id", "slide_abc123", "RECTANGLE")

        assert result == {}
        call_args = mock_service.presentations().batchUpdate.call_args
        requests = call_args[1]["body"]["requests"]

        assert "createShape" in requests[0]
        assert requests[0]["createShape"]["shapeType"] == "RECTANGLE"

    def test_create_shape_custom_size(self):
        """Test creating shape with custom size and position."""
        mock_service = Mock()
        mock_service.presentations().batchUpdate().execute.return_value = {}

        result = create_shape(
            mock_service,
            "test-pres-id",
            "slide_abc123",
            "ELLIPSE",
            x=300,
            y=200,
            width=250,
            height=250,
        )

        assert result == {}
        call_args = mock_service.presentations().batchUpdate.call_args
        requests = call_args[1]["body"]["requests"]

        assert requests[0]["createShape"]["shapeType"] == "ELLIPSE"
        # Verify size conversion to EMUs
        size = requests[0]["createShape"]["elementProperties"]["size"]
        assert size["width"]["magnitude"] == 250 * 12700
        assert size["height"]["magnitude"] == 250 * 12700


# ============================================================================
# IMAGE OPERATION TESTS
# ============================================================================


class TestImageOperations:
    """Tests for image operations."""

    def test_create_image(self):
        """Test creating an image."""
        mock_service = Mock()
        mock_service.presentations().batchUpdate().execute.return_value = {}

        result = create_image(
            mock_service, "test-pres-id", "slide_abc123", "https://example.com/image.png"
        )

        assert result == {}
        call_args = mock_service.presentations().batchUpdate.call_args
        requests = call_args[1]["body"]["requests"]

        assert "createImage" in requests[0]
        assert requests[0]["createImage"]["url"] == "https://example.com/image.png"

    def test_create_image_custom_size(self):
        """Test creating image with custom size and position."""
        mock_service = Mock()
        mock_service.presentations().batchUpdate().execute.return_value = {}

        result = create_image(
            mock_service,
            "test-pres-id",
            "slide_abc123",
            "https://example.com/chart.png",
            x=50,
            y=100,
            width=500,
            height=400,
        )

        assert result == {}
        call_args = mock_service.presentations().batchUpdate.call_args
        requests = call_args[1]["body"]["requests"]

        # Verify position
        transform = requests[0]["createImage"]["elementProperties"]["transform"]
        assert transform["translateX"] == 50 * 12700
        assert transform["translateY"] == 100 * 12700


# ============================================================================
# OUTPUT FORMATTING TESTS
# ============================================================================


class TestOutputFormatting:
    """Tests for output formatting functions."""

    def test_format_presentation_summary(self):
        """Test formatting presentation summary as markdown."""
        presentation = {
            "presentationId": "abc123",
            "title": "Test Presentation",
            "slides": [
                {"objectId": "slide1"},
                {"objectId": "slide2"},
            ],
        }

        result = format_presentation_summary(presentation)

        assert result.startswith("### Test Presentation\n")
        assert "- **Presentation ID:** abc123" in result
        assert "- **Slides:** 2" in result

    def test_format_slide_info(self):
        """Test formatting slide information as markdown."""
        slide = {
            "objectId": "slide_abc123",
            "slideProperties": {"layoutObjectId": "layout1"},
            "pageElements": [
                {"shape": {"shapeType": "TEXT_BOX"}},
                {"shape": {"shapeType": "RECTANGLE"}},
                {"image": {"sourceUrl": "https://example.com/img.png"}},
            ],
        }

        result = format_slide_info(slide, 0)

        assert result.startswith("### Slide 1\n")
        assert "- **ID:** slide_abc123" in result
        assert "1 text" in result
        assert "1 shapes" in result
        assert "1 images" in result


# ============================================================================
# CLI COMMAND HANDLER TESTS
# ============================================================================


class TestCLICommands:
    """Tests for CLI command handlers."""

    @patch("google_slides.check_slides_connectivity")
    def test_cmd_check_success(self, mock_check, capsys):
        """Test check command when authenticated."""
        mock_check.return_value = {
            "authenticated": True,
            "test_presentation_id": "test-pres-123",
            "scopes": {"readonly": True, "write": True, "all_scopes": []},
        }

        args = Mock()
        result = cmd_check(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Successfully authenticated" in captured.out

    @patch("google_slides.check_slides_connectivity")
    def test_cmd_check_failure(self, mock_check, capsys):
        """Test check command when authentication fails."""
        mock_check.return_value = {
            "authenticated": False,
            "error": "No credentials found",
        }

        args = Mock()
        result = cmd_check(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Authentication failed" in captured.out

    @patch("google_slides.check_slides_connectivity")
    def test_cmd_check_warning_no_write_scope(self, mock_check, capsys):
        """Test check command warns when write scope not granted."""
        mock_check.return_value = {
            "authenticated": True,
            "test_presentation_id": "test-pres-123",
            "scopes": {"readonly": True, "write": False, "all_scopes": []},
        }

        args = Mock()
        result = cmd_check(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Write scope not granted" in captured.out

    @patch("google_slides.save_config")
    @patch("google_slides.load_config")
    def test_cmd_auth_setup(self, mock_load, mock_save, capsys):
        """Test auth setup command."""
        mock_load.return_value = None
        args = Mock(client_id="test-id", client_secret="test-secret")

        result = cmd_auth_setup(args)

        assert result == 0
        mock_save.assert_called_once()
        captured = capsys.readouterr()
        assert "OAuth client credentials saved" in captured.out

    @patch("google_slides.build_slides_service")
    @patch("google_slides.create_presentation")
    def test_cmd_presentations_create(self, mock_create, _mock_build_service, capsys):
        """Test presentations create command."""
        mock_create.return_value = {
            "presentationId": "new-pres-123",
            "title": "New Presentation",
            "slides": [{"objectId": "slide1"}],
        }

        args = Mock(title="New Presentation", json=False)
        result = cmd_presentations_create(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Presentation created successfully" in captured.out
        assert "new-pres-123" in captured.out

    @patch("google_slides.build_slides_service")
    @patch("google_slides.get_presentation")
    def test_cmd_presentations_get(self, mock_get, _mock_build_service, capsys):
        """Test presentations get command."""
        mock_get.return_value = {
            "presentationId": "pres-123",
            "title": "Test Presentation",
            "slides": [{"objectId": "slide1", "slideProperties": {}, "pageElements": []}],
        }

        args = Mock(presentation_id="pres-123", json=False)
        result = cmd_presentations_get(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Test Presentation" in captured.out

    @patch("google_slides.build_slides_service")
    @patch("google_slides.read_presentation_content")
    def test_cmd_presentations_read(self, mock_read, _mock_build_service, capsys):
        """Test presentations read command."""
        mock_read.return_value = "--- Slide 1 ---\nTitle Text\n\n--- Slide 2 ---\nContent"

        args = Mock(presentation_id="pres-123", format="text", json=False)
        result = cmd_presentations_read(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "--- Slide 1 ---" in captured.out
        assert "Title Text" in captured.out

    @patch("google_slides.build_slides_service")
    @patch("google_slides.read_presentation_content")
    def test_cmd_presentations_read_json(self, mock_read, _mock_build_service, capsys):
        """Test presentations read command with JSON output."""
        mock_read.return_value = "Slide content here"

        args = Mock(presentation_id="pres-123", format="text", json=True)
        result = cmd_presentations_read(args)

        assert result == 0
        captured = capsys.readouterr()
        assert '"content"' in captured.out
        assert "Slide content here" in captured.out

    @patch("google_slides.export_presentation_as_pdf")
    def test_cmd_presentations_read_pdf_format(self, mock_export, tmp_path, capsys):
        """Test presentations read command with PDF format."""
        mock_export.return_value = b"%PDF-1.4 mock content"
        output_file = tmp_path / "test.pdf"

        args = Mock(presentation_id="pres-123", format="pdf", output=str(output_file), json=False)
        result = cmd_presentations_read(args)

        assert result == 0
        assert output_file.exists()
        assert output_file.read_bytes() == b"%PDF-1.4 mock content"
        captured = capsys.readouterr()
        assert "PDF saved to:" in captured.out

    @patch("google_slides.export_presentation_as_pdf")
    def test_cmd_presentations_read_pdf_format_default_output(
        self, mock_export, tmp_path, capsys, monkeypatch
    ):
        """Test presentations read command with PDF format using default output filename."""
        mock_export.return_value = b"%PDF-1.4 mock content"
        # Change to tmp_path so default file is created there
        monkeypatch.chdir(tmp_path)

        args = Mock(presentation_id="pres-123", format="pdf", output=None, json=False)
        result = cmd_presentations_read(args)

        assert result == 0
        default_file = tmp_path / "pres-123.pdf"
        assert default_file.exists()
        assert default_file.read_bytes() == b"%PDF-1.4 mock content"
        captured = capsys.readouterr()
        assert "PDF saved to: pres-123.pdf" in captured.out

    @patch("google_slides.build_slides_service")
    @patch("google_slides.create_slide")
    def test_cmd_slides_create(self, mock_create, _mock_build_service, capsys):
        """Test slides create command."""
        mock_create.return_value = {
            "replies": [
                {
                    "createSlide": {
                        "objectId": "slide_abc123",
                    }
                }
            ]
        }

        args = Mock(presentation_id="pres-123", layout="BLANK", index=None, json=False)
        result = cmd_slides_create(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Slide created successfully" in captured.out
        assert "slide_abc123" in captured.out

    @patch("google_slides.build_slides_service")
    @patch("google_slides.delete_slide")
    def test_cmd_slides_delete(self, mock_delete, _mock_build_service, capsys):
        """Test slides delete command."""
        mock_delete.return_value = {}

        args = Mock(presentation_id="pres-123", slide_id="slide_abc123", json=False)
        result = cmd_slides_delete(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Slide deleted successfully" in captured.out

    @patch("google_slides.build_slides_service")
    @patch("google_slides.insert_text")
    def test_cmd_text_insert(self, mock_insert, _mock_build_service, capsys):
        """Test text insert command."""
        mock_insert.return_value = {}

        args = Mock(
            presentation_id="pres-123",
            slide_id="slide_abc123",
            text="Hello World",
            x=100,
            y=100,
            width=400,
            height=100,
            json=False,
        )
        result = cmd_text_insert(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Text inserted successfully" in captured.out
        assert "Hello World" in captured.out

    @patch("google_slides.build_slides_service")
    @patch("google_slides.create_shape")
    def test_cmd_shapes_create(self, mock_create, _mock_build_service, capsys):
        """Test shapes create command."""
        mock_create.return_value = {}

        args = Mock(
            presentation_id="pres-123",
            slide_id="slide_abc123",
            shape_type="RECTANGLE",
            x=100,
            y=100,
            width=200,
            height=200,
            json=False,
        )
        result = cmd_shapes_create(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Shape created successfully" in captured.out
        assert "RECTANGLE" in captured.out

    @patch("google_slides.build_slides_service")
    @patch("google_slides.create_image")
    def test_cmd_images_create(self, mock_create, _mock_build_service, capsys):
        """Test images create command."""
        mock_create.return_value = {}

        args = Mock(
            presentation_id="pres-123",
            slide_id="slide_abc123",
            image_url="https://example.com/image.png",
            x=100,
            y=100,
            width=300,
            height=200,
            json=False,
        )
        result = cmd_images_create(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Image created successfully" in captured.out
        assert "https://example.com/image.png" in captured.out

    @patch("google_slides.delete_credential")
    @patch("builtins.print")
    def test_cmd_auth_reset(self, _mock_print, mock_delete):
        """Test auth reset command."""
        args = Mock()
        exit_code = cmd_auth_reset(args)

        assert exit_code == 0
        mock_delete.assert_called_once_with("google-slides-token-json")

    @patch("google_slides.get_credential")
    @patch("builtins.print")
    def test_cmd_auth_status_with_token(self, _mock_print, mock_get_credential):
        """Test auth status command with stored token."""
        token_data = {
            "token": "access-token",
            "refresh_token": "refresh-token",
            "scopes": ["https://www.googleapis.com/auth/presentations.readonly"],
            "expiry": "2025-01-01T00:00:00Z",
            "client_id": "1234567890abcdef.apps.googleusercontent.com",
        }
        mock_get_credential.return_value = json.dumps(token_data)

        args = Mock()
        exit_code = cmd_auth_status(args)

        assert exit_code == 0

    @patch("google_slides.get_credential")
    @patch("builtins.print")
    def test_cmd_auth_status_no_token(self, _mock_print, mock_get_credential):
        """Test auth status command with no stored token."""
        mock_get_credential.return_value = None

        args = Mock()
        exit_code = cmd_auth_status(args)

        assert exit_code == 1


# ============================================================================
# ARGUMENT PARSER TESTS
# ============================================================================


class TestArgumentParser:
    """Tests for CLI argument parser."""

    def test_parser_check_command(self):
        """Test parser for check command."""
        parser = build_parser()
        args = parser.parse_args(["check"])
        assert args.command == "check"

    def test_parser_auth_setup(self):
        """Test parser for auth setup command."""
        parser = build_parser()
        args = parser.parse_args(
            ["auth", "setup", "--client-id", "id", "--client-secret", "secret"]
        )
        assert args.command == "auth"
        assert args.auth_command == "setup"
        assert args.client_id == "id"
        assert args.client_secret == "secret"

    def test_parser_auth_reset(self):
        """Test parser for auth reset command."""
        parser = build_parser()

        # Test auth reset
        args = parser.parse_args(["auth", "reset"])
        assert args.command == "auth"
        assert args.auth_command == "reset"

    def test_parser_auth_status(self):
        """Test parser for auth status command."""
        parser = build_parser()

        # Test auth status
        args = parser.parse_args(["auth", "status"])
        assert args.command == "auth"
        assert args.auth_command == "status"

    def test_parser_presentations_create(self):
        """Test parser for presentations create command."""
        parser = build_parser()
        args = parser.parse_args(["presentations", "create", "--title", "Test"])
        assert args.command == "presentations"
        assert args.presentations_command == "create"
        assert args.title == "Test"

    def test_parser_presentations_get(self):
        """Test parser for presentations get command."""
        parser = build_parser()
        args = parser.parse_args(["presentations", "get", "pres-123"])
        assert args.command == "presentations"
        assert args.presentations_command == "get"
        assert args.presentation_id == "pres-123"

    def test_parser_presentations_read(self):
        """Test parser for presentations read command."""
        parser = build_parser()
        args = parser.parse_args(["presentations", "read", "pres-123"])
        assert args.command == "presentations"
        assert args.presentations_command == "read"
        assert args.presentation_id == "pres-123"

    def test_parser_presentations_read_json(self):
        """Test parser for presentations read with --json flag."""
        parser = build_parser()
        args = parser.parse_args(["presentations", "read", "pres-123", "--json"])
        assert args.presentations_command == "read"
        assert args.json is True

    def test_parser_presentations_read_default_format(self):
        """Test parser for presentations read defaults to text format."""
        parser = build_parser()
        args = parser.parse_args(["presentations", "read", "pres-123"])
        assert args.format == "text"

    def test_parser_presentations_read_pdf_format(self):
        """Test parser for presentations read with pdf format and output."""
        parser = build_parser()
        args = parser.parse_args(
            ["presentations", "read", "pres-123", "--format", "pdf", "--output", "output.pdf"]
        )
        assert args.format == "pdf"
        assert args.output == "output.pdf"

    def test_parser_presentations_read_output_short_flag(self):
        """Test parser for presentations read with -o short flag."""
        parser = build_parser()
        args = parser.parse_args(
            ["presentations", "read", "pres-123", "--format", "pdf", "-o", "pres.pdf"]
        )
        assert args.output == "pres.pdf"

    def test_parser_slides_create(self):
        """Test parser for slides create command."""
        parser = build_parser()
        args = parser.parse_args(["slides", "create", "pres-123", "--layout", "TITLE"])
        assert args.command == "slides"
        assert args.slides_command == "create"
        assert args.presentation_id == "pres-123"
        assert args.layout == "TITLE"

    def test_parser_slides_create_with_index(self):
        """Test parser for slides create with index."""
        parser = build_parser()
        args = parser.parse_args(
            ["slides", "create", "pres-123", "--layout", "BLANK", "--index", "2"]
        )
        assert args.index == 2

    def test_parser_slides_delete(self):
        """Test parser for slides delete command."""
        parser = build_parser()
        args = parser.parse_args(["slides", "delete", "pres-123", "--slide-id", "slide_abc123"])
        assert args.command == "slides"
        assert args.slides_command == "delete"
        assert args.slide_id == "slide_abc123"

    def test_parser_text_insert(self):
        """Test parser for text insert command."""
        parser = build_parser()
        args = parser.parse_args(
            ["text", "insert", "pres-123", "--slide-id", "slide_abc123", "--text", "Hello"]
        )
        assert args.command == "text"
        assert args.text_command == "insert"
        assert args.text == "Hello"

    def test_parser_text_insert_with_position(self):
        """Test parser for text insert with position."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "text",
                "insert",
                "pres-123",
                "--slide-id",
                "slide_abc123",
                "--text",
                "Hello",
                "--x",
                "200",
                "--y",
                "150",
                "--width",
                "500",
                "--height",
                "120",
            ]
        )
        assert args.x == 200
        assert args.y == 150
        assert args.width == 500
        assert args.height == 120

    def test_parser_shapes_create(self):
        """Test parser for shapes create command."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "shapes",
                "create",
                "pres-123",
                "--slide-id",
                "slide_abc123",
                "--shape-type",
                "RECTANGLE",
            ]
        )
        assert args.command == "shapes"
        assert args.shapes_command == "create"
        assert args.shape_type == "RECTANGLE"

    def test_parser_images_create(self):
        """Test parser for images create command."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "images",
                "create",
                "pres-123",
                "--slide-id",
                "slide_abc123",
                "--image-url",
                "https://example.com/img.png",
            ]
        )
        assert args.command == "images"
        assert args.images_command == "create"
        assert args.image_url == "https://example.com/img.png"

    def test_parser_json_flag(self):
        """Test parser handles --json flag."""
        parser = build_parser()
        args = parser.parse_args(["presentations", "get", "pres-123", "--json"])
        assert args.json is True


# ============================================================================
# AUTHENTICATION FLOW TESTS
# ============================================================================


class TestAuthenticationFlow:
    """Tests for authentication flow edge cases."""

    @patch("google_slides.InstalledAppFlow")
    @patch("google_slides.get_oauth_client_config")
    @patch("google_slides.set_credential")
    @patch("google_slides.get_credential")
    def test_get_google_credentials_oauth_flow(
        self, mock_get_cred, mock_set_cred, mock_get_config, mock_flow_class
    ):
        """Test OAuth flow when no token exists."""
        mock_get_cred.return_value = None
        mock_config = {"installed": {"client_id": "id", "client_secret": "secret"}}
        mock_get_config.return_value = mock_config

        mock_flow_instance = Mock()
        mock_flow_class.from_client_config.return_value = mock_flow_instance
        mock_creds = Mock()
        mock_creds.to_json.return_value = '{"token": "new"}'
        mock_flow_instance.run_local_server.return_value = mock_creds

        result = get_google_credentials("google-slides", ["https://scope"])

        assert result == mock_creds
        mock_set_cred.assert_called_once_with("google-slides-token-json", '{"token": "new"}')

    @patch("google_slides.Request")
    @patch("google_slides.Credentials")
    @patch("google_slides.set_credential")
    @patch("google_slides.get_credential")
    def test_get_google_credentials_refresh_token(
        self, mock_get_cred, mock_set_cred, mock_creds_class, _mock_request_class
    ):
        """Test token refresh when expired."""
        token_json = '{"token": "expired", "refresh_token": "refresh"}'
        mock_get_cred.return_value = token_json

        mock_creds = Mock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh"
        mock_creds.to_json.return_value = '{"token": "refreshed"}'
        mock_creds_class.from_authorized_user_info.return_value = mock_creds

        result = get_google_credentials("google-slides", ["https://scope"])

        mock_creds.refresh.assert_called_once()
        mock_set_cred.assert_called_once_with("google-slides-token-json", '{"token": "refreshed"}')
        assert result == mock_creds

    @patch("google_slides.InstalledAppFlow")
    @patch("google_slides.get_oauth_client_config")
    @patch("google_slides.Credentials")
    @patch("google_slides.get_credential")
    def test_get_google_credentials_corrupted_token(
        self, mock_get_cred, mock_creds_class, mock_get_config, _mock_flow_class
    ):
        """Test handling of corrupted token."""
        mock_get_cred.return_value = "invalid json"
        mock_creds_class.from_authorized_user_info.side_effect = Exception("Parse error")
        mock_get_config.side_effect = AuthenticationError("No credentials")

        with pytest.raises(AuthenticationError):
            get_google_credentials("google-slides", ["https://scope"])

    @patch("google_slides.InstalledAppFlow")
    @patch("google_slides.get_oauth_client_config")
    @patch("google_slides.get_credential")
    def test_get_google_credentials_oauth_flow_failure(
        self, mock_get_cred, mock_get_config, mock_flow_class
    ):
        """Test OAuth flow failure."""
        mock_get_cred.return_value = None
        mock_config = {"installed": {"client_id": "id", "client_secret": "secret"}}
        mock_get_config.return_value = mock_config

        mock_flow_instance = Mock()
        mock_flow_class.from_client_config.return_value = mock_flow_instance
        mock_flow_instance.run_local_server.side_effect = Exception("Flow failed")

        with pytest.raises(AuthenticationError, match="OAuth flow failed"):
            get_google_credentials("google-slides", ["https://scope"])

    @patch("google_slides.delete_credential")
    @patch("google_slides._run_oauth_flow")
    @patch("google_slides.get_credential")
    @patch("google_slides.Credentials")
    def test_get_google_credentials_scope_mismatch(
        self,
        mock_creds_class,
        mock_get_credential,
        mock_run_oauth,
        mock_delete_credential,
    ):
        """Test re-auth triggers when token lacks requested scopes."""
        token_data = {
            "token": "access-token",
            "refresh_token": "refresh-token",
            "scopes": ["https://www.googleapis.com/auth/presentations.readonly"],
        }
        mock_get_credential.return_value = json.dumps(token_data)

        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds_class.from_authorized_user_info.return_value = mock_creds

        mock_new_creds = Mock()
        mock_run_oauth.return_value = mock_new_creds

        result = get_google_credentials(
            "google-slides",
            [
                "https://www.googleapis.com/auth/presentations.readonly",
                "https://www.googleapis.com/auth/presentations",
            ],
        )

        assert result == mock_new_creds
        mock_delete_credential.assert_called_once_with("google-slides-token-json")
        call_args = mock_run_oauth.call_args[0]
        merged_scopes = set(call_args[1])
        assert "https://www.googleapis.com/auth/presentations.readonly" in merged_scopes
        assert "https://www.googleapis.com/auth/presentations" in merged_scopes

    @patch("google_slides.get_credential")
    @patch("google_slides.Credentials")
    def test_get_google_credentials_no_scopes_in_token(self, mock_creds_class, mock_get_credential):
        """Test backward compatibility when token has no scopes field."""
        token_data = {"token": "access-token", "refresh_token": "refresh-token"}
        mock_get_credential.return_value = json.dumps(token_data)

        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds_class.from_authorized_user_info.return_value = mock_creds

        result = get_google_credentials("google-slides", ["https://scope"])

        assert result == mock_creds


# ============================================================================
# API ERROR HANDLING TESTS
# ============================================================================


class TestAPIErrorHandling:
    """Tests for API error handling."""

    def test_handle_api_error_basic(self):
        """Test basic API error handling."""
        from googleapiclient.errors import HttpError

        error = Mock(spec=HttpError)
        error.resp = Mock()
        error.resp.status = 404
        error.resp.reason = "Not found"
        error.content = b'{"error": {"message": "Presentation not found"}}'

        with pytest.raises(SlidesAPIError, match="Presentation not found.*404"):
            handle_api_error(error)

    def test_handle_api_error_insufficient_scope(self):
        """Test insufficient scope error with helpful message."""
        from googleapiclient.errors import HttpError

        error = Mock(spec=HttpError)
        error.resp = Mock()
        error.resp.status = 403
        error.resp.reason = "Forbidden"
        error.content = b'{"error": {"message": "Insufficient permissions"}}'

        with pytest.raises(SlidesAPIError, match="Insufficient OAuth scope"):
            handle_api_error(error)

    def test_handle_api_error_malformed_response(self):
        """Test error with malformed JSON response."""
        from googleapiclient.errors import HttpError

        error = Mock(spec=HttpError)
        error.resp = Mock()
        error.resp.status = 500
        error.resp.reason = "Internal Server Error"
        error.content = b"not json"

        with pytest.raises(SlidesAPIError, match="Internal Server Error.*500"):
            handle_api_error(error)

    def test_slides_api_error_attributes(self):
        """Test SlidesAPIError attributes."""
        error = SlidesAPIError("Test error", status_code=404, details={"key": "value"})
        assert str(error) == "Test error"
        assert error.status_code == 404
        assert error.details == {"key": "value"}


# ============================================================================
# BUILD SERVICE TESTS
# ============================================================================


class TestBuildService:
    """Tests for build_slides_service function."""

    @patch("google_slides.get_google_credentials")
    @patch("google_slides.build")
    def test_build_slides_service_default_scopes(self, mock_build, mock_get_creds):
        """Test building service with default scopes."""
        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds
        mock_service = Mock()
        mock_build.return_value = mock_service

        result = build_slides_service()

        mock_get_creds.assert_called_once_with("google-slides", SLIDES_SCOPES_DEFAULT)
        mock_build.assert_called_once_with("slides", "v1", credentials=mock_creds)
        assert result == mock_service

    @patch("google_slides.get_google_credentials")
    @patch("google_slides.build")
    def test_build_slides_service_custom_scopes(self, mock_build, mock_get_creds):
        """Test building service with custom scopes."""
        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds
        mock_service = Mock()
        mock_build.return_value = mock_service

        custom_scopes = ["https://custom.scope"]
        result = build_slides_service(custom_scopes)

        mock_get_creds.assert_called_once_with("google-slides", custom_scopes)
        assert result == mock_service

    @patch("google_slides.get_google_credentials")
    @patch("google_slides.build")
    def test_build_drive_service_default_scopes(self, mock_build, mock_get_creds):
        """Test building Drive service with default scopes."""
        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds
        mock_service = Mock()
        mock_build.return_value = mock_service

        result = build_drive_service()

        mock_get_creds.assert_called_once_with("google-slides", DRIVE_SCOPES_READONLY)
        mock_build.assert_called_once_with("drive", "v3", credentials=mock_creds)
        assert result == mock_service
