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
from .crawler import UnityCrawler

logger = logging.getLogger(__name__)


class UnityMCPServer:
    """MCP server for Unity documentation search and retrieval."""
    
    def __init__(self, data_dir: str, openai_api_key: str):
        """Initialize the MCP server.
        
        Args:
            data_dir: Directory for data storage
            openai_api_key: OpenAI API key
        """
        self.data_dir = Path(data_dir)
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
    
    async def run(self) -> None:
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def serve(data_dir: str, openai_api_key: str, check_version: bool = True) -> None:
    """Start the MCP server.
    
    Args:
        data_dir: Directory for data storage
        openai_api_key: OpenAI API key
        check_version: Check for documentation updates on startup
    
    Note:
        All logging output goes to stderr and ./logs/unity_mcp.log to avoid
        interfering with the MCP JSON-RPC protocol on stdout.
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
                logger.warning("No documentation found locally!")
                logger.warning(f"Run 'python main.py --download' to download version {latest}")
        else:
            logger.info(f"Documentation is up-to-date (version {current})")
    
    server = UnityMCPServer(data_dir, openai_api_key)
    await server.run()
