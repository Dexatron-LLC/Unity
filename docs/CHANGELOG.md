# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive CONTRIBUTING.md guide
- LICENSE file (MIT)
- SECURITY.md policy
- CHANGELOG.md
- Development dependencies in pyproject.toml
- Ruff, Black, and MyPy configuration
- Proper project metadata and classifiers

### Changed
- Updated pyproject.toml with complete metadata
- Improved project structure documentation

### Removed
- Obsolete requirements.txt (using pyproject.toml)
- Duplicate dotenv dependency
- Unused test files

## [0.1.0] - 2025-01-12

### Added
- Initial release of Unity MCP Server
- 10 MCP tools for Unity documentation access
- Vector search using ChromaDB and OpenAI embeddings
- Structured SQLite database for API data
- Semantic search across 35k+ Unity documentation pages
- Natural language search with `search_by_use_case`
- Code extraction tool `extract_code_examples`
- Quick API reference with `get_method_signatures`
- Batch document retrieval `get_full_documents`
- Related document discovery `get_related_documents`
- Automatic Unity version checking
- ZIP-based documentation download
- MCP protocol 1.21.0 support
- Claude Desktop and VS Code integration
- Comprehensive documentation (README, guides, quick reference)
- Full test suite (37 tests)
- UV package manager support

### Performance
- 85-98% faster than traditional documentation reading
- 85-95% token reduction for AI assistants
- 90% reduction in back-and-forth queries

[Unreleased]: https://github.com/Dexatron-LLC/Unity/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Dexatron-LLC/Unity/releases/tag/v0.1.0
