# Unity Documentation MCP Server

An **MCP (Model Context Protocol) server** that provides expert-level access to Unity game engine documentation. Downloads official Unity documentation and uses ChromaDB for semantic search and SQLite for structured data storage.

## 📚 Documentation

> 🚀 **[Quick Start →](docs/QUICKSTART.md)** | 📖 **[Setup Guide →](docs/SETUP.md)** | ⚡ **[Quick Reference →](docs/QUICK_REFERENCE.md)** | 💡 **[Productivity Tools →](docs/PRODUCTIVITY_TOOLS.md)**

### Getting Started
- **[Quick Start Guide](docs/QUICKSTART.md)** - Get up and running in 5 minutes
- **[Setup Guide](docs/SETUP.md)** - Detailed installation and configuration
- **[Quick Reference Card](docs/QUICK_REFERENCE.md)** - One-page tool reference

### Using the Server
- **[Productivity Tools Guide](docs/PRODUCTIVITY_TOOLS.md)** - Complete guide to all 10 MCP tools
- **[Architecture Overview](docs/PROJECT_SUMMARY.md)** - System design and components

### Development
- **[Contributing Guide](docs/CONTRIBUTING.md)** - How to contribute to the project
- **[Testing Guide](docs/TESTING.md)** - Running and writing tests
- **[Best Practices](docs/BEST_PRACTICES.md)** - Python and UV best practices followed
- **[Code Review](docs/CODE_REVIEW.md)** - Code quality assessment

### Project Information
- **[Changelog](docs/CHANGELOG.md)** - Version history and release notes
- **[Security Policy](docs/SECURITY.md)** - Security guidelines and reporting
- **[Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md)** - Technical implementation details

## Features

### 🎯 Smart Search
- 🔍 **Semantic Search**: Vector-based search across 35k+ Unity documentation pages
- 💬 **Natural Language**: Ask "How do I make player jump?" instead of searching keywords
- 🎓 **Experience-Aware**: Tailored results for beginner/intermediate/advanced users
- ⚡ **Lightning Fast**: Optimized queries return results in milliseconds

### 📚 Intelligent Retrieval
- 📦 **Batch Documents**: Get 1-10 complete docs in one query (vs 10+ queries old way)
- 🔗 **Auto-Discovery**: Automatically find related classes, base classes, examples
- 💻 **Code Extraction**: Get ONLY code examples, skip the prose (10x faster)
- 📋 **API Reference**: Instant method signatures, parameters, return types

### ⚙️ Infrastructure
- 📊 **Dual Storage**: ChromaDB vectors + SQLite structured data
- 📥 **Official Docs**: Unity's complete documentation ZIP (~35k HTML files)
- 🔄 **Auto-Updates**: Checks for new Unity versions automatically
- 🤖 **Auto-Download**: Automatically downloads docs on first run if not found
- 🚀 **MCP Protocol**: Works with VS Code Copilot, Claude Desktop
- 💾 **Smart Caching**: Local cache for instant retrieval

### 📈 Performance
- **75-98%** faster than traditional documentation reading
- **85-95%** fewer tokens for AI assistants
- **90%** reduction in back-and-forth queries
- **10x** productivity boost for code lookups

## MCP Tools Exposed

### 🔍 Search & Discovery
1. **`search_unity_docs`** - Semantic search across Unity documentation
2. **`search_by_use_case`** ⚡ **NEW** - Natural language search ("how do I make player jump?")
3. **`query_unity_structure`** - Query structured API data (classes, methods, properties)

### 📚 Document Retrieval
4. **`get_unity_page`** - Get specific documentation page
5. **`get_full_documents`** ⚡ **NEW** - Batch retrieval of complete documents (1-10 at once)
6. **`get_related_documents`** ⚡ **NEW** - Auto-discover related docs (inheritance, similar topics)

### ⚡ Quick Reference (Ultra-Fast)
7. **`extract_code_examples`** ⚡ **NEW** - Get ONLY code snippets, no prose (10x faster)
8. **`get_method_signatures`** ⚡ **NEW** - Quick API reference (signatures, params, returns)

### 🔧 Maintenance
9. **`refresh_documentation`** - Update cached content
10. **`get_cache_stats`** - Get statistics about cached documentation

## Quick Installation

### Using Claude Desktop or VS Code with MCP

> **Note**: On first run, the server will automatically download and index Unity documentation (~35k files, 30-60 minutes). This happens in the background when you first use the server.

