# Unity MCP Server - Project Summary

## Overview

Complete MCP (Model Context Protocol) server implementation for Unity game engine documentation. Provides intelligent search and retrieval of Unity Manual and ScriptReference documentation.

## Architecture

### Components

1. **Storage Layer** (`src/storage/`)
   - **VectorStore** (ChromaDB): Semantic search using OpenAI embeddings
   - **StructuredStore** (SQLite): Relational data for classes, methods, properties

2. **Scraping Layer** (`src/scraper/`)
   - **UnityDocsScraper**: Playwright-based web scraper
   - Handles both Manual and ScriptReference documentation
   - Search functionality and content extraction

3. **Processing Layer** (`src/processor/`)
   - **ContentProcessor**: Extracts structured data from HTML
   - Parses class definitions, methods, properties
   - Chunks content for vector embeddings

4. **Crawler Layer** (`src/crawler/`)
   - **UnityCrawler**: Orchestrates scraping and indexing
   - Handles full documentation crawls
   - Processes and stores in dual databases

5. **MCP Server** (`src/server.py`)
   - Exposes 5 MCP tools
   - Handles tool calls and responses
   - stdio-based communication

## MCP Tools

### 1. search_unity_docs
Semantic search across Unity documentation using vector embeddings.

**Parameters:**
- `query` (required): Search query
- `doc_type` (optional): "manual", "script_reference", or "both"
- `max_results` (optional): Number of results (default: 5)

**Returns:** Ranked search results with content previews

### 2. query_unity_structure
Query structured API data from SQLite database.

**Parameters:**
- `query` (required): Search term
- `query_type` (optional): "class", "method", or "auto"

**Returns:** Structured data with class/method signatures and descriptions

### 3. get_unity_page
Retrieve specific Unity documentation page.

**Parameters:**
- `url` (required): Unity docs URL

**Returns:** Full page content (cached or fetched)

### 4. refresh_documentation
Update cached documentation for a specific page.

**Parameters:**
- `url` (required): Page URL to refresh

**Returns:** Confirmation message

### 5. get_cache_stats
Get statistics about cached documentation.

**Parameters:** None

**Returns:** Counts for pages, classes, methods, properties

## Data Flow

```
Unity Docs (Web)
    ↓
UnityDocsScraper (Playwright)
    ↓
ContentProcessor
    ↓
    ├─→ VectorStore (ChromaDB) → Semantic Search
    └─→ StructuredStore (SQLite) → Structured Queries
```

## Technology Stack

- **Python 3.11+**
- **MCP Protocol**: Model Context Protocol for tool exposure
- **Playwright**: Web scraping and browser automation
- **ChromaDB**: Vector database for semantic search
- **OpenAI API**: Text embeddings (text-embedding-3-small)
- **SQLite**: Relational database for structured data
- **BeautifulSoup**: HTML parsing
- **asyncio**: Async I/O operations

## File Structure

```
Unity/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── server.py              # MCP server implementation
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── vector_store.py    # ChromaDB wrapper
│   │   └── structured_store.py # SQLite wrapper
│   ├── scraper/
│   │   ├── __init__.py
│   │   └── unity_scraper.py   # Playwright scraper
│   ├── processor/
│   │   ├── __init__.py
│   │   └── content_processor.py # Content extraction
│   └── crawler/
│       ├── __init__.py
│       └── unity_crawler.py   # Documentation crawler
├── data/                       # Generated cache (gitignored)
│   ├── chromadb/              # Vector embeddings
│   └── unity_docs.db          # SQLite database
├── main.py                     # Entry point with CLI
├── test_server.py              # Test suite
├── pyproject.toml              # Project dependencies
├── requirements.txt            # Pip requirements
├── .env.example                # Environment template
├── README.md                   # User documentation
├── SETUP.md                    # Setup instructions
└── .gitignore                  # Git ignore rules
```

## Database Schema

### SQLite Tables

1. **pages**: All documentation pages
   - id, url, title, doc_type, content, timestamps

2. **classes**: Unity API classes
   - id, name, namespace, page_id, description, inherits_from, is_static

3. **methods**: Class methods
   - id, class_id, name, return_type, is_static, description, signature

4. **properties**: Class properties
   - id, class_id, name, property_type, is_static, description

5. **parameters**: Method parameters
   - id, method_id, name, param_type, description, position

### ChromaDB Collections

1. **unity_manual**: Manual documentation chunks
2. **unity_script_reference**: ScriptReference chunks

Each document has:
- Embedding vector (1536 dimensions)
- Metadata (URL, title, doc_type, etc.)
- Full text content

## Usage Modes

### 1. Crawler Mode
```bash
python main.py --crawl-all [--doc-type TYPE] [--max-pages N]
```

Indexes Unity documentation into local cache.

### 2. Server Mode (Default)
```bash
python main.py
```

Runs as MCP server, exposing tools to VS Code Copilot.

## Performance Characteristics

- **Initial crawl**: ~30-60 minutes for full documentation
- **Storage**: ~500MB-1GB for fully indexed docs
- **Search latency**: <1s for semantic search (after warm-up)
- **Structured queries**: <100ms
- **Embedding generation**: ~0.5s per query (first time)

## Integration with VS Code

Configure in VS Code settings:

```json
{
  "mcp.servers": {
    "unity-docs": {
      "command": "python",
      "args": ["d:\\Source\\AI\\Agents\\Unity\\main.py"],
      "env": {
        "OPENAI_API_KEY": "your-key"
      }
    }
  }
}
```

## Key Features

✅ **Dual Storage**: Both vector and structured data
✅ **Semantic Search**: AI-powered relevance ranking
✅ **Structured Queries**: Fast class/method lookups
✅ **Efficient Caching**: Local storage for speed
✅ **Async Operations**: Non-blocking I/O
✅ **Configurable**: CLI arguments and environment variables
✅ **Testable**: Comprehensive test suite
✅ **Documented**: README, SETUP guide, inline docs

## Future Enhancements

Potential improvements:
- Multiple Unity version support
- Incremental updates (detect changed pages)
- GraphQL API for advanced queries
- RAG (Retrieval Augmented Generation) mode
- Code example extraction and testing
- Documentation versioning
- Advanced filtering (by Unity version, platform)

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python test_server.py

# Crawl docs (test)
python main.py --crawl-all --max-pages 10

# Full crawl
python main.py --crawl-all

# Run server
python main.py

# Check stats
python -c "from src.storage import VectorStore; import os; print(VectorStore('./data', os.getenv('OPENAI_API_KEY')).get_stats())"
```

## Error Handling

- Graceful failure for missing pages
- Retry logic for transient errors
- Comprehensive logging
- Validation of inputs
- Type hints throughout

## Security Considerations

- API keys in environment variables (not hardcoded)
- .gitignore prevents committing secrets
- Input validation on tool parameters
- Safe file path handling

## License

MIT License (permissive open source)

---

**Status**: ✅ Complete and ready for use

**Author**: AI-assisted development
**Date**: November 12, 2025
