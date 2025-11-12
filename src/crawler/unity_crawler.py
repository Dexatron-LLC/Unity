"""Documentation crawler for Unity docs."""

import logging
import asyncio
from typing import Optional
from pathlib import Path

from ..scraper import UnityDocsScraper
from ..storage import VectorStore, StructuredStore
from ..processor import ContentProcessor

logger = logging.getLogger(__name__)


class UnityCrawler:
    """Crawls and processes Unity documentation."""
    
    def __init__(
        self,
        vector_store: VectorStore,
        structured_store: StructuredStore,
        scraper: UnityDocsScraper
    ):
        """Initialize the crawler.
        
        Args:
            vector_store: Vector store instance
            structured_store: Structured store instance
            scraper: Unity docs scraper instance
        """
        self.vector_store = vector_store
        self.structured_store = structured_store
        self.scraper = scraper
        self.processor = ContentProcessor()
    
    async def crawl_and_index(
        self,
        doc_type: str = "both",
        max_pages: Optional[int] = None
    ) -> None:
        """Crawl Unity documentation and index it.
        
        Args:
            doc_type: 'manual', 'script_reference', or 'both'
            max_pages: Maximum number of pages to crawl
        """
        logger.info(f"Starting crawl of {doc_type} documentation...")
        
        # Discover all pages
        urls = await self.scraper.crawl_all_pages(doc_type, max_pages)
        
        logger.info(f"Found {len(urls)} pages. Starting indexing...")
        
        # Process each page
        processed = 0
        errors = 0
        
        for i, url in enumerate(urls):
            try:
                logger.info(f"Processing {i+1}/{len(urls)}: {url}")
                
                # Fetch page
                page_data = await self.scraper.fetch_page(url)
                
                # Process and store
                await self._process_and_store_page(page_data)
                
                processed += 1
                
                # Rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                errors += 1
        
        logger.info(f"Crawl complete. Processed: {processed}, Errors: {errors}")
        
        # Print stats
        vector_stats = self.vector_store.get_stats()
        structured_stats = self.structured_store.get_stats()
        
        logger.info(f"Vector store stats: {vector_stats}")
        logger.info(f"Structured store stats: {structured_stats}")
    
    async def _process_and_store_page(self, page_data: dict) -> None:
        """Process a page and store in both databases.
        
        Args:
            page_data: Page data from scraper
        """
        url = page_data["url"]
        title = page_data["title"]
        content = page_data["content"]
        html = page_data["html"]
        doc_type = page_data["doc_type"]
        
        page_id = UnityDocsScraper.get_page_id(url)
        
        # Store in structured database
        self.structured_store.add_page(
            page_id=page_id,
            url=url,
            title=title,
            doc_type=doc_type,
            content=content
        )
        
        # Process based on document type
        if doc_type == "script_reference":
            # Extract structured data
            structured_data = self.processor.extract_script_reference_data(
                html, url, title
            )
            
            # Store class information
            if structured_data["class_name"]:
                class_id = self.structured_store.add_class(
                    name=structured_data["class_name"],
                    namespace=structured_data["namespace"],
                    page_id=page_id,
                    description=structured_data["description"],
                    inherits_from=structured_data["inherits_from"],
                    is_static=structured_data["is_static"]
                )
                
                # Store methods
                for method in structured_data["methods"]:
                    self.structured_store.add_method(
                        class_id=class_id,
                        name=method["name"],
                        return_type=method.get("return_type"),
                        is_static=method.get("is_static", False),
                        description=method.get("description"),
                        signature=method.get("signature")
                    )
                
                # Store properties
                for prop in structured_data["properties"]:
                    self.structured_store.add_property(
                        class_id=class_id,
                        name=prop["name"],
                        property_type=prop.get("property_type"),
                        is_static=prop.get("is_static", False),
                        description=prop.get("description")
                    )
        
        elif doc_type == "manual":
            # Extract manual data (sections, code examples)
            manual_data = self.processor.extract_manual_data(html, url, title)
            # Manual data is already in the content, but we could store sections separately if needed
        
        # Store in vector database
        # Prepare content for embedding
        chunks = self.processor.prepare_for_vector_store(
            content=content,
            metadata={
                "url": url,
                "title": title,
                "doc_type": doc_type
            },
            chunk_size=1000
        )
        
        # Add each chunk to vector store
        for i, (chunk_text, chunk_metadata) in enumerate(chunks):
            chunk_id = f"{page_id}_chunk_{i}"
            self.vector_store.add_document(
                doc_id=chunk_id,
                url=url,
                title=f"{title} (part {i+1})" if len(chunks) > 1 else title,
                content=chunk_text,
                doc_type=doc_type,
                metadata=chunk_metadata
            )
    
    async def index_single_page(self, url: str) -> None:
        """Index a single page.
        
        Args:
            url: Page URL to index
        """
        logger.info(f"Indexing single page: {url}")
        
        try:
            page_data = await self.scraper.fetch_page(url)
            await self._process_and_store_page(page_data)
            logger.info(f"Successfully indexed: {url}")
        except Exception as e:
            logger.error(f"Error indexing {url}: {e}")
            raise
