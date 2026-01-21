"""Tests for the Crawler class."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from bs4 import BeautifulSoup
from docs_crawler.crawler import Crawler
from urllib.parse import urlparse


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

        # Test single part domain
        assert crawler.extract_subdomain("http://localhost") == "localhost"

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

    def test_convert_to_markdown_basic(self):
        """Test basic HTML to Markdown conversion."""
        crawler = Crawler()

        html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Hello World</h1>
                <p>This is a test.</p>
            </body>
        </html>
        """

        markdown, title = crawler.convert_to_markdown(html)

        assert title == "Test Page"
        assert "# Hello World" in markdown
        assert "This is a test" in markdown

    def test_convert_to_markdown_removes_nav(self):
        """Test that navigation elements are removed."""
        crawler = Crawler()

        html = """
        <html>
            <body>
                <nav>Navigation menu</nav>
                <main>
                    <h1>Content</h1>
                    <p>Main content here</p>
                </main>
                <footer>Footer</footer>
            </body>
        </html>
        """

        markdown, title = crawler.convert_to_markdown(html)

        # Nav and footer should be removed
        assert "Navigation menu" not in markdown
        assert "Footer" not in markdown

        # Main content should remain
        assert "Content" in markdown
        assert "Main content here" in markdown

    def test_fetch_sitemap_empty(self):
        """Test sitemap fetching with no sitemap URL configured."""
        crawler = Crawler()  # No base_url, no sitemap_url
        urls = crawler.fetch_sitemap()
        assert urls == []

    @pytest.mark.skipif(
        True,
        reason="Requires lxml parser - skipped in basic tests"
    )
    @patch('docs_crawler.crawler.requests.Session')
    def test_fetch_sitemap_success(self, mock_session_class):
        """Test successful sitemap fetching."""
        # Mock the response
        mock_response = Mock()
        mock_response.content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url><loc>https://example.com/docs/page1</loc></url>
            <url><loc>https://example.com/docs/page2</loc></url>
            <url><loc>https://example.com/about</loc></url>
        </urlset>
        """
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        crawler = Crawler(base_url="https://example.com")
        crawler.session = mock_session

        urls = crawler.fetch_sitemap()

        # Should only return /docs/ URLs
        assert len(urls) == 2
        assert "https://example.com/docs/page1" in urls
        assert "https://example.com/docs/page2" in urls
        assert "https://example.com/about" not in urls

    def test_extract_links_from_page_mock(self):
        """Test link extraction from a mocked Playwright page."""
        crawler = Crawler()

        # Create mock page
        mock_page = Mock()

        # Mock link elements
        mock_link1 = Mock()
        mock_link1.get_attribute.return_value = "/docs/page1"

        mock_link2 = Mock()
        mock_link2.get_attribute.return_value = "/docs/page2"

        mock_link3 = Mock()
        mock_link3.get_attribute.return_value = "/about"

        mock_link4 = Mock()
        mock_link4.get_attribute.return_value = "https://external.com/page"

        mock_page.query_selector_all.return_value = [
            mock_link1, mock_link2, mock_link3, mock_link4
        ]

        current_url = "https://example.com/docs/intro"
        links = crawler.extract_links_from_page(mock_page, current_url, path_filter='/docs/')

        # Should only return same-domain /docs/ links
        assert len(links) == 2
        assert "https://example.com/docs/page1" in links
        assert "https://example.com/docs/page2" in links

    def test_extract_links_handles_fragments(self):
        """Test that URL fragments are removed."""
        crawler = Crawler()

        mock_page = Mock()
        mock_link = Mock()
        mock_link.get_attribute.return_value = "/docs/page1#section"
        mock_page.query_selector_all.return_value = [mock_link]

        links = crawler.extract_links_from_page(
            mock_page,
            "https://example.com/docs/intro",
            path_filter='/docs/'
        )

        # Fragment should be removed
        assert "https://example.com/docs/page1" in links
        assert "#section" not in list(links)[0]

    def test_extract_links_handles_query_params(self):
        """Test that query parameters are preserved."""
        crawler = Crawler()

        mock_page = Mock()
        mock_link = Mock()
        mock_link.get_attribute.return_value = "/docs/page1?version=2.0"
        mock_page.query_selector_all.return_value = [mock_link]

        links = crawler.extract_links_from_page(
            mock_page,
            "https://example.com/docs/intro",
            path_filter='/docs/'
        )

        # Query params should be preserved
        assert "https://example.com/docs/page1?version=2.0" in links

    def test_crawler_with_custom_content_selectors(self):
        """Test crawler accepts custom content selectors."""
        crawler = Crawler(
            base_url="https://example.com",
            content_selectors=[".custom-content", "#main-article"],
        )
        assert crawler.content_selectors == [".custom-content", "#main-article"]

    def test_crawler_with_custom_exclude_selectors(self):
        """Test crawler accepts custom exclude selectors."""
        crawler = Crawler(
            base_url="https://example.com",
            exclude_selectors=[".ads", ".comments"],
        )
        assert crawler.exclude_selectors == [".ads", ".comments"]

    def test_crawler_default_selectors_are_none(self):
        """Test crawler defaults to None for custom selectors."""
        crawler = Crawler(base_url="https://example.com")
        assert crawler.content_selectors is None
        assert crawler.exclude_selectors is None

    def test_convert_to_markdown_with_custom_content_selector(self):
        """Test custom content selector extracts specific content."""
        crawler = Crawler(
            base_url="https://example.com",
            content_selectors=[".my-content"],
        )
        html = """
        <html>
        <head><title>Test</title></head>
        <body>
            <div class="sidebar">Sidebar content</div>
            <div class="my-content">
                <h1>Main Content</h1>
                <p>This is the main content.</p>
            </div>
            <div class="other">Other content</div>
        </body>
        </html>
        """
        markdown, title = crawler.convert_to_markdown(html)
        assert "Main Content" in markdown
        assert "This is the main content" in markdown
        assert "Sidebar content" not in markdown
        assert "Other content" not in markdown

    def test_convert_to_markdown_with_custom_exclude_selector(self):
        """Test custom exclude selector removes specific elements."""
        crawler = Crawler(
            base_url="https://example.com",
            exclude_selectors=[".remove-me"],
        )
        html = """
        <html>
        <head><title>Test</title></head>
        <body>
            <article>
                <h1>Article</h1>
                <p>Keep this.</p>
                <div class="remove-me">Remove this.</div>
            </article>
        </body>
        </html>
        """
        markdown, title = crawler.convert_to_markdown(html)
        assert "Keep this" in markdown
        assert "Remove this" not in markdown


class TestCLI:
    """Test cases for CLI functionality."""

    def test_extract_subdomain_from_cli(self):
        """Test subdomain extraction in CLI module."""
        from docs_crawler.cli import extract_subdomain

        assert extract_subdomain("https://example.com") == "example"
        assert extract_subdomain("https://docs.github.com") == "github"
        assert extract_subdomain("http://localhost") == "localhost"
        # For .co.uk domains, it will extract 'co' - this is expected behavior


class TestPerformance:
    """Performance and edge case tests."""

    def test_large_html_conversion(self):
        """Test conversion of large HTML documents."""
        crawler = Crawler()

        # Generate large HTML
        large_html = "<html><body>"
        for i in range(1000):
            large_html += f"<p>Paragraph {i}</p>"
        large_html += "</body></html>"

        markdown, title = crawler.convert_to_markdown(large_html)

        # Should complete without errors
        assert markdown is not None
        assert "Paragraph 0" in markdown
        assert "Paragraph 999" in markdown

    def test_malformed_html_handling(self):
        """Test handling of malformed HTML."""
        crawler = Crawler()

        malformed_html = """
        <html>
            <body>
                <p>Unclosed paragraph
                <div>Unclosed div
                <h1>Missing closing tag
        """

        # Should not raise an exception
        markdown, title = crawler.convert_to_markdown(malformed_html)
        assert markdown is not None

    def test_empty_html(self):
        """Test handling of empty HTML."""
        crawler = Crawler()

        markdown, title = crawler.convert_to_markdown("")
        assert markdown == ""
        assert title == "No Title"
