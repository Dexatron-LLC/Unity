"""Unit tests for content processor."""

import unittest
from unittest.mock import Mock

from src.processor.content_processor import ContentProcessor


class TestContentProcessor(unittest.TestCase):
    """Test cases for ContentProcessor."""
    
    def test_extract_script_reference_data_basic(self):
        """Test extracting basic script reference data."""
        html = """
        <html>
            <body>
                <h1>GameObject</h1>
                <div class="description">
                    Base class for all entities in Unity scenes.
                </div>
            </body>
        </html>
        """
        
        result = ContentProcessor.extract_script_reference_data(
            html,
            "https://docs.unity3d.com/ScriptReference/GameObject.html",
            "GameObject"
        )
        
        self.assertEqual(result["type"], "script_reference")
        self.assertEqual(result["class_name"], "GameObject")
        self.assertIn("Base class", result["description"])
    
    def test_extract_script_reference_with_namespace(self):
        """Test extracting class with namespace."""
        html = "<html><body><h1>UnityEngine.GameObject</h1></body></html>"
        
        result = ContentProcessor.extract_script_reference_data(
            html,
            "https://test.com",
            "UnityEngine.GameObject"
        )
        
        self.assertEqual(result["namespace"], "UnityEngine")
        self.assertEqual(result["class_name"], "GameObject")
    
    def test_extract_methods(self):
        """Test extracting methods from HTML."""
        html = """
        <html>
            <body>
                <h2>Public Methods</h2>
                <table>
                    <tr><th>Method</th><th>Description</th></tr>
                    <tr>
                        <td>SetActive</td>
                        <td>Activates/Deactivates the GameObject</td>
                    </tr>
                    <tr>
                        <td>GetComponent</td>
                        <td>Gets a component attached to the GameObject</td>
                    </tr>
                </table>
            </body>
        </html>
        """
        
        result = ContentProcessor.extract_script_reference_data(html, "", "Test")
        
        self.assertEqual(len(result["methods"]), 2)
        self.assertEqual(result["methods"][0]["name"], "SetActive")
        self.assertIn("Activates", result["methods"][0]["description"])
    
    def test_extract_properties(self):
        """Test extracting properties from HTML."""
        html = """
        <html>
            <body>
                <h2>Public Properties</h2>
                <table>
                    <tr><th>Property</th><th>Description</th></tr>
                    <tr>
                        <td>transform</td>
                        <td>The Transform attached to this GameObject</td>
                    </tr>
                    <tr>
                        <td>name</td>
                        <td>The name of the object</td>
                    </tr>
                </table>
            </body>
        </html>
        """
        
        result = ContentProcessor.extract_script_reference_data(html, "", "Test")
        
        self.assertEqual(len(result["properties"]), 2)
        self.assertEqual(result["properties"][0]["name"], "transform")
        self.assertIn("Transform", result["properties"][0]["description"])
    
    def test_extract_manual_data(self):
        """Test extracting manual page data."""
        html = """
        <html>
            <body>
                <div class="content">
                    <h2>Introduction</h2>
                    <p>This is the introduction section.</p>
                    <h2>Getting Started</h2>
                    <p>Here's how to get started.</p>
                    <pre>GameObject obj = new GameObject();</pre>
                </div>
            </body>
        </html>
        """
        
        result = ContentProcessor.extract_manual_data(
            html,
            "https://docs.unity3d.com/Manual/GameObjects.html",
            "GameObjects"
        )
        
        self.assertEqual(result["type"], "manual")
        self.assertEqual(result["title"], "GameObjects")
        self.assertEqual(len(result["sections"]), 2)
        self.assertEqual(result["sections"][0]["title"], "Introduction")
        self.assertEqual(len(result["code_examples"]), 1)
    
    def test_prepare_for_vector_store_small_content(self):
        """Test preparing small content (no chunking needed)."""
        content = "This is a short piece of content."
        metadata = {"title": "Test", "url": "https://test.com"}
        
        chunks = ContentProcessor.prepare_for_vector_store(
            content,
            metadata,
            chunk_size=1000
        )
        
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0][0], content)
        self.assertEqual(chunks[0][1]["title"], "Test")
    
    def test_prepare_for_vector_store_large_content(self):
        """Test preparing large content (needs chunking)."""
        # Create content larger than chunk size
        content = " ".join(["word"] * 500)  # ~2500 characters
        metadata = {"title": "Test", "url": "https://test.com"}
        
        chunks = ContentProcessor.prepare_for_vector_store(
            content,
            metadata,
            chunk_size=1000
        )
        
        self.assertGreater(len(chunks), 1)
        
        # Check that each chunk has metadata with chunk_index
        for i, (chunk_text, chunk_meta) in enumerate(chunks):
            self.assertEqual(chunk_meta["chunk_index"], i)
            self.assertEqual(chunk_meta["title"], "Test")
            self.assertLessEqual(len(chunk_text), 1200)  # Allow some buffer
    
    def test_extract_static_class(self):
        """Test detecting static classes."""
        html = """
        <html>
            <body>
                <h1>Mathf static class</h1>
            </body>
        </html>
        """
        
        result = ContentProcessor.extract_script_reference_data(
            html, "", "Mathf static class"
        )
        
        self.assertTrue(result["is_static"])
    
    def test_extract_inheritance(self):
        """Test extracting class inheritance."""
        html = """
        <html>
            <body>
                <p>Inherits from: <a href="#">MonoBehaviour</a></p>
            </body>
        </html>
        """
        
        result = ContentProcessor.extract_script_reference_data(html, "", "MyClass")
        
        self.assertEqual(result["inherits_from"], "MonoBehaviour")
    
    def test_extract_constructors(self):
        """Test extracting constructors."""
        html = """
        <html>
            <body>
                <h2>Constructors</h2>
                <table>
                    <tr><th>Constructor</th><th>Description</th></tr>
                    <tr>
                        <td>GameObject()</td>
                        <td>Creates a new GameObject</td>
                    </tr>
                    <tr>
                        <td>GameObject(string name)</td>
                        <td>Creates a new GameObject with name</td>
                    </tr>
                </table>
            </body>
        </html>
        """
        
        result = ContentProcessor.extract_script_reference_data(html, "", "GameObject")
        
        self.assertEqual(len(result["constructors"]), 2)
        self.assertEqual(result["constructors"][0]["signature"], "GameObject()")
        self.assertIn("Creates", result["constructors"][0]["description"])


if __name__ == "__main__":
    unittest.main()