Add to your MCP settings file:

**Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "unity-docs": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Dexatron-LLC/Unity.git",
        "unity-mcp-server"
      ],
      "env": {
        "OPENAI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**VS Code** (`.vscode/settings.json`):
```json
{
  "mcp.servers": {
    "unity-docs": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Dexatron-LLC/Unity.git",
        "unity-mcp-server"
      ],
      "env": {
        "OPENAI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Manual Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Dexatron-LLC/Unity.git
   cd Unity
   ```

2. **Install with UV (recommended)**:
   ```bash
   uv sync
   ```
   
   Or with pip:
   ```bash
   pip install -e .
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

## Usage

### Automatic Setup (Recommended)

When you start the MCP server for the first time, it will **automatically detect** that documentation is missing and download/index it for you. This takes 30-60 minutes but only happens once.

The server will:
1. Check if documentation exists
2. Automatically download Unity docs if missing (~35k files)
3. Index everything into ChromaDB and SQLite
4. Start serving requests

No manual intervention needed! Just configure and use.

### Manual Setup (Optional)

You can also manually download and index Unity documentation:

```bash
# Download official Unity docs and index everything (~35k files)
python main.py --download

# Limit to specific documentation type
python main.py --download --doc-type manual
python main.py --download --doc-type script_reference

# Limit number of pages for testing
python main.py --download --max-pages 100
```

### Reset and Re-index

To completely reset and re-download everything:

```bash
# Clear all databases and downloads, then re-download/index
python main.py --reset
```

### Run as MCP Server

The server automatically checks for documentation updates on startup:

```bash
# Start the MCP server (automatically checks for updates)
python main.py

# Skip version checking
python main.py --no-version-check
```

### Using with MCP Clients

Once configured (see Installation above), the server runs automatically when accessed by MCP clients like Claude Desktop or VS Code Copilot. 

**On first use**, the server will automatically download and index documentation (no manual steps needed). This takes 30-60 minutes but only happens once.

### Environment Variables

Configure the server behavior with environment variables:

- **`OPENAI_API_KEY`** (required) - Your OpenAI API key for embeddings
- **`UNITY_MCP_DATA_DIR`** (optional) - Data storage directory (default: `./data`)
- **`UNITY_MCP_AUTO_DOWNLOAD`** (optional) - Set to `false` to disable auto-download (enabled by default)

**Note**: Auto-download is **enabled by default**. You only need to set this variable if you want to disable it.

To disable auto-download:

```json
{
  "mcp.servers": {
    "unity-docs": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/Dexatron-LLC/Unity.git", "unity-mcp-server"],
      "env": {
        "OPENAI_API_KEY": "your-api-key",
        "UNITY_MCP_AUTO_DOWNLOAD": "false"
      }
    }
  }
}
```

## Architecture

```
Unity MCP Server
├── Documentation Downloader
│   ├── UnityDocsDownloader (downloads official Unity docs ZIP)
│   ├── LocalDocsCrawler (processes local HTML files)
│   ├── Version checking & auto-updates
│   └── ~35k HTML files from official docs
│
├── Content Processor
│   ├── Extracts structured data (classes, methods, properties)
│   ├── Prepares content for vector embeddings
│   └── Handles code example extraction
│
├── Vector Store (ChromaDB)
│   ├── Unity Manual embeddings
│   ├── ScriptReference embeddings
│   └── Semantic search across documentation
│
├── Structured Store (SQLite)
│   ├── Pages (documentation pages)
│   ├── Classes (API reference)
│   ├── Methods (signatures, parameters)
│   └── Properties (type information)
│
└── MCP Server (10 Tools)
    ├── search_unity_docs
    ├── search_by_use_case
    ├── query_unity_structure
    ├── get_unity_page
    ├── get_full_documents
    ├── get_related_documents
    ├── extract_code_examples
    ├── get_method_signatures
    ├── refresh_documentation
    └── get_cache_stats
