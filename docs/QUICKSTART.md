# Quick Start Guide

## Prerequisites
- Python 3.11+
- OpenAI API key

## 2-Minute Setup (Automatic)

> **New!** The server now automatically downloads documentation on first use. No manual setup required!

### 1. Install
```bash
# Using uvx (recommended - no local installation needed)
uvx --from "git+https://github.com/Dexatron-LLC/Unity.git" unity-mcp-server

# Or clone and install locally
cd d:\Source\AI\Agents\Unity
uv sync
# or: pip install -e .
```

### 2. Configure VS Code

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
        "OPENAI_API_KEY": "your-key-here"
      }
    }
  }
}
```

**For local development**:
```json
{
  "mcp.servers": {
    "unity-docs": {
      "command": "uv",
      "args": ["run", "--directory", "d:\\Source\\AI\\Agents\\Unity", "python", "main.py"],
      "env": {
        "OPENAI_API_KEY": "your-key-here"
      }
    }
  }
}
```

### 3. Use It!

In VS Code Copilot:
```
@unity-docs How do I create a GameObject?
```

**First time**: The server will automatically download and index ~35k Unity docs (takes 30-60 minutes, happens in background).

**After that**: Instant responses from cached documentation!

## Manual Setup (Optional)

If you prefer to pre-download documentation:

```bash
# Full download and index (30-60 minutes)
python main.py --download

# Quick test with 10 pages
python main.py --download --max-pages 10
```

## That's It!

For detailed setup, see [SETUP.md](SETUP.md)

For architecture details, see [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
