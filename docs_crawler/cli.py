import os
import sys
import argparse
import logging
from docs_crawler.crawler import Crawler

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point for docs-crawler."""
    parser = argparse.ArgumentParser(
        description="Crawl and convert documentation to Markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Crawl from sitemap
  docs-crawler --base-url https://example.com

  # Crawl from a list of URLs in a file
  docs-crawler --mode list --file urls.txt

  # Specify custom output folder
  docs-crawler --base-url https://example.com --folder my-docs
        """
    )

    parser.add_argument(
        '--mode',
        choices=['sitemap', 'list'],
        default='sitemap',
        help="Source of URLs: 'sitemap' (default) or 'list' (text file)."
    )

    parser.add_argument(
        '--base-url',
        help="Base URL of the documentation site (e.g., https://example.com)"
    )

    parser.add_argument(
        '--sitemap-url',
        help="URL of the sitemap (overrides auto-detected sitemap URL)"
    )

    parser.add_argument(
        '--file',
        help="Path to the text file containing URLs (required if mode is 'list')."
    )

    parser.add_argument(
        '--folder',
        help="Custom folder name under output directory (overrides auto-detection from domain)."
    )

    parser.add_argument(
        '--output-dir',
        default='output',
        help="Output directory for markdown files (default: output)"
    )

    args = parser.parse_args()

    # Validate arguments
    urls = None
    if args.mode == 'sitemap':
        if not args.base_url and not args.sitemap_url:
            parser.error("--base-url or --sitemap-url is required when mode is 'sitemap'")
    elif args.mode == 'list':
        if not args.file:
            parser.error("--file is required when mode is 'list'")

        if not os.path.exists(args.file):
            logger.error(f"File not found: {args.file}")
            sys.exit(1)

        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(urls)} URLs from {args.file}")
        except Exception as e:
            logger.error(f"Failed to read file {args.file}: {e}")
            sys.exit(1)

    # Create and run crawler
    crawler = Crawler(
        base_url=args.base_url,
        sitemap_url=args.sitemap_url,
        output_dir=args.output_dir,
        custom_folder=args.folder
    )

    try:
        crawler.run(urls)
    except KeyboardInterrupt:
        logger.info("\nCrawling interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error during crawling: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
