"""Local file crawler for Unity documentation."""

import logging
from pathlib import Path
from typing import List, Optional, Set
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class LocalDocsCrawler:
    """Crawls local Unity documentation files."""
    
    def __init__(self, docs_root: Path):
        """Initialize local crawler.
        
        Args:
            docs_root: Root directory of extracted documentation
        """
        self.docs_root = Path(docs_root)
    
    def find_html_files(
        self,
        base_path: Path,
        max_files: Optional[int] = None
    ) -> List[Path]:
        """Find all HTML files in a directory.
        
        Args:
            base_path: Base directory to search
            max_files: Maximum number of files to return
            
        Returns:
            List of HTML file paths
        """
        if not base_path.exists():
            logger.warning(f"Path does not exist: {base_path}")
            return []
        
        html_files = []
        
        for html_file in base_path.rglob("*.html"):
            # Skip index files and special pages
            if html_file.name in ["index.html", "search.html"]:
                continue
            
            html_files.append(html_file)
            
            if max_files and len(html_files) >= max_files:
                break
        
        logger.info(f"Found {len(html_files)} HTML files in {base_path}")
        return html_files
    
    def read_html_file(self, file_path: Path) -> dict:
        """Read and parse an HTML file.
        
        Args:
            file_path: Path to HTML file
            
        Returns:
            Dictionary with file content and metadata
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else file_path.stem
            
            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.decompose()
            
            # Extract main content
            content_div = soup.find('div', class_=['content', 'main-content', 'documentation'])
            if not content_div:
                content_div = soup.find('main')
            
            if content_div:
                content_text = content_div.get_text(separator='\n', strip=True)
            else:
                content_text = soup.get_text(separator='\n', strip=True)
            
            # Determine doc type from path
            if 'Manual' in str(file_path):
                doc_type = 'manual'
            elif 'ScriptReference' in str(file_path):
                doc_type = 'script_reference'
            else:
                doc_type = 'unknown'
            
            # Generate URL (relative path from docs root)
            relative_path = file_path.relative_to(self.docs_root)
            url = f"file:///{relative_path.as_posix()}"
            
            return {
                'path': str(file_path),
                'url': url,
                'title': title_text,
                'content': content_text,
                'html': html_content,
                'doc_type': doc_type
            }
            
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            raise
    
    def get_manual_files(
        self,
        manual_path: Path,
        max_files: Optional[int] = None
    ) -> List[Path]:
        """Get all Manual documentation files.
        
        Args:
            manual_path: Path to Manual directory
            max_files: Maximum number of files
            
        Returns:
            List of HTML file paths
        """
        return self.find_html_files(manual_path, max_files)
    
    def get_script_reference_files(
        self,
        script_path: Path,
        max_files: Optional[int] = None
    ) -> List[Path]:
        """Get all ScriptReference documentation files.
        
        Args:
            script_path: Path to ScriptReference directory
            max_files: Maximum number of files
            
        Returns:
            List of HTML file paths
        """
        return self.find_html_files(script_path, max_files)
