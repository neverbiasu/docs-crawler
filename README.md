# Docs Crawler

A powerful documentation crawler that converts web documentation to Markdown format using Playwright for JavaScript-rendered content.

## Features

- Crawls documentation from sitemaps or URL lists
- Uses Playwright to handle JavaScript-rendered Single Page Applications (SPAs)
- Converts HTML to clean Markdown format
- Auto-detects domain-based folder structure
- Generates an index of all crawled pages
- Progress tracking with tqdm
- Retry logic for failed requests

## Requirements

- Python 3.8+
- Poetry (for dependency management)

## Installation

### Using Poetry (Recommended)

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Clone the repository
git clone https://github.com/neverbiasu/docs-crawler.git
cd docs-crawler

# Install dependencies
poetry install

# Install Playwright browsers
poetry run playwright install chromium
```

### Using pip

```bash
pip install docs-crawler
playwright install chromium
```

## Usage

### Command Line Interface

The package provides a `docs-crawler` command:

```bash
# Crawl from sitemap
poetry run docs-crawler --base-url https://antigravity.google

# Crawl from a list of URLs
poetry run docs-crawler --mode list --file urls.txt

# Specify custom output folder
poetry run docs-crawler --base-url https://example.com --folder my-docs

# Specify custom sitemap URL
poetry run docs-crawler --sitemap-url https://example.com/custom-sitemap.xml
```

### Python API

```python
from docs_crawler import Crawler

# Create crawler instance
crawler = Crawler(
    base_url="https://antigravity.google",
    output_dir="output",
    custom_folder="antigravity"
)

# Run from sitemap
crawler.run()

# Or run with custom URLs
urls = [
    "https://example.com/docs/page1",
    "https://example.com/docs/page2"
]
crawler.run(urls)
```

## Output

- The downloaded Markdown files will be saved in the `output/` directory (or custom directory).
- An index of all downloaded pages is available at `output/{folder}/index.md`.
- Files are organized by domain or custom folder name.

## Development

```bash
# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Format code
poetry run black .

# Lint code
poetry run flake8

# Type checking
poetry run mypy docs_crawler
```

## Configuration

The crawler can be configured through:
- Command-line arguments
- Python API parameters
- Environment variables (coming soon)

## Notes

- The crawler uses Playwright to handle JavaScript-rendered content, making it suitable for modern SPAs.
- It filters for pages under `/docs/` from the sitemap by default.
- Respects retry limits and timeouts to be polite to servers.
- Auto-detects domain-based folder structure or uses custom folder names.

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
