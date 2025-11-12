"""Quick test script for Unity MCP Server components."""

import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

from src.storage import VectorStore, StructuredStore
from src.scraper import UnityDocsScraper

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_scraper():
    """Test the Unity docs scraper."""
    logger.info("Testing Unity scraper...")
    
    async with UnityDocsScraper() as scraper:
        # Test fetching a page
        test_url = "https://docs.unity3d.com/ScriptReference/GameObject.html"
        logger.info(f"Fetching: {test_url}")
        
        page_data = await scraper.fetch_page(test_url)
        
        logger.info(f"Title: {page_data['title']}")
        logger.info(f"Content length: {len(page_data['content'])} characters")
        logger.info(f"Doc type: {page_data['doc_type']}")
        logger.info("✓ Scraper test passed")


def test_storage():
    """Test the storage components."""
    logger.info("Testing storage...")
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY not set")
        return
    
    data_dir = "./test_data"
    Path(data_dir).mkdir(exist_ok=True)
    
    # Test structured store
    structured_store = StructuredStore(data_dir)
    structured_store.add_page(
        page_id="test123",
        url="https://test.com",
        title="Test Page",
        doc_type="manual",
        content="Test content"
    )
    
    page = structured_store.get_page("test123")
    assert page is not None
    assert page["title"] == "Test Page"
    logger.info("✓ Structured store test passed")
    
    # Test vector store
    vector_store = VectorStore(data_dir, openai_api_key)
    vector_store.add_document(
        doc_id="test456",
        url="https://test.com",
        title="Test Doc",
        content="This is a test document about Unity GameObjects",
        doc_type="manual"
    )
    
    results = vector_store.search("GameObject", doc_type="manual", n_results=1)
    assert len(results) > 0
    logger.info("✓ Vector store test passed")
    
    # Cleanup
    import shutil
    shutil.rmtree(data_dir)
    logger.info("✓ All storage tests passed")


async def test_end_to_end():
    """Test end-to-end functionality."""
    logger.info("Testing end-to-end functionality...")
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY not set")
        return
    
    data_dir = "./test_data"
    Path(data_dir).mkdir(exist_ok=True)
    
    # Initialize components
    vector_store = VectorStore(data_dir, openai_api_key)
    structured_store = StructuredStore(data_dir)
    
    # Fetch and process a single page
    async with UnityDocsScraper() as scraper:
        from src.crawler import UnityCrawler
        
        crawler = UnityCrawler(vector_store, structured_store, scraper)
        
        # Index a single page
        test_url = "https://docs.unity3d.com/ScriptReference/GameObject.html"
        await crawler.index_single_page(test_url)
        
        logger.info("✓ Page indexed successfully")
    
    # Search for the indexed content
    results = vector_store.search("GameObject", n_results=1)
    assert len(results) > 0
    logger.info(f"✓ Found {len(results)} results in vector store")
    
    # Check structured data
    stats = structured_store.get_stats()
    logger.info(f"✓ Structured store stats: {stats}")
    
    # Cleanup
    import shutil
    shutil.rmtree(data_dir)
    logger.info("✓ End-to-end test passed")


async def main():
    """Run all tests."""
    logger.info("=== Unity MCP Server Tests ===\n")
    
    try:
        await test_scraper()
        print()
        
        test_storage()
        print()
        
        await test_end_to_end()
        print()
        
        logger.info("=== All tests passed! ===")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
