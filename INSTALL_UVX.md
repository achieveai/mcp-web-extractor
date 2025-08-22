# Installing and Running with uvx

[uvx](https://github.com/astral-sh/uv) is a fast Python package installer and runner that makes it easy to run Python applications without manual virtual environment management.

## Prerequisites

First, install `uv` if you haven't already:

### Windows
```powershell
# Using PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or using winget
winget install --id=astral-sh.uv -e

# Or using Scoop
scoop install uv
```

### macOS/Linux
```bash
# Using curl
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using Homebrew
brew install uv

# Or using pip
pip install uv
```

## Running the MCP Server with uvx

### Quick Start (No Installation Required)

Run the server directly from PyPI:

```bash
# Install from PyPI and run
uvx mcp-trafilatura
```

For local development:

```bash
# From the project directory
uvx --from . mcp-trafilatura

# Or from any location
uvx --from /path/to/mcp-trafilatura mcp-trafilatura
```

### For Development

If you're actively developing the server:

```bash
# Create a virtual environment with uv
uv venv

# Install the package in editable mode
uv pip install -e .

# Run with uv
uv run mcp-trafilatura
```

## Configuring MCP Clients to Use uvx

### Claude Desktop Configuration

Edit your Claude Desktop configuration file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

Add the following configuration:

```json
{
  "mcpServers": {
    "trafilatura": {
      "command": "uvx",
      "args": ["mcp-trafilatura"]
    }
  }
}
```

For local development:
```json
{
  "mcpServers": {
    "trafilatura": {
      "command": "uvx",
      "args": ["--from", "/absolute/path/to/mcp-trafilatura", "mcp-trafilatura"]
    }
  }
}
```

**Note**: Replace `/absolute/path/to/mcp-trafilatura` with the actual absolute path to your project directory.

### VS Code with Continue

Add to your Continue configuration:

```json
{
  "mcpServers": [
    {
      "name": "trafilatura",
      "command": "uvx",
      "args": ["mcp-trafilatura"]
    }
  ]
}
```

### Environment Variables (Optional)

You can set environment variables for the server:

```json
{
  "mcpServers": {
    "trafilatura": {
      "command": "uvx",
      "args": ["mcp-trafilatura"],
      "env": {
        "LOG_LEVEL": "DEBUG",
        "TIMEOUT": "60"
      }
    }
  }
}
```

## Benefits of Using uvx

1. **No Virtual Environment Management**: uvx handles virtual environments automatically
2. **Isolated Dependencies**: Each tool runs in its own isolated environment
3. **Fast Installation**: uv is significantly faster than pip
4. **Reproducible**: Ensures consistent dependency versions
5. **Simple Updates**: Just pull the latest code and uvx handles the rest

## Troubleshooting

### Command Not Found

If `uvx` is not found, ensure uv is installed and in your PATH:

```bash
# Check if uv is installed
uv --version

# If not found, reinstall uv and ensure it's in PATH
```

### Permission Errors

On Unix-like systems, you might need to make the script executable:

```bash
chmod +x src/trafilatura_mcp/server.py
```

### Dependencies Not Found

If you get import errors, ensure all dependencies are specified in `pyproject.toml`:

```bash
# Clear uv cache and retry
uv cache clean
uvx --from . mcp-trafilatura
```

### Debugging

To see more detailed output:

```bash
# Run with verbose output
uvx --from . --verbose mcp-trafilatura

# Or set debug logging
LOG_LEVEL=DEBUG uvx --from . mcp-trafilatura
```

## Publishing to PyPI (Optional)

If you want to make the server available via `uvx trafilatura-mcp` without specifying a path:

1. Build the package:
   ```bash
   uv build
   ```

2. Upload to PyPI:
   ```bash
   uv publish
   ```

3. Then anyone can run:
   ```bash
   uvx mcp-trafilatura
   ```

## Alternative: Using uv pip

If you prefer a more traditional approach with uv:

```bash
# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
uv pip install .

# Run the server
mcp-trafilatura
```

## Notes

- uvx always uses the latest compatible Python version available on your system
- Dependencies are cached globally, so subsequent runs are faster
- The server runs in an isolated environment, preventing conflicts with system packages
- Updates to the code are automatically picked up when using `--from .`