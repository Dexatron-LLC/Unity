"""Download and extract Unity documentation from official ZIP."""

import os
import json
import logging
import zipfile
import requests
from pathlib import Path
from typing import Optional, Tuple
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class UnityDocsDownloader:
    """Downloads Unity documentation ZIP file."""
    
    # Unity offline documentation page (contains latest version link)
    OFFLINE_DOCS_PAGE = "https://docs.unity3d.com/Manual/OfflineDocumentation.html"
    
    # Fallback URL (2022.2)
    FALLBACK_URL = "https://storage.googleapis.com/docscloudstorage/2022.2/UnityDocumentation.zip"
    
    def __init__(self, download_dir: str):
        """Initialize downloader.
        
        Args:
            download_dir: Directory to download and extract documentation
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.zip_path = self.download_dir / "UnityDocumentation.zip"
        self.extract_dir = self.download_dir / "UnityDocumentation"
        self.version_file = self.download_dir / "version.json"
    
    def get_latest_version_url(self) -> Tuple[str, str]:
        """Fetch the latest documentation version and download URL.
        
        Returns:
            Tuple of (version, download_url)
        """
        try:
            logger.info(f"Checking for latest documentation version at {self.OFFLINE_DOCS_PAGE}")
            response = requests.get(self.OFFLINE_DOCS_PAGE, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find the download link
            download_link = soup.find('a', string=lambda text: text and 'Download:' in text)
            if download_link and download_link.get('href'):
                url = download_link['href']
                
                # Extract version from URL (e.g., .../2022.2/UnityDocumentation.zip)
                parts = url.split('/')
                for i, part in enumerate(parts):
                    if 'UnityDocumentation.zip' in part and i > 0:
                        version = parts[i-1]
                        logger.info(f"Found latest version: {version}")
                        return version, url
            
            logger.warning("Could not find download link on offline docs page")
        except Exception as e:
            logger.warning(f"Error fetching latest version: {e}")
        
        # Fallback to hardcoded version
        logger.info("Using fallback URL (2022.2)")
        return "2022.2", self.FALLBACK_URL
    
    def get_current_version(self) -> Optional[str]:
        """Get currently downloaded version.
        
        Returns:
            Version string or None if not downloaded
        """
        # Ensure download directory exists
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r') as f:
                    data = json.load(f)
                    return data.get('version')
            except Exception as e:
                logger.warning(f"Error reading version file: {e}")
        return None
    
    def save_version(self, version: str, url: str) -> None:
        """Save downloaded version information.
        
        Args:
            version: Version string
            url: Download URL
        """
        # Ensure download directory exists
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.version_file, 'w') as f:
                json.dump({
                    'version': version,
                    'url': url,
                    'downloaded_at': str(Path(self.zip_path).stat().st_mtime) if self.zip_path.exists() else None
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving version file: {e}")
    
    def check_for_updates(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """Check if a newer version is available.
        
        Returns:
            Tuple of (update_available, current_version, latest_version)
        """
        current = self.get_current_version()
        latest, url = self.get_latest_version_url()
        
        if current is None:
            logger.info("No local version found")
            return True, None, latest
        
        if current != latest:
            logger.info(f"Update available: {current} -> {latest}")
            return True, current, latest
        
        logger.info(f"Documentation is up-to-date (version {current})")
        return False, current, latest
    
    def download(self, force: bool = False, check_version: bool = True) -> Path:
        """Download Unity documentation ZIP.
        
        Args:
            force: Force re-download even if file exists
            check_version: Check for updates before downloading
            
        Returns:
            Path to downloaded ZIP file
        """
        # Ensure download directory exists
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for updates if requested
        if check_version and not force:
            update_available, current, latest = self.check_for_updates()
            if update_available:
                if current:
                    logger.info(f"Update available: {current} -> {latest}")
                    force = True  # Force download of new version
                else:
                    logger.info(f"No local version found. Will download version {latest}")
            
        # Get latest URL
        version, url = self.get_latest_version_url()
        
        if self.zip_path.exists() and not force:
            logger.info(f"Documentation ZIP already exists: {self.zip_path}")
            return self.zip_path
        
        logger.info(f"Downloading Unity documentation version {version} from {url}")
        logger.info("This may take several minutes (file is ~200-300MB)...")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        last_logged_progress = 0
        
        with open(self.zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Only log every 10% to avoid spam
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        if progress - last_logged_progress >= 10:
                            logger.info(f"Download progress: {progress:.1f}%")
                            last_logged_progress = progress
        
        logger.info(f"Download complete: {self.zip_path}")
        
        # Save version information
        self.save_version(version, url)
        
        return self.zip_path
    
    def extract(self, force: bool = False) -> Path:
        """Extract Unity documentation ZIP.
        
        Args:
            force: Force re-extraction even if directory exists
            
        Returns:
            Path to extracted documentation directory
        """
        if self.extract_dir.exists() and not force:
            logger.info(f"Documentation already extracted: {self.extract_dir}")
            return self.extract_dir
        
        # Clean up old Documentation directory before extraction
        docs_dir = self.download_dir / "Documentation"
        if docs_dir.exists():
            logger.info(f"Removing old documentation directory: {docs_dir} (this may take a moment...)")
            import shutil
            try:
                shutil.rmtree(docs_dir)
                logger.info("Old documentation removed successfully")
            except Exception as e:
                logger.warning(f"Could not fully remove old documentation: {e}")
        
        logger.info(f"Extracting documentation to {self.extract_dir}")
        
        with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.download_dir)
        
        logger.info("Extraction complete")
        
        # Clean up ZIP file to save disk space
        if self.zip_path.exists():
            logger.info(f"Removing ZIP file to save disk space: {self.zip_path}")
            self.zip_path.unlink()
        
        # Return the actual extracted directory (ZIP contains "Documentation" not "UnityDocumentation")
        actual_docs_dir = self.download_dir / "Documentation"
        return actual_docs_dir
    
    def download_and_extract(self, force: bool = False) -> Path:
        """Download and extract Unity documentation.
        
        Args:
            force: Force re-download and re-extraction
            
        Returns:
            Path to extracted documentation directory
        """
        self.download(force)
        return self.extract(force)
    
    def get_manual_path(self) -> Optional[Path]:
        """Get path to Manual documentation.
        
        Returns:
            Path to Manual directory or None if not found
        """
        # ZIP extracts to Documentation/en/Manual
        manual_path = self.download_dir / "Documentation" / "en" / "Manual"
        if manual_path.exists():
            return manual_path
        return None
    
    def get_script_reference_path(self) -> Optional[Path]:
        """Get path to ScriptReference documentation.
        
        Returns:
            Path to ScriptReference directory or None if not found
        """
        # ZIP extracts to Documentation/en/ScriptReference
        script_path = self.download_dir / "Documentation" / "en" / "ScriptReference"
        if script_path.exists():
            return script_path
        return None
