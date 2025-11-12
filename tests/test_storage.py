"""Unit tests for storage modules."""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.storage.vector_store import VectorStore
from src.storage.structured_store import StructuredStore


class TestStructuredStore(unittest.TestCase):
    """Test cases for StructuredStore."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.store = StructuredStore(self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.store.close()
        shutil.rmtree(self.test_dir)
    
    def test_add_and_get_page(self):
        """Test adding and retrieving a page."""
        self.store.add_page(
            page_id="test123",
            url="https://test.com/page",
            title="Test Page",
            doc_type="manual",
            content="Test content"
        )
        
        page = self.store.get_page("test123")
        
        self.assertIsNotNone(page)
        self.assertEqual(page["title"], "Test Page")
        self.assertEqual(page["url"], "https://test.com/page")
        self.assertEqual(page["doc_type"], "manual")
        self.assertEqual(page["content"], "Test content")
    
    def test_get_nonexistent_page(self):
        """Test getting a page that doesn't exist."""
        page = self.store.get_page("nonexistent")
        self.assertIsNone(page)
    
    def test_get_page_by_url(self):
        """Test retrieving page by URL."""
        self.store.add_page(
            page_id="test456",
            url="https://test.com/unique",
            title="Unique Page",
            doc_type="script_reference",
            content="Content"
        )
        
        page = self.store.get_page_by_url("https://test.com/unique")
        
        self.assertIsNotNone(page)
        self.assertEqual(page["title"], "Unique Page")
    
    def test_add_class(self):
        """Test adding a Unity class."""
        # First add a page
        self.store.add_page(
            page_id="page1",
            url="https://test.com",
            title="GameObject",
            doc_type="script_reference",
            content="Test"
        )
        
        class_id = self.store.add_class(
            name="GameObject",
            namespace="UnityEngine",
            page_id="page1",
            description="Base class for all entities",
            inherits_from="Object",
            is_static=False
        )
        
        self.assertIsNotNone(class_id)
        self.assertGreater(class_id, 0)
    
    def test_get_class(self):
        """Test retrieving a class with methods and properties."""
        # Add page
        self.store.add_page("page1", "https://test.com", "Transform", "script_reference", "Test")
        
        # Add class
        class_id = self.store.add_class(
            name="Transform",
            namespace="UnityEngine",
            page_id="page1",
            description="Position, rotation and scale"
        )
        
        # Add method
        self.store.add_method(
            class_id=class_id,
            name="Translate",
            return_type="void",
            description="Moves the transform"
        )
        
        # Add property
        self.store.add_property(
            class_id=class_id,
            name="position",
            property_type="Vector3",
            description="World position"
        )
        
        # Retrieve class
        cls = self.store.get_class("Transform")
        
        self.assertIsNotNone(cls)
        self.assertEqual(cls["name"], "Transform")
        self.assertEqual(cls["namespace"], "UnityEngine")
        self.assertEqual(len(cls["methods"]), 1)
        self.assertEqual(len(cls["properties"]), 1)
        self.assertEqual(cls["methods"][0]["name"], "Translate")
        self.assertEqual(cls["properties"][0]["name"], "position")
    
    def test_search_classes(self):
        """Test searching for classes."""
        self.store.add_page("p1", "url1", "GameObject", "script_reference", "")
        self.store.add_page("p2", "url2", "Transform", "script_reference", "")
        
        self.store.add_class("GameObject", "UnityEngine", "p1", "Game object class")
        self.store.add_class("Transform", "UnityEngine", "p2", "Transform component")
        
        results = self.store.search_classes("Game")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "GameObject")
    
    def test_search_methods(self):
        """Test searching for methods."""
        self.store.add_page("p1", "url1", "GameObject", "script_reference", "")
        class_id = self.store.add_class("GameObject", "UnityEngine", "p1")
        
        self.store.add_method(
            class_id=class_id,
            name="SetActive",
            return_type="void",
            description="Activates/deactivates the GameObject"
        )
        
        results = self.store.search_methods("Active")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "SetActive")
        self.assertEqual(results[0]["class_name"], "GameObject")
    
    def test_get_stats(self):
        """Test getting database statistics."""
        stats = self.store.get_stats()
        
        self.assertIn("pages_count", stats)
        self.assertIn("classes_count", stats)
        self.assertIn("methods_count", stats)
        self.assertIn("properties_count", stats)
        self.assertEqual(stats["pages_count"], 0)


