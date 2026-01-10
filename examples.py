"""Example usage of the docs-crawler package."""
from docs_crawler import Crawler

# Example 1: Crawl from sitemap
def example_sitemap_crawl():
    """Example of crawling from a sitemap."""
    crawler = Crawler(
        base_url="https://antigravity.google",
        output_dir="docs",
        custom_folder="antigravity"
    )
    crawler.run()


# Example 2: Crawl from a list of URLs
def example_list_crawl():
    """Example of crawling from a custom list of URLs."""
    urls = [
        "https://antigravity.google/docs/introduction",
        "https://antigravity.google/docs/getting-started",
        "https://antigravity.google/docs/api-reference",
    ]

    crawler = Crawler(
        base_url="https://antigravity.google",
        output_dir="docs",
        custom_folder="antigravity"
    )
    crawler.run(urls)


# Example 3: Crawl with custom sitemap URL
def example_custom_sitemap():
    """Example of crawling with a custom sitemap URL."""
    crawler = Crawler(
        base_url="https://example.com",
        sitemap_url="https://example.com/docs/sitemap.xml",
        output_dir="output",
        custom_folder="example-docs"
    )
    crawler.run()


if __name__ == "__main__":
    # Uncomment the example you want to run
    # example_sitemap_crawl()
    # example_list_crawl()
    # example_custom_sitemap()
    pass
