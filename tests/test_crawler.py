"""Tests for the Crawler class."""
import pytest
from docs_crawler.crawler import Crawler


class TestCrawler:
    """Test cases for the Crawler class."""

    def test_crawler_initialization(self):
        """Test that Crawler can be initialized with parameters."""
        crawler = Crawler(
            base_url="https://example.com",
            output_dir="test_docs",
            custom_folder="test"
        )
        assert crawler.base_url == "https://example.com"
        assert crawler.output_dir == "test_docs"
        assert crawler.custom_folder == "test"

    def test_extract_subdomain(self):
        """Test subdomain extraction from URLs."""
        crawler = Crawler()

        # Test standard domain
        assert crawler.extract_subdomain("https://docs.example.com") == "example"

        # Test subdomain
        assert crawler.extract_subdomain("https://antigravity.google") == "antigravity"

        # Test localhost
        assert crawler.extract_subdomain("http://localhost:8000") == "localhost"

    def test_sitemap_url_auto_generation(self):
        """Test that sitemap URL is auto-generated from base URL."""
        crawler = Crawler(base_url="https://example.com")
        assert crawler.sitemap_url == "https://example.com/sitemap.xml"

    def test_custom_sitemap_url(self):
        """Test that custom sitemap URL overrides auto-generation."""
        crawler = Crawler(
            base_url="https://example.com",
            sitemap_url="https://example.com/custom-sitemap.xml"
        )
        assert crawler.sitemap_url == "https://example.com/custom-sitemap.xml"