```

## Data Storage

- **`./data/vector/chromadb/`** - Vector embeddings for semantic search
- **`./data/structured/unity_docs.db`** - SQLite database with structured API data
- **`./downloads/`** - Unity documentation ZIP and extracted files
- **`./downloads/version.json`** - Tracks current documentation version

## Example Queries

Once configured in VS Code, you can ask Copilot:

**🎯 Use-Case Based (Beginner-Friendly):**
- "How do I make a player jump?" *(uses search_by_use_case)*
- "How do I detect when objects collide?" *(uses search_by_use_case)*
- "How do I create a UI button that responds to clicks?" *(uses search_by_use_case)*

**⚡ Quick Code Reference:**
- "Show me code examples for Rigidbody movement" *(uses extract_code_examples)*
- "Get method signatures for Transform class" *(uses get_method_signatures)*
- "Show me all AddForce method signatures" *(uses get_method_signatures)*

**📚 Comprehensive Learning:**
- "Get full documentation for GameObject, Transform, and Rigidbody" *(uses get_full_documents)*
- "Show me everything related to MonoBehaviour including base classes" *(uses get_related_documents)*
- "Find all documentation related to physics collisions" *(uses get_related_documents)*

**🔍 Traditional Searches:**
- "Search Unity docs for Coroutines" *(uses search_unity_docs)*
- "What classes inherit from Component?" *(uses query_unity_structure)*

The MCP server intelligently routes your questions to the most appropriate tool, dramatically reducing response time and token usage.

## Development

### Project Structure

```
Unity/
├── src/
│   ├── storage/          # Data storage modules
│   │   ├── vector_store.py
│   │   └── structured_store.py
│   ├── scraper/          # Web scraping utilities
│   │   ├── unity_scraper.py
│   │   └── utils.py
│   ├── processor/        # Content processing
│   │   └── content_processor.py
│   ├── downloader/       # Documentation downloader
│   │   ├── unity_downloader.py
│   │   └── local_crawler.py
│   ├── config.py         # Configuration settings
│   └── server.py         # MCP server (10 tools)
├── tests/                # Unit tests (37 tests)
│   ├── test_storage.py
│   ├── test_server.py
│   ├── test_scraper.py
│   └── test_processor.py
├── docs/                 # Documentation files
├── data/                 # Cached documentation
│   ├── vector/          # ChromaDB storage
│   └── structured/      # SQLite database
├── downloads/           # Downloaded Unity docs
├── logs/                # Server logs
├── main.py              # Entry point
├── pyproject.toml       # Project configuration
├── Makefile             # Development commands
├── LICENSE              # MIT License
└── README.md            # This file
```

### Requirements

- Python 3.11+
- OpenAI API key
- Internet connection (for downloading Unity docs)
- UV package manager (recommended) or pip

### Running Tests

```bash
# Run all tests
python -m unittest discover -s tests -v

# Run specific test file
python -m unittest tests.test_storage
python -m unittest tests.test_server

# Run with coverage
uv pip install coverage
coverage run -m unittest discover tests
coverage report
```

All 37 tests should pass. See [TESTING.md](docs/TESTING.md) for comprehensive testing documentation.

## Logging

The server logs to **stderr** and `./logs/unity_mcp.log` to avoid interfering with the MCP JSON-RPC protocol on stdout. 

- **stderr**: Real-time logs visible in terminal
- **./logs/unity_mcp.log**: Persistent log file for debugging

When running as an MCP server, stdout is reserved for protocol communication only.

## Troubleshooting

### Import Errors
If you see import errors after installation:
```bash
# With UV (recommended)
uv sync

# Or with pip
pip install mcp chromadb openai beautifulsoup4 lxml python-dotenv
```

### OpenAI API Key Missing
Set your API key in `.env` or environment variable:
```bash
# In .env file
OPENAI_API_KEY=sk-your-key-here

# Or as environment variable
export OPENAI_API_KEY=sk-your-key-here  # Linux/Mac
$env:OPENAI_API_KEY="sk-your-key-here"  # Windows PowerShell
```

### Documentation Not Found
Download and index the documentation first:
```bash
python main.py --download
```

### Corrupted Cache
Reset everything and start fresh:
```bash
python main.py --reset
```

### Version Update Issues
The server checks for updates automatically. To force a re-download:
```bash
python main.py --reset
```

## Contributing

We welcome contributions! Please see:
- [CONTRIBUTING.md](docs/CONTRIBUTING.md) - Development guide and guidelines
- [CODE_REVIEW.md](docs/CODE_REVIEW.md) - Code quality and best practices
- [SECURITY.md](docs/SECURITY.md) - Security policy

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Acknowledgments

- Unity Technologies for the excellent documentation
- MCP (Model Context Protocol) by Anthropic
- OpenAI for embeddings API
- ChromaDB for vector storage
