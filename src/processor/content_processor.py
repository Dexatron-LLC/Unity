"""Content processor for Unity documentation."""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ContentProcessor:
    """Processes Unity documentation content for structured storage."""
    
    @staticmethod
    def extract_script_reference_data(
        html: str,
        url: str,
        title: str
    ) -> Dict[str, Any]:
        """Extract structured data from Script Reference pages.
        
        Args:
            html: Page HTML content
            url: Page URL
            title: Page title
            
        Returns:
            Dictionary with extracted structured data
        """
        soup = BeautifulSoup(html, "lxml")
        
        result = {
            "type": "script_reference",
            "url": url,
            "title": title,
            "class_name": None,
            "namespace": None,
            "inherits_from": None,
            "description": None,
            "is_static": False,
            "methods": [],
            "properties": [],
            "constructors": []
        }
        
        try:
            # Extract class name from title
            class_match = re.match(r"^(\w+(?:\.\w+)*)\s*(?:class)?", title, re.IGNORECASE)
            if class_match:
                full_name = class_match.group(1)
                if "." in full_name:
                    parts = full_name.rsplit(".", 1)
                    result["namespace"] = parts[0]
                    result["class_name"] = parts[1]
                else:
                    result["class_name"] = full_name
            
            # Extract description
            desc_section = soup.find("div", class_=["description", "subsection"])
            if desc_section:
                result["description"] = desc_section.get_text(strip=True)
            
            # Extract inheritance
            inheritance = soup.find(string=re.compile(r"Inherits from", re.IGNORECASE))
            if inheritance:
                parent = inheritance.find_next("a")
                if parent:
                    result["inherits_from"] = parent.get_text(strip=True)
            
            # Check if static
            if "static" in title.lower() or "static class" in html.lower():
                result["is_static"] = True
            
            # Extract methods
            result["methods"] = ContentProcessor._extract_methods(soup)
            
            # Extract properties
            result["properties"] = ContentProcessor._extract_properties(soup)
            
            # Extract constructors
            result["constructors"] = ContentProcessor._extract_constructors(soup)
            
        except Exception as e:
            logger.error(f"Error extracting script reference data: {e}")
        
        return result
    
    @staticmethod
    def _extract_methods(soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract methods from Script Reference page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of method dictionaries
        """
        methods = []
        
        # Look for methods section
        methods_section = soup.find(["h2", "h3"], string=re.compile(r"^(Public|Static)\s+Methods?", re.IGNORECASE))
        
        if methods_section:
            # Find the table or list of methods
            table = methods_section.find_next("table")
            if table:
                rows = table.find_all("tr")
                for row in rows[1:]:  # Skip header
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        method_name_cell = cols[0]
                        desc_cell = cols[1]
                        
                        method_name = method_name_cell.get_text(strip=True)
                        description = desc_cell.get_text(strip=True)
                        
                        # Try to extract signature
                        signature = method_name
                        is_static = "static" in methods_section.get_text().lower()
                        
                        # Parse method name and return type
                        parts = method_name.split()
                        actual_name = parts[-1] if parts else method_name
                        return_type = " ".join(parts[:-1]) if len(parts) > 1 else None
                        
                        methods.append({
                            "name": actual_name,
                            "return_type": return_type,
                            "is_static": is_static,
                            "description": description,
                            "signature": signature
                        })
        
        return methods
    
    @staticmethod
    def _extract_properties(soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract properties from Script Reference page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of property dictionaries
        """
        properties = []
        
        # Look for properties section
        props_section = soup.find(["h2", "h3"], string=re.compile(r"^(Public|Static)\s+Properties", re.IGNORECASE))
        
        if props_section:
            # Find the table or list of properties
            table = props_section.find_next("table")
            if table:
                rows = table.find_all("tr")
                for row in rows[1:]:  # Skip header
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        prop_name_cell = cols[0]
                        desc_cell = cols[1]
                        
                        prop_text = prop_name_cell.get_text(strip=True)
                        description = desc_cell.get_text(strip=True)
                        
                        is_static = "static" in props_section.get_text().lower()
                        
                        # Parse property name and type
                        parts = prop_text.split()
                        actual_name = parts[-1] if parts else prop_text
                        prop_type = " ".join(parts[:-1]) if len(parts) > 1 else None
                        
                        properties.append({
                            "name": actual_name,
                            "property_type": prop_type,
                            "is_static": is_static,
                            "description": description
                        })
        
        return properties
    
    @staticmethod
    def _extract_constructors(soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract constructors from Script Reference page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of constructor dictionaries
        """
        constructors = []
        
        # Look for constructor section
        ctor_section = soup.find(["h2", "h3"], string=re.compile(r"Constructors?", re.IGNORECASE))
        
        if ctor_section:
            table = ctor_section.find_next("table")
            if table:
                rows = table.find_all("tr")
                for row in rows[1:]:  # Skip header
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        signature = cols[0].get_text(strip=True)
                        description = cols[1].get_text(strip=True)
                        
                        constructors.append({
                            "signature": signature,
                            "description": description
                        })
        
        return constructors
    
    @staticmethod
    def extract_manual_data(
        html: str,
        url: str,
        title: str
    ) -> Dict[str, Any]:
        """Extract structured data from Manual pages.
        
        Args:
            html: Page HTML content
            url: Page URL
            title: Page title
            
        Returns:
            Dictionary with extracted data
        """
        soup = BeautifulSoup(html, "lxml")
        
        result = {
            "type": "manual",
            "url": url,
            "title": title,
            "sections": [],
            "code_examples": []
        }
        
        try:
            # Extract content sections
            content_div = soup.find("div", class_=["content", "main-content"])
            if content_div:
                # Extract sections with headings
                headings = content_div.find_all(["h1", "h2", "h3", "h4"])
                for heading in headings:
                    section_title = heading.get_text(strip=True)
                    
                    # Get content until next heading
                    section_content = []
                    for sibling in heading.find_next_siblings():
                        if sibling.name in ["h1", "h2", "h3", "h4"]:
                            break
                        section_content.append(sibling.get_text(strip=True))
                    
                    result["sections"].append({
                        "title": section_title,
                        "content": "\n".join(section_content)
                    })
                
                # Extract code examples
                code_blocks = content_div.find_all("pre")
                for i, code in enumerate(code_blocks):
                    result["code_examples"].append({
                        "index": i,
                        "code": code.get_text(strip=True),
                        "language": code.get("class", [""])[0] if code.get("class") else "csharp"
                    })
        
        except Exception as e:
            logger.error(f"Error extracting manual data: {e}")
        
        return result
    
    @staticmethod
    def prepare_for_vector_store(
        content: str,
        metadata: Dict[str, Any],
        chunk_size: int = 1000
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Prepare content for vector store by chunking if necessary.
        
        Args:
            content: Text content
            metadata: Metadata dictionary
            chunk_size: Maximum chunk size in characters
            
        Returns:
            List of (chunk_text, chunk_metadata) tuples
        """
        # If content is small enough, return as single chunk
        if len(content) <= chunk_size:
            return [(content, metadata)]
        
        # Split into chunks
        chunks = []
        words = content.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            
            if current_length + word_length > chunk_size and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                chunk_metadata = metadata.copy()
                chunk_metadata["chunk_index"] = len(chunks)
                chunks.append((chunk_text, chunk_metadata))
                
                # Start new chunk
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_index"] = len(chunks)
            chunks.append((chunk_text, chunk_metadata))
        
        return chunks
