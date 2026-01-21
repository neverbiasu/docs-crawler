"""Cache module for incremental crawling support."""

import os
import json
import hashlib
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

CACHE_VERSION = 1
CACHE_FILENAME = ".docs-crawler-cache.json"
PROGRESS_FILENAME = ".docs-crawler-progress.json"


class CrawlCache:
    """
    Manages cache for incremental crawling.

    Stores metadata about crawled pages to detect changes:
    - URL
    - Content hash (MD5)
    - Last crawl timestamp
    - ETag and Last-Modified headers (if available)
    """

    def __init__(self, cache_dir):
        """
        Initialize the cache.

        Args:
            cache_dir: Directory to store the cache file
        """
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, CACHE_FILENAME)
        self.data = self._load_cache()

    def _load_cache(self):
        """Load cache from disk."""
        if not os.path.exists(self.cache_file):
            return {"version": CACHE_VERSION, "pages": {}}

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check version compatibility
            if data.get("version") != CACHE_VERSION:
                logger.warning("Cache version mismatch, creating new cache")
                return {"version": CACHE_VERSION, "pages": {}}

            return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load cache: {e}")
            return {"version": CACHE_VERSION, "pages": {}}

    def save(self):
        """Save cache to disk."""
        os.makedirs(self.cache_dir, exist_ok=True)
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Cache saved to {self.cache_file}")
        except IOError as e:
            logger.error(f"Failed to save cache: {e}")

    @staticmethod
    def compute_hash(content):
        """Compute MD5 hash of content."""
        if isinstance(content, str):
            content = content.encode("utf-8")
        return hashlib.md5(content).hexdigest()

    def get_page_info(self, url):
        """
        Get cached info for a URL.

        Args:
            url: The URL to look up

        Returns:
            dict or None: Cached page info or None if not cached
        """
        return self.data["pages"].get(url)

    def update_page(self, url, content_hash, etag=None, last_modified=None):
        """
        Update cache entry for a URL.

        Args:
            url: The URL
            content_hash: MD5 hash of the markdown content
            etag: ETag header value (optional)
            last_modified: Last-Modified header value (optional)
        """
        self.data["pages"][url] = {
            "content_hash": content_hash,
            "last_crawled": datetime.now().isoformat(),
            "etag": etag,
            "last_modified": last_modified,
        }

    def is_changed(self, url, new_content_hash):
        """
        Check if a page has changed since last crawl.

        Args:
            url: The URL to check
            new_content_hash: Hash of the new content

        Returns:
            bool: True if changed or not in cache, False if unchanged
        """
        cached = self.get_page_info(url)
        if not cached:
            return True
        return cached.get("content_hash") != new_content_hash

    def remove_page(self, url):
        """Remove a URL from cache."""
        if url in self.data["pages"]:
            del self.data["pages"][url]

    def get_cached_urls(self):
        """Get all cached URLs."""
        return set(self.data["pages"].keys())

    def get_stats(self):
        """Get cache statistics."""
        return {
            "total_pages": len(self.data["pages"]),
            "cache_file": self.cache_file,
        }

    def clear(self):
        """Clear all cache data."""
        self.data = {"version": CACHE_VERSION, "pages": {}}
        logger.info("Cache cleared")


class CrawlProgress:
    """
    Manages crawl progress for resume functionality.

    Stores:
    - All URLs to crawl
    - Completed URLs
    - Failed URLs
    - Crawl start time
    """

    def __init__(self, progress_dir):
        """
        Initialize progress tracker.

        Args:
            progress_dir: Directory to store the progress file
        """
        self.progress_dir = progress_dir
        self.progress_file = os.path.join(progress_dir, PROGRESS_FILENAME)
        self.data = None

    def exists(self):
        """Check if a progress file exists."""
        return os.path.exists(self.progress_file)

    def load(self):
        """Load progress from disk."""
        if not self.exists():
            return None

        try:
            with open(self.progress_file, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            logger.info(
                f"Loaded progress: {len(self.data.get('completed', []))} completed, "
                f"{len(self.data.get('pending', []))} pending"
            )
            return self.data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load progress: {e}")
            return None

    def start(self, urls):
        """
        Start a new crawl session.

        Args:
            urls: List of URLs to crawl
        """
        self.data = {
            "started_at": datetime.now().isoformat(),
            "total": len(urls),
            "pending": list(urls),
            "completed": [],
            "failed": [],
        }
        self.save()
        logger.info(f"Started new crawl session with {len(urls)} URLs")

    def save(self):
        """Save progress to disk."""
        if self.data is None:
            return

        os.makedirs(self.progress_dir, exist_ok=True)
        try:
            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Failed to save progress: {e}")

    def mark_completed(self, url):
        """Mark a URL as completed."""
        if self.data is None:
            return

        if url in self.data["pending"]:
            self.data["pending"].remove(url)
        if url not in self.data["completed"]:
            self.data["completed"].append(url)

    def mark_failed(self, url, error=None):
        """Mark a URL as failed."""
        if self.data is None:
            return

        if url in self.data["pending"]:
            self.data["pending"].remove(url)
        if url not in self.data["failed"]:
            self.data["failed"].append({"url": url, "error": str(error) if error else None})

    def get_pending_urls(self):
        """Get list of pending URLs."""
        if self.data is None:
            return []
        return self.data.get("pending", [])

    def get_stats(self):
        """Get progress statistics."""
        if self.data is None:
            return None

        return {
            "total": self.data.get("total", 0),
            "completed": len(self.data.get("completed", [])),
            "failed": len(self.data.get("failed", [])),
            "pending": len(self.data.get("pending", [])),
            "started_at": self.data.get("started_at"),
        }

    def is_complete(self):
        """Check if all URLs have been processed."""
        if self.data is None:
            return True
        return len(self.data.get("pending", [])) == 0

    def clear(self):
        """Clear progress file."""
        if self.exists():
            try:
                os.remove(self.progress_file)
                logger.info("Progress file cleared")
            except IOError as e:
                logger.error(f"Failed to clear progress file: {e}")
        self.data = None
