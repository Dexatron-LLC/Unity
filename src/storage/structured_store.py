"""Structured data store using SQLite."""

import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class StructuredStore:
    """Manages structured Unity documentation data using SQLite."""
    
    def __init__(self, data_dir: str):
        """Initialize the structured store.
        
        Args:
            data_dir: Directory to store SQLite database
        """
        self.data_dir = Path(data_dir).absolute() / "structured"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.data_dir / "unity_docs.db"
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        self._create_tables()
        logger.info("Structured store initialized")
    
    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Pages table - stores all documentation pages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                id TEXT PRIMARY KEY,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                doc_type TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Classes table - Unity API classes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                namespace TEXT,
                page_id TEXT,
                description TEXT,
                inherits_from TEXT,
                is_static INTEGER DEFAULT 0,
                FOREIGN KEY (page_id) REFERENCES pages(id)
            )
        """)
        
        # Methods table - class methods
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                return_type TEXT,
                is_static INTEGER DEFAULT 0,
                description TEXT,
                signature TEXT,
                FOREIGN KEY (class_id) REFERENCES classes(id)
            )
        """)
        
        # Properties table - class properties
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                property_type TEXT,
                is_static INTEGER DEFAULT 0,
                description TEXT,
                FOREIGN KEY (class_id) REFERENCES classes(id)
            )
        """)
        
        # Parameters table - method parameters
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                param_type TEXT,
                description TEXT,
                position INTEGER,
                FOREIGN KEY (method_id) REFERENCES methods(id)
            )
        """)
        
        # Create indices for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pages_doc_type ON pages(doc_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_classes_name ON classes(name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_methods_name ON methods(name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_properties_name ON properties(name)
        """)
        
        self.conn.commit()
    
    def add_page(
        self,
        page_id: str,
        url: str,
        title: str,
        doc_type: str,
        content: str
    ) -> None:
        """Add or update a documentation page.
        
        Args:
            page_id: Unique page identifier
            url: Page URL
            title: Page title
            doc_type: 'manual' or 'script_reference'
            content: Page content
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO pages (id, url, title, doc_type, content, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (page_id, url, title, doc_type, content))
        self.conn.commit()
        logger.info(f"Added/updated page: {title}")
    
    def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get a page by ID.
        
        Args:
            page_id: Page identifier
            
        Returns:
            Page data or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM pages WHERE id = ?", (page_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_page_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get a page by URL.
        
        Args:
            url: Page URL
            
        Returns:
            Page data or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM pages WHERE url = ?", (url,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def add_class(
        self,
        name: str,
        namespace: Optional[str],
        page_id: str,
        description: Optional[str] = None,
        inherits_from: Optional[str] = None,
        is_static: bool = False
    ) -> int:
        """Add or update a Unity class.
        
        Args:
            name: Class name
            namespace: Class namespace
            page_id: Associated page ID
            description: Class description
            inherits_from: Parent class name
            is_static: Whether the class is static
            
        Returns:
            Class ID
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO classes 
            (name, namespace, page_id, description, inherits_from, is_static)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, namespace, page_id, description, inherits_from, int(is_static)))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_class(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a class by name.
        
        Args:
            name: Class name
            
        Returns:
            Class data with methods and properties
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM classes WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        class_data = dict(row)
        class_id = class_data["id"]
        
        # Get methods
        cursor.execute("SELECT * FROM methods WHERE class_id = ?", (class_id,))
        class_data["methods"] = [dict(row) for row in cursor.fetchall()]
        
        # Get properties
        cursor.execute("SELECT * FROM properties WHERE class_id = ?", (class_id,))
        class_data["properties"] = [dict(row) for row in cursor.fetchall()]
        
        return class_data
    
    def add_method(
        self,
        class_id: int,
        name: str,
        return_type: Optional[str] = None,
        is_static: bool = False,
        description: Optional[str] = None,
        signature: Optional[str] = None
    ) -> int:
        """Add a method to a class.
        
        Args:
            class_id: Class ID
            name: Method name
            return_type: Return type
            is_static: Whether the method is static
            description: Method description
            signature: Full method signature
            
        Returns:
            Method ID
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO methods 
            (class_id, name, return_type, is_static, description, signature)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (class_id, name, return_type, int(is_static), description, signature))
        self.conn.commit()
        return cursor.lastrowid
    
    def add_property(
        self,
        class_id: int,
        name: str,
        property_type: Optional[str] = None,
        is_static: bool = False,
        description: Optional[str] = None
    ) -> int:
        """Add a property to a class.
        
        Args:
            class_id: Class ID
            name: Property name
            property_type: Property type
            is_static: Whether the property is static
            description: Property description
            
        Returns:
            Property ID
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO properties 
            (class_id, name, property_type, is_static, description)
            VALUES (?, ?, ?, ?, ?)
        """, (class_id, name, property_type, int(is_static), description))
        self.conn.commit()
        return cursor.lastrowid
    
    def search_classes(self, query: str) -> List[Dict[str, Any]]:
        """Search for classes by name.
        
        Args:
            query: Search query
            
        Returns:
            List of matching classes
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM classes 
            WHERE name LIKE ? OR description LIKE ?
            ORDER BY name
        """, (f"%{query}%", f"%{query}%"))
        return [dict(row) for row in cursor.fetchall()]
    
    def search_methods(self, query: str) -> List[Dict[str, Any]]:
        """Search for methods by name.
        
        Args:
            query: Search query
            
        Returns:
            List of matching methods with class info
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.*, c.name as class_name, c.namespace
            FROM methods m
            JOIN classes c ON m.class_id = c.id
            WHERE m.name LIKE ? OR m.description LIKE ?
            ORDER BY m.name
        """, (f"%{query}%", f"%{query}%"))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the structured store.
        
        Returns:
            Dictionary with counts for each table
        """
        cursor = self.conn.cursor()
        
        stats = {}
        for table in ["pages", "classes", "methods", "properties"]:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            stats[f"{table}_count"] = cursor.fetchone()["count"]
        
        return stats
    
    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()
