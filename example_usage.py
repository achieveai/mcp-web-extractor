#!/usr/bin/env python3
"""
Example usage of the Trafilatura MCP Server

This script demonstrates how to test the server functionality directly.
Note: In production, the server would be used through MCP protocol.
"""

import asyncio
import json
from typing import Any, Dict

from trafilatura_mcp.server import extract_markdown_tool


async def test_url_extraction():
    """Test extracting content from a URL."""
    print("Testing URL extraction...")
    
    args = {
        "url": "https://example.com",
        "precision": True,
        "include_tables": True,
        "output_format": "markdown"
    }
    
    try:
        result = await extract_markdown_tool(args)
        print(f"✅ URL extraction successful!")
        print(f"Content length: {len(result[0].text)} characters")
        print(f"First 200 characters:\n{result[0].text[:200]}...")
    except Exception as e:
        print(f"❌ URL extraction failed: {e}")


async def test_html_extraction():
    """Test extracting content from HTML."""
    print("\nTesting HTML extraction...")
    
    sample_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Article</title>
    </head>
    <body>
        <nav>Navigation menu</nav>
        <header>
            <h1>Main Article Title</h1>
        </header>
        <article>
            <h2>Introduction</h2>
            <p>This is the main content of the article. It contains important 
            information that should be extracted.</p>
            
            <h2>Details</h2>
            <p>Here are more details about the topic. This paragraph contains
            useful information for the reader.</p>
            
            <table>
                <tr><th>Column 1</th><th>Column 2</th></tr>
                <tr><td>Data 1</td><td>Data 2</td></tr>
            </table>
        </article>
        <footer>Footer content</footer>
        <script>console.log('ads');</script>
    </body>
    </html>
    """
    
    args = {
        "html": sample_html,
        "precision": True,
        "include_tables": True,
        "include_comments": False,
        "output_format": "markdown"
    }
    
    try:
        result = await extract_markdown_tool(args)
        print(f"✅ HTML extraction successful!")
        print(f"Extracted content:\n{result[0].text}")
    except Exception as e:
        print(f"❌ HTML extraction failed: {e}")


async def test_different_formats():
    """Test different output formats."""
    print("\nTesting different output formats...")
    
    sample_html = """
    <html><body>
        <h1>Test Title</h1>
        <p>This is a test paragraph with <strong>bold text</strong> and 
        <a href="https://example.com">a link</a>.</p>
    </body></html>
    """
    
    formats = ["markdown", "txt", "xml"]
    
    for fmt in formats:
        args = {
            "html": sample_html,
            "output_format": fmt,
            "precision": True
        }
        
        try:
            result = await extract_markdown_tool(args)
            print(f"✅ {fmt.upper()} format:")
            print(f"{result[0].text}\n")
        except Exception as e:
            print(f"❌ {fmt.upper()} format failed: {e}")


async def main():
    """Run all test examples."""
    print("🚀 Trafilatura MCP Server - Example Usage\n")
    print("=" * 50)
    
    # Test HTML extraction (always works, no network required)
    await test_html_extraction()
    
    # Test different formats
    await test_different_formats()
    
    # Test URL extraction (requires internet connection)
    try:
        await test_url_extraction()
    except Exception as e:
        print(f"ℹ️  URL test skipped (no internet or connection issue): {e}")
    
    print("\n" + "=" * 50)
    print("✨ Example usage complete!")
    print("\nTo use this as an MCP server, run:")
    print("  trafilatura-mcp")
    print("\nOr install and configure in your MCP client.")


if __name__ == "__main__":
    asyncio.run(main())