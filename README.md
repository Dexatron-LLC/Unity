# Unity Documentation MCP Server

An **MCP (Model Context Protocol) server** that provides expert-level access to Unity game engine documentation. This server uses Playwright for web scraping, ChromaDB for semantic search, and SQLite for structured data storage.

> 🚀 **[Quick Start Guide →](QUICKSTART.md)** | 📖 **[Detailed Setup →](SETUP.md)** | 🏗️ **[Architecture →](PROJECT_SUMMARY.md)** | 🧪 **[Testing Guide →](TESTING.md)**

## Features

- 🔍 **Semantic Search**: Vector-based search across Unity Manual and ScriptReference
- 📊 **Structured Data**: SQLite database with Unity classes, methods, and properties
- 🌐 **Web Scraping**: Playwright-based scraper for Unity documentation
- 💾 **Dual Storage**: Both vector embeddings and structured data
- 🚀 **MCP Compatible**: Works with VS Code Copilot and other MCP clients
- 📦 **Efficient Caching**: Local cache for fast retrieval

## MCP Tools Exposed

1. **`search_unity_docs`** - Semantic search across Unity documentation
2. **`query_unity_structure`** - Query structured API data (classes, methods, properties)
3. **`get_unity_page`** - Get specific documentation page
4. **`refresh_documentation`** - Update cached content
5. **`get_cache_stats`** - Get statistics about cached documentation

## Installation

1. **Clone the repository**:
   ```bash
   cd d:\Source\AI\Agents\Unity
   ```

2. **Install dependencies**:
   ```bash
   pip install -e .
   ```

3. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

## Usage

### 1. Crawl Documentation (First Time Setup)

Before using the MCP server, crawl and index the Unity documentation:

```bash
# Crawl all documentation (this may take a while)
python main.py --crawl-all

# Crawl only Manual documentation
python main.py --crawl-all --doc-type manual

# Crawl only ScriptReference
python main.py --crawl-all --doc-type script_reference

# Limit number of pages
python main.py --crawl-all --max-pages 100
```

### 2. Run as MCP Server

Once documentation is indexed, start the MCP server:

```bash
python main.py
```

### 3. Configure in VS Code

Add to your VS Code settings (`.vscode/settings.json` or user settings):

```json
{
  "mcp.servers": {
    "unity-docs": {
      "command": "python",
      "args": ["d:\\Source\\AI\\Agents\\Unity\\main.py"],
      "env": {
        "OPENAI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Or use the MCP settings file (`~/.mcp/settings.json`):

```json
{
  "mcpServers": {
    "unity-docs": {
      "command": "python",
      "args": ["d:\\Source\\AI\\Agents\\Unity\\main.py"],
      "env": {
        "OPENAI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Architecture

```
Unity MCP Server
├── Vector Store (ChromaDB)
│   ├── Unity Manual embeddings
│   └── ScriptReference embeddings
│
├── Structured Store (SQLite)
│   ├── Pages
│   ├── Classes
│   ├── Methods
│   └── Properties
│
├── Web Scraper (Playwright)
│   ├── Search functionality
│   ├── Page fetching
│   └── Content extraction
│
└── MCP Server
    ├── search_unity_docs
    ├── query_unity_structure
    ├── get_unity_page
    ├── refresh_documentation
    └── get_cache_stats
```

## Data Storage

All data is stored in the `./data` directory:

- `chromadb/` - Vector embeddings
- `unity_docs.db` - SQLite database with structured data

## Example Queries

Once configured in VS Code, you can ask Copilot:

- "How do I create a GameObject in Unity?"
- "Show me the Transform class methods"
- "What is Unity's Event System?"
- "How do I use Unity's new Input System?"
- "Explain Unity Coroutines"

The MCP server will use semantic search and structured queries to provide accurate, documentation-based answers.

## Development

### Project Structure

```
Unity/
├── src/
│   ├── storage/          # Data storage modules
│   │   ├── vector_store.py
│   │   └── structured_store.py
│   ├── scraper/          # Web scraping
│   │   └── unity_scraper.py
│   ├── processor/        # Content processing
│   │   └── content_processor.py
│   ├── crawler/          # Documentation crawler
│   │   └── unity_crawler.py
│   └── server.py         # MCP server
├── data/                 # Cached documentation
├── main.py              # Entry point
├── pyproject.toml       # Dependencies
└── README.md
```

### Requirements

- Python 3.11+
- OpenAI API key
- Internet connection (for initial crawl)

### Running Tests

```bash
# Run all tests
python run_tests.py

# Run with coverage
pip install coverage
coverage run -m unittest discover tests
coverage report

# Run specific test file
python -m unittest tests.test_storage
```

See [TESTING.md](TESTING.md) for comprehensive testing documentation.

## Logging

The server logs to **stderr** and `./logs/unity_mcp.log` to avoid interfering with the MCP JSON-RPC protocol on stdout. 

- **stderr**: Real-time logs visible in terminal
- **./logs/unity_mcp.log**: Persistent log file for debugging

When running as an MCP server, stdout is reserved for protocol communication only.

## Troubleshooting

### Import Errors
If you see import errors after installation, install dependencies:
```bash
pip install mcp playwright chromadb openai beautifulsoup4 lxml aiohttp python-dotenv
```

### Playwright Browser Not Found
Install Playwright browsers:
```bash
playwright install chromium
```

### OpenAI API Key Missing
Set your API key in `.env` or pass it via command line:
```bash
python main.py --openai-api-key your-key-here
```

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Acknowledgments

- Unity Technologies for the excellent documentation
- MCP (Model Context Protocol) by Anthropic
- OpenAI for embeddings API
- ChromaDB for vector storage
