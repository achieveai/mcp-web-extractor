# MCP Trafilatura Server

[![PyPI version](https://badge.fury.io/py/mcp-trafilatura-server.svg)](https://badge.fury.io/py/mcp-trafilatura-server)
[![Python](https://img.shields.io/pypi/pyversions/mcp-trafilatura-server.svg)](https://pypi.org/project/mcp-trafilatura-server/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A Model Context Protocol (MCP) server that provides web content extraction capabilities using [Trafilatura](https://trafilatura.readthedocs.io/)'s Python API. This server allows MCP clients to extract clean, readable content from web pages and HTML documents.

## Features

- **Clean Content Extraction**: Uses Trafilatura's advanced algorithms to extract main article content while filtering out navigation, ads, and boilerplate
- **Multiple Output Formats**: Supports Markdown, plain text, and XML output
- **Flexible Input**: Accept either URLs (with automatic fetching) or raw HTML content
- **Configurable Extraction**: Fine-tune extraction behavior with precision, inclusion of tables, images, links, and comments
- **Async Implementation**: Non-blocking operations with proper timeout handling
- **Robust Error Handling**: Comprehensive error handling with informative error messages
- **Type Safety**: Full type hints and Pydantic validation

## Installation

### Quick Install via pip

```bash
pip install mcp-trafilatura-server
```

### Option 1: Using uvx (Recommended - No Installation)

The easiest way to run the server with any MCP client:

```bash
# Run directly with uvx (no installation needed)
uvx mcp-trafilatura-server

# Or specify from local directory during development
uvx --from . mcp-trafilatura-server
```

For use with Claude Desktop, add to your configuration:

```json
{
  "mcpServers": {
    "trafilatura": {
      "command": "uvx",
      "args": ["mcp-trafilatura-server"]
    }
  }
}
```

Or for local development:
```json
{
  "mcpServers": {
    "trafilatura": {
      "command": "uvx",
      "args": ["--from", "/path/to/mcp-trafilatura", "mcp-trafilatura-server"]
    }
  }
}
```

### Option 2: Using uv for Development

```bash
# Clone the repository
git clone https://github.com/achieveai/mcp-web-extractor.git
cd mcp-trafilatura

# Create virtual environment and install
uv venv
uv pip install -e .

# Run the server
uv run mcp-trafilatura-server
```

### Option 3: Traditional pip Installation

```bash
# Install from PyPI
pip install mcp-trafilatura-server

# Or for development:
git clone https://github.com/achieveai/mcp-web-extractor.git
cd mcp-trafilatura
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### Option 4: Using requirements.txt

```bash
# Install dependencies directly
pip install -r requirements.txt

# Then install the package
pip install -e .
```

## Usage

### As an MCP Server

The server can be used with any MCP-compatible client. Register it in your client configuration:

```json
{
  "mcpServers": {
    "web-extractor": {
      "command": "mcp-trafilatura-server",
      "args": []
    }
  }
}
```

### Direct Usage

You can also run the server directly:

```bash
# Run the server (listens on stdio)
mcp-trafilatura-server

# Or run the module directly
python -m trafilatura_mcp.server
```

## Tool: extract_markdown

The server provides a single tool called `extract_markdown` that extracts content from web pages or HTML.

### Parameters

#### Required (one of):
- `url` (string): URL to fetch and extract content from (http/https only)
- `html` (string): Raw HTML content to extract from

#### Optional:
- `precision` (boolean, default: true): Favor precision over recall in extraction
- `include_comments` (boolean, default: false): Include HTML comments in output
- `include_tables` (boolean, default: true): Include tables in extracted content
- `include_images` (boolean, default: true): Include images in extracted content
- `include_links` (boolean, default: true): Include links in extracted content
- `timeout` (integer, default: 30): Request timeout in seconds for URL fetching (5-120)
- `output_format` (string, default: "markdown"): Output format - "markdown", "txt", or "xml"

### Example Usage

#### Extracting from a URL:

```json
{
  "name": "extract_markdown",
  "arguments": {
    "url": "https://example.com/article",
    "precision": true,
    "include_tables": true,
    "output_format": "markdown"
  }
}
```

#### Extracting from HTML:

```json
{
  "name": "extract_markdown",
  "arguments": {
    "html": "<html><body><h1>Title</h1><p>Content...</p></body></html>",
    "include_comments": false,
    "output_format": "txt"
  }
}
```

#### Minimal usage:

```json
{
  "name": "extract_markdown",
  "arguments": {
    "url": "https://news.ycombinator.com/"
  }
}
```

## Configuration for Popular MCP Clients

### Claude Desktop

Add to your Claude Desktop configuration file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Using uvx (recommended - no installation needed):
```json
{
  "mcpServers": {
    "trafilatura": {
      "command": "uvx",
      "args": ["mcp-trafilatura-server"]
    }
  }
}
```

Or if installed via pip:
```json
{
  "mcpServers": {
    "web-extractor": {
      "command": "mcp-trafilatura-server",
      "args": []
    }
  }
}
```

### VS Code with Continue

Add to your Continue configuration:

```json
{
  "mcpServers": [
    {
      "name": "trafilatura",
      "command": "uvx",
      "args": ["mcp-trafilatura-server"]
    }
  ]
}
```

## Development

### Project Structure

```
mcp-trafilatura/
├── src/
│   └── trafilatura_mcp/
│       ├── __init__.py
│       ├── server.py          # Main server implementation
│       └── py.typed           # Type hints marker
├── pyproject.toml             # Package configuration
├── requirements.txt           # Dependencies
├── LICENSE                    # GPL-3.0 license
├── MANIFEST.in                # Package data files
└── README.md                  # This file
```

### Development Setup

```bash
# Clone the repository
git clone https://github.com/achieveai/mcp-web-extractor.git
cd mcp-trafilatura

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run type checking
mypy src/

# Run linting
ruff check src/

# Format code
black src/
isort src/
```

### Testing

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=trafilatura_mcp
```

## Error Handling

The server provides comprehensive error handling:

- **Input Validation**: Invalid URLs, missing required parameters, or invalid parameter values
- **Network Errors**: Connection timeouts, HTTP errors, or unreachable URLs
- **Extraction Errors**: Empty content, parsing failures, or unsupported content types
- **Server Errors**: Internal errors with detailed logging

All errors are returned as proper MCP error responses with descriptive messages.

## Logging

The server uses Python's built-in logging with INFO level by default. Logs include:
- Server startup and shutdown
- URL fetching attempts
- Content extraction operations
- Error conditions with details

## Dependencies

- **modelcontextprotocol**: MCP protocol implementation
- **pydantic**: Data validation and settings management
- **trafilatura**: Core content extraction functionality
- **httpx**: Async HTTP client for URL fetching
- **typing-extensions**: Additional type hints support

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0) because it directly imports and uses Trafilatura's Python API, which is GPL-3.0 licensed. See the LICENSE file for details.

**Important**: Since this server uses Trafilatura's Python API (Option B from docs), it constitutes a derivative work under GPL-3.0. If you need different licensing terms, consider:
- Using Option A (CLI subprocess approach) for more licensing flexibility
- Implementing your own extraction logic
- Contacting Trafilatura maintainers for commercial licensing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Support

For issues, questions, or contributions, please visit the project repository or open an issue.

## Changelog

### v0.1.0
- Initial release
- Basic content extraction from URLs and HTML
- Support for multiple output formats
- Comprehensive error handling and validation
- Async implementation with timeout support