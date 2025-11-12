"""Unit tests for MCP server."""

import unittest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import tempfile
import shutil

from src.server import UnityMCPServer


class TestUnityMCPServer(unittest.IsolatedAsyncioTestCase):
    """Test cases for UnityMCPServer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.mock_api_key = "test-api-key"
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    @patch('src.server.VectorStore')
    @patch('src.server.StructuredStore')
    def test_initialization(self, mock_structured, mock_vector):
        """Test MCP server initialization."""
        mock_vector_instance = Mock()
        mock_structured_instance = Mock()
        mock_vector.return_value = mock_vector_instance
        mock_structured.return_value = mock_structured_instance
        
        server = UnityMCPServer(self.test_dir, self.mock_api_key)
        
        self.assertIsNotNone(server)
        self.assertIsNotNone(server.server)
        mock_vector.assert_called_once()
        mock_structured.assert_called_once()
    
    @patch('src.server.VectorStore')
    @patch('src.server.StructuredStore')
    async def test_search_unity_docs(self, mock_structured, mock_vector):
        """Test search_unity_docs tool."""
        # Setup mocks
        mock_vector_instance = Mock()
        mock_structured_instance = Mock()
        mock_vector.return_value = mock_vector_instance
        mock_structured.return_value = mock_structured_instance
        
        mock_vector_instance.search = Mock(return_value=[
            {
                "metadata": {
                    "title": "GameObject",
                    "url": "https://test.com",
                    "doc_type": "script_reference"
                },
                "content": "GameObject is the base class..."
            }
        ])
        
        server = UnityMCPServer(self.test_dir, self.mock_api_key)
        
        # Test search
        args = {
            "query": "GameObject",
            "doc_type": "both",
            "max_results": 5
        }
        
        result = await server._search_unity_docs(args)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertIn("GameObject", result[0].text)
        mock_vector_instance.search.assert_called_once()
    
    @patch('src.server.VectorStore')
    @patch('src.server.StructuredStore')
    async def test_query_unity_structure(self, mock_structured, mock_vector):
        """Test query_unity_structure tool."""
        # Setup mocks
        mock_vector_instance = Mock()
        mock_structured_instance = Mock()
        mock_vector.return_value = mock_vector_instance
        mock_structured.return_value = mock_structured_instance
        
        mock_structured_instance.search_classes = Mock(return_value=[
            {
                "name": "GameObject",
                "namespace": "UnityEngine",
                "description": "Base class for all entities",
                "inherits_from": "Object"
            }
        ])
        
        mock_structured_instance.search_methods = Mock(return_value=[])
        
        server = UnityMCPServer(self.test_dir, self.mock_api_key)
        
        # Test query
        args = {
            "query": "GameObject",
            "query_type": "auto"
        }
        
        result = await server._query_unity_structure(args)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertIn("GameObject", result[0].text)
        mock_structured_instance.search_classes.assert_called_once()
    
    @patch('src.server.VectorStore')
    @patch('src.server.StructuredStore')
    async def test_get_unity_page_cached(self, mock_structured, mock_vector):
        """Test get_unity_page with cached page."""
        # Setup mocks
        mock_vector_instance = Mock()
        mock_structured_instance = Mock()
        mock_vector.return_value = mock_vector_instance
        mock_structured.return_value = mock_structured_instance
        
        mock_structured_instance.get_page = Mock(return_value={
            "title": "GameObject",
            "url": "https://test.com",
            "doc_type": "script_reference",
            "content": "GameObject content..."
        })
        
        server = UnityMCPServer(self.test_dir, self.mock_api_key)
        
        # Test get page
        args = {
            "url": "https://docs.unity3d.com/ScriptReference/GameObject.html"
        }
        
        result = await server._get_unity_page(args)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertIn("GameObject", result[0].text)
        self.assertIn("cached", result[0].text)
        mock_structured_instance.get_page.assert_called_once()
    
    @patch('src.server.VectorStore')
    @patch('src.server.StructuredStore')
    async def test_get_cache_stats(self, mock_structured, mock_vector):
        """Test get_cache_stats tool."""
        # Setup mocks
        mock_vector_instance = Mock()
        mock_structured_instance = Mock()
        mock_vector.return_value = mock_vector_instance
        mock_structured.return_value = mock_structured_instance
        
        mock_vector_instance.get_stats = Mock(return_value={
            "manual_count": 10,
            "script_reference_count": 20,
            "total_count": 30
        })
        
        mock_structured_instance.get_stats = Mock(return_value={
            "pages_count": 25,
            "classes_count": 100,
            "methods_count": 500,
            "properties_count": 300
        })
        
        server = UnityMCPServer(self.test_dir, self.mock_api_key)
        
        # Test stats
        result = await server._get_cache_stats({})
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertIn("10", result[0].text)  # manual_count
        self.assertIn("100", result[0].text)  # classes_count
        mock_vector_instance.get_stats.assert_called_once()
        mock_structured_instance.get_stats.assert_called_once()
    
    @patch('src.server.VectorStore')
    @patch('src.server.StructuredStore')
    async def test_search_no_results(self, mock_structured, mock_vector):
        """Test search with no results."""
        mock_vector_instance = Mock()
        mock_structured_instance = Mock()
        mock_vector.return_value = mock_vector_instance
        mock_structured.return_value = mock_structured_instance
        
        mock_vector_instance.search = Mock(return_value=[])
        
        server = UnityMCPServer(self.test_dir, self.mock_api_key)
        
        args = {"query": "nonexistent"}
        result = await server._search_unity_docs(args)
        
        self.assertIsNotNone(result)
        self.assertIn("No results", result[0].text)


if __name__ == "__main__":
    unittest.main()
