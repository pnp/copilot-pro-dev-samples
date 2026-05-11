"""
tests/test_textract_client.py
------------------------------
Unit tests for extractor.textract_client using mocked boto3.

All AWS calls are intercepted — no real AWS credentials needed.

Import strategy: we import textract_client via importlib to avoid triggering
extractor/__init__.py (which eagerly imports azure_cu_client requiring
AZURE_CU_ENDPOINT). The module is isolated and patched directly.
"""

import importlib
import importlib.util
import json
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Module-level import: load textract_client without going through extractor/__init__
# ---------------------------------------------------------------------------

def _load_textract_client():
    """Import extractor.textract_client bypassing extractor/__init__.py eager imports."""
    spec = importlib.util.spec_from_file_location(
        "extractor.textract_client",
        Path(__file__).parent.parent / "extractor" / "textract_client.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


textract_client = _load_textract_client()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "textract_sample_response.json"


@pytest.fixture()
def sample_response():
    """Load the realistic Textract response fixture."""
    with open(FIXTURE_PATH) as f:
        return json.load(f)


@pytest.fixture()
def env_vars(monkeypatch):
    """Set required environment variables for all tests."""
    monkeypatch.setenv("AWS_S3_BUCKET", "test-bucket")
    monkeypatch.setenv("AWS_S3_PREFIX", "textract-input")
    monkeypatch.setenv("AWS_REGION", "us-east-1")


def _make_boto3_mock(s3_mock, textract_mock):
    """Return a boto3 module mock whose .client() dispatches by service name."""
    boto3_mock = MagicMock()

    def client_side_effect(service_name, **kwargs):
        if service_name == "s3":
            return s3_mock
        if service_name == "textract":
            return textract_mock
        raise ValueError(f"Unexpected boto3 service: {service_name}")

    boto3_mock.client.side_effect = client_side_effect
    return boto3_mock


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAnalyzeDocument:

    def test_uploads_pdf_to_s3_and_starts_analysis(self, env_vars, sample_response, tmp_path):
        """S3 upload_file is called with correct bucket/key; result contains Blocks."""
        # Arrange
        fake_pdf = tmp_path / "report.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4 fake")

        s3_mock = MagicMock()
        textract_mock = MagicMock()
        textract_mock.start_document_analysis.return_value = {"JobId": "job-abc"}
        textract_mock.get_document_analysis.return_value = sample_response
        boto3_mock = _make_boto3_mock(s3_mock, textract_mock)

        # Act — patch boto3 on the already-loaded module object
        with patch.object(textract_client, "boto3", boto3_mock):
            result = textract_client.analyze_document(str(fake_pdf))

        # Assert: S3 upload called with correct kwargs
        s3_mock.upload_file.assert_called_once()
        upload_call_kwargs = s3_mock.upload_file.call_args
        assert upload_call_kwargs.kwargs["Bucket"] == "test-bucket"
        assert upload_call_kwargs.kwargs["Filename"] == str(fake_pdf)
        assert upload_call_kwargs.kwargs["Key"].startswith("textract-input/")
        assert upload_call_kwargs.kwargs["Key"].endswith(".pdf")

        # Assert: Textract start called with correct kwargs
        textract_mock.start_document_analysis.assert_called_once()
        start_call_kwargs = textract_mock.start_document_analysis.call_args.kwargs
        assert start_call_kwargs["FeatureTypes"] == ["TABLES"]
        assert start_call_kwargs["DocumentLocation"]["S3Object"]["Bucket"] == "test-bucket"

        # Assert: result contains Blocks
        assert "Blocks" in result
        assert len(result["Blocks"]) > 0

    def test_polls_until_succeeded(self, env_vars, tmp_path):
        """get_document_analysis is called 3 times: IN_PROGRESS x2, then SUCCEEDED."""
        fake_pdf = tmp_path / "report.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4 fake")

        s3_mock = MagicMock()
        textract_mock = MagicMock()
        textract_mock.start_document_analysis.return_value = {"JobId": "job-poll-test"}

        # IN_PROGRESS, IN_PROGRESS, SUCCEEDED
        textract_mock.get_document_analysis.side_effect = [
            {"JobStatus": "IN_PROGRESS"},
            {"JobStatus": "IN_PROGRESS"},
            {"JobStatus": "SUCCEEDED", "Blocks": [{"Id": "b1", "BlockType": "PAGE"}]},
        ]
        boto3_mock = _make_boto3_mock(s3_mock, textract_mock)

        with patch.object(textract_client, "boto3", boto3_mock):
            with patch.object(textract_client, "time") as mock_time:
                # Make time.time() always return 0 so the timeout never triggers
                mock_time.time.return_value = 0
                mock_time.sleep = MagicMock()
                result = textract_client.analyze_document(str(fake_pdf))

        # 3 calls to get_document_analysis during polling
        assert textract_mock.get_document_analysis.call_count == 3
        assert result["Blocks"] == [{"Id": "b1", "BlockType": "PAGE"}]

    def test_raises_on_failed_job(self, env_vars, tmp_path):
        """RuntimeError is raised with 'Textract job failed' when status is FAILED."""
        fake_pdf = tmp_path / "report.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4 fake")

        s3_mock = MagicMock()
        textract_mock = MagicMock()
        textract_mock.start_document_analysis.return_value = {"JobId": "job-fail-test"}
        textract_mock.get_document_analysis.return_value = {
            "JobStatus": "FAILED",
            "StatusMessage": "Unsupported document type",
        }
        boto3_mock = _make_boto3_mock(s3_mock, textract_mock)

        with patch.object(textract_client, "boto3", boto3_mock):
            with patch.object(textract_client, "time") as mock_time:
                mock_time.time.return_value = 0
                mock_time.sleep = MagicMock()
                with pytest.raises(RuntimeError, match="Textract job failed"):
                    textract_client.analyze_document(str(fake_pdf))

    def test_cleans_up_s3_after_success(self, env_vars, sample_response, tmp_path):
        """delete_object is called after a successful analysis run."""
        fake_pdf = tmp_path / "report.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4 fake")

        s3_mock = MagicMock()
        textract_mock = MagicMock()
        textract_mock.start_document_analysis.return_value = {"JobId": "job-cleanup-ok"}
        textract_mock.get_document_analysis.return_value = sample_response
        boto3_mock = _make_boto3_mock(s3_mock, textract_mock)

        with patch.object(textract_client, "boto3", boto3_mock):
            textract_client.analyze_document(str(fake_pdf))

        # delete_object must have been called once
        s3_mock.delete_object.assert_called_once()
        delete_kwargs = s3_mock.delete_object.call_args.kwargs
        assert delete_kwargs["Bucket"] == "test-bucket"
        assert delete_kwargs["Key"].startswith("textract-input/")

    def test_cleans_up_s3_even_on_failure(self, env_vars, tmp_path):
        """delete_object is called even when Textract fails (finally block)."""
        fake_pdf = tmp_path / "report.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4 fake")

        s3_mock = MagicMock()
        textract_mock = MagicMock()
        textract_mock.start_document_analysis.return_value = {"JobId": "job-cleanup-fail"}
        textract_mock.get_document_analysis.return_value = {
            "JobStatus": "FAILED",
            "StatusMessage": "Access denied",
        }
        boto3_mock = _make_boto3_mock(s3_mock, textract_mock)

        with patch.object(textract_client, "boto3", boto3_mock):
            with patch.object(textract_client, "time") as mock_time:
                mock_time.time.return_value = 0
                mock_time.sleep = MagicMock()
                with pytest.raises(RuntimeError):
                    textract_client.analyze_document(str(fake_pdf))

        # S3 cleanup must still have been called
        s3_mock.delete_object.assert_called_once()

    def test_handles_pagination(self, env_vars, tmp_path):
        """Blocks from multiple pages are merged into a single list."""
        fake_pdf = tmp_path / "report.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4 fake")

        page1_blocks = [{"Id": "b1", "BlockType": "PAGE"}, {"Id": "b2", "BlockType": "TABLE"}]
        page2_blocks = [{"Id": "b3", "BlockType": "CELL"}, {"Id": "b4", "BlockType": "WORD"}]

        s3_mock = MagicMock()
        textract_mock = MagicMock()
        textract_mock.start_document_analysis.return_value = {"JobId": "job-paginate"}

        # First get_document_analysis call (during polling): SUCCEEDED with NextToken
        # Second call (pagination loop): more blocks, no NextToken
        textract_mock.get_document_analysis.side_effect = [
            {
                "JobStatus": "SUCCEEDED",
                "Blocks": page1_blocks,
                "NextToken": "token-page-2",
            },
            {
                "JobStatus": "SUCCEEDED",
                "Blocks": page2_blocks,
                # No NextToken -- this is the last page
            },
        ]
        boto3_mock = _make_boto3_mock(s3_mock, textract_mock)

        with patch.object(textract_client, "boto3", boto3_mock):
            result = textract_client.analyze_document(str(fake_pdf))

        # All blocks from both pages must be present
        assert len(result["Blocks"]) == 4
        block_ids = [b["Id"] for b in result["Blocks"]]
        assert block_ids == ["b1", "b2", "b3", "b4"]

        # Pagination call must pass NextToken
        second_call_kwargs = textract_mock.get_document_analysis.call_args_list[1].kwargs
        assert second_call_kwargs.get("NextToken") == "token-page-2"
