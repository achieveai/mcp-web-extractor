"""
Trafilatura MCP Server

A Model Context Protocol (MCP) server that provides web content extraction
capabilities using Trafilatura's Python API for extracting clean text and
markdown from web pages and HTML content.
"""

__version__ = "0.1.0"
__author__ = "MCP Trafilatura Server"
__email__ = "noreply@example.com"

from .server import main

__all__ = ["main"]