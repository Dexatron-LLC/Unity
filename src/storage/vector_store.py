"""Vector store using ChromaDB for semantic search."""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings
import requests

from ..config import config

logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """Base class for embedding providers."""
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        raise NotImplementedError


class OpenAIEmbedding(EmbeddingProvider):
    """OpenAI embedding provider."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """Initialize OpenAI embedding provider.
        
        Args:
            api_key: OpenAI API key
            model: Embedding model name
        """
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model
        logger.info(f"OpenAI embedding provider initialized (model: {model})")
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding


class OllamaEmbedding(EmbeddingProvider):
    """Ollama embedding provider."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "nomic-embed-text"):
        """Initialize Ollama embedding provider.
        
        Args:
            base_url: Ollama server URL
            model: Embedding model name
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._verify_connection()
        logger.info(f"Ollama embedding provider initialized (url: {base_url}, model: {model})")
    
    def _verify_connection(self) -> None:
        """Verify connection to Ollama server."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            # Check if the model is available
            models = response.json().get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models]
            
            if self.model not in model_names and f"{self.model}:latest" not in [m.get("name", "") for m in models]:
                logger.warning(
                    f"Model '{self.model}' not found in Ollama. Available models: {model_names}. "
                    f"You may need to run: ollama pull {self.model}"
                )
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                f"Make sure Ollama is running (ollama serve) and accessible."
            )
        except Exception as e:
            logger.warning(f"Could not verify Ollama connection: {e}")
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        response = requests.post(
            f"{self.base_url}/api/embeddings",
            json={
                "model": self.model,
                "prompt": text
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()["embedding"]


def create_embedding_provider(
    openai_api_key: Optional[str] = None,
    use_ollama: bool = False,
    ollama_base_url: Optional[str] = None,
    ollama_model: Optional[str] = None,
    openai_model: Optional[str] = None
) -> EmbeddingProvider:
    """Create an embedding provider based on configuration.
    
    Args:
        openai_api_key: OpenAI API key (required for OpenAI)
        use_ollama: Whether to use Ollama instead of OpenAI
        ollama_base_url: Ollama server URL
        ollama_model: Ollama embedding model
        openai_model: OpenAI embedding model
        
    Returns:
        Configured embedding provider
    """
    # Check config for provider preference if not explicitly set
    if not use_ollama and config.is_ollama():
        use_ollama = True
    
    if use_ollama:
        base_url = ollama_base_url or config.ollama_base_url
        model = ollama_model or config.ollama_embedding_model
        return OllamaEmbedding(base_url=base_url, model=model)
    else:
        if not openai_api_key:
            raise ValueError("OpenAI API key is required when using OpenAI embeddings")
        model = openai_model or config.openai_embedding_model
        return OpenAIEmbedding(api_key=openai_api_key, model=model)


class VectorStore:
    """Manages vector embeddings and semantic search using ChromaDB."""
    
    def __init__(
        self,
        data_dir: str,
        openai_api_key: Optional[str] = None,
        use_ollama: bool = False,
        ollama_base_url: Optional[str] = None,
        ollama_model: Optional[str] = None
    ):
        """Initialize the vector store.
        
        Args:
            data_dir: Directory to store ChromaDB data
            openai_api_key: OpenAI API key for embeddings (required if not using Ollama)
            use_ollama: Use Ollama for embeddings instead of OpenAI
            ollama_base_url: Ollama server URL (default: http://localhost:11434)
            ollama_model: Ollama embedding model (default: nomic-embed-text)
        """
        self.data_dir = Path(data_dir).absolute() / "vector"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding provider
        self.embedding_provider = create_embedding_provider(
            openai_api_key=openai_api_key,
            use_ollama=use_ollama,
            ollama_base_url=ollama_base_url,
            ollama_model=ollama_model
        )
        
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
        """Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        return self.embedding_provider.get_embedding(text)
    
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
    
    def close(self) -> None:
        """Close the vector store and release resources."""
        # ChromaDB's PersistentClient doesn't have an explicit close method,
        # but we can clear our references to allow garbage collection
        self.manual_collection = None
        self.script_collection = None
        self.chroma_client = None
        logger.info("Vector store closed")
