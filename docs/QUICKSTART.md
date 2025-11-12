# Quick Start Guide

## Prerequisites
- Python 3.11+
- OpenAI API key

## 5-Minute Setup

### 1. Install
```bash
cd d:\Source\AI\Agents\Unity
uv sync
# or: pip install -e .
```

### 2. Configure
```bash
# Create .env file
echo OPENAI_API_KEY=your-key-here > .env
```

### 3. Test (Optional)
```bash
# Quick test with 10 pages
python main.py --download --max-pages 10
```

### 4. Index Documentation
```bash
# Full download and index (30-60 minutes)
python main.py --download
```

### 5. Configure VS Code

Add to `.vscode/settings.json`:
```json
{
  "mcp.servers": {
    "unity-docs": {
      "command": "python",
      "args": ["d:\\Source\\AI\\Agents\\Unity\\main.py"],
      "env": {
        "OPENAI_API_KEY": "your-key-here"
      }
    }
  }
}
```

### 6. Use It!

In VS Code Copilot:
```
@unity-docs How do I create a GameObject?
```

## That's It!

For detailed setup, see [SETUP.md](SETUP.md)

For architecture details, see [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
