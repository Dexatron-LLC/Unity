"""MCP server for Unity documentation."""

import os
import logging
import asyncio
from typing import Any, Sequence
from pathlib import Path

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

from .storage import VectorStore, StructuredStore
from .scraper.utils import get_page_id, get_doc_type

logger = logging.getLogger(__name__)


class UnityMCPServer:
    """MCP server for Unity documentation search and retrieval."""
    
    def __init__(self, data_dir: str, openai_api_key: str):
        """Initialize the MCP server.
        
        Args:
            data_dir: Directory for data storage
            openai_api_key: OpenAI API key
        """
        self.data_dir = Path(data_dir).absolute()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize stores
        self.vector_store = VectorStore(str(self.data_dir), openai_api_key)
        self.structured_store = StructuredStore(str(self.data_dir))
        
        # Initialize MCP server
        self.server = Server("unity-docs-expert")
        
        # Register handlers
        self._register_handlers()
        
        logger.info("Unity MCP Server initialized")
    
    def _register_handlers(self) -> None:
        """Register MCP server handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available MCP tools."""
            return [
                Tool(
                    name="search_unity_docs",
                    description=(
                        "Search Unity documentation using semantic search. "
                        "Searches both Manual and ScriptReference documentation. "
                        "Returns relevant documentation pages with content."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for Unity documentation"
                            },
                            "doc_type": {
                                "type": "string",
                                "enum": ["manual", "script_reference", "both"],
                                "description": "Type of documentation to search",
                                "default": "both"
                            },
                            "max_results": {
                                "type": "number",
                                "description": "Maximum number of results to return",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="query_unity_structure",
                    description=(
                        "Query structured Unity API data. Search for classes, methods, "
                        "and properties with their signatures and descriptions."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (class name, method name, etc.)"
                            },
                            "query_type": {
                                "type": "string",
                                "enum": ["class", "method", "auto"],
                                "description": "Type of query",
                                "default": "auto"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_unity_page",
                    description=(
                        "Get a specific Unity documentation page by URL. "
                        "Fetches from cache if available, otherwise retrieves from web."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL of the Unity documentation page"
                            }
                        },
                        "required": ["url"]
                    }
                ),
                Tool(
                    name="refresh_documentation",
                    description=(
                        "Refresh cached documentation by fetching and re-indexing a page. "
                        "Use this to update outdated cached content."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL of the page to refresh"
                            }
                        },
                        "required": ["url"]
                    }
                ),
                Tool(
                    name="get_cache_stats",
                    description=(
                        "Get statistics about the cached documentation including "
                        "number of pages, classes, methods, etc."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_full_documents",
                    description=(
                        "Get complete content of multiple Unity documentation pages at once. "
                        "Much more efficient than repeated individual page requests. "
                        "Performs a search and returns full document content for all results."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query to find relevant documents"
                            },
                            "max_documents": {
                                "type": "number",
                                "description": "Maximum number of full documents to return (1-10)",
                                "default": 3,
                                "minimum": 1,
                                "maximum": 10
                            },
                            "doc_type": {
                                "type": "string",
                                "enum": ["manual", "script_reference", "both"],
                                "description": "Type of documentation to search",
                                "default": "both"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_related_documents",
                    description=(
                        "Get documents related to a Unity class or topic. "
                        "Automatically finds base classes, derived classes, related components, "
                        "and contextually similar pages. Great for comprehensive understanding."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "class_name": {
                                "type": "string",
                                "description": "Unity class name to find related documents for"
                            },
                            "topic": {
                                "type": "string",
                                "description": "Topic to find related documents for (alternative to class_name)"
                            },
                            "include_inheritance": {
                                "type": "boolean",
                                "description": "Include base and derived classes",
                                "default": true
                            },
                            "max_related": {
                                "type": "number",
                                "description": "Maximum number of related documents (1-5)",
                                "default": 3,
                                "minimum": 1,
                                "maximum": 5
                            }
                        }
                    }
                ),
                Tool(
                    name="extract_code_examples",
                    description=(
                        "Extract ONLY code examples from Unity documentation. "
                        "Returns pure code snippets without surrounding text. "
                        "Perfect for quick reference and reducing token usage. "
                        "10x faster than reading full documentation."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query to find relevant code examples"
                            },
                            "language": {
                                "type": "string",
                                "enum": ["csharp", "javascript", "any"],
                                "description": "Programming language filter",
                                "default": "any"
                            },
                            "max_examples": {
                                "type": "number",
                                "description": "Maximum number of code examples (1-10)",
                                "default": 5,
                                "minimum": 1,
                                "maximum": 10
                            },
                            "doc_type": {
                                "type": "string",
                                "enum": ["manual", "script_reference", "both"],
                                "description": "Documentation type to search",
                                "default": "both"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_method_signatures",
                    description=(
                        "Get quick API reference with method signatures, parameters, and return types. "
                        "No documentation prose - just the API facts you need. "
                        "Extremely fast and minimal token usage. Perfect for quick lookups."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "class_name": {
                                "type": "string",
                                "description": "Unity class name to get methods for (e.g., 'Transform', 'Rigidbody')"
                            },
                            "method_name": {
                                "type": "string",
                                "description": "Specific method name to search for (searches across all classes)"
                            },
                            "include_properties": {
                                "type": "boolean",
                                "description": "Include property signatures as well",
                                "default": true
                            },
                            "static_only": {
                                "type": "boolean",
                                "description": "Return only static methods/properties",
                                "default": false
                            }
                        }
                    }
                ),
                Tool(
                    name="search_by_use_case",
                    description=(
                        "Search Unity docs by natural language use case or goal. "
                        "Ask 'How do I make a player jump?' instead of searching for specific APIs. "
                        "Beginner-friendly, intention-based search that understands what you're trying to accomplish. "
                        "Returns relevant documentation with context for your specific goal."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "use_case": {
                                "type": "string",
                                "description": "Describe what you want to accomplish (e.g., 'make player jump', 'detect collisions', 'create UI button')"
                            },
                            "experience_level": {
                                "type": "string",
                                "enum": ["beginner", "intermediate", "advanced"],
                                "description": "Your Unity experience level for tailored results",
                                "default": "intermediate"
                            },
                            "max_results": {
                                "type": "number",
                                "description": "Maximum number of relevant solutions (1-5)",
                                "default": 3,
                                "minimum": 1,
                                "maximum": 5
                            },
                            "prefer_code": {
                                "type": "boolean",
                                "description": "Prefer results with code examples",
                                "default": true
                            }
                        },
                        "required": ["use_case"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
            """Handle tool calls."""
            try:
                if name == "search_unity_docs":
                    return await self._search_unity_docs(arguments)
                elif name == "query_unity_structure":
                    return await self._query_unity_structure(arguments)
                elif name == "get_unity_page":
                    return await self._get_unity_page(arguments)
                elif name == "refresh_documentation":
                    return await self._refresh_documentation(arguments)
                elif name == "get_cache_stats":
                    return await self._get_cache_stats(arguments)
                elif name == "get_full_documents":
                    return await self._get_full_documents(arguments)
                elif name == "get_related_documents":
                    return await self._get_related_documents(arguments)
                elif name == "extract_code_examples":
                    return await self._extract_code_examples(arguments)
                elif name == "get_method_signatures":
                    return await self._get_method_signatures(arguments)
                elif name == "search_by_use_case":
                    return await self._search_by_use_case(arguments)
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )]
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]
    
    async def _search_unity_docs(self, args: dict) -> Sequence[TextContent]:
        """Search Unity documentation."""
        query = args["query"]
        doc_type = args.get("doc_type", "both")
        max_results = args.get("max_results", 5)
        
        # Map doc_type for vector store
        vector_doc_type = None
        if doc_type == "manual":
            vector_doc_type = "manual"
        elif doc_type == "script_reference":
            vector_doc_type = "script_reference"
        
        # Search vector store
        results = self.vector_store.search(
            query=query,
            doc_type=vector_doc_type,
            n_results=max_results
        )
        
        if not results:
            return [TextContent(
                type="text",
                text=f"No results found for query: {query}"
            )]
        
        # Format results
        response_parts = [f"Found {len(results)} results for '{query}':\n"]
        
        for i, result in enumerate(results):
            metadata = result["metadata"]
            content = result["content"][:500]  # Truncate for preview
            
            response_parts.append(f"\n{i+1}. **{metadata['title']}**")
            response_parts.append(f"   URL: {metadata['url']}")
            response_parts.append(f"   Type: {metadata['doc_type']}")
            response_parts.append(f"   Preview: {content}...")
            response_parts.append("")
        
        return [TextContent(
            type="text",
            text="\n".join(response_parts)
        )]
    
    async def _query_unity_structure(self, args: dict) -> Sequence[TextContent]:
        """Query structured Unity data."""
        query = args["query"]
        query_type = args.get("query_type", "auto")
        
        response_parts = []
        
        # Search classes
        if query_type in ("class", "auto"):
            classes = self.structured_store.search_classes(query)
            if classes:
                response_parts.append(f"**Classes matching '{query}':**\n")
                for cls in classes[:5]:
                    response_parts.append(f"- **{cls['name']}**")
                    if cls['namespace']:
                        response_parts.append(f"  Namespace: {cls['namespace']}")
                    if cls['inherits_from']:
                        response_parts.append(f"  Inherits: {cls['inherits_from']}")
                    if cls['description']:
                        desc = cls['description'][:200]
                        response_parts.append(f"  Description: {desc}...")
                    response_parts.append("")
        
        # Search methods
        if query_type in ("method", "auto"):
            methods = self.structured_store.search_methods(query)
            if methods:
                response_parts.append(f"\n**Methods matching '{query}':**\n")
                for method in methods[:5]:
                    response_parts.append(
                        f"- **{method['class_name']}.{method['name']}**"
                    )
                    if method['return_type']:
                        response_parts.append(f"  Returns: {method['return_type']}")
                    if method['signature']:
                        response_parts.append(f"  Signature: {method['signature']}")
                    if method['description']:
                        desc = method['description'][:200]
                        response_parts.append(f"  Description: {desc}...")
                    response_parts.append("")
        
        if not response_parts:
            return [TextContent(
                type="text",
                text=f"No structured data found for query: {query}"
            )]
        
        return [TextContent(
            type="text",
            text="\n".join(response_parts)
        )]
    
    async def _get_unity_page(self, args: dict) -> Sequence[TextContent]:
        """Get a Unity documentation page."""
        url = args["url"]
        
        # Try to get from cache first
        page_id = get_page_id(url)
        doc_type = get_doc_type(url)
        
        page = self.structured_store.get_page(page_id)
        
        if page:
            return [TextContent(
                type="text",
                text=(
                    f"**{page['title']}** (cached)\n\n"
                    f"URL: {page['url']}\n"
                    f"Type: {page['doc_type']}\n\n"
                    f"{page['content']}"
                )
            )]
        
        # Not in cache - web scraping is no longer supported
        return [TextContent(
            type="text",
            text=(
                f"Page not found in cache: {url}\n\n"
                f"Web scraping is no longer supported. Please run the download command to index documentation:\n"
                f"python main.py --download"
            )
        )]
    
    async def _refresh_documentation(self, args: dict) -> Sequence[TextContent]:
        """Refresh a cached page."""
        url = args["url"]
        
        # Web scraping is no longer supported
        return [TextContent(
            type="text",
            text=(
                f"Refresh from web is no longer supported.\n\n"
                f"To update documentation, run:\npython main.py --download\n\n"
                f"This will check for updates and re-index all documentation if a new version is available."
            )
        )]
    
    async def _get_cache_stats(self, args: dict) -> Sequence[TextContent]:
        """Get cache statistics."""
        vector_stats = self.vector_store.get_stats()
        structured_stats = self.structured_store.get_stats()
        
        stats_text = (
            "**Unity Documentation Cache Statistics:**\n\n"
            f"**Vector Store:**\n"
            f"- Manual pages: {vector_stats['manual_count']}\n"
            f"- Script Reference pages: {vector_stats['script_reference_count']}\n"
            f"- Total chunks: {vector_stats['total_count']}\n\n"
            f"**Structured Store:**\n"
            f"- Total pages: {structured_stats['pages_count']}\n"
            f"- Classes: {structured_stats['classes_count']}\n"
            f"- Methods: {structured_stats['methods_count']}\n"
            f"- Properties: {structured_stats['properties_count']}\n"
        )
        
        return [TextContent(
            type="text",
            text=stats_text
        )]
    
    async def _get_full_documents(self, args: dict) -> Sequence[TextContent]:
        """Get full content of multiple documents based on search query."""
        query = args["query"]
        max_docs = min(args.get("max_documents", 3), 10)
        doc_type = args.get("doc_type", "both")
        
        # Map doc_type for vector store
        vector_doc_type = None
        if doc_type == "manual":
            vector_doc_type = "manual"
        elif doc_type == "script_reference":
            vector_doc_type = "script_reference"
        
        # Search vector store to find relevant documents
        search_results = self.vector_store.search(
            query=query,
            doc_type=vector_doc_type,
            n_results=max_docs * 3  # Get more results to find unique pages
        )
        
        if not search_results:
            return [TextContent(
                type="text",
                text=f"No documents found for query: {query}"
            )]
        
        # Get unique page URLs from search results
        seen_urls = set()
        documents = []
        
        for result in search_results:
            url = result["metadata"]["url"]
            if url not in seen_urls:
                seen_urls.add(url)
                
                # Get full page content from structured store
                page_id = get_page_id(url)
                page = self.structured_store.get_page(page_id)
                
                if page:
                    documents.append(page)
                    if len(documents) >= max_docs:
                        break
        
        if not documents:
            return [TextContent(
                type="text",
                text=f"Found search results but no full documents available. Try running: python main.py --download"
            )]
        
        # Format response with full document content
        response_parts = [
            f"# Found {len(documents)} full document(s) for '{query}'\n"
        ]
        
        for i, doc in enumerate(documents):
            response_parts.append(f"\n{'='*80}")
            response_parts.append(f"## Document {i+1}: {doc['title']}")
            response_parts.append(f"**URL:** {doc['url']}")
            response_parts.append(f"**Type:** {doc['doc_type']}")
            response_parts.append(f"{'='*80}\n")
            response_parts.append(doc['content'])
            response_parts.append("\n")
        
        return [TextContent(
            type="text",
            text="\n".join(response_parts)
        )]
    
    async def _get_related_documents(self, args: dict) -> Sequence[TextContent]:
        """Get documents related to a class or topic."""
        class_name = args.get("class_name")
        topic = args.get("topic")
        include_inheritance = args.get("include_inheritance", True)
        max_related = min(args.get("max_related", 3), 5)
        
        if not class_name and not topic:
            return [TextContent(
                type="text",
                text="Please provide either 'class_name' or 'topic' parameter"
            )]
        
        response_parts = []
        related_urls = set()
        
        # If class_name provided, get inheritance hierarchy and class info
        if class_name:
            class_data = self.structured_store.get_class(class_name)
            
            if class_data:
                response_parts.append(f"# Related Documents for Class: {class_name}\n")
                
                # Get the main class page
                page_id = class_data.get("page_id")
                if page_id:
                    page = self.structured_store.get_page(page_id)
                    if page:
                        related_urls.add(page["url"])
                        response_parts.append(f"\n## Main Documentation: {page['title']}")
                        response_parts.append(f"**URL:** {page['url']}")
                        response_parts.append(f"**Namespace:** {class_data.get('namespace', 'N/A')}")
                        if class_data.get('inherits_from'):
                            response_parts.append(f"**Inherits From:** {class_data['inherits_from']}")
                        response_parts.append(f"\n{page['content'][:1000]}...\n")
                
                # Get base class if inheritance is enabled
                if include_inheritance and class_data.get("inherits_from"):
                    base_class = class_data["inherits_from"]
                    base_data = self.structured_store.get_class(base_class)
                    if base_data and base_data.get("page_id"):
                        base_page = self.structured_store.get_page(base_data["page_id"])
                        if base_page and base_page["url"] not in related_urls:
                            related_urls.add(base_page["url"])
                            response_parts.append(f"\n## Base Class: {base_page['title']}")
                            response_parts.append(f"**URL:** {base_page['url']}")
                            response_parts.append(f"\n{base_page['content'][:800]}...\n")
            else:
                response_parts.append(f"# Searching for: {class_name}\n")
                response_parts.append(f"Class '{class_name}' not found in structured data. Performing semantic search...\n")
        
        # Perform semantic search for additional related content
        search_query = class_name or topic
        search_results = self.vector_store.search(
            query=search_query,
            n_results=max_related * 2
        )
        
        added_count = 0
        for result in search_results:
            if added_count >= max_related:
                break
                
            url = result["metadata"]["url"]
            if url not in related_urls:
                related_urls.add(url)
                page_id = get_page_id(url)
                page = self.structured_store.get_page(page_id)
                
                if page:
                    response_parts.append(f"\n## Related: {page['title']}")
                    response_parts.append(f"**URL:** {page['url']}")
                    response_parts.append(f"**Type:** {page['doc_type']}")
                    response_parts.append(f"\n{page['content'][:800]}...\n")
                    added_count += 1
        
        if not response_parts:
            return [TextContent(
                type="text",
                text=f"No related documents found for: {class_name or topic}"
            )]
        
        response_parts.insert(0, f"\nTotal related documents: {len(related_urls)}\n")
        
        return [TextContent(
            type="text",
            text="\n".join(response_parts)
        )]
    
    async def _extract_code_examples(self, args: dict) -> Sequence[TextContent]:
        """Extract code examples from Unity documentation."""
        from bs4 import BeautifulSoup
        
        query = args["query"]
        language = args.get("language", "any")
        max_examples = min(args.get("max_examples", 5), 10)
        doc_type = args.get("doc_type", "both")
        
        # Map doc_type for vector store
        vector_doc_type = None
        if doc_type == "manual":
            vector_doc_type = "manual"
        elif doc_type == "script_reference":
            vector_doc_type = "script_reference"
        
        # Search for relevant pages
        search_results = self.vector_store.search(
            query=query,
            doc_type=vector_doc_type,
            n_results=max_examples * 3  # Get more to find pages with code
        )
        
        if not search_results:
            return [TextContent(
                type="text",
                text=f"No documentation found for: {query}"
            )]
        
        # Extract code examples from pages
        code_examples = []
        seen_urls = set()
        
        for result in search_results:
            if len(code_examples) >= max_examples:
                break
                
            url = result["metadata"]["url"]
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            # Get full page
            page_id = get_page_id(url)
            page = self.structured_store.get_page(page_id)
            
            if not page:
                continue
            
            # Parse HTML to find code blocks
            soup = BeautifulSoup(page["content"], "html.parser")
            
            # Find code blocks (Unity docs use <pre><code> or <div class="code-example">)
            code_blocks = soup.find_all(["pre", "code"])
            
            for block in code_blocks:
                code_text = block.get_text().strip()
                
                # Skip empty or very short snippets
                if len(code_text) < 10:
                    continue
                
                # Language filtering
                if language != "any":
                    # Simple heuristic: C# has "void", "class", JavaScript has "var", "function"
                    if language == "csharp" and not any(kw in code_text for kw in ["void", "class", "public", "private"]):
                        continue
                    elif language == "javascript" and not any(kw in code_text for kw in ["var", "function", "let", "const"]):
                        continue
                
                code_examples.append({
                    "code": code_text,
                    "source": page["title"],
                    "url": url,
                    "doc_type": page["doc_type"]
                })
                
                if len(code_examples) >= max_examples:
                    break
        
        if not code_examples:
            return [TextContent(
                type="text",
                text=f"No code examples found for '{query}'. Try searching for topics with code samples like 'player movement' or 'collision detection'."
            )]
        
        # Format response
        response_parts = [
            f"# Found {len(code_examples)} Code Example(s) for '{query}'\n"
        ]
        
        for i, example in enumerate(code_examples):
            response_parts.append(f"\n## Example {i+1}: {example['source']}")
            response_parts.append(f"**Source:** {example['url']}")
            response_parts.append(f"**Type:** {example['doc_type']}")
            response_parts.append(f"\n```csharp\n{example['code']}\n```\n")
        
        return [TextContent(
            type="text",
            text="\n".join(response_parts)
        )]
    
    async def _get_method_signatures(self, args: dict) -> Sequence[TextContent]:
        """Get method and property signatures for quick API reference."""
        class_name = args.get("class_name")
        method_name = args.get("method_name")
        include_properties = args.get("include_properties", True)
        static_only = args.get("static_only", False)
        
        if not class_name and not method_name:
            return [TextContent(
                type="text",
                text="Please provide either 'class_name' or 'method_name' parameter"
            )]
        
        response_parts = []
        
        # Search by class name
        if class_name:
            class_data = self.structured_store.get_class(class_name)
            
            if not class_data:
                return [TextContent(
                    type="text",
                    text=f"Class '{class_name}' not found in database. Try: python main.py --download"
                )]
            
            response_parts.append(f"# API Reference: {class_name}\n")
            response_parts.append(f"**Namespace:** {class_data.get('namespace', 'N/A')}")
            if class_data.get("inherits_from"):
                response_parts.append(f"**Inherits:** {class_data['inherits_from']}")
            response_parts.append("")
            
            # Methods
            methods = class_data.get("methods", [])
            if methods:
                filtered_methods = [m for m in methods if not static_only or m.get("is_static")]
                
                if filtered_methods:
                    response_parts.append(f"## Methods ({len(filtered_methods)})\n")
                    for method in filtered_methods:
                        static_marker = "static " if method.get("is_static") else ""
                        return_type = method.get("return_type", "void")
                        signature = method.get("signature", f"{method['name']}()")
                        
                        response_parts.append(f"### {static_marker}{return_type} {signature}")
                        if method.get("description"):
                            desc = method["description"][:150]
                            response_parts.append(f"{desc}..." if len(method["description"]) > 150 else desc)
                        response_parts.append("")
            
            # Properties
            if include_properties:
                properties = class_data.get("properties", [])
                if properties:
                    filtered_props = [p for p in properties if not static_only or p.get("is_static")]
                    
                    if filtered_props:
                        response_parts.append(f"## Properties ({len(filtered_props)})\n")
                        for prop in filtered_props:
                            static_marker = "static " if prop.get("is_static") else ""
                            prop_type = prop.get("property_type", "object")
                            
                            response_parts.append(f"### {static_marker}{prop_type} {prop['name']}")
                            if prop.get("description"):
                                desc = prop["description"][:150]
                                response_parts.append(f"{desc}..." if len(prop["description"]) > 150 else desc)
                            response_parts.append("")
        
        # Search by method name
        elif method_name:
            methods = self.structured_store.search_methods(method_name)
            
            if not methods:
                return [TextContent(
                    type="text",
                    text=f"No methods found matching '{method_name}'"
                )]
            
            filtered_methods = [m for m in methods if not static_only or m.get("is_static")]
            
            if not filtered_methods:
                return [TextContent(
                    type="text",
                    text=f"No {'static ' if static_only else ''}methods found matching '{method_name}'"
                )]
            
            response_parts.append(f"# Methods matching '{method_name}' ({len(filtered_methods)})\n")
            
            for method in filtered_methods:
                static_marker = "static " if method.get("is_static") else ""
                return_type = method.get("return_type", "void")
                signature = method.get("signature", f"{method['name']}()")
                class_name = method.get("class_name", "Unknown")
                namespace = method.get("namespace", "")
                
                response_parts.append(f"## {namespace}.{class_name}.{method['name']}")
                response_parts.append(f"```csharp\n{static_marker}{return_type} {signature}\n```")
                if method.get("description"):
                    response_parts.append(f"{method['description']}")
                response_parts.append("")
        
        if not response_parts:
            return [TextContent(
                type="text",
                text="No API signatures found"
            )]
        
        return [TextContent(
            type="text",
            text="\n".join(response_parts)
        )]
    
    async def _search_by_use_case(self, args: dict) -> Sequence[TextContent]:
        """Search Unity documentation by use case or goal."""
        use_case = args["use_case"]
        experience_level = args.get("experience_level", "intermediate")
        max_results = min(args.get("max_results", 3), 5)
        prefer_code = args.get("prefer_code", True)
        
        # Enhance the query based on experience level
        query_enhancements = {
            "beginner": f"{use_case} tutorial basics getting started simple example",
            "intermediate": f"{use_case} implementation best practices example",
            "advanced": f"{use_case} advanced optimization performance architecture"
        }
        
        enhanced_query = query_enhancements.get(experience_level, use_case)
        
        # Search with enhanced query
        search_results = self.vector_store.search(
            query=enhanced_query,
            n_results=max_results * 2
        )
        
        if not search_results:
            return [TextContent(
                type="text",
                text=f"No documentation found for use case: '{use_case}'. Try rephrasing or using more specific terms."
            )]
        
        # Process results
        solutions = []
        seen_urls = set()
        
        for result in search_results:
            if len(solutions) >= max_results:
                break
            
            url = result["metadata"]["url"]
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            page_id = get_page_id(url)
            page = self.structured_store.get_page(page_id)
            
            if not page:
                continue
            
            # Check for code if preferred
            has_code = "<code>" in page["content"] or "<pre>" in page["content"]
            
            if prefer_code and not has_code:
                continue
            
            # Extract a relevant snippet
            content = page["content"]
            snippet_length = 500 if experience_level == "beginner" else 300
            snippet = content[:snippet_length] + "..." if len(content) > snippet_length else content
            
            solutions.append({
                "title": page["title"],
                "url": url,
                "doc_type": page["doc_type"],
                "snippet": snippet,
                "has_code": has_code,
                "relevance": result.get("distance", 0)  # Lower is better
            })
        
        if not solutions:
            return [TextContent(
                type="text",
                text=f"No solutions found for '{use_case}'. Try:\n- Removing 'prefer_code' filter\n- Using different keywords\n- Simplifying your use case description"
            )]
        
        # Format response
        level_intro = {
            "beginner": "Here are beginner-friendly solutions:",
            "intermediate": "Here are practical solutions:",
            "advanced": "Here are advanced techniques:"
        }
        
        response_parts = [
            f"# Solutions for: '{use_case}'\n",
            level_intro.get(experience_level, "Here are relevant solutions:"),
            ""
        ]
        
        for i, solution in enumerate(solutions):
            response_parts.append(f"\n## Solution {i+1}: {solution['title']}")
            response_parts.append(f"**URL:** {solution['url']}")
            response_parts.append(f"**Type:** {solution['doc_type']}")
            if solution["has_code"]:
                response_parts.append("✅ **Contains code examples**")
            response_parts.append(f"\n{solution['snippet']}\n")
            response_parts.append(f"[Read full documentation]({solution['url']})\n")
        
        # Add helpful tips
        response_parts.append("\n---\n")
        response_parts.append("💡 **Next Steps:**")
        if experience_level == "beginner":
            response_parts.append("- Read through the examples carefully")
            response_parts.append("- Try implementing in a test project")
            response_parts.append("- Use 'extract_code_examples' tool for just the code")
        else:
            response_parts.append("- Use 'get_full_documents' for complete documentation")
            response_parts.append("- Use 'get_related_documents' to explore related APIs")
            response_parts.append("- Use 'extract_code_examples' to get code snippets")
        
        return [TextContent(
            type="text",
            text="\n".join(response_parts)
        )]
    
    async def run(self) -> None:
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def _download_and_index_docs(data_dir: str, download_dir: str, openai_api_key: str) -> None:
    """Download and index Unity documentation.
    
    Args:
        data_dir: Directory for data storage
        download_dir: Directory to download documentation
        openai_api_key: OpenAI API key
    """
    from pathlib import Path
    import shutil
    from .downloader import UnityDocsDownloader
    from .downloader.local_crawler import LocalDocsCrawler
    from .processor import ContentProcessor
    from .scraper.utils import get_page_id
    import hashlib
    
    logger.info("Step 1/4: Clearing old data (if any)...")
    
    # Clear databases
    data_path = Path(data_dir).absolute()
    download_path = Path(download_dir).absolute()
    
    vector_db = data_path / "vector" / "chromadb"
    structured_db = data_path / "structured" / "unity_docs.db"
    
    if vector_db.exists():
        shutil.rmtree(vector_db)
        logger.info(f"  Cleared vector database")
    
    if structured_db.exists():
        structured_db.unlink()
        logger.info(f"  Cleared structured database")
    
    # Clear downloads
    if download_path.exists():
        shutil.rmtree(download_path)
        logger.info(f"  Cleared downloads directory")
    
    download_path.mkdir(parents=True, exist_ok=True)
    
    logger.info("Step 2/4: Downloading Unity documentation...")
    
    # Download documentation
    downloader = UnityDocsDownloader(str(download_path))
    extract_dir = downloader.download_and_extract()
    
    logger.info("Step 3/4: Indexing documentation...")
    
    # Get documentation paths
    manual_path = downloader.get_manual_path()
    script_path = downloader.get_script_reference_path()
    
    if not manual_path and not script_path:
        raise RuntimeError("Could not find documentation in extracted files")
    
    # Initialize storage
    vector_store = VectorStore(data_dir, openai_api_key)
    structured_store = StructuredStore(data_dir)
    processor = ContentProcessor()
    
    # Initialize local crawler with absolute path
    docs_root = Path(download_dir).absolute() / "Documentation"
    local_crawler = LocalDocsCrawler(docs_root)
    
    # Collect files
    files_to_process = []
    
    if manual_path:
        logger.info(f"  Finding Manual files...")
        manual_files = local_crawler.get_manual_files(manual_path)
        files_to_process.extend(manual_files)
        logger.info(f"  Found {len(manual_files)} Manual files")
    
    if script_path:
        logger.info(f"  Finding ScriptReference files...")
        script_files = local_crawler.get_script_reference_files(script_path)
        files_to_process.extend(script_files)
        logger.info(f"  Found {len(script_files)} ScriptReference files")
    
    logger.info(f"Step 4/4: Processing {len(files_to_process)} files...")
    
    # Process files
    processed = 0
    
    for i, file_path in enumerate(files_to_process):
        try:
            if (i + 1) % 1000 == 0:
                logger.info(f"  Progress: {i + 1}/{len(files_to_process)} files")
            
            # Read file
            page_data = local_crawler.read_html_file(file_path)
            
            # Generate page ID
            page_id = hashlib.md5(page_data['url'].encode()).hexdigest()
            
            # Store in structured database
            structured_store.add_page(
                page_id=page_id,
                url=page_data['url'],
                title=page_data['title'],
                doc_type=page_data['doc_type'],
                content=page_data['content']
            )
            
            # Process based on doc type
            if page_data['doc_type'] == 'script_reference':
                structured_data = processor.extract_script_reference_data(
                    page_data['html'], page_data['url'], page_data['title']
                )
                
                if structured_data['class_name']:
                    class_id = structured_store.add_class(
                        name=structured_data['class_name'],
                        namespace=structured_data['namespace'],
                        page_id=page_id,
                        description=structured_data['description'],
                        inherits_from=structured_data['inherits_from'],
                        is_static=structured_data['is_static']
                    )
                    
                    for method in structured_data['methods']:
                        structured_store.add_method(
                            class_id=class_id,
                            name=method['name'],
                            return_type=method.get('return_type'),
                            is_static=method.get('is_static', False),
                            description=method.get('description'),
                            signature=method.get('signature')
                        )
                    
                    for prop in structured_data['properties']:
                        structured_store.add_property(
                            class_id=class_id,
                            name=prop['name'],
                            property_type=prop.get('property_type'),
                            is_static=prop.get('is_static', False),
                            description=prop.get('description')
                        )
            
            # Prepare for vector store
            chunks = processor.prepare_for_vector_store(
                content=page_data['content'],
                metadata={
                    'url': page_data['url'],
                    'title': page_data['title'],
                    'doc_type': page_data['doc_type']
                },
                chunk_size=1000
            )
            
            # Add to vector store
            for j, (chunk_text, chunk_metadata) in enumerate(chunks):
                chunk_id = f"{page_id}_chunk_{j}"
                vector_store.add_document(
                    doc_id=chunk_id,
                    url=page_data['url'],
                    title=f"{page_data['title']} (part {j+1})" if len(chunks) > 1 else page_data['title'],
                    content=chunk_text,
                    doc_type=page_data['doc_type'],
                    metadata=chunk_metadata
                )
            
            processed += 1
            
        except Exception as e:
            logger.warning(f"  Error processing {file_path.name}: {e}")
    
    logger.info(f"Successfully processed {processed}/{len(files_to_process)} files")


