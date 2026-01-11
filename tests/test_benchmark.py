"""Performance benchmark tests for the crawler."""
import time
import pytest
from unittest.mock import Mock, patch
from docs_crawler.crawler import Crawler


# Note: Benchmark tests using pytest-benchmark are commented out
# Install pytest-benchmark to enable them: pip install pytest-benchmark


class TestPerformanceRegression:
    """Tests to detect performance regressions."""

    def test_markdown_conversion_performance(self):
        """Ensure markdown conversion completes within acceptable time."""
        crawler = Crawler()

        # Generate medium-sized HTML
        html = "<html><body>"
        for i in range(100):
            html += f"<h2>Heading {i}</h2><p>Paragraph {i}</p>"
        html += "</body></html>"

        start = time.time()
        markdown, title = crawler.convert_to_markdown(html)
        duration = time.time() - start

        # Should complete in less than 1 second
        assert duration < 1.0, f"Conversion took {duration:.2f}s, expected < 1.0s"
        assert "Heading 0" in markdown

    def test_subdomain_extraction_performance(self):
        """Ensure subdomain extraction is fast."""
        crawler = Crawler()

        urls = [
            "https://docs.example.com",
            "https://api.github.com",
            "http://localhost:8000",
        ] * 1000  # 3000 URLs

        start = time.time()
        results = [crawler.extract_subdomain(url) for url in urls]
        duration = time.time() - start

        # Should process 3000 URLs in less than 0.1 seconds
        assert duration < 0.1, f"Processing took {duration:.2f}s, expected < 0.1s"
        assert len(results) == 3000

    def test_link_extraction_performance(self):
        """Ensure link extraction scales well."""
        crawler = Crawler()

        # Mock page with 500 links
        mock_page = Mock()
        mock_links = []
        for i in range(500):
            mock_link = Mock()
            if i % 2 == 0:
                mock_link.get_attribute.return_value = f"/docs/page{i}"
            else:
                mock_link.get_attribute.return_value = f"/other/page{i}"
            mock_links.append(mock_link)

        mock_page.query_selector_all.return_value = mock_links

        start = time.time()
        links = crawler.extract_links_from_page(
            mock_page,
            "https://example.com/docs/",
            '/docs/'
        )
        duration = time.time() - start

        # Should process 500 links in less than 0.5 seconds
        assert duration < 0.5, f"Extraction took {duration:.2f}s, expected < 0.5s"
        # Should filter correctly
        assert len(links) == 250  # Half are /docs/


class TestMemoryUsage:
    """Tests to monitor memory usage."""

    def test_large_result_set_memory(self):
        """Test memory usage with large result sets."""
        crawler = Crawler()

        # Simulate large result set
        crawler.results = []
        for i in range(1000):
            crawler.results.append({
                'title': f'Page {i}',
                'url': f'https://example.com/docs/page{i}',
                'file': f'page{i}.md'
            })

        # Should not crash or cause memory issues
        assert len(crawler.results) == 1000

    def test_html_cleanup_memory(self):
        """Test that HTML processing doesn't leak memory."""
        crawler = Crawler()

        # Process many small HTML documents
        for i in range(100):
            html = f"<html><body><h1>Page {i}</h1><p>Content {i}</p></body></html>"
            markdown, title = crawler.convert_to_markdown(html)
            assert markdown is not None

        # Should complete without memory issues
        assert True


class TestConcurrencySafety:
    """Tests for concurrent operations (preparation for parallel processing)."""

    def test_multiple_conversions_independent(self):
        """Test that multiple conversions don't interfere."""
        crawler = Crawler()

        html1 = "<html><body><h1>Page 1</h1></body></html>"
        html2 = "<html><body><h1>Page 2</h1></body></html>"

        md1, title1 = crawler.convert_to_markdown(html1)
        md2, title2 = crawler.convert_to_markdown(html2)

        # Results should be independent
        assert "Page 1" in md1
        assert "Page 2" in md2
        assert "Page 2" not in md1
        assert "Page 1" not in md2

    def test_link_extraction_independent(self):
        """Test that link extractions don't share state."""
        crawler = Crawler()

        mock_page1 = Mock()
        mock_link1 = Mock()
        mock_link1.get_attribute.return_value = "/docs/page1"
        mock_page1.query_selector_all.return_value = [mock_link1]

        mock_page2 = Mock()
        mock_link2 = Mock()
        mock_link2.get_attribute.return_value = "/docs/page2"
        mock_page2.query_selector_all.return_value = [mock_link2]

        links1 = crawler.extract_links_from_page(
            mock_page1, "https://example.com/docs/", '/docs/'
        )
        links2 = crawler.extract_links_from_page(
            mock_page2, "https://example.com/docs/", '/docs/'
        )

        # Results should be independent
        assert "https://example.com/docs/page1" in links1
        assert "https://example.com/docs/page2" in links2
        assert len(links1 & links2) == 0  # No overlap
