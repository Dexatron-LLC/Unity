"""Unit tests for web scraper."""

import unittest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import asyncio

from src.scraper.unity_scraper import UnityDocsScraper


class TestUnityDocsScraper(unittest.TestCase):
    """Test cases for UnityDocsScraper."""
    
    def test_get_page_id(self):
        """Test generating page ID from URL."""
        url1 = "https://docs.unity3d.com/Manual/GameObject.html"
        url2 = "https://docs.unity3d.com/ScriptReference/GameObject.html"
        
        id1 = UnityDocsScraper.get_page_id(url1)
        id2 = UnityDocsScraper.get_page_id(url2)
        
        self.assertIsNotNone(id1)
        self.assertIsNotNone(id2)
        self.assertNotEqual(id1, id2)
        self.assertEqual(len(id1), 32)  # MD5 hash length
    
    def test_get_doc_type(self):
        """Test determining document type from URL."""
        manual_url = "https://docs.unity3d.com/Manual/GameObject.html"
        script_url = "https://docs.unity3d.com/ScriptReference/GameObject.html"
        other_url = "https://example.com/page.html"
        
        self.assertEqual(UnityDocsScraper.get_doc_type(manual_url), "manual")
        self.assertEqual(UnityDocsScraper.get_doc_type(script_url), "script_reference")
        self.assertEqual(UnityDocsScraper.get_doc_type(other_url), "unknown")
    
    def test_is_unity_docs_url_manual(self):
        """Test URL validation for Manual docs."""
        scraper = UnityDocsScraper()
        
        valid = "https://docs.unity3d.com/Manual/page.html"
        invalid = "https://example.com/Manual/page.html"
        script = "https://docs.unity3d.com/ScriptReference/page.html"
        
        self.assertTrue(scraper._is_unity_docs_url(valid, "manual"))
        self.assertFalse(scraper._is_unity_docs_url(invalid, "manual"))
        self.assertFalse(scraper._is_unity_docs_url(script, "manual"))
    
    def test_is_unity_docs_url_script_reference(self):
        """Test URL validation for ScriptReference docs."""
        scraper = UnityDocsScraper()
        
        valid = "https://docs.unity3d.com/ScriptReference/page.html"
        manual = "https://docs.unity3d.com/Manual/page.html"
        
        self.assertTrue(scraper._is_unity_docs_url(valid, "script_reference"))
        self.assertFalse(scraper._is_unity_docs_url(manual, "script_reference"))
    
    def test_is_unity_docs_url_both(self):
        """Test URL validation for both doc types."""
        scraper = UnityDocsScraper()
        
        manual = "https://docs.unity3d.com/Manual/page.html"
        script = "https://docs.unity3d.com/ScriptReference/page.html"
        invalid = "https://example.com/page.html"
        
        self.assertTrue(scraper._is_unity_docs_url(manual, "both"))
        self.assertTrue(scraper._is_unity_docs_url(script, "both"))
        self.assertFalse(scraper._is_unity_docs_url(invalid, "both"))
    
    @patch('src.scraper.unity_scraper.async_playwright')
    async def test_start_and_close(self, mock_playwright):
        """Test starting and closing the browser."""
        mock_pw_instance = AsyncMock()
        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_browser = AsyncMock()
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        
        scraper = UnityDocsScraper()
        await scraper.start()
        
        self.assertIsNotNone(scraper.browser)
        self.assertIsNotNone(scraper.playwright)
        
        await scraper.close()
        mock_browser.close.assert_called_once()
    
    @patch('src.scraper.unity_scraper.async_playwright')
    async def test_fetch_page(self, mock_playwright):
        """Test fetching a page."""
        # Setup mocks
        mock_pw_instance = AsyncMock()
        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_browser = AsyncMock()
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        
        mock_page = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_page.goto = AsyncMock()
        mock_page.content = AsyncMock(return_value="""
            <html>
                <head><title>GameObject</title></head>
                <body>
                    <h1>GameObject Class</h1>
                    <div class="content">
                        <p>Base class for all entities in Unity scenes.</p>
                    </div>
                </body>
            </html>
        """)
        mock_page.close = AsyncMock()
        
        scraper = UnityDocsScraper()
        await scraper.start()
        
        url = "https://docs.unity3d.com/ScriptReference/GameObject.html"
        result = await scraper.fetch_page(url)
        
        self.assertEqual(result["url"], url)
        self.assertEqual(result["title"], "GameObject Class")
        self.assertIn("Base class", result["content"])
        self.assertEqual(result["doc_type"], "script_reference")
        
        await scraper.close()
    
    @patch('src.scraper.unity_scraper.async_playwright')
    async def test_context_manager(self, mock_playwright):
        """Test async context manager usage."""
        mock_pw_instance = AsyncMock()
        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_browser = AsyncMock()
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        
        async with UnityDocsScraper() as scraper:
            self.assertIsNotNone(scraper.browser)
        
        mock_browser.close.assert_called_once()


class TestScraperAsync(unittest.IsolatedAsyncioTestCase):
    """Async test cases for UnityDocsScraper."""
    
    @patch('src.scraper.unity_scraper.async_playwright')
    async def test_fetch_page_async(self, mock_playwright):
        """Test async page fetching."""
        mock_pw_instance = AsyncMock()
        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_browser = AsyncMock()
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        
        mock_page = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_page.goto = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html><h1>Test</h1></html>")
        mock_page.close = AsyncMock()
        
        async with UnityDocsScraper() as scraper:
            result = await scraper.fetch_page("https://docs.unity3d.com/Manual/test.html")
            self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
