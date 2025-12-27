import os
import time
import requests
import threading
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from queue import Queue
from tqdm import tqdm
import logging
from concurrent.futures import ThreadPoolExecutor

# Configuration
BASE_URL = "https://antigravity.google"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"
OUTPUT_DIR = "docs"
CONCURRENCY = 5
REQUEST_INTERVAL = 0.5
MAX_RETRIES = 3

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

class Crawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; Bot/1.0; +http://example.com)'
        })
        self.results = []
        self.lock = threading.Lock()

    def fetch_sitemap(self):
        """Fetches and parses the sitemap to extract /docs/ URLs."""
        try:
            logger.info(f"Fetching sitemap from {SITEMAP_URL}")
            response = self.session.get(SITEMAP_URL)
            response.raise_for_status()
            
            # XML parsing (using lxml if available, else html.parser)
            # sitemap files are often just text/xml
            soup = BeautifulSoup(response.content, 'xml')
            urls = [loc.text for loc in soup.find_all('loc')]
            
            # Filter for /docs/
            doc_urls = [url for url in urls if '/docs/' in urlparse(url).path]
            logger.info(f"Found {len(doc_urls)} pages under /docs/")
            return doc_urls
        except Exception as e:
            logger.error(f"Failed to fetch sitemap: {e}")
            return []

    def process_url(self, url):
        """Downloads and converts a single URL."""
        slug = urlparse(url).path.strip('/').replace('/', '_')
        if not slug:
            slug = "index"
        filename = f"{slug}.md"
        filepath = os.path.join(OUTPUT_DIR, filename)

        content = None
        title = None
        
        for attempt in range(MAX_RETRIES):
            try:
                # Rate limiting (per thread)
                time.sleep(REQUEST_INTERVAL)
                
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                content = response.content
                break
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == MAX_RETRIES - 1:
                    logger.error(f"Failed to download {url} after {MAX_RETRIES} attempts")
                    return
        
        if content:
            try:
                markdown_content, page_title = self.convert_to_markdown(content)
                title = page_title
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                with self.lock:
                    self.results.append({'title': title, 'url': url, 'file': filename})
            except Exception as e:
                logger.error(f"Error converting {url}: {e}")

    def convert_to_markdown(self, html_content):
        """Extracts content and converts to Markdown."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.text.strip() if title_tag else "No Title"

        # Remove unwanted elements
        # 'nav', 'footer', 'sidebar', 'toc', 'breadcrumbs'
        # We need to be a bit aggressive or use heuristics for classes if tags aren't standard
        for tag in soup.find_all(['nav', 'footer', 'script', 'style', 'noscript', 'iframe']):
            tag.decompose()
            
        # Common classes/IDs for unwanted elements
        unwanted_selectors = [
            '.sidebar', '#sidebar', 
            '.toc', '#toc', 
            '.breadcrumbs', '.breadcrumb', 
            '.footer', '.header', '.nav'
        ]
        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()

        # Prioritize content extraction
        content_element = soup.find('main')
        if not content_element:
            content_element = soup.find('article')
        if not content_element:
            content_element = soup.find('body')
            
        if not content_element:
            return "", title

        # Convert to Markdown
        # markdownify can take a soup object or string.
        # We pass the string representation of the filtered element.
        markdown = md(str(content_element), heading_style="ATX", strip=['a', 'img']) 
        # Requirement says "Only extract body text...". 
        # "Target: extract main/article/body" usually implies keeping formatting like headers, lists, etc.
        # But "Only extract body text" might mean stripping images/links? 
        # Usually "Convert to Markdown" implies keeping structure. 
        # "remove nav, footer..." implies the rest is valuable.
        # I will keep standard markdown formatting.
        
        return markdown.strip(), title

    def generate_index(self):
        """Generates the index.md file."""
        index_path = os.path.join(OUTPUT_DIR, "index.md")
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("# Documentation Index\n\n")
            f.write("| Title | Original URL | Local File |\n")
            f.write("|-------|--------------|------------|\n")
            for item in sorted(self.results, key=lambda x: x['title']):
                f.write(f"| {item['title']} | [{item['url']}]({item['url']}) | [{item['file']}]({item['file']}) |\n")
        logger.info(f"Generated index at {index_path}")

    def run(self):
        urls = self.fetch_sitemap()
        if not urls:
            logger.warning("No URLs found to process.")
            return

        logger.info(f"Starting download of {len(urls)} pages with {CONCURRENCY} threads...")
        
        with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
            # Using tqdm for progress bar
            list(tqdm(executor.map(self.process_url, urls), total=len(urls), unit="page"))
            
        self.generate_index()
        logger.info("Done.")

if __name__ == "__main__":
    crawler = Crawler()
    crawler.run()
