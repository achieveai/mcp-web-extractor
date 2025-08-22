"""
Trafilatura MCP Server

A Model Context Protocol (MCP) server that exposes Trafilatura's web content
extraction capabilities as a tool. This implementation uses Trafilatura's
Python API directly for better performance and tighter integration.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field, field_validator, model_validator
from trafilatura import extract, fetch_url

from modelcontextprotocol.server import Server
from modelcontextprotocol.transport.stdio import stdio_transport
from modelcontextprotocol.types import (
    CallToolRequest,
    CallToolResult,
    ErrorCode,
    McpError,
    TextContent,
    Tool,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExtractMarkdownInput(BaseModel):
    """Input model for the extract_markdown tool."""
    
    # Primary input (exactly one required)
    url: Optional[str] = Field(
        default=None,
        description="URL to fetch and extract content from"
    )
    html: Optional[str] = Field(
        default=None,
        description="Raw HTML content to extract from"
    )
    
    # Content extraction options
    precision: bool = Field(
        default=True,
        description="Favor precision over recall (more conservative extraction)"
    )
    include_comments: bool = Field(
        default=False,
        description="Include HTML comments in the extracted content"
    )
    include_tables: bool = Field(
        default=True,
        description="Include tables in the extracted content"
    )
    include_images: bool = Field(
        default=True,
        description="Include images in the extracted content"
    )
    include_links: bool = Field(
        default=True,
        description="Include links in the extracted content"
    )
    
    # Network options (only used with URL)
    timeout: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Request timeout in seconds (5-120)"
    )
    
    # Output format options
    output_format: str = Field(
        default="markdown",
        description="Output format: 'markdown', 'txt', or 'xml'"
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate URL format if provided."""
        if v is None:
            return v
        
        try:
            result = urlparse(v)
            if not result.scheme or not result.netloc:
                raise ValueError("URL must include scheme and netloc (e.g., https://example.com)")
            if result.scheme not in ("http", "https"):
                raise ValueError("URL scheme must be http or https")
            return v
        except Exception as e:
            raise ValueError(f"Invalid URL format: {e}")

    @field_validator("output_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        """Validate output format."""
        valid_formats = {"markdown", "txt", "xml"}
        if v not in valid_formats:
            raise ValueError(f"Output format must be one of: {', '.join(valid_formats)}")
        return v

    @model_validator(mode="after")
    def validate_input_source(self) -> "ExtractMarkdownInput":
        """Ensure exactly one of url or html is provided."""
        url_provided = self.url is not None
        html_provided = self.html is not None and self.html.strip()
        
        if url_provided == html_provided:  # Both true or both false
            raise ValueError("Provide exactly one of 'url' or 'html'")
        
        return self


async def fetch_url_async(url: str, timeout: int = 30) -> Optional[str]:
    """
    Fetch URL content asynchronously with proper error handling.
    
    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        HTML content as string, or None if fetch failed
    """
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; Trafilatura-MCP/0.1.0)"
            }
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.TimeoutException:
        logger.error(f"Timeout fetching URL: {url}")
        raise McpError(ErrorCode.INTERNAL_ERROR, f"Timeout fetching URL: {url}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching URL {url}: {e.response.status_code}")
        raise McpError(
            ErrorCode.INTERNAL_ERROR,
            f"HTTP {e.response.status_code} error fetching URL: {url}"
        )
    except Exception as e:
        logger.error(f"Error fetching URL {url}: {e}")
        raise McpError(ErrorCode.INTERNAL_ERROR, f"Error fetching URL: {e}")


async def extract_content_async(
    html: str,
    output_format: str = "markdown",
    precision: bool = True,
    include_comments: bool = False,
    include_tables: bool = True,
    include_images: bool = True,
    include_links: bool = True,
) -> Optional[str]:
    """
    Extract content from HTML using Trafilatura in a thread pool.
    
    Args:
        html: HTML content to extract from
        output_format: Output format ('markdown', 'txt', or 'xml')
        precision: Favor precision over recall
        include_comments: Include HTML comments
        include_tables: Include tables
        include_images: Include images
        include_links: Include links
        
    Returns:
        Extracted content as string, or None if extraction failed
    """
    def _extract():
        return extract(
            html,
            output_format=output_format,
            favor_recall=not precision,
            include_comments=include_comments,
            include_tables=include_tables,
            include_images=include_images,
            include_links=include_links,
        )
    
    try:
        # Run extraction in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _extract)
        return result
    except Exception as e:
        logger.error(f"Error during content extraction: {e}")
        raise McpError(ErrorCode.INTERNAL_ERROR, f"Content extraction failed: {e}")


async def extract_markdown_tool(args: Dict[str, Any]) -> List[TextContent]:
    """
    Extract main article content and return as markdown using Trafilatura API.
    
    Args:
        args: Tool arguments containing URL or HTML and extraction options
        
    Returns:
        List containing the extracted content as TextContent
        
    Raises:
        McpError: If validation fails or extraction fails
    """
    try:
        # Validate input
        try:
            input_data = ExtractMarkdownInput(**args)
        except Exception as e:
            logger.error(f"Input validation failed: {e}")
            raise McpError(ErrorCode.INVALID_PARAMS, f"Invalid parameters: {e}")
        
        # Get HTML content
        html_content: Optional[str] = None
        
        if input_data.url:
            logger.info(f"Fetching content from URL: {input_data.url}")
            html_content = await fetch_url_async(input_data.url, input_data.timeout)
        else:
            html_content = input_data.html
        
        if not html_content or not html_content.strip():
            raise McpError(ErrorCode.INTERNAL_ERROR, "No HTML content available for extraction")
        
        # Extract content using Trafilatura
        logger.info("Extracting content using Trafilatura API")
        extracted_content = await extract_content_async(
            html_content,
            output_format=input_data.output_format,
            precision=input_data.precision,
            include_comments=input_data.include_comments,
            include_tables=input_data.include_tables,
            include_images=input_data.include_images,
            include_links=input_data.include_links,
        )
        
        if not extracted_content or not extracted_content.strip():
            raise McpError(
                ErrorCode.INTERNAL_ERROR,
                "Trafilatura returned empty content. The page may not contain extractable text."
            )
        
        logger.info(f"Successfully extracted {len(extracted_content)} characters")
        return [TextContent(type="text", text=extracted_content.strip())]
        
    except McpError:
        raise  # Re-raise MCP errors as-is
    except Exception as e:
        logger.error(f"Unexpected error in extract_markdown_tool: {e}")
        raise McpError(ErrorCode.INTERNAL_ERROR, f"Unexpected error: {e}")


# Initialize MCP server
server = Server(name="trafilatura-mcp", version="0.1.0")


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="extract_markdown",
            description=(
                "Extract main article content from web pages or HTML and return as "
                "markdown, plain text, or XML. Uses Trafilatura's advanced content "
                "extraction algorithms to identify and clean the main textual content "
                "while filtering out navigation, ads, and boilerplate."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to fetch and extract content from (http/https only)"
                    },
                    "html": {
                        "type": "string",
                        "description": "Raw HTML content to extract from"
                    },
                    "precision": {
                        "type": "boolean",
                        "description": "Favor precision over recall (default: true)",
                        "default": True
                    },
                    "include_comments": {
                        "type": "boolean",
                        "description": "Include HTML comments in extracted content (default: false)",
                        "default": False
                    },
                    "include_tables": {
                        "type": "boolean",
                        "description": "Include tables in extracted content (default: true)",
                        "default": True
                    },
                    "include_images": {
                        "type": "boolean",
                        "description": "Include images in extracted content (default: true)",
                        "default": True
                    },
                    "include_links": {
                        "type": "boolean",
                        "description": "Include links in extracted content (default: true)",
                        "default": True
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Request timeout in seconds for URL fetching (5-120, default: 30)",
                        "minimum": 5,
                        "maximum": 120,
                        "default": 30
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Output format (default: 'markdown')",
                        "enum": ["markdown", "txt", "xml"],
                        "default": "markdown"
                    }
                },
                "oneOf": [
                    {"required": ["url"]},
                    {"required": ["html"]}
                ],
                "additionalProperties": False
            }
        )
    ]


@server.call_tool()
async def call_tool(request: CallToolRequest) -> CallToolResult:
    """Handle tool calls."""
    if request.method != "tools/call":
        raise McpError(ErrorCode.METHOD_NOT_FOUND, f"Method not found: {request.method}")
    
    if request.params.name != "extract_markdown":
        raise McpError(ErrorCode.INVALID_PARAMS, f"Unknown tool: {request.params.name}")
    
    try:
        content = await extract_markdown_tool(request.params.arguments or {})
        return CallToolResult(content=content, isError=False)
    except McpError as e:
        logger.error(f"Tool call failed: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=str(e))],
            isError=True
        )
    except Exception as e:
        logger.error(f"Unexpected error in tool call: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Internal error: {e}")],
            isError=True
        )


def main() -> None:
    """Main entry point for the MCP server."""
    logger.info("Starting Trafilatura MCP Server v0.1.0")
    try:
        server.run(stdio_transport())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()