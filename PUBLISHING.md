# Publishing to PyPI

This guide covers how to publish `mcp-web-extractor` to PyPI.

## Prerequisites

1. Ensure you have a PyPI account at https://pypi.org
2. Create an API token at https://pypi.org/manage/account/token/
3. Install build tools:
   ```bash
   pip install -U pip build twine
   ```

## Pre-Publishing Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Update CHANGELOG or version notes in README
- [ ] Ensure all tests pass
- [ ] Verify LICENSE file is present
- [ ] Check that package name is available on PyPI

## Building the Package

1. Clean previous builds:
   ```bash
   rm -rf dist/ build/ *.egg-info/
   ```

2. Build source distribution and wheel:
   ```bash
   python -m build
   ```

3. Verify the build:
   ```bash
   twine check dist/*
   ```

## Testing on TestPyPI (Recommended First Step)

1. Create a TestPyPI account at https://test.pypi.org
2. Create an API token for TestPyPI
3. Set environment variables:
   ```bash
   export TWINE_USERNAME="__token__"
   export TWINE_PASSWORD="pypi-AgENdGVzdC..."  # Your TestPyPI token
   ```

4. Upload to TestPyPI:
   ```bash
   twine upload -r testpypi dist/*
   ```

5. Test installation from TestPyPI:
   ```bash
   # Create a fresh virtual environment
   python -m venv test-env
   source test-env/bin/activate  # On Windows: test-env\Scripts\activate
   
   # Install from TestPyPI
   pip install -i https://test.pypi.org/simple/ mcp-web-extractor==0.1.0 \
     --extra-index-url https://pypi.org/simple
   
   # Test the command
   mcp-web-extractor --help
   ```

## Publishing to PyPI

1. Set your PyPI credentials:
   ```bash
   export TWINE_USERNAME="__token__"
   export TWINE_PASSWORD="pypi-AgENdGVzdC..."  # Your real PyPI token
   ```

2. Upload to PyPI:
   ```bash
   twine upload dist/*
   ```

3. Verify installation:
   ```bash
   pip install mcp-web-extractor
   mcp-web-extractor --help
   ```

## Using GitHub Actions (Optional)

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine
      
      - name: Build package
        run: python -m build
      
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

Then add your PyPI token as a GitHub secret named `PYPI_API_TOKEN`.

## Version Management

Follow semantic versioning (SemVer):
- MAJOR version for incompatible API changes
- MINOR version for new functionality (backwards compatible)
- PATCH version for backwards compatible bug fixes

Examples:
- `0.1.0` → `0.1.1` (bug fix)
- `0.1.1` → `0.2.0` (new feature)
- `0.2.0` → `1.0.0` (stable release or breaking change)

## Post-Publishing

1. Create a git tag:
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   git push origin v0.1.0
   ```

2. Update installation instructions in README if needed

3. Announce the release (optional):
   - GitHub releases page
   - Project documentation
   - Social media

## Troubleshooting

### Name Already Taken
- Choose a different name (e.g., `mcp-web-extractor-extract`)
- Check availability at https://pypi.org/project/YOUR-NAME/

### Upload Fails
- Verify your API token is correct
- Check that version number was incremented
- Ensure all required files are present

### Installation Issues
- Test in a clean virtual environment
- Verify all dependencies are specified in `pyproject.toml`
- Check Python version compatibility

### Missing Files in Package
- Update `MANIFEST.in` to include necessary files
- Verify with `tar -tzf dist/*.tar.gz` after building

## Quick Command Reference

```bash
# Full publishing workflow
rm -rf dist/ build/
python -m build
twine check dist/*
twine upload -r testpypi dist/*  # Test first
twine upload dist/*               # Then production
```

## Using uvx After Publishing

Once published to PyPI, users can run directly with:

```bash
# No installation needed!
uvx mcp-web-extractor

# Or with pipx
pipx run mcp-web-extractor
```

This makes the tool instantly available to all MCP users without any setup.