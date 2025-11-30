"""Configuration settings for Unity MCP Server."""

import os
from pathlib import Path
from typing import Optional, Literal


class Config:
    """Configuration manager."""
    
    # Supported embedding providers
    PROVIDER_OPENAI = "openai"
    PROVIDER_OLLAMA = "ollama"
    
    def __init__(self):
        """Initialize configuration."""
        # Embedding provider configuration
        self.embedding_provider: str = os.getenv(
            "EMBEDDING_PROVIDER", self.PROVIDER_OPENAI
        ).lower()
        
        # OpenAI settings
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.openai_embedding_model: str = os.getenv(
            "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
        )
        
        # Ollama settings
        self.ollama_base_url: str = os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )
        self.ollama_embedding_model: str = os.getenv(
            "OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"
        )
        
        # Data directory
        self.data_dir: Path = Path(os.getenv("DATA_DIR", "./data"))
        
        # Unity documentation URLs
        self.unity_manual_url = "https://docs.unity3d.com/Manual/index.html"
        self.unity_script_ref_url = "https://docs.unity3d.com/ScriptReference/index.html"
        
        # Processing settings
        self.chunk_size = 1000  # Characters per chunk for vector store
        self.max_results_default = 5
        
        # Crawl settings
        self.crawl_delay = 0.5  # Seconds between requests
        self.request_timeout = 30000  # Milliseconds
    
    def is_ollama(self) -> bool:
        """Check if using Ollama provider.
        
        Returns:
            True if Ollama is the configured provider
        """
        return self.embedding_provider == self.PROVIDER_OLLAMA
    
    def is_openai(self) -> bool:
        """Check if using OpenAI provider.
        
        Returns:
            True if OpenAI is the configured provider
        """
        return self.embedding_provider == self.PROVIDER_OPENAI
        
    def validate(self) -> bool:
        """Validate configuration.
        
        Returns:
            True if configuration is valid
        """
        if self.is_openai() and not self.openai_api_key:
            return False
        return True
    
    def ensure_data_dir(self) -> None:
        """Ensure data directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def get_provider_info(self) -> str:
        """Get human-readable provider information.
        
        Returns:
            String describing the current embedding provider configuration
        """
        if self.is_ollama():
            return f"Ollama ({self.ollama_base_url}, model: {self.ollama_embedding_model})"
        else:
            return f"OpenAI (model: {self.openai_embedding_model})"


# Global config instance
config = Config()
