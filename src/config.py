"""Configuration settings for Unity MCP Server."""

import os
from pathlib import Path
from typing import Optional


class Config:
    """Configuration manager."""
    
    def __init__(self):
        """Initialize configuration."""
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
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
        
    def validate(self) -> bool:
        """Validate configuration.
        
        Returns:
            True if configuration is valid
        """
        if not self.openai_api_key:
            return False
        return True
    
    def ensure_data_dir(self) -> None:
        """Ensure data directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)


# Global config instance
config = Config()
