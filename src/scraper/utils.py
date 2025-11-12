"""Utility functions for Unity documentation processing."""

import hashlib


def get_page_id(url: str) -> str:
    """Generate a unique ID for a page URL.
    
    Args:
        url: Page URL
        
    Returns:
        MD5 hash of the URL
    """
    return hashlib.md5(url.encode()).hexdigest()


def get_doc_type(url: str) -> str:
    """Determine document type from URL.
    
    Args:
        url: Page URL
        
    Returns:
        'manual' or 'script_reference'
    """
    if "/Manual/" in url:
        return "manual"
    elif "/ScriptReference/" in url:
        return "script_reference"
    return "unknown"
