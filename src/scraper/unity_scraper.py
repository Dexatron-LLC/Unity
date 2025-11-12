"""Web scraping tools for Unity documentation."""

import logging
import asyncio
import hashlib
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class UnityDocsScraper:
    """Scrapes Unity documentation using Playwright."""
    
    MANUAL_BASE = "https://docs.unity3d.com/Manual/"
    SCRIPT_REF_BASE = "https://docs.unity3d.com/ScriptReference/"
    
    def __init__(self):
        """Initialize the scraper."""
        self.browser: Optional[Browser] = None
        self.playwright = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start(self) -> None:
        """Start the browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        logger.info("Browser started")
    
    async def close(self) -> None:
        """Close the browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed")
    
    @staticmethod
    def get_page_id(url: str) -> str:
        """Generate a unique ID for a page URL.
        
        Args:
            url: Page URL
            
        Returns:
            MD5 hash of the URL
        """
        return hashlib.md5(url.encode()).hexdigest()
    
    @staticmethod
    def get_doc_type(url: str) -> str:
        """Determine document type from URL.
        
        Args:
            url: Page URL
            
        Returns:
            'manual' or 'script_reference'
        """
        if "/Manual/" in url:
            return "manual"
        elif "/ScriptReference/" in url:
            return "script_reference"
        return "unknown"
    
    async def search_unity_docs(
        self,
        query: str,
        doc_type: str = "both",
        max_results: int = 10
    ) -> List[Dict[str, str]]:
        """Search Unity documentation using the search function.
        
        Args:
            query: Search query
            doc_type: 'manual', 'script_reference', or 'both'
            max_results: Maximum number of results
            
        Returns:
            List of search results with title and URL
        """
        if not self.browser:
            raise RuntimeError("Browser not started. Call start() first.")
        
        results = []
        search_targets = []
        
        if doc_type in ("manual", "both"):
            search_targets.append(("manual", self.MANUAL_BASE))
        if doc_type in ("script_reference", "both"):
            search_targets.append(("script_reference", self.SCRIPT_REF_BASE))
        
        for target_type, base_url in search_targets:
            try:
                page = await self.browser.new_page()
                await page.goto(f"{base_url}index.html", wait_until="networkidle")
                
                # Find and click search box
                search_selector = 'input[type="search"], input[placeholder*="Search"], .search-input'
                await page.wait_for_selector(search_selector, timeout=5000)
                await page.fill(search_selector, query)
                
                # Wait for search results
                await page.wait_for_timeout(1000)  # Give time for results to appear
                
                # Extract search results
                results_html = await page.content()
                soup = BeautifulSoup(results_html, "lxml")
                
                # Find result links (adapt selectors based on Unity docs structure)
                result_links = soup.find_all("a", class_=["search-result", "result-item"])
                if not result_links:
                    # Fallback: find all links in search results area
                    search_results_div = soup.find("div", class_=["search-results", "results"])
                    if search_results_div:
                        result_links = search_results_div.find_all("a", href=True)
                
                for link in result_links[:max_results]:
                    title = link.get_text(strip=True)
                    href = link.get("href", "")
                    
                    if href and title:
                        full_url = urljoin(base_url, href)
                        results.append({
                            "title": title,
                            "url": full_url,
                            "doc_type": target_type
                        })
                
                await page.close()
                
            except Exception as e:
                logger.error(f"Error searching {target_type}: {e}")
        
        return results[:max_results]
    
    async def fetch_page(self, url: str) -> Dict[str, Any]:
        """Fetch a Unity documentation page.
        
        Args:
            url: Page URL
            
        Returns:
            Dictionary with page content and metadata
        """
        if not self.browser:
            raise RuntimeError("Browser not started. Call start() first.")
        
        try:
            page = await self.browser.new_page()
            await page.goto(url, wait_until="networkidle")
            
            # Get page content
            content_html = await page.content()
            soup = BeautifulSoup(content_html, "lxml")
            
            # Extract title
            title = soup.find("h1")
            title_text = title.get_text(strip=True) if title else soup.title.string
            
            # Extract main content
            content_div = soup.find("div", class_=["content", "main-content", "documentation"])
            if not content_div:
                content_div = soup.find("main")
            
            if content_div:
                # Remove script and style elements
                for script in content_div(["script", "style"]):
                    script.decompose()
                
                content_text = content_div.get_text(separator="\n", strip=True)
            else:
                content_text = soup.get_text(separator="\n", strip=True)
            
            await page.close()
            
            return {
                "url": url,
                "title": title_text,
                "content": content_text,
                "html": content_html,
                "doc_type": self.get_doc_type(url)
            }
            
        except Exception as e:
            logger.error(f"Error fetching page {url}: {e}")
            raise
    
    async def crawl_all_pages(
        self,
        doc_type: str = "both",
        max_pages: Optional[int] = None
    ) -> List[str]:
        """Crawl all documentation pages.
        
        Args:
            doc_type: 'manual', 'script_reference', or 'both'
            max_pages: Maximum number of pages to crawl (None for unlimited)
            
        Returns:
            List of page URLs discovered
        """
        if not self.browser:
            raise RuntimeError("Browser not started. Call start() first.")
        
        urls_to_crawl: Set[str] = set()
        crawled_urls: Set[str] = set()
        discovered_urls: List[str] = []
        
        # Start URLs
        if doc_type in ("manual", "both"):
            urls_to_crawl.add(f"{self.MANUAL_BASE}index.html")
        if doc_type in ("script_reference", "both"):
            urls_to_crawl.add(f"{self.SCRIPT_REF_BASE}index.html")
        
        page = await self.browser.new_page()
        
        try:
            while urls_to_crawl and (max_pages is None or len(crawled_urls) < max_pages):
                url = urls_to_crawl.pop()
                
                if url in crawled_urls:
                    continue
                
                try:
                    logger.info(f"Crawling: {url}")
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    
                    # Get all links
                    links = await page.query_selector_all("a[href]")
                    
                    for link in links:
                        href = await link.get_attribute("href")
                        if not href:
                            continue
                        
                        # Make absolute URL
                        absolute_url = urljoin(url, href)
                        
                        # Filter Unity docs URLs only
                        if self._is_unity_docs_url(absolute_url, doc_type):
                            if absolute_url not in crawled_urls:
                                urls_to_crawl.add(absolute_url)
                                if absolute_url not in discovered_urls:
                                    discovered_urls.append(absolute_url)
                    
                    crawled_urls.add(url)
                    
                    # Rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error crawling {url}: {e}")
                    crawled_urls.add(url)  # Mark as crawled to avoid retry
        
        finally:
            await page.close()
        
        logger.info(f"Crawling complete. Discovered {len(discovered_urls)} pages.")
        return discovered_urls
    
    def _is_unity_docs_url(self, url: str, doc_type: str) -> bool:
        """Check if URL is a valid Unity documentation URL.
        
        Args:
            url: URL to check
            doc_type: 'manual', 'script_reference', or 'both'
            
        Returns:
            True if URL is valid Unity docs URL
        """
        parsed = urlparse(url)
        
        # Must be Unity docs domain
        if "docs.unity3d.com" not in parsed.netloc:
            return False
        
        # Check document type
        if doc_type == "manual":
            return "/Manual/" in url
        elif doc_type == "script_reference":
            return "/ScriptReference/" in url
        else:  # both
            return "/Manual/" in url or "/ScriptReference/" in url
