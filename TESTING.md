# Unity MCP Server - Testing Guide

## Overview

Comprehensive unit tests for all components of the Unity MCP Server, including storage, scraping, processing, crawling, and MCP server functionality.

## Test Structure

```
tests/
├── __init__.py
├── test_storage.py         # Vector and structured store tests
├── test_scraper.py         # Web scraping tests
├── test_processor.py       # Content processing tests
├── test_crawler.py         # Crawling orchestration tests
├── test_server.py          # MCP server tests
└── test_integration.py     # End-to-end integration tests
```

## Running Tests

### Run All Tests

```bash
# Using the test runner
python run_tests.py

# Using unittest directly
python -m unittest discover tests

# Using pytest (if installed)
pytest tests/
```

### Run Specific Test Files

```bash
# Test storage only
python -m unittest tests.test_storage

# Test scraper only
python -m unittest tests.test_scraper

# Test integration only
python -m unittest tests.test_integration
```

### Run Specific Test Classes

```bash
# Test VectorStore only
python -m unittest tests.test_storage.TestVectorStore

# Test StructuredStore only
python -m unittest tests.test_storage.TestStructuredStore
```

### Run Specific Test Methods

```bash
# Test single method
python -m unittest tests.test_storage.TestStructuredStore.test_add_and_get_page
```

### Run with Coverage

```bash
# Install coverage first
pip install coverage

# Run with coverage
coverage run -m unittest discover tests
coverage report
coverage html  # Generate HTML report
```

## Test Coverage

### Storage Tests (`test_storage.py`)

**TestStructuredStore:**
- ✅ `test_add_and_get_page` - Adding and retrieving pages
- ✅ `test_get_nonexistent_page` - Handling missing pages
- ✅ `test_get_page_by_url` - URL-based page lookup
- ✅ `test_add_class` - Adding Unity classes
- ✅ `test_get_class` - Retrieving classes with methods/properties
- ✅ `test_search_classes` - Searching for classes
- ✅ `test_search_methods` - Searching for methods
- ✅ `test_get_stats` - Database statistics

**TestVectorStore:**
- ✅ `test_initialization` - Vector store setup
- ✅ `test_add_document` - Adding documents with embeddings
- ✅ `test_search` - Semantic search functionality
- ✅ `test_get_stats` - Vector store statistics

### Scraper Tests (`test_scraper.py`)

**TestUnityDocsScraper:**
- ✅ `test_get_page_id` - URL to ID conversion
- ✅ `test_get_doc_type` - Document type detection
- ✅ `test_is_unity_docs_url_manual` - Manual URL validation
- ✅ `test_is_unity_docs_url_script_reference` - Script URL validation
- ✅ `test_is_unity_docs_url_both` - Combined URL validation
- ✅ `test_start_and_close` - Browser lifecycle
- ✅ `test_fetch_page` - Page fetching
- ✅ `test_context_manager` - Async context manager

**TestScraperAsync:**
- ✅ `test_fetch_page_async` - Async page operations

### Processor Tests (`test_processor.py`)

**TestContentProcessor:**
- ✅ `test_extract_script_reference_data_basic` - Basic extraction
- ✅ `test_extract_script_reference_with_namespace` - Namespace parsing
- ✅ `test_extract_methods` - Method extraction
- ✅ `test_extract_properties` - Property extraction
- ✅ `test_extract_manual_data` - Manual page processing
- ✅ `test_prepare_for_vector_store_small_content` - Small content
- ✅ `test_prepare_for_vector_store_large_content` - Content chunking
- ✅ `test_extract_static_class` - Static class detection
- ✅ `test_extract_inheritance` - Inheritance parsing
- ✅ `test_extract_constructors` - Constructor extraction

### Crawler Tests (`test_crawler.py`)

**TestUnityCrawler:**
- ✅ `test_process_and_store_page_script_reference` - Script page processing
- ✅ `test_process_and_store_page_manual` - Manual page processing
- ✅ `test_index_single_page` - Single page indexing
- ✅ `test_crawl_and_index` - Full crawl workflow

### Server Tests (`test_server.py`)

**TestUnityMCPServer:**
- ✅ `test_initialization` - Server setup
- ✅ `test_search_unity_docs` - Search tool
- ✅ `test_query_unity_structure` - Structured query tool
- ✅ `test_get_unity_page_cached` - Cached page retrieval
- ✅ `test_get_cache_stats` - Statistics tool
- ✅ `test_search_no_results` - Empty result handling

