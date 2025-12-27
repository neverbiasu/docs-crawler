# Google Antigravity Docs Crawler

This script crawls the documentation pages from [Google Antigravity](https://antigravity.google) and converts them to Markdown.

## Requirements

- Python 3.x
- Dependencies: `requests`, `markdownify`, `beautifulsoup4`, `tqdm`, `lxml`

## Installation

```bash
pip install requests markdownify beautifulsoup4 tqdm lxml
```

## Usage

Run the crawler with a single command:

```bash
python3 crawl_and_convert.py
```

## Output

- The downloaded Markdown files will be saved in the `docs/` directory.
- An index of all downloaded pages is available at `docs/index.md`.

## Notes

- The script adheres to `robots.txt` (User-Agent is allowed).
- It uses 5 concurrent threads with a 0.5s interval per thread to be polite.
- It filters for pages under `/docs/` from the sitemap.
- **Note:** The target website is a Single Page Application (SPA) utilizing Angular. The content is rendered client-side. As per the requirements, this script uses `requests` and `BeautifulSoup`, which fetch the server-side HTML. If the server does not perform Server-Side Rendering (SSR), the downloaded files may contain minimal content. This is a limitation of using static scraping tools on an SPA.
