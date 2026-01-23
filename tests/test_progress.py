"""Tests for CrawlProgress class."""

import os
import json
import tempfile
import pytest
from docs_crawler.cache import CrawlProgress


class TestCrawlProgress:
    """Test cases for CrawlProgress functionality."""

    def test_progress_initialization(self):
        """Test progress initializes with correct attributes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            progress = CrawlProgress(tmpdir)
            assert progress.progress_dir == tmpdir
            assert progress.data is None

    def test_progress_start(self):
        """Test starting a new crawl session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            progress = CrawlProgress(tmpdir)
            urls = ["http://example.com/1", "http://example.com/2"]
            progress.start(urls)

            assert progress.data is not None
            assert progress.data["total"] == 2
            assert progress.data["pending"] == urls
            assert progress.data["completed"] == []
            assert progress.data["failed"] == []
            assert "started_at" in progress.data

    def test_progress_save_and_load(self):
        """Test saving and loading progress."""
        with tempfile.TemporaryDirectory() as tmpdir:
            progress = CrawlProgress(tmpdir)
            urls = ["http://example.com/1", "http://example.com/2"]
            progress.start(urls)
            progress.save()

            # Load in new instance
            progress2 = CrawlProgress(tmpdir)
            assert progress2.exists()
            loaded = progress2.load()

            assert loaded is not None
            assert loaded["total"] == 2
            assert loaded["pending"] == urls

    def test_progress_mark_completed(self):
        """Test marking URL as completed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            progress = CrawlProgress(tmpdir)
            urls = ["http://example.com/1", "http://example.com/2"]
            progress.start(urls)

            progress.mark_completed("http://example.com/1")

            assert "http://example.com/1" not in progress.data["pending"]
            assert "http://example.com/1" in progress.data["completed"]

    def test_progress_mark_failed(self):
        """Test marking URL as failed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            progress = CrawlProgress(tmpdir)
            urls = ["http://example.com/1", "http://example.com/2"]
            progress.start(urls)

            progress.mark_failed("http://example.com/1", "timeout error")

            assert "http://example.com/1" not in progress.data["pending"]
            assert len(progress.data["failed"]) == 1
            assert progress.data["failed"][0]["url"] == "http://example.com/1"
            assert progress.data["failed"][0]["error"] == "timeout error"

    def test_progress_get_pending_urls(self):
        """Test getting pending URLs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            progress = CrawlProgress(tmpdir)
            urls = ["http://example.com/1", "http://example.com/2"]
            progress.start(urls)
            progress.mark_completed("http://example.com/1")

            pending = progress.get_pending_urls()
            assert pending == ["http://example.com/2"]

    def test_progress_get_stats(self):
        """Test getting progress statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            progress = CrawlProgress(tmpdir)
            urls = ["http://example.com/1", "http://example.com/2", "http://example.com/3"]
            progress.start(urls)
            progress.mark_completed("http://example.com/1")
            progress.mark_failed("http://example.com/2", "error")

            stats = progress.get_stats()
            assert stats["total"] == 3
            assert stats["completed"] == 1
            assert stats["failed"] == 1
            assert stats["pending"] == 1

    def test_progress_is_complete(self):
        """Test checking if crawl is complete."""
        with tempfile.TemporaryDirectory() as tmpdir:
            progress = CrawlProgress(tmpdir)
            urls = ["http://example.com/1"]
            progress.start(urls)

            assert not progress.is_complete()

            progress.mark_completed("http://example.com/1")
            assert progress.is_complete()

    def test_progress_clear(self):
        """Test clearing progress file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            progress = CrawlProgress(tmpdir)
            urls = ["http://example.com/1"]
            progress.start(urls)
            progress.save()

            assert progress.exists()
            progress.clear()
            assert not progress.exists()

    def test_progress_exists_false_when_no_file(self):
        """Test exists returns False when no progress file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            progress = CrawlProgress(tmpdir)
            assert not progress.exists()

    def test_progress_load_returns_none_when_no_file(self):
        """Test load returns None when no progress file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            progress = CrawlProgress(tmpdir)
            assert progress.load() is None

    def test_progress_load_handles_corrupted_file(self):
        """Test load handles corrupted JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            progress = CrawlProgress(tmpdir)
            # Write corrupted JSON
            with open(progress.progress_file, "w") as f:
                f.write("not valid json {{{")

            result = progress.load()
            assert result is None
