"""Main entry point for Unity MCP Server."""

import logging
import argparse
import asyncio
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables BEFORE importing config
load_dotenv()

from src.server import serve
from src.storage import VectorStore, StructuredStore
from src.scraper.utils import get_page_id
from src.downloader import UnityDocsDownloader
from src.downloader.local_crawler import LocalDocsCrawler
from src.processor import ContentProcessor
from src.config import config

# Configure logging - explicitly use stderr and log file to avoid interfering with MCP protocol on stdout
log_dir = Path("./logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Defaults to stderr (safe for MCP)
        logging.FileHandler(log_dir / "unity_mcp.log")  # Also log to file
    ]
)
logger = logging.getLogger(__name__)


def download_and_index_docs(
    data_dir: str,
    download_dir: str,
    openai_api_key: str = None,
    doc_type: str = "both",
    max_pages: int = None,
    check_version: bool = True,
    use_ollama: bool = False,
    ollama_base_url: str = None,
    ollama_model: str = None
) -> None:
    """Download and index Unity documentation from ZIP.
    
    Args:
        data_dir: Directory for data storage
        download_dir: Directory to download documentation
        openai_api_key: OpenAI API key (required if not using Ollama)
        doc_type: Type of docs to process
        max_pages: Maximum number of pages
        check_version: Check for documentation updates
        use_ollama: Use Ollama for embeddings instead of OpenAI
        ollama_base_url: Ollama server URL
        ollama_model: Ollama embedding model
    """
    logger.info("Starting Unity documentation download and indexing...")
    logger.info(f"Embedding provider: {'Ollama' if use_ollama else 'OpenAI'}")
    
    # Download and extract documentation
    downloader = UnityDocsDownloader(download_dir)
    
    # Check for updates if requested
    if check_version:
        update_available, current, latest = downloader.check_for_updates()
        if update_available:
            if current:
                logger.info(f"New documentation version available: {current} -> {latest}")
                logger.info("Downloading updated documentation...")
                # Clear old databases before updating
                logger.info("Clearing old databases...")
                vector_db = Path(data_dir) / "vector" / "chromadb"
                structured_db = Path(data_dir) / "structured" / "unity_docs.db"
                if vector_db.exists():
                    import shutil
                    shutil.rmtree(vector_db)
                    logger.info(f"Removed vector database: {vector_db}")
                if structured_db.exists():
                    structured_db.unlink()
                    logger.info(f"Removed structured database: {structured_db}")
            else:
                logger.info(f"Downloading documentation version {latest}...")
    
    extract_dir = downloader.download_and_extract()
    
    # Get paths to documentation
    manual_path = downloader.get_manual_path()
    script_path = downloader.get_script_reference_path()
    
    if not manual_path and not script_path:
        logger.error("Could not find documentation in extracted files")
        return
    
    # Initialize storage with appropriate embedding provider
    vector_store = VectorStore(
        data_dir,
        openai_api_key=openai_api_key,
        use_ollama=use_ollama,
        ollama_base_url=ollama_base_url,
        ollama_model=ollama_model
    )
    structured_store = StructuredStore(data_dir)
    processor = ContentProcessor()
    
    # Initialize local crawler with actual documentation root
    docs_root = Path(download_dir).absolute() / "Documentation"
    local_crawler = LocalDocsCrawler(docs_root)
    
    # Collect files to process
    files_to_process = []
    
    if doc_type in ("manual", "both") and manual_path:
        logger.info(f"Finding Manual files in {manual_path}")
        manual_files = local_crawler.get_manual_files(manual_path, max_pages)
        files_to_process.extend(manual_files)
        logger.info(f"Found {len(manual_files)} Manual files")
    
    if doc_type in ("script_reference", "both") and script_path:
        logger.info(f"Finding ScriptReference files in {script_path}")
        script_files = local_crawler.get_script_reference_files(script_path, max_pages)
        files_to_process.extend(script_files)
        logger.info(f"Found {len(script_files)} ScriptReference files")
    
    if max_pages:
        files_to_process = files_to_process[:max_pages]
    
    logger.info(f"Processing {len(files_to_process)} files...")
    
    # Process files
    processed = 0
    errors = 0
    
    for i, file_path in enumerate(files_to_process):
        try:
            if (i + 1) % 10 == 0:
                logger.info(f"Processing {i + 1}/{len(files_to_process)}: {file_path.name}")
            
            # Read file
            page_data = local_crawler.read_html_file(file_path)
            
            # Generate page ID from URL
            import hashlib
            page_id = hashlib.md5(page_data['url'].encode()).hexdigest()
            
            # Store in structured database
            structured_store.add_page(
                page_id=page_id,
                url=page_data['url'],
                title=page_data['title'],
                doc_type=page_data['doc_type'],
                content=page_data['content']
            )
            
            # Process based on doc type
            if page_data['doc_type'] == 'script_reference':
                structured_data = processor.extract_script_reference_data(
                    page_data['html'], page_data['url'], page_data['title']
                )
                
                if structured_data['class_name']:
                    class_id = structured_store.add_class(
                        name=structured_data['class_name'],
                        namespace=structured_data['namespace'],
                        page_id=page_id,
                        description=structured_data['description'],
                        inherits_from=structured_data['inherits_from'],
                        is_static=structured_data['is_static']
                    )
                    
                    for method in structured_data['methods']:
                        structured_store.add_method(
                            class_id=class_id,
                            name=method['name'],
                            return_type=method.get('return_type'),
                            is_static=method.get('is_static', False),
                            description=method.get('description'),
                            signature=method.get('signature')
                        )
                    
                    for prop in structured_data['properties']:
                        structured_store.add_property(
                            class_id=class_id,
                            name=prop['name'],
                            property_type=prop.get('property_type'),
                            is_static=prop.get('is_static', False),
                            description=prop.get('description')
                        )
            
            # Prepare for vector store
            chunks = processor.prepare_for_vector_store(
                content=page_data['content'],
                metadata={
                    'url': page_data['url'],
                    'title': page_data['title'],
                    'doc_type': page_data['doc_type']
                },
                chunk_size=1000
            )
            
            # Add to vector store
            for j, (chunk_text, chunk_metadata) in enumerate(chunks):
                chunk_id = f"{page_id}_chunk_{j}"
                vector_store.add_document(
                    doc_id=chunk_id,
                    url=page_data['url'],
                    title=f"{page_data['title']} (part {j+1})" if len(chunks) > 1 else page_data['title'],
                    content=chunk_text,
                    doc_type=page_data['doc_type'],
                    metadata=chunk_metadata
                )
            
            processed += 1
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            errors += 1
    
    logger.info(f"Indexing complete! Processed: {processed}, Errors: {errors}")
    
    # Print stats
    vector_stats = vector_store.get_stats()
    structured_stats = structured_store.get_stats()
    
    logger.info(f"Vector store: {vector_stats}")
    logger.info(f"Structured store: {structured_stats}")