### Integration Tests (`test_integration.py`)

**TestIntegration:**
- ✅ `test_structured_store_full_workflow` - Complete SQLite workflow
- ✅ `test_vector_store_workflow` - Complete vector workflow
- ✅ `test_content_processor_pipeline` - Full HTML processing
- ✅ `test_chunking_large_content` - Large document handling

**TestEndToEndScenarios:**
- ✅ `test_page_id_consistency` - ID generation consistency
- ✅ `test_doc_type_detection` - Type detection accuracy
- ✅ `test_database_stats` - Statistics accuracy

## Test Data Locations

Tests use temporary directories that are cleaned up after each test:
- Vector data: `<temp_dir>/vector/chromadb/`
- Structured data: `<temp_dir>/structured/unity_docs.db`

## Mocking Strategy

### External Dependencies Mocked

1. **OpenAI API** - All embedding calls are mocked
2. **ChromaDB** - Collections and persistence mocked
3. **Playwright** - Browser and page operations mocked
4. **Network requests** - No actual HTTP calls in unit tests

### Why Mock?

- **Speed**: Tests run in seconds, not minutes
- **Reliability**: No network dependencies
- **Cost**: No OpenAI API charges during testing
- **Isolation**: Each test is independent

## Writing New Tests

### Template for New Test

```python
import unittest
from unittest.mock import Mock, patch

class TestNewFeature(unittest.TestCase):
    """Test cases for new feature."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Initialize test data
        pass
    
    def tearDown(self):
        """Clean up after tests."""
        # Clean up resources
        pass
    
    def test_feature_works(self):
        """Test that feature works correctly."""
        # Arrange
        expected = "result"
        
        # Act
        actual = my_function()
        
        # Assert
        self.assertEqual(actual, expected)
```

### Best Practices

1. **One assertion per test** (when possible)
2. **Use descriptive test names** (`test_add_page_with_valid_data`)
3. **Follow AAA pattern** (Arrange, Act, Assert)
4. **Clean up resources** in `tearDown()`
5. **Use temporary directories** for file operations
6. **Mock external services** to avoid dependencies

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python run_tests.py
```

## Troubleshooting

### Import Errors

If you see import errors, ensure the project is in your Python path:

```bash
# Add project to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:d:/Source/AI/Agents/Unity"

# Or run from project root
cd d:\Source\AI\Agents\Unity
python -m unittest discover tests
```

### Async Test Issues

For async tests, use `unittest.IsolatedAsyncioTestCase`:

```python
class TestAsync(unittest.IsolatedAsyncioTestCase):
    async def test_async_function(self):
        result = await my_async_function()
        self.assertIsNotNone(result)
```

### Mock Not Working

Ensure you're mocking the right import path:

```python
# Mock where it's used, not where it's defined
@patch('src.storage.vector_store.OpenAI')  # Correct
# Not: @patch('openai.OpenAI')
```

## Test Statistics

- **Total Test Files**: 6
- **Total Test Classes**: 11
- **Total Test Methods**: 40+
- **Estimated Run Time**: 5-10 seconds
- **Code Coverage Target**: >80%

## Future Test Additions

Potential areas for additional testing:
- [ ] Performance/load tests
- [ ] Network failure scenarios
- [ ] Database corruption recovery
- [ ] Concurrent access tests
- [ ] Memory leak tests
- [ ] Rate limiting tests

## Running Tests in Development

### Quick Development Loop

```bash
# Watch mode (requires pytest-watch)
pip install pytest-watch
ptw tests/

# Run specific test during development
python -m unittest tests.test_storage.TestStructuredStore.test_add_and_get_page -v
```

### Pre-commit Testing

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
python run_tests.py
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

## Test Results Format

```
test_add_and_get_page (tests.test_storage.TestStructuredStore) ... ok
test_add_class (tests.test_storage.TestStructuredStore) ... ok
test_get_class (tests.test_storage.TestStructuredStore) ... ok
test_search_classes (tests.test_storage.TestStructuredStore) ... ok
...

----------------------------------------------------------------------
Ran 45 tests in 8.234s

OK
```

---

**Note**: All tests are designed to run without external dependencies. The actual Unity documentation is not accessed during testing.
