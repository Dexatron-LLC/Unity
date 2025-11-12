# Unity MCP Server - Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
# Navigate to project directory
cd d:\Source\AI\Agents\Unity

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Configure Environment

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-your-actual-api-key-here
DATA_DIR=./data
```

### 3. Index Documentation

Run the crawler to index Unity documentation:

```bash
# Start with a small test (100 pages)
python main.py --crawl-all --max-pages 100

# Or index everything (may take 30-60 minutes)
python main.py --crawl-all
```

### 4. Test the Server

Run the test script to verify everything works:

```bash
python test_server.py
```

### 5. Configure MCP in VS Code

#### Option A: Workspace Settings

Create/edit `.vscode/settings.json` in your workspace:

```json
{
  "mcp.servers": {
    "unity-docs": {
      "command": "python",
      "args": ["d:\\Source\\AI\\Agents\\Unity\\main.py"],
      "env": {
        "OPENAI_API_KEY": "your-api-key-here",
        "PYTHONPATH": "d:\\Source\\AI\\Agents\\Unity"
      }
    }
  }
}
```

#### Option B: User Settings (Global)

Add to your VS Code user settings:

1. Open Command Palette (`Ctrl+Shift+P`)
2. Type "Preferences: Open User Settings (JSON)"
3. Add the MCP server configuration (same as above)

#### Option C: MCP Configuration File

Create `%USERPROFILE%\.mcp\settings.json`:

```json
{
  "mcpServers": {
    "unity-docs": {
      "command": "python",
      "args": ["d:\\Source\\AI\\Agents\\Unity\\main.py"],
      "env": {
        "OPENAI_API_KEY": "sk-your-key-here"
      }
    }
  }
}
```

### 6. Restart VS Code

After configuring, restart VS Code for the MCP server to be recognized.

### 7. Use with Copilot

Open any file and ask Copilot Unity-related questions:

```
@unity-docs How do I create a GameObject?
@unity-docs What are Unity Coroutines?
@unity-docs Show me Transform class methods
```

## Advanced Configuration

### Crawl Specific Documentation

```bash
# Only Unity Manual
python main.py --crawl-all --doc-type manual

# Only Script Reference
python main.py --crawl-all --doc-type script_reference

# Limit pages
python main.py --crawl-all --doc-type script_reference --max-pages 200
```

### Custom Data Directory

```bash
python main.py --data-dir ./custom_data --crawl-all
```

### Run as Service (Windows)

Create a batch file `start_unity_mcp.bat`:

```batch
@echo off
cd /d d:\Source\AI\Agents\Unity
python main.py
```

Run it in the background or set up as a Windows service.

## Troubleshooting

### Issue: "OpenAI API key required"

**Solution**: Ensure `.env` file exists with valid `OPENAI_API_KEY`

### Issue: "Cannot find implementation or library stub for module"

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### Issue: "Playwright browser not found"

**Solution**: Install browsers:
```bash
playwright install chromium
```

### Issue: MCP server not showing in VS Code

**Solution**: 
1. Check VS Code has MCP extension/support
2. Verify JSON configuration syntax
3. Check VS Code logs: `Developer: Show Logs` → `Window`
4. Restart VS Code

### Issue: Slow searches

**Solution**: The first search generates embeddings. Subsequent searches are faster.

### Issue: Out of memory during crawl

**Solution**: Crawl in batches:
```bash
python main.py --crawl-all --doc-type manual --max-pages 500
python main.py --crawl-all --doc-type script_reference --max-pages 500
```

## Performance Tips

1. **Initial crawl**: Start with `--max-pages 100` to test
2. **Incremental indexing**: Use `refresh_documentation` tool for specific pages
3. **Cache location**: Use SSD for faster vector search
4. **Memory**: Expect ~500MB-1GB for fully indexed docs

## Maintenance

### Update Documentation Cache

```bash
# Re-crawl everything
python main.py --crawl-all

# Or use the refresh_documentation tool via MCP
```

### Clear Cache

```bash
# Delete the data directory
rm -r ./data

# Re-index
python main.py --crawl-all
```

### Check Cache Stats

Use the MCP tool `get_cache_stats` or check directly:

```python
from src.storage import VectorStore, StructuredStore
import os

vector_store = VectorStore("./data", os.getenv("OPENAI_API_KEY"))
print(vector_store.get_stats())
```

## Next Steps

- Explore the MCP tools in VS Code Copilot
- Index additional Unity documentation versions
- Customize the scraper for your needs
- Contribute improvements!

## Support

- Issues: Create an issue on GitHub
- Documentation: See README.md
- Testing: Run `python test_server.py`
