# Unity MCP Server - Setup Guide

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/Dexatron-LLC/Unity.git
cd Unity
```

### 2. Install Dependencies

**Option A: Using UV (Recommended)**
```bash
# Install UV if you don't have it
# See: https://github.com/astral-sh/uv

# Install dependencies
uv sync
```

**Option B: Using pip**
```bash
pip install -e .
```

### 3. Configure Environment

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 4. Download & Index Documentation (Optional)

> **New!** The server now automatically downloads documentation on first use. You can skip this step!

If you prefer to pre-download documentation manually:

```bash
# Download and index all documentation (~35k files, may take 30-60 minutes)
python main.py --download

# Or start with a smaller test
python main.py --download --max-pages 100
```

**Automatic Mode (Recommended)**: Just configure the MCP server and it will download documentation automatically on first use.

### 5. Test the Server

Run the test suite to verify everything works:

```bash
python -m unittest discover -s tests -v
```

All 37 tests should pass.

### 6. Configure MCP in VS Code

#### Option A: Using uvx (Simplest - Recommended)

Add to `.vscode/settings.json`:

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

This will automatically clone and run the server from GitHub.

#### Option B: Local Installation

If you cloned the repository locally:

```json
{
  "mcp.servers": {
    "unity-docs": {
      "command": "python",
      "args": ["path/to/Unity/main.py"],
      "env": {
        "OPENAI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

#### Option C: Claude Desktop

Add to `claude_desktop_config.json`:

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
        "OPENAI_API_KEY": "sk-your-key-here"
      }
    }
  }
}
```

### 7. Restart VS Code

After configuring, restart VS Code for the MCP server to be recognized.

### 8. Use with Copilot

Open any file and ask Copilot Unity-related questions:

```
@unity-docs How do I create a GameObject?
@unity-docs What are Unity Coroutines?
@unity-docs Show me Transform class methods
```

**First Time Use**: The server will automatically download and index documentation (~35k files, 30-60 minutes). This happens in the background and only occurs once.

**After Setup**: All queries are instant, served from local cache!

## Environment Variables

Configure server behavior with environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ Yes | - | Your OpenAI API key for embeddings |
| `UNITY_MCP_DATA_DIR` | ❌ No | `./data` | Directory for storing cached data |
| `UNITY_MCP_AUTO_DOWNLOAD` | ❌ No | `true` | Set to `false` to disable auto-download |

> **Note**: Auto-download is enabled by default. Only set `UNITY_MCP_AUTO_DOWNLOAD=false` if you want to disable it.

**Example - Disable auto-download**:
```json
{
  "env": {
    "OPENAI_API_KEY": "your-key",
    "UNITY_MCP_AUTO_DOWNLOAD": "false"
  }
}
```

## Advanced Configuration

### Download Specific Documentation

```bash
# Only Unity Manual
python main.py --download --doc-type manual

# Only Script Reference
python main.py --download --doc-type script_reference

# Limit pages for testing
python main.py --download --max-pages 200
```

### Version Management

```bash
# Check for updates on startup (default behavior)
python main.py

# Skip version checking
python main.py --no-version-check

# Force complete reset and re-download
python main.py --reset
```

### Custom Data Directory

```bash
python main.py --download --data-dir ./custom_data --download-dir ./custom_downloads
```

### Standalone Server Mode

Run as a standalone server (for development/testing):

```bash
# Start MCP server
python main.py

# The server will log to stderr and ./logs/unity_mcp.log
```

## Troubleshooting

### Issue: "OpenAI API key required"

**Solution**: Ensure `.env` file exists with valid `OPENAI_API_KEY` or set environment variable:
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-key-here"

# Linux/Mac
export OPENAI_API_KEY=sk-your-key-here
```

### Issue: "Cannot find implementation or library stub for module"

**Solution**: Install dependencies:
```bash
# With UV
uv sync

# With pip
pip install -e .
```

### Issue: "Documentation not found"

**Solution**: Download and index documentation first:
```bash
python main.py --download
```

### Issue: MCP server not showing in VS Code

**Solution**: 
1. Ensure UV is installed: `pip install uv`
2. Verify JSON configuration syntax
3. Check VS Code logs: `Developer: Show Logs` → `Window`
4. Restart VS Code
5. For `uvx` mode, ensure git is installed

### Issue: Slow searches

**Solution**: The first search generates embeddings. Subsequent searches are faster. Ensure you've run `--download` to index documentation.

### Issue: Out of memory during download

**Solution**: Process in batches:
```bash
python main.py --download --doc-type manual --max-pages 1000
python main.py --download --doc-type script_reference --max-pages 1000
```

### Issue: Corrupted or stale cache

**Solution**: Reset everything:
```bash
python main.py --reset
```

This will:
1. Clear all databases
2. Delete downloads directory
3. Re-download Unity docs
4. Re-index everything

## Performance Tips

1. **Initial download**: Start with `--max-pages 100` to test
2. **Storage**: Use SSD for faster vector search
3. **Memory**: Expect ~500MB-1GB for fully indexed docs (~35k files)
4. **Network**: Initial download is ~200-300MB ZIP file
5. **Updates**: Server checks for new Unity versions automatically on startup

## Maintenance

### Update Documentation

The server automatically checks for new Unity documentation versions on startup. To force an update:

```bash
# Force complete reset and re-download
python main.py --reset
```

### Check Cache Stats

Use the MCP tool `get_cache_stats` via Copilot:

```
@unity-docs get cache statistics
```

Or check directly:

```python
from src.storage import VectorStore, StructuredStore
import os

data_dir = "./data"
vector_store = VectorStore(data_dir, os.getenv("OPENAI_API_KEY"))
structured_store = StructuredStore(data_dir)

print(vector_store.get_stats())
print(structured_store.get_stats())
```

### Version Tracking

The server tracks Unity documentation versions in `downloads/version.json`. Current version is automatically detected from Unity's official docs page.

## Next Steps

- Explore the MCP tools in VS Code Copilot or Claude Desktop
- Ask Unity-related questions through your MCP client
- Check out [QUICKSTART.md](QUICKSTART.md) for quick reference
- Review [TESTING.md](TESTING.md) for development information

## Support

- **Repository**: https://github.com/Dexatron-LLC/Unity
- **Issues**: Create an issue on GitHub
- **Documentation**: See README.md and PROJECT_SUMMARY.md
- **Testing**: Run `python -m unittest discover -s tests -v`

## What's New

- **ZIP Download**: Now downloads official Unity docs instead of web scraping (much faster!)
- **Auto-Updates**: Automatically checks for new Unity documentation versions
- **Reset Command**: `--reset` flag for complete refresh
- **Version Tracking**: Tracks Unity doc versions in `version.json`
- **Better Logging**: Logs to stderr and file, not stdout (MCP-compliant)
- **No Playwright**: Removed Playwright dependency (faster, simpler setup)
