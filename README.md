# Docs Crawler

A powerful documentation crawler that converts web documentation to Markdown format using Playwright for JavaScript-rendered content.

## Features

- **High Performance**:
  - Async concurrent crawling (default 5x concurrency)
  - Smart wait strategy (DOMContentLoaded + Selectors) avoids slow network idle waits
  - Merged discovery and crawling phase for 2x efficiency in recursive mode
- **Smart & Incremental**:
  - Incremental updates (only crawls changed pages based on content hash)
  - Tries sitemap first, automatically falls back to recursive link discovery
- **Flexible Modes**:
  - **Sitemap Mode**: Crawl from sitemap.xml
  - **Discover Mode**: Find and save documentation URLs before crawling
  - **List Mode**: Crawl from a text file of URLs
- **Content Processing**:
  - Uses Playwright to handle JavaScript-rendered Single Page Applications (SPAs)
  - Converts HTML to clean Markdown format
  - Auto-detects domain-based folder structure
  - Generates an index of all crawled pages
- **Robustness**:
  - Progress tracking with tqdm
  - Retry logic for failed requests
  - Resume capability for interrupted crawls

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

The package provides a `docs-crawler` command with several modes and optimizations.

#### 1. Sitemap Mode (Default & Fastest)
Tries to fetch URLs from sitemap first. If sitemap is missing, it automatically switches to **concurrent recursive discovery**.

```bash
# Standard crawl (default 5 concurrent workers)
poetry run docs-crawler --base-url https://example.com

# Boost concurrency for high-performance (e.g., 10 workers)
poetry run docs-crawler --base-url https://example.com --concurrency 10

# Incremental update (skip unchanged pages)
poetry run docs-crawler --base-url https://example.com --incremental
```

#### 2. Discover Mode
Discover all documentation URLs and save them to a file for review before crawling.

```bash
# Discover links and save to auto-generated file (e.g., example_urls.txt)
poetry run docs-crawler --mode discover --base-url https://example.com
```

#### 3. List Mode
Crawl from a list of URLs in a text file.

```bash
# Crawl from URL list
poetry run docs-crawler --mode list --file urls.txt
```

#### Common Options

```bash
# Smart wait settings
--concurrency 5         # Number of parallel tabs (default: 5)
--incremental           # Skip pages with unchanged content
--force                 # Force re-crawl all pages

# Output settings
--output-dir output     # Default output directory
--folder my-docs        # Custom subfolder name

# Discovery settings
--path-filter /docs/    # Only follow links containing this path
--max-depth 100         # Maximum number of pages to discover
```

### Python API

```python
from docs_crawler import Crawler

# Create crawler instance
crawler = Crawler(
    base_url="https://fastapi.tiangolo.com",
    output_dir="output"
)

# Run with high performance settings
crawler.run(
    concurrency=10,      # Run 10 tabs in parallel
    incremental=True     # Skip unchanged pages
)
```

## Visualizations

### Terminal Output
The crawler provides real-time progress tracking with detailed statistics:

```text
2026-02-08 14:53:53 - INFO - Starting concurrent download of 50 pages (concurrency=5)...
Crawling: 100%|██████████| 50/50 [00:15<00:00,  3.20page/s]
2026-02-08 14:54:08 - INFO - ==================================================
2026-02-08 14:54:08 - INFO - Crawl Summary:
2026-02-08 14:54:08 - INFO -   Total URLs: 50
2026-02-08 14:54:08 - INFO -   Successful: 48
2026-02-08 14:54:08 - INFO -   Skipped (unchanged): 2
2026-02-08 14:54:08 - INFO -   Failed: 0
2026-02-08 14:54:08 - INFO -   Success Rate: 96.0%
2026-02-08 14:54:08 - INFO - ==================================================
```

### Output Structure
Files are organized automatically by domain, with a generated index:

```text
output/
├── example/
│   ├── index.md          # Table of contents with links
│   ├── intro.md          # Converted documentation pages
│   ├── getting-started.md
│   ├── api-reference.md
│   └── advanced.md
└── failed_urls.txt       # Report of any failed downloads
```

### Generated Index
The `index.md` file provides easy navigation:

| Title | Original URL | Local File |
|-------|--------------|------------|
| Introduction | [https://example.com/docs](...) | [intro.md](intro.md) |
| API Reference | [https://example.com/docs/api](...) | [api_reference.md](api_reference.md) |

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

## How It Works

### Link Discovery

The crawler uses a smart two-step approach:

1. **Sitemap First**: Attempts to fetch URLs from the sitemap.xml file
2. **Recursive Discovery Fallback**: If sitemap is unavailable or empty, automatically discovers links by:
   - Starting from a base URL (e.g., `/docs/`)
   - Extracting all internal links matching the path filter
   - Recursively crawling pages to find more documentation links
   - Respecting the max-depth limit to avoid excessive crawling

### Workflow Example

```bash
# Step 1: Discover links and save for review
poetry run docs-crawler --mode discover --base-url https://example.com
# Output: example_urls.txt

# Step 2: Review and edit urls.txt if needed
# (Remove unwanted URLs, add missing ones, etc.)

# Step 3: Crawl the URLs
poetry run docs-crawler --mode list --file example_urls.txt
```

## Notes

- The crawler uses Playwright to handle JavaScript-rendered content, making it suitable for modern SPAs.
- Default path filter is `/docs/` but can be customized with `--path-filter`
- Respects retry limits and timeouts to be polite to servers.
- Auto-detects domain-based folder structure or uses custom folder names.
- Recursive discovery avoids infinite loops by tracking visited URLs
- URL files are named using the subdomain for easy identification (e.g., `github_urls.txt`, `example_urls.txt`)

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
