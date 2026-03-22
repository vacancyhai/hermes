"""Unit tests for ai_extractor and pdf_extractor services."""

import json
from unittest.mock import MagicMock, patch

import pytest


# --- pdf_extractor ---

def test_extract_text_from_pdf_single_page():
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Page one text"
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)

    with patch("pdfplumber.open", return_value=mock_pdf):
        from app.services.pdf_extractor import extract_text_from_pdf
        result = extract_text_from_pdf("/fake/path.pdf")

    assert result == "Page one text"


def test_extract_text_from_pdf_multiple_pages():
    page1 = MagicMock()
    page1.extract_text.return_value = "First page"
    page2 = MagicMock()
    page2.extract_text.return_value = "Second page"
    mock_pdf = MagicMock()
    mock_pdf.pages = [page1, page2]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)

    with patch("pdfplumber.open", return_value=mock_pdf):
        from app.services.pdf_extractor import extract_text_from_pdf
        result = extract_text_from_pdf("/fake/path.pdf")

    assert result == "First page\n\nSecond page"


def test_extract_text_from_pdf_empty_page():
    """Pages with no text (None) are skipped."""
    page1 = MagicMock()
    page1.extract_text.return_value = None
    page2 = MagicMock()
    page2.extract_text.return_value = "Real text"
    mock_pdf = MagicMock()
    mock_pdf.pages = [page1, page2]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)

    with patch("pdfplumber.open", return_value=mock_pdf):
        from app.services.pdf_extractor import extract_text_from_pdf
        result = extract_text_from_pdf("/fake/path.pdf")

    assert result == "Real text"


def test_extract_text_from_pdf_all_empty():
    page = MagicMock()
    page.extract_text.return_value = None
    mock_pdf = MagicMock()
    mock_pdf.pages = [page]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)

    with patch("pdfplumber.open", return_value=mock_pdf):
        from app.services.pdf_extractor import extract_text_from_pdf
        result = extract_text_from_pdf("/fake/path.pdf")

    assert result == ""


# --- ai_extractor ---

def test_extract_job_data_no_api_key():
    """Returns None immediately when ANTHROPIC_API_KEY is not set."""
    with patch("app.services.ai_extractor.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = None
        from app.services.ai_extractor import extract_job_data
        result = extract_job_data("some pdf text")

    assert result is None


def test_extract_job_data_returns_parsed_json():
    """Successful Claude API call returns parsed dict."""
    expected = {"job_title": "SSC CGL 2024", "organization": "SSC", "total_vacancies": 1000}

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps(expected))]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("app.services.ai_extractor.settings") as mock_settings, \
         patch("anthropic.Anthropic", return_value=mock_client):
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_settings.AI_MODEL = "claude-3-haiku-20240307"
        from app.services.ai_extractor import extract_job_data
        result = extract_job_data("some pdf text")

    assert result == expected


def test_extract_job_data_strips_markdown_code_block():
    """Response wrapped in ```json``` is parsed correctly."""
    inner = {"job_title": "Test Job"}
    response_text = f"```json\n{json.dumps(inner)}\n```"

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=response_text)]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("app.services.ai_extractor.settings") as mock_settings, \
         patch("anthropic.Anthropic", return_value=mock_client):
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_settings.AI_MODEL = "claude-3-haiku-20240307"
        from app.services.ai_extractor import extract_job_data
        result = extract_job_data("pdf text")

    assert result == inner


def test_extract_job_data_strips_plain_code_block():
    """Response wrapped in ``` (no language) is parsed correctly."""
    inner = {"job_title": "Plain Block"}
    response_text = f"```\n{json.dumps(inner)}\n```"

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=response_text)]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("app.services.ai_extractor.settings") as mock_settings, \
         patch("anthropic.Anthropic", return_value=mock_client):
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_settings.AI_MODEL = "claude-3-haiku-20240307"
        from app.services.ai_extractor import extract_job_data
        result = extract_job_data("pdf text")

    assert result == inner


def test_extract_job_data_api_exception_returns_none():
    """Exception from API call returns None (no crash)."""
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("API error")

    with patch("app.services.ai_extractor.settings") as mock_settings, \
         patch("anthropic.Anthropic", return_value=mock_client):
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_settings.AI_MODEL = "claude-3-haiku-20240307"
        from app.services.ai_extractor import extract_job_data
        result = extract_job_data("pdf text")

    assert result is None


def test_extract_job_data_invalid_json_returns_none():
    """Non-JSON response returns None."""
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="not valid json at all")]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("app.services.ai_extractor.settings") as mock_settings, \
         patch("anthropic.Anthropic", return_value=mock_client):
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_settings.AI_MODEL = "claude-3-haiku-20240307"
        from app.services.ai_extractor import extract_job_data
        result = extract_job_data("pdf text")

    assert result is None
