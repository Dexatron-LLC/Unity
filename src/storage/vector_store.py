"""Vector store using ChromaDB for semantic search."""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings
from openai import OpenAI

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages vector embeddings and semantic search using ChromaDB."""
    
    def __init__(self, data_dir: str, openai_api_key: str):
        """Initialize the vector store.
        
        Args:
            data_dir: Directory to store ChromaDB data
            openai_api_key: OpenAI API key for embeddings
        """
        self.data_dir = Path(data_dir) / "vector"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.openai_client = OpenAI(api_key=openai_api_key)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.data_dir / "chromadb"),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Create or get collections
        self.manual_collection = self.chroma_client.get_or_create_collection(
            name="unity_manual",
            metadata={"description": "Unity Manual documentation"}
        )
        
        self.script_collection = self.chroma_client.get_or_create_collection(
            name="unity_script_reference",
            metadata={"description": "Unity Script Reference documentation"}
        )
        
        logger.info("Vector store initialized")
    
    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    def add_document(
        self,
        doc_id: str,
        url: str,
        title: str,
        content: str,
        doc_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a document to the vector store.
        
        Args:
            doc_id: Unique document identifier
            url: Document URL
            title: Document title
            content: Document content
            doc_type: 'manual' or 'script_reference'
            metadata: Additional metadata
        """
        try:
            # Generate embedding
            embedding = self._get_embedding(content)
            
            # Prepare metadata
            doc_metadata = {
                "url": url,
                "title": title,
                "doc_type": doc_type,
                **(metadata or {})
            }
            
            # Select collection
            collection = (
                self.manual_collection if doc_type == "manual"
                else self.script_collection
            )
            
            # Add to collection
            collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[doc_metadata]
            )
            
            logger.info(f"Added document: {title} ({doc_id})")
            
        except Exception as e:
            logger.error(f"Error adding document {doc_id}: {e}")
            raise
    
    def search(
        self,
        query: str,
        doc_type: Optional[str] = None,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for documents using semantic search.
        
        Args:
            query: Search query
            doc_type: Filter by 'manual', 'script_reference', or None for both
            n_results: Number of results to return
            
        Returns:
            List of search results with content and metadata
        """
        try:
            # Generate query embedding
            query_embedding = self._get_embedding(query)
            
            results = []
            
            # Search in appropriate collections
            collections = []
            if doc_type == "manual":
                collections = [self.manual_collection]
            elif doc_type == "script_reference":
                collections = [self.script_collection]
            else:
                collections = [self.manual_collection, self.script_collection]
            
            for collection in collections:
                collection_results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results
                )
                
                # Format results
                if collection_results["ids"]:
                    for i in range(len(collection_results["ids"][0])):
                        results.append({
                            "id": collection_results["ids"][0][i],
                            "content": collection_results["documents"][0][i],
                            "metadata": collection_results["metadatas"][0][i],
                            "distance": collection_results["distances"][0][i] if "distances" in collection_results else None
                        })
            
            # Sort by distance if available
            if results and results[0].get("distance") is not None:
                results.sort(key=lambda x: x["distance"])
            
            return results[:n_results]
            
        except Exception as e:
            logger.error(f"Error searching: {e}")
            raise
    
    def get_document(self, doc_id: str, doc_type: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID.
        
        Args:
            doc_id: Document identifier
            doc_type: 'manual' or 'script_reference'
            
        Returns:
            Document data or None if not found
        """
        try:
            collection = (
                self.manual_collection if doc_type == "manual"
                else self.script_collection
            )
            
            result = collection.get(ids=[doc_id])
            
            if result["ids"]:
                return {
                    "id": result["ids"][0],
                    "content": result["documents"][0],
                    "metadata": result["metadatas"][0]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting document {doc_id}: {e}")
            return None
    
    def document_exists(self, doc_id: str, doc_type: str) -> bool:
        """Check if a document exists in the store.
        
        Args:
            doc_id: Document identifier
            doc_type: 'manual' or 'script_reference'
            
        Returns:
            True if document exists
        """
        return self.get_document(doc_id, doc_type) is not None
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the vector store.
        
        Returns:
            Dictionary with counts for each collection
        """
        return {
            "manual_count": self.manual_collection.count(),
            "script_reference_count": self.script_collection.count(),
            "total_count": self.manual_collection.count() + self.script_collection.count()
        }
    
    def clear(self, doc_type: Optional[str] = None) -> None:
        """Clear documents from the store.
        
        Args:
            doc_type: 'manual', 'script_reference', or None for all
        """
        if doc_type == "manual" or doc_type is None:
            self.chroma_client.delete_collection("unity_manual")
            self.manual_collection = self.chroma_client.create_collection(
                name="unity_manual",
                metadata={"description": "Unity Manual documentation"}
            )
        
        if doc_type == "script_reference" or doc_type is None:
            self.chroma_client.delete_collection("unity_script_reference")
            self.script_collection = self.chroma_client.create_collection(
                name="unity_script_reference",
                metadata={"description": "Unity Script Reference documentation"}
            )
        
        logger.info(f"Cleared vector store: {doc_type or 'all'}")
