"""Integration tests for Unity MCP Server."""

import unittest
import tempfile
import shutil
import os
from unittest.mock import patch, AsyncMock, MagicMock

from src.storage import VectorStore, StructuredStore
from src.scraper import UnityDocsScraper
from src.crawler import UnityCrawler
from src.processor import ContentProcessor


class TestIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for the entire pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.mock_api_key = "test-api-key"
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_structured_store_full_workflow(self):
        """Test full workflow with structured store."""
        store = StructuredStore(self.test_dir)
        
        # Add page
        store.add_page(
            page_id="go1",
            url="https://docs.unity3d.com/ScriptReference/GameObject.html",
            title="GameObject",
            doc_type="script_reference",
            content="Base class for all entities"
        )
        
        # Add class
        class_id = store.add_class(
            name="GameObject",
            namespace="UnityEngine",
            page_id="go1",
            description="Base class for all entities in Unity",
            inherits_from="Object"
        )
        
        # Add methods
        method_id = store.add_method(
            class_id=class_id,
            name="SetActive",
            return_type="void",
            description="Activates/Deactivates the GameObject"
        )
        
        # Add properties
        prop_id = store.add_property(
            class_id=class_id,
            name="transform",
            property_type="Transform",
            description="The Transform attached to this GameObject"
        )
        
        # Retrieve and verify
        cls = store.get_class("GameObject")
        self.assertIsNotNone(cls)
        self.assertEqual(cls["name"], "GameObject")
        self.assertEqual(len(cls["methods"]), 1)
        self.assertEqual(len(cls["properties"]), 1)
        
        # Search
        classes = store.search_classes("Game")
        self.assertEqual(len(classes), 1)
        
        methods = store.search_methods("Active")
        self.assertEqual(len(methods), 1)
        
        store.close()
    
    @patch('src.storage.vector_store.OpenAI')
    @patch('src.storage.vector_store.chromadb.PersistentClient')
    def test_vector_store_workflow(self, mock_chroma, mock_openai):
        """Test vector store workflow."""
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
        
        # Create store
        store = VectorStore(self.test_dir, self.mock_api_key)
        
        # Add document
        store.add_document(
            doc_id="test1",
            url="https://test.com",
            title="GameObject",
            content="GameObject is the base class for all entities in Unity scenes",
            doc_type="script_reference"
        )
        
        # Verify embedding was created
        mock_openai_instance.embeddings.create.assert_called()
        mock_collection.add.assert_called()
    
    def test_content_processor_pipeline(self):
        """Test content processor with real HTML."""
        html = """
        <html>
            <body>
                <h1>UnityEngine.GameObject</h1>
                <div class="description">
                    Base class for all entities in Unity scenes.
                </div>
                <p>Inherits from: <a href="#">Object</a></p>
                <h2>Public Methods</h2>
                <table>
                    <tr><th>Method</th><th>Description</th></tr>
                    <tr>
                        <td>SetActive</td>
                        <td>Activates/Deactivates the GameObject.</td>
                    </tr>
                    <tr>
                        <td>GetComponent</td>
                        <td>Gets the component of Type type.</td>
                    </tr>
                </table>
                <h2>Public Properties</h2>
                <table>
                    <tr><th>Property</th><th>Description</th></tr>
                    <tr>
                        <td>transform</td>
                        <td>The Transform attached to this GameObject.</td>
                    </tr>
                </table>
            </body>
        </html>
        """
        
        result = ContentProcessor.extract_script_reference_data(
            html,
            "https://docs.unity3d.com/ScriptReference/GameObject.html",
            "UnityEngine.GameObject"
        )
        
        # Verify extracted data
        self.assertEqual(result["class_name"], "GameObject")
        self.assertEqual(result["namespace"], "UnityEngine")
        self.assertEqual(result["inherits_from"], "Object")
        self.assertIn("Base class", result["description"])
        self.assertEqual(len(result["methods"]), 2)
        self.assertEqual(len(result["properties"]), 1)
        
        # Verify methods
        method_names = [m["name"] for m in result["methods"]]
        self.assertIn("SetActive", method_names)
        self.assertIn("GetComponent", method_names)
        
        # Verify properties
        self.assertEqual(result["properties"][0]["name"], "transform")
    
    def test_chunking_large_content(self):
        """Test content chunking for large documents."""
        # Create large content
        large_content = " ".join(["Unity"] * 1000)  # ~6000 characters
        metadata = {"title": "Large Doc", "url": "https://test.com"}
        
        chunks = ContentProcessor.prepare_for_vector_store(
            large_content,
            metadata,
            chunk_size=1000
        )
        
        self.assertGreater(len(chunks), 1)
        
        # Verify all chunks
        total_length = 0
        for i, (chunk_text, chunk_meta) in enumerate(chunks):
            self.assertEqual(chunk_meta["chunk_index"], i)
            self.assertLessEqual(len(chunk_text), 1200)
            total_length += len(chunk_text.split())
        
        # Verify we didn't lose content
        self.assertGreater(total_length, 900)  # Should have most words


class TestEndToEndScenarios(unittest.TestCase):
    """End-to-end scenario tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_page_id_consistency(self):
        """Test that page IDs are consistent."""
        url = "https://docs.unity3d.com/ScriptReference/GameObject.html"
        
        id1 = UnityDocsScraper.get_page_id(url)
        id2 = UnityDocsScraper.get_page_id(url)
        
        self.assertEqual(id1, id2)
    
    def test_doc_type_detection(self):
        """Test document type detection."""
        manual_url = "https://docs.unity3d.com/Manual/GameObjects.html"
        script_url = "https://docs.unity3d.com/ScriptReference/GameObject.html"
        
        self.assertEqual(UnityDocsScraper.get_doc_type(manual_url), "manual")
        self.assertEqual(UnityDocsScraper.get_doc_type(script_url), "script_reference")
    
    def test_database_stats(self):
        """Test database statistics collection."""
        store = StructuredStore(self.test_dir)
        
        # Add some data
        store.add_page("p1", "url1", "Page 1", "manual", "content")
        store.add_page("p2", "url2", "Page 2", "script_reference", "content")
        
        class_id = store.add_class("TestClass", "Test", "p2")
        store.add_method(class_id, "TestMethod")
        store.add_property(class_id, "testProp")
        
        # Get stats
        stats = store.get_stats()
        
        self.assertEqual(stats["pages_count"], 2)
        self.assertEqual(stats["classes_count"], 1)
        self.assertEqual(stats["methods_count"], 1)
        self.assertEqual(stats["properties_count"], 1)
        
        store.close()


if __name__ == "__main__":
    unittest.main()
