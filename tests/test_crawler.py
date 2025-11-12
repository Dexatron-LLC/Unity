"""Unit tests for crawler."""

import unittest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import tempfile
import shutil

from src.crawler.unity_crawler import UnityCrawler
from src.storage import VectorStore, StructuredStore
from src.scraper import UnityDocsScraper


class TestUnityCrawler(unittest.IsolatedAsyncioTestCase):
    """Test cases for UnityCrawler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create mock stores
        self.mock_vector_store = Mock(spec=VectorStore)
        self.mock_structured_store = Mock(spec=StructuredStore)
        self.mock_scraper = Mock(spec=UnityDocsScraper)
        
        self.crawler = UnityCrawler(
            self.mock_vector_store,
            self.mock_structured_store,
            self.mock_scraper
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    async def test_process_and_store_page_script_reference(self):
        """Test processing and storing a script reference page."""
        page_data = {
            "url": "https://docs.unity3d.com/ScriptReference/GameObject.html",
            "title": "GameObject",
            "content": "GameObject is the base class for all entities.",
            "html": """
                <html>
                    <body>
                        <h1>GameObject</h1>
                        <div class="description">Base class</div>
                        <h2>Public Methods</h2>
                        <table>
                            <tr><td>SetActive</td><td>Activates GameObject</td></tr>
                        </table>
                    </body>
                </html>
            """,
            "doc_type": "script_reference"
        }
        
        # Mock structured store methods
        self.mock_structured_store.add_page = Mock()
        self.mock_structured_store.add_class = Mock(return_value=1)
        self.mock_structured_store.add_method = Mock()
        self.mock_structured_store.add_property = Mock()
        
        # Mock vector store
        self.mock_vector_store.add_document = Mock()
        
        await self.crawler._process_and_store_page(page_data)
        
        # Verify structured store calls
        self.mock_structured_store.add_page.assert_called_once()
        self.mock_structured_store.add_class.assert_called_once()
        
        # Verify vector store calls
        self.assertTrue(self.mock_vector_store.add_document.called)
    
    async def test_process_and_store_page_manual(self):
        """Test processing and storing a manual page."""
        page_data = {
            "url": "https://docs.unity3d.com/Manual/GameObjects.html",
            "title": "GameObjects",
            "content": "GameObjects are the fundamental objects in Unity.",
            "html": """
                <html>
                    <body>
                        <div class="content">
                            <h2>Introduction</h2>
                            <p>GameObjects are fundamental.</p>
                        </div>
                    </body>
                </html>
            """,
            "doc_type": "manual"
        }
        
        self.mock_structured_store.add_page = Mock()
        self.mock_vector_store.add_document = Mock()
        
        await self.crawler._process_and_store_page(page_data)
        
        # Verify structured store calls
        self.mock_structured_store.add_page.assert_called_once()
        
        # Verify vector store calls
        self.assertTrue(self.mock_vector_store.add_document.called)
    
    async def test_index_single_page(self):
        """Test indexing a single page."""
        test_url = "https://docs.unity3d.com/ScriptReference/GameObject.html"
        
        mock_page_data = {
            "url": test_url,
            "title": "GameObject",
            "content": "Test content",
            "html": "<html><body>Test</body></html>",
            "doc_type": "script_reference"
        }
        
        self.mock_scraper.fetch_page = AsyncMock(return_value=mock_page_data)
        self.mock_structured_store.add_page = Mock()
        self.mock_vector_store.add_document = Mock()
        
        await self.crawler.index_single_page(test_url)
        
        self.mock_scraper.fetch_page.assert_called_once_with(test_url)
        self.mock_structured_store.add_page.assert_called_once()
    
    async def test_crawl_and_index(self):
        """Test crawling and indexing multiple pages."""
        mock_urls = [
            "https://docs.unity3d.com/Manual/page1.html",
            "https://docs.unity3d.com/Manual/page2.html"
        ]
        
        self.mock_scraper.crawl_all_pages = AsyncMock(return_value=mock_urls)
        self.mock_scraper.fetch_page = AsyncMock(return_value={
            "url": "test",
            "title": "Test",
            "content": "Content",
            "html": "<html></html>",
            "doc_type": "manual"
        })
        
        self.mock_structured_store.add_page = Mock()
        self.mock_structured_store.get_stats = Mock(return_value={
            "pages_count": 2,
            "classes_count": 0
        })
        self.mock_vector_store.add_document = Mock()
        self.mock_vector_store.get_stats = Mock(return_value={
            "manual_count": 2,
            "script_reference_count": 0,
            "total_count": 2
        })
        
        await self.crawler.crawl_and_index("manual", max_pages=2)
        
        self.mock_scraper.crawl_all_pages.assert_called_once_with("manual", 2)
        self.assertEqual(self.mock_scraper.fetch_page.call_count, 2)


if __name__ == "__main__":
    unittest.main()