async def serve(data_dir: str, openai_api_key: str, check_version: bool = True, auto_download: bool = False) -> None:
    """Start the MCP server.
    
    Args:
        data_dir: Directory for data storage
        openai_api_key: OpenAI API key
        check_version: Check for documentation updates on startup
        auto_download: Automatically download documentation if not found (not recommended for VS Code)
    
    Note:
        All logging output goes to stderr and ./logs/unity_mcp.log to avoid
        interfering with the MCP JSON-RPC protocol on stdout.
        
        Auto-download is disabled by default because VS Code expects the server to
        start immediately. To download documentation, run: python main.py --reset
    """
    # Check for documentation updates on startup
    if check_version:
        from .downloader import UnityDocsDownloader
        downloader = UnityDocsDownloader("./downloads")
        
        update_available, current, latest = downloader.check_for_updates()
        if update_available:
            if current:
                logger.warning(f"Documentation update available: {current} -> {latest}")
                logger.warning(f"Run 'python main.py --download' to update")
            else:
                logger.error("=" * 60)
                logger.error("DOCUMENTATION NOT FOUND!")
                logger.error("=" * 60)
                logger.error("The Unity MCP server requires documentation to be downloaded first.")
                logger.error("")
                logger.error("To download documentation (~35k files, 30-60 minutes):")
                logger.error("  1. Open a terminal in the Unity MCP directory")
                logger.error("  2. Run: python main.py --reset")
                logger.error("")
                logger.error("After download completes, restart VS Code to use the server.")
                logger.error("=" * 60)
                
                if auto_download:
                    logger.info("AUTO-DOWNLOAD: Starting first-time setup...")
                    logger.info("This will take 30-60 minutes but only happens once.")
                    
                    try:
                        # Download and index documentation directly
                        await _download_and_index_docs(data_dir, "./downloads", openai_api_key)
                        logger.info("=" * 60)
                        logger.info("Documentation downloaded and indexed successfully!")
                        logger.info("Server is now ready to use.")
                        logger.info("=" * 60)
                    except Exception as e:
                        logger.error("=" * 60)
                        logger.error(f"Error during auto-download: {e}")
                        logger.error("Please run manually: python main.py --reset")
                        logger.error("=" * 60)
                        import traceback
                        logger.error(traceback.format_exc())
        else:
            logger.info(f"Documentation is up-to-date (version {current})")
    
    server = UnityMCPServer(data_dir, openai_api_key)
    await server.run()


def main() -> None:
    """Main entry point for the MCP server when installed as a package."""
    import sys
    
    # Get OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY environment variable is required")
        sys.exit(1)
    
    # Use default data directory
    data_dir = os.getenv("UNITY_MCP_DATA_DIR", "./data")
    
    # Check if auto-download should be enabled (disabled by default for VS Code compatibility)
    auto_download = os.getenv("UNITY_MCP_AUTO_DOWNLOAD", "false").lower() == "true"
    
    # Run the server
    asyncio.run(serve(data_dir, openai_api_key, check_version=True, auto_download=auto_download))
