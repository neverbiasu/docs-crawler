# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-01-19

### Added

#### Incremental Crawling
- **Content Hash Cache**: Store MD5 hash of crawled content to detect changes
- **Skip Unchanged Pages**: Only re-crawl pages with changed content
- **Cache File**: `.docs-crawler-cache.json` stores page metadata in output directory
- **New CLI Options**:
  - `--incremental` - Enable incremental mode, skip unchanged pages
  - `--force` - Force re-crawl all pages, ignoring cache
- **Summary Statistics**: Show skipped page count in crawl summary

### Changed
- Crawl summary now shows "Skipped (unchanged)" count

---

## [0.2.1] - 2026-01-16

### Added

#### Error Handling
- **Failure Reports**: Generate `failed_urls.txt` with failed URLs and error messages
- **Crawl Summary**: Display success/fail counts and success rate after crawl
- **Structured Error Info**: Return detailed error information for failed pages

#### Configuration File Support
- **YAML Config**: Support for `docs-crawler.yaml` configuration files
- **Auto-detect Config**: Automatically find config file in current directory
- **New CLI Options**:
  - `--config` - Specify path to YAML config file
  - `--init-config` - Generate example config file
- **CLI Override**: Command line arguments override config file values

### Dependencies
- Added `pyyaml` for YAML config parsing

---

## [0.2.0] - 2026-01-15

### Added

#### Concurrent Crawling
- **Async/Await Support**: Implemented concurrent page processing using `asyncio` and `playwright.async_api`
- **5x Performance Improvement**: Reduced crawl time from ~48s to ~9s for 20 pages
- **New CLI Option**: `--concurrency` parameter to control number of concurrent pages (default: 5)
- **Backward Compatible**: Use `--concurrency 1` for sequential mode

#### CLI Enhancements
- `--concurrency` - Number of concurrent pages to process (default: 5)

### Changed
- Default crawling mode is now concurrent (5 workers)
- Improved code formatting with Black
- Better error handling with specific exception types

### Technical Details

#### Performance
- Sequential mode: ~2.4s per page
- Concurrent mode (5 workers): ~2.2 pages per second
- 5x speedup achieved with default settings

---

## [0.1.0] - 2026-01-11

### Added

#### Core Features
- **Smart Link Discovery**: Automatically discovers documentation URLs with sitemap-first strategy and recursive fallback
- **Discover Mode**: Preview and confirm URLs before crawling with `--mode discover`
- **Three Crawling Modes**:
  - `sitemap` - Crawl from sitemap with automatic fallback to recursive discovery
  - `discover` - Find and save URLs to file for review
  - `list` - Crawl from URL list file
- **Intelligent Fallback**: Automatically switches from sitemap to recursive link discovery if sitemap is unavailable
- **Subdomain-based Naming**: Auto-generates URL files like `example_urls.txt` based on domain

#### CLI Enhancements
- `--mode discover` - New discover mode
- `--start-url` - Starting URL for recursive discovery
- `--path-filter` - Customizable path pattern filter (default: `/docs/`)
- `--max-depth` - Maximum number of URLs to discover (default: 100)
- `--output-file` - Custom output filename for discovered URLs
- `--output-dir` - Custom output directory (default: `output`)

#### Developer Experience
- Comprehensive test suite with 95.5% pass rate (21/22 tests)
- Performance regression tests for conversion, extraction, and memory
- Concurrency safety tests
- Detailed performance analysis documentation
- Test summary with benchmarks

#### Documentation
- `PERFORMANCE_ANALYSIS.md` - Detailed performance analysis and optimization roadmap
- `TEST_SUMMARY.md` - Complete test coverage report
- `WORK_SUMMARY.md` - Development work summary
- Enhanced README with usage examples for all three modes
- Installation guide for both Poetry and pip

### Changed
- Default output directory changed from `docs/` to `output/`
- Restructured project from single script to proper Python package
- CLI help messages improved with more examples
- README completely rewritten with comprehensive usage guide

### Fixed
- Improved HTML to Markdown conversion with better element filtering
- Better handling of navigation and footer elements removal
- More robust URL normalization (fragment removal, query param preservation)

### Technical Details

#### Performance Baseline
- Markdown conversion: < 1s for 100 paragraphs
- Subdomain extraction: < 0.1s for 3,000 URLs
- Link extraction: < 0.5s for 500 links

#### Known Limitations
- Serial page processing (optimization planned for v0.2.0)
- Recursive discovery limited by max-depth to prevent infinite loops
- Performance: ~2-3 seconds per page (10-20x improvement possible with planned optimizations)

#### Dependencies
- Python 3.8+
- Playwright for JavaScript-rendered content
- BeautifulSoup4 for HTML parsing
- Markdownify for Markdown conversion
- LXML for sitemap parsing
- Requests for HTTP operations
- tqdm for progress tracking

### Testing
- 21 unit tests passing
- 3 performance regression tests
- 4 memory and concurrency safety tests
- Test execution time: < 0.3 seconds

---

## [Unreleased]

### Planned for v0.4.0
- Progress save/resume functionality
- Content filtering with custom CSS selectors

---

[0.3.0]: https://github.com/neverbiasu/docs-crawler/releases/tag/v0.3.0
[0.2.1]: https://github.com/neverbiasu/docs-crawler/releases/tag/v0.2.1
[0.2.0]: https://github.com/neverbiasu/docs-crawler/releases/tag/v0.2.0
[0.1.0]: https://github.com/neverbiasu/docs-crawler/releases/tag/v0.1.0
