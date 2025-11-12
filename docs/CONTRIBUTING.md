# Contributing to Unity MCP Server

Thank you for your interest in contributing to Unity MCP Server! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites
- Python 3.11 or higher
- [UV package manager](https://github.com/astral-sh/uv)
- Git
- OpenAI API key

### Initial Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Dexatron-LLC/Unity.git
   cd Unity
   ```

2. **Install UV (if not already installed):**
   ```bash
   # On Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Set up the environment:**
   ```bash
   # Install dependencies
   uv sync
   
   # Install dev dependencies
   uv sync --extra dev
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_server.py -v

# Run specific test
uv run pytest tests/test_server.py::TestUnityMCPServer::test_search_unity_docs
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Format code with black
uv run black src tests

# Lint with ruff
uv run ruff check src tests

# Type checking with mypy
uv run mypy src

# Run all quality checks
uv run black src tests && uv run ruff check src tests && uv run mypy src
```

### Running the Server

```bash
# Download and index documentation (first time)
uv run python main.py --download

# Run the MCP server
uv run python main.py

# Run with debugging
uv run python main.py --log-level DEBUG
```

## Code Style Guidelines

### Python Style
- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting (line length: 100)
- Use [Ruff](https://docs.astral.sh/ruff/) for linting
- Use type hints for all function signatures
- Write docstrings for all public functions and classes (Google style)

### Example:
```python
from typing import Optional

def process_document(doc_id: str, content: str, max_length: Optional[int] = None) -> dict:
    """Process a Unity documentation page.
    
    Args:
        doc_id: Unique document identifier
        content: Document content to process
        max_length: Maximum content length (optional)
        
    Returns:
        Dictionary containing processed document data
        
    Raises:
        ValueError: If doc_id is empty or content is invalid
    """
    if not doc_id:
        raise ValueError("doc_id cannot be empty")
    
    # Implementation...
    return {"id": doc_id, "processed": True}
```

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add code extraction tool for productivity
fix: resolve import error in vector store
docs: update README with new tools
test: add tests for method signatures
refactor: improve structured store query performance
chore: update dependencies
```

### Branch Naming
- `feat/feature-name` - New features
- `fix/bug-description` - Bug fixes
- `docs/what-changed` - Documentation updates
- `refactor/what-changed` - Code refactoring
- `test/what-added` - Test additions

## Making Changes

### 1. Create a Branch
```bash
git checkout -b feat/your-feature-name
```

### 2. Make Your Changes
- Write clean, documented code
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes
```bash
# Run tests
uv run pytest

# Check code quality
uv run black src tests
uv run ruff check src tests
uv run mypy src
```

### 4. Commit Your Changes
```bash
git add .
git commit -m "feat: add your feature description"
```

### 5. Push and Create PR
```bash
git push origin feat/your-feature-name
```

Then create a Pull Request on GitHub.

## Pull Request Guidelines

### PR Checklist
- [ ] Code follows project style guidelines
- [ ] All tests pass (`uv run pytest`)
- [ ] New tests added for new functionality
- [ ] Documentation updated (README, docstrings, etc.)
- [ ] No breaking changes (or clearly documented)
- [ ] Commit messages follow Conventional Commits
- [ ] PR description clearly explains changes

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Tests pass
- [ ] Code formatted with black
- [ ] Linting passes
- [ ] Documentation updated
```

## Project Structure

```
Unity/
├── src/
│   ├── server.py           # MCP server implementation
│   ├── storage/            # Vector and structured storage
│   ├── processor/          # Content processing
│   ├── downloader/         # Documentation downloading
│   └── scraper/            # Utility functions
├── tests/                  # Test suite
├── docs/                   # Documentation
├── main.py                 # CLI entry point
├── pyproject.toml         # Project configuration
└── README.md              # Main documentation
```

## Adding New MCP Tools

When adding a new MCP tool:

1. **Define the tool in `src/server.py`:**
   ```python
   Tool(
       name="your_tool_name",
       description="Clear description of what it does",
       inputSchema={...}
   )
   ```

2. **Implement the handler:**
   ```python
   async def _your_tool_name(self, args: dict) -> Sequence[TextContent]:
       """Handle your tool."""
       # Implementation
       return [TextContent(type="text", text="result")]
   ```

3. **Add to dispatcher:**
   ```python
   elif name == "your_tool_name":
       return await self._your_tool_name(arguments)
   ```

4. **Write tests:**
   ```python
   def test_your_tool_name(self):
       """Test your tool."""
       # Test implementation
   ```

5. **Update documentation:**
   - Add to README.md
   - Add to QUICK_REFERENCE.md
   - Add to PRODUCTIVITY_TOOLS.md if applicable

## Getting Help

- **Documentation:** Check README.md and other guides
- **Issues:** Search existing issues or create a new one
- **Discussions:** Use GitHub Discussions for questions
- **Discord:** [Join our Discord](https://discord.gg/your-server) (if available)

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to Unity MCP Server! 🚀
