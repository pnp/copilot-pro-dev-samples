"""
Tests for PDF hash caching in main.py — covers:
  Fix 3: Skip Azure CU API call when cached result exists for the same PDF.
"""

import json
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

from main import _pdf_hash, _load_cached_result, _save_cached_result


class TestPdfHash:
    """_pdf_hash produces a stable SHA-256 hex digest of file contents."""

    def test_same_content_same_hash(self, tmp_path):
        """Two files with identical content produce the same hash."""
        f1 = tmp_path / "a.pdf"
        f2 = tmp_path / "b.pdf"
        f1.write_bytes(b"identical content")
        f2.write_bytes(b"identical content")
        assert _pdf_hash(f1) == _pdf_hash(f2)

    def test_different_content_different_hash(self, tmp_path):
        """Two files with different content produce different hashes."""
        f1 = tmp_path / "a.pdf"
        f2 = tmp_path / "b.pdf"
        f1.write_bytes(b"content A")
        f2.write_bytes(b"content B")
        assert _pdf_hash(f1) != _pdf_hash(f2)

    def test_hash_is_sha256(self, tmp_path):
        """The hash matches Python's hashlib.sha256."""
        f = tmp_path / "test.pdf"
        content = b"test data"
        f.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert _pdf_hash(f) == expected


class TestCacheRoundTrip:
    """_save_cached_result and _load_cached_result form a cache round-trip."""

    def test_save_then_load(self, tmp_path, monkeypatch):
        """A saved result can be loaded back for the same PDF."""
        # Point CACHE_DIR to tmp_path.
        monkeypatch.setattr("main.CACHE_DIR", tmp_path / ".cache")

        pdf = tmp_path / "report.pdf"
        pdf.write_bytes(b"PDF bytes here")
        result = {"status": "succeeded", "contents": [{"markdown": "hello"}]}

        _save_cached_result(pdf, result)
        loaded = _load_cached_result(pdf)

        assert loaded == result

    def test_cache_miss_returns_none(self, tmp_path, monkeypatch):
        """When no cache exists, returns None."""
        monkeypatch.setattr("main.CACHE_DIR", tmp_path / ".cache")

        pdf = tmp_path / "new_report.pdf"
        pdf.write_bytes(b"never cached")

        assert _load_cached_result(pdf) is None

    def test_different_pdf_misses(self, tmp_path, monkeypatch):
        """Cache for PDF-A does not match PDF-B."""
        monkeypatch.setattr("main.CACHE_DIR", tmp_path / ".cache")

        pdf_a = tmp_path / "a.pdf"
        pdf_b = tmp_path / "b.pdf"
        pdf_a.write_bytes(b"content A")
        pdf_b.write_bytes(b"content B")

        result = {"status": "succeeded"}
        _save_cached_result(pdf_a, result)

        assert _load_cached_result(pdf_b) is None