async def crawl_all_docs(
    data_dir: str,
    openai_api_key: str,
    doc_type: str = "both",
    max_pages: int = None
) -> None:
    """Crawl and index all Unity documentation (DEPRECATED - web scraping removed).
    
    Args:
        data_dir: Directory for data storage
        openai_api_key: OpenAI API key
        doc_type: Type of docs to crawl
        max_pages: Maximum number of pages
    """
    logger.error("Web scraping mode (--crawl-all) has been removed.")
    logger.error("Please use --download mode instead:")
    logger.error("  python main.py --download")
    logger.error("")
    logger.error("The --download mode is faster and more reliable as it downloads")
    logger.error("the official Unity documentation ZIP file instead of web scraping.")
    raise SystemExit(1)


def reset_all(
    data_dir: str,
    download_dir: str,
    openai_api_key: str = None,
    use_ollama: bool = False,
    ollama_base_url: str = None,
    ollama_model: str = None,
    max_pages: int = None
) -> None:
    """Reset everything: clear databases, delete downloads, and re-download/process.
    
    Args:
        data_dir: Directory for data storage
        download_dir: Directory for downloads
        openai_api_key: OpenAI API key (required if not using Ollama)
        use_ollama: Use Ollama for embeddings instead of OpenAI
        ollama_base_url: Ollama server URL
        ollama_model: Ollama embedding model
        max_pages: Maximum number of pages to process (None for all)
    """
    logger.info("=" * 60)
    logger.info("RESET: Starting complete reset...")
    logger.info(f"Embedding provider: {'Ollama' if use_ollama else 'OpenAI'}")
    logger.info("=" * 60)
    
    data_path = Path(data_dir).absolute()
    download_path = Path(download_dir).absolute()
    
    # 1. Clear databases
    logger.info("Step 1/4: Clearing databases...")
    vector_db = data_path / "vector" / "chromadb"
    structured_db = data_path / "structured" / "unity_docs.db"
    
    if vector_db.exists():
        try:
            shutil.rmtree(vector_db)
            logger.info(f"  [OK] Removed vector database: {vector_db}")
        except Exception as e:
            logger.error(f"  [ERROR] Error removing vector database: {e}")
    else:
        logger.info(f"  - Vector database not found (already clean)")
    
    if structured_db.exists():
        try:
            structured_db.unlink()
            logger.info(f"  [OK] Removed structured database: {structured_db}")
        except Exception as e:
            logger.error(f"  [ERROR] Error removing structured database: {e}")
    else:
        logger.info(f"  - Structured database not found (already clean)")
    
    # 2. Delete downloads directory
    logger.info("Step 2/4: Clearing downloads directory...")
    if download_path.exists():
        try:
            logger.info(f"  - Removing {download_path}... (this may take a moment)")
            shutil.rmtree(download_path)
            logger.info(f"  [OK] Removed downloads directory: {download_path}")
        except Exception as e:
            logger.error(f"  [ERROR] Error removing downloads directory: {e}")
    else:
        logger.info(f"  - Downloads directory not found (already clean)")
    
    # Recreate download directory
    download_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"  [OK] Recreated downloads directory")
    
    # 3. Download fresh documentation
    logger.info("Step 3/4: Downloading fresh Unity documentation...")
    downloader = UnityDocsDownloader(str(download_path))
    
    try:
        zip_path = downloader.download(force=True, check_version=False)
        logger.info(f"  [OK] Downloaded: {zip_path}")
    except Exception as e:
        logger.error(f"  [ERROR] Error downloading: {e}")
        raise
    
    # 4. Extract and index
    logger.info("Step 4/4: Extracting and indexing documentation...")
    try:
        docs_dir = downloader.extract(zip_path)
        logger.info(f"  [OK] Extracted to: {docs_dir}")
    except Exception as e:
        logger.error(f"  ✗ Error extracting: {e}")
        raise
    
    # Index all documentation
    logger.info("  - Starting indexing process...")
    vector_store = VectorStore(
        str(data_path),
        openai_api_key=openai_api_key,
        use_ollama=use_ollama,
        ollama_base_url=ollama_base_url,
        ollama_model=ollama_model
    )
    structured_store = StructuredStore(str(data_path))
    processor = ContentProcessor()
    local_crawler = LocalDocsCrawler(str(docs_dir))
    
    # Get all HTML files
    all_files = local_crawler.find_html_files(docs_dir)
    logger.info(f"  - Found {len(all_files)} HTML files total")
    
    # Limit files if max_pages specified
    if max_pages:
        all_files = all_files[:max_pages]
        logger.info(f"  - Limited to {max_pages} files for processing")
    
    processed = 0
    errors = 0
    
    for file_path in all_files:
        try:
            # Read HTML file using local crawler (returns parsed data with content)
            page_data = local_crawler.read_html_file(file_path)
            
            # Generate page ID
            page_id = get_page_id(page_data['url'])
            
            # Store in structured database
            structured_store.add_page(
                page_id=page_id,
                url=page_data['url'],
                title=page_data['title'],
                doc_type=page_data['doc_type'],
                content=page_data['content']
            )
            
            # Process based on doc type for structured extraction
            if page_data['doc_type'] == 'script_reference':
                structured_data = processor.extract_script_reference_data(
                    page_data['html'], page_data['url'], page_data['title']
                )
                
                if structured_data.get('class_name'):
                    structured_store.add_class(
                        name=structured_data['class_name'],
                        namespace=structured_data.get('namespace'),
                        page_id=page_id,
                        description=structured_data.get('description'),
                        inherits_from=structured_data.get('inherits_from'),
                        is_static=structured_data.get('is_static', False)
                    )
            
            # Add to vector store
            metadata = {
                "url": page_data['url'],
                "title": page_data['title'],
                "doc_type": page_data['doc_type']
            }
            chunks = processor.prepare_for_vector_store(page_data['content'], metadata)
            for i, (chunk_text, chunk_meta) in enumerate(chunks):
                doc_id = f"{page_id}_{i}"
                vector_store.add_document(
                    doc_id=doc_id,
                    url=page_data['url'],
                    title=page_data['title'],
                    content=chunk_text,
                    doc_type=page_data['doc_type'],
                    metadata=chunk_meta
                )
            
            processed += 1
            
            if processed % 100 == 0:
                logger.info(f"  - Processed {processed}/{len(all_files)} files...")
                
        except Exception as e:
            errors += 1
            if errors <= 10:  # Only log first 10 errors
                logger.warning(f"  - Error processing {file_path.name}: {e}")
    
    logger.info("=" * 60)
    logger.info(f"RESET COMPLETE!")
    logger.info(f"  Total files: {len(all_files)}")
    logger.info(f"  Processed: {processed}")
    logger.info(f"  Errors: {errors}")
    logger.info("=" * 60)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Unity Documentation MCP Server"
    )
    
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download Unity documentation ZIP and index locally (recommended)"
    )
    
    parser.add_argument(
        "--crawl-all",
        action="store_true",
        help="Crawl and index Unity documentation via web scraping (slower)"
    )
    
    parser.add_argument(
        "--doc-type",
        choices=["manual", "script_reference", "both"],
        default="both",
        help="Type of documentation to process (default: both)"
    )
    
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of pages to process (default: unlimited)"
    )
    
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Directory for data storage (default: ./data, or UNITY_MCP_DATA_DIR env var)"
    )
    
    parser.add_argument(
        "--download-dir",
        type=str,
        default=None,
        help="Directory for downloaded ZIP files (default: <data-dir>/downloads, or UNITY_MCP_DOWNLOAD_DIR env var)"
    )
    
    parser.add_argument(
        "--openai-api-key",
        type=str,
        default=None,
        help="OpenAI API key (can also use OPENAI_API_KEY env var)"
    )
    
    parser.add_argument(
        "--no-version-check",
        action="store_true",
        help="Skip checking for documentation updates"
    )
    
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset everything: clear databases, delete downloads, and re-download/process documentation"
    )
    
    # Ollama configuration arguments
    parser.add_argument(
        "--use-ollama",
        action="store_true",
        help="Use Ollama for embeddings instead of OpenAI (can also set EMBEDDING_PROVIDER=ollama)"
    )
    
    parser.add_argument(
        "--ollama-url",
        type=str,
        default=None,
        help="Ollama server URL (default: http://localhost:11434, can also use OLLAMA_BASE_URL env var)"
    )
    
    parser.add_argument(
        "--ollama-model",
        type=str,
        default=None,
        help="Ollama embedding model (default: nomic-embed-text, can also use OLLAMA_EMBEDDING_MODEL env var)"
    )
    
    args = parser.parse_args()
    
    # Determine embedding provider
    use_ollama = args.use_ollama or config.is_ollama()
    ollama_base_url = args.ollama_url or config.ollama_base_url
    ollama_model = args.ollama_model or config.ollama_embedding_model
    
    # Get OpenAI API key (only required if not using Ollama)
    openai_api_key = args.openai_api_key or os.getenv("OPENAI_API_KEY")
    
    if not use_ollama and not openai_api_key:
        logger.error("OpenAI API key required when not using Ollama.")
        logger.error("Set OPENAI_API_KEY env var, use --openai-api-key, or use --use-ollama for local embeddings.")
        return
    
    # Log embedding provider
    if use_ollama:
        logger.info(f"Using Ollama for embeddings (url: {ollama_base_url}, model: {ollama_model})")
    else:
        logger.info("Using OpenAI for embeddings")
    
    # Get data directory from args, env var, or default
    data_dir_str = args.data_dir or os.getenv("UNITY_MCP_DATA_DIR", "./data")
    data_dir = Path(data_dir_str).absolute()
    data_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Data directory: {data_dir}")
    
    # Get download directory from args, env var, or default (under data dir)
    default_download_dir = str(data_dir / "downloads")
    download_dir_str = args.download_dir or os.getenv("UNITY_MCP_DOWNLOAD_DIR", default_download_dir)
    download_dir = Path(download_dir_str).absolute()
    download_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Download directory: {download_dir}")
    
    if args.reset:
        # Complete reset: clear everything and re-download
        reset_all(
            str(data_dir),
            str(download_dir),
            openai_api_key=openai_api_key,
            use_ollama=use_ollama,
            ollama_base_url=ollama_base_url,
            ollama_model=ollama_model,
            max_pages=args.max_pages
        )
    elif args.download:
        # Download and index from ZIP (recommended)
        download_and_index_docs(
            str(data_dir),
            str(download_dir),
            openai_api_key=openai_api_key,
            doc_type=args.doc_type,
            max_pages=args.max_pages,
            check_version=not args.no_version_check,
            use_ollama=use_ollama,
            ollama_base_url=ollama_base_url,
            ollama_model=ollama_model
        )
    elif args.crawl_all:
        # Web scraping (legacy)
        asyncio.run(crawl_all_docs(
            str(data_dir),
            openai_api_key,
            args.doc_type,
            args.max_pages
        ))
    else:
        # Run MCP server
        logger.info("Starting Unity MCP Server...")
        asyncio.run(serve(
            str(data_dir),
            openai_api_key=openai_api_key,
            check_version=not args.no_version_check,
            use_ollama=use_ollama,
            ollama_base_url=ollama_base_url,
            ollama_model=ollama_model
        ))


if __name__ == "__main__":
    main()