class TestVectorStore(unittest.TestCase):
    """Test cases for VectorStore."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.mock_api_key = "test-api-key"
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    @patch('src.storage.vector_store.OpenAI')
    @patch('src.storage.vector_store.chromadb.PersistentClient')
    def test_initialization(self, mock_chroma, mock_openai):
        """Test VectorStore initialization."""
        mock_client = MagicMock()
        mock_chroma.return_value = mock_client
        mock_client.get_or_create_collection.return_value = MagicMock()
        
        store = VectorStore(self.test_dir, self.mock_api_key)
        
        self.assertIsNotNone(store)
        mock_chroma.assert_called_once()
        self.assertEqual(mock_client.get_or_create_collection.call_count, 2)
    
    @patch('src.storage.vector_store.OpenAI')
    @patch('src.storage.vector_store.chromadb.PersistentClient')
    def test_add_document(self, mock_chroma, mock_openai):
        """Test adding a document to vector store."""
        # Setup mocks
        mock_client = MagicMock()
        mock_chroma.return_value = mock_client
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        mock_openai_instance.embeddings.create.return_value = mock_response
        
        store = VectorStore(self.test_dir, self.mock_api_key)
        
        # Add document
        store.add_document(
            doc_id="test123",
            url="https://test.com",
            title="Test Document",
            content="This is test content about Unity",
            doc_type="manual"
        )
        
        # Verify embedding was created
        mock_openai_instance.embeddings.create.assert_called_once()
        
        # Verify document was added to collection
        mock_collection.add.assert_called_once()
    
    @patch('src.storage.vector_store.OpenAI')
    @patch('src.storage.vector_store.chromadb.PersistentClient')
    def test_search(self, mock_chroma, mock_openai):
        """Test searching in vector store."""
        # Setup mocks
        mock_client = MagicMock()
        mock_chroma.return_value = mock_client
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        mock_openai_instance.embeddings.create.return_value = mock_response
        
        # Mock search results
        mock_collection.query.return_value = {
            "ids": [["doc1"]],
            "documents": [["Test content"]],
            "metadatas": [[{"title": "Test", "url": "https://test.com"}]],
            "distances": [[0.5]]
        }
        
        store = VectorStore(self.test_dir, self.mock_api_key)
        
        # Search
        results = store.search("GameObject", doc_type="manual", n_results=5)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "doc1")
        self.assertEqual(results[0]["content"], "Test content")
    
    @patch('src.storage.vector_store.OpenAI')
    @patch('src.storage.vector_store.chromadb.PersistentClient')
    def test_get_stats(self, mock_chroma, mock_openai):
        """Test getting vector store statistics."""
        mock_client = MagicMock()
        mock_chroma.return_value = mock_client
        mock_manual_collection = MagicMock()
        mock_script_collection = MagicMock()
        
        mock_manual_collection.count.return_value = 10
        mock_script_collection.count.return_value = 20
        
        mock_client.get_or_create_collection.side_effect = [
            mock_manual_collection,
            mock_script_collection
        ]
        
        store = VectorStore(self.test_dir, self.mock_api_key)
        stats = store.get_stats()
        
        self.assertEqual(stats["manual_count"], 10)
        self.assertEqual(stats["script_reference_count"], 20)
        self.assertEqual(stats["total_count"], 30)


if __name__ == "__main__":
    unittest.main()
