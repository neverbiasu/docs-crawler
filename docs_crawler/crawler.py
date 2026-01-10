import os
import logging
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from playwright.sync_api import sync_playwright
from tqdm import tqdm
import requests

# Configuration
MAX_RETRIES = 3
PAGE_LOAD_TIMEOUT = 30000  # 30秒超时

# Setup logging
logger = logging.getLogger(__name__)


class Crawler:
    def __init__(self, base_url=None, sitemap_url=None, output_dir="output", custom_folder=None):
        """
        Initialize the crawler.

        Args:
            base_url: Base URL of the documentation site
            sitemap_url: URL of the sitemap
            output_dir: Output directory for markdown files
            custom_folder: Custom folder name under output_dir
        """
        self.base_url = base_url
        self.sitemap_url = sitemap_url or (f"{base_url}/sitemap.xml" if base_url else None)
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; Bot/1.0; +http://example.com)'
        })
        self.results = []
        self.subdomain = None
        self.custom_folder = custom_folder

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

    def extract_subdomain(self, url):
        """从URL中提取二级域名（主域名）作为文件夹名。"""
        parsed = urlparse(url)
        hostname = parsed.hostname
        if hostname:
            parts = hostname.split('.')

            # 提取二级域名（主域名）的逻辑：
            # code.claude.com -> parts[-2] = 'claude'
            # antigravity.google -> parts[-2] = 'antigravity'
            # example.com -> parts[-2] = 'example'
            # localhost -> parts[-1] = 'localhost'

            if len(parts) >= 2:
                # 取倒数第二个部分作为二级域名
                return parts[-2]
            elif len(parts) == 1:
                # 只有一个部分，如 localhost
                return parts[0]

        return 'default'

    def fetch_sitemap(self):
        """Fetches and parses the sitemap to extract /docs/ URLs."""
        if not self.sitemap_url:
            logger.error("No sitemap URL configured")
            return []

        try:
            logger.info(f"Fetching sitemap from {self.sitemap_url}")
            response = self.session.get(self.sitemap_url)
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

    def process_url_with_playwright(self, page, url):
        """Downloads and converts a single URL using Playwright."""
        # 如果还没有设置subdomain，从当前URL提取或使用custom_folder
        if self.subdomain is None:
            if self.custom_folder:
                self.subdomain = self.custom_folder
                logger.info(f"Using custom folder: {self.subdomain}")
            else:
                self.subdomain = self.extract_subdomain(url)
                logger.info(f"Using auto-detected folder (domain): {self.subdomain}")
            # 创建子文件夹
            self.output_subdir = os.path.join(self.output_dir, self.subdomain)
            os.makedirs(self.output_subdir, exist_ok=True)

        slug = urlparse(url).path.strip('/').replace('/', '_')
        if not slug:
            slug = "index"
        filename = f"{slug}.md"
        filepath = os.path.join(self.output_subdir, filename)

        content = None
        title = None

        for attempt in range(MAX_RETRIES):
            try:
                # 导航到页面
                page.goto(url, timeout=PAGE_LOAD_TIMEOUT)

                # 等待主内容加载完成
                # 尝试等待文章内容或主区域
                try:
                    page.wait_for_selector('article, main, [role="main"]', timeout=10000)
                except:
                    pass

                # 额外等待确保JS完全渲染
                page.wait_for_load_state('networkidle', timeout=15000)

                # 获取渲染后的HTML
                content = page.content()
                break
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == MAX_RETRIES - 1:
                    logger.error(f"Failed to download {url} after {MAX_RETRIES} attempts")
                    return None

        if content:
            try:
                markdown_content, page_title = self.convert_to_markdown(content)
                title = page_title

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)

                return {'title': title, 'url': url, 'file': filename}
            except Exception as e:
                logger.error(f"Error converting {url}: {e}")

        return None

    def convert_to_markdown(self, html_content):
        """Extracts content and converts to Markdown."""
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract title
        title_tag = soup.find('title')
        title = title_tag.text.strip() if title_tag else "No Title"

        # Remove unwanted elements
        for tag in soup.find_all(['nav', 'footer', 'script', 'style', 'noscript', 'iframe', 'header']):
            tag.decompose()

        # Common classes/IDs for unwanted elements
        unwanted_selectors = [
            '.sidebar', '#sidebar',
            '.toc', '#toc',
            '.breadcrumbs', '.breadcrumb',
            '.footer', '.header', '.nav',
            '[role="navigation"]',
            '.navigation',
            '.menu'
        ]
        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()

        # Prioritize content extraction - 尝试更具体的选择器
        content_element = None

        # 尝试找到文档内容区域
        content_selectors = [
            'article',
            '[role="main"]',
            '.docs-content',
            '.content',
            '.markdown-body',
            'main',
            '.main-content'
        ]

        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element and len(content_element.get_text(strip=True)) > 100:
                break

        if not content_element:
            content_element = soup.find('body')

        if not content_element:
            return "", title

        # Convert to Markdown
        markdown = md(str(content_element), heading_style="ATX", strip=['img'])

        # 清理多余的空行
        lines = markdown.split('\n')
        cleaned_lines = []
        prev_empty = False
        for line in lines:
            is_empty = not line.strip()
            if is_empty and prev_empty:
                continue
            cleaned_lines.append(line)
            prev_empty = is_empty

        return '\n'.join(cleaned_lines).strip(), title

    def generate_index(self):
        """Generates the index.md file."""
        index_path = os.path.join(self.output_subdir, "index.md")
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("# Documentation Index\n\n")
            f.write("| Title | Original URL | Local File |\n")
            f.write("|-------|--------------|------------|\n")
            for item in sorted(self.results, key=lambda x: x['title']):
                f.write(f"| {item['title']} | [{item['url']}]({item['url']}) | [{item['file']}]({item['file']}) |\n")
        logger.info(f"Generated index at {index_path}")

    def run(self, urls=None):
        """
        Run the crawler.

        Args:
            urls: List of URLs to crawl. If None, fetches from sitemap.
        """
        if urls is None:
            urls = self.fetch_sitemap()

        if not urls:
            logger.warning("No URLs found to process.")
            return

        logger.info(f"Starting download of {len(urls)} pages using Playwright...")

        with sync_playwright() as p:
            # 启动浏览器
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()

            # 使用 tqdm 显示进度
            for url in tqdm(urls, unit="page"):
                result = self.process_url_with_playwright(page, url)
                if result:
                    self.results.append(result)

            browser.close()

        self.generate_index()
        logger.info("Done.")
