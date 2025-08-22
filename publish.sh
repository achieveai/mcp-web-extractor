#!/bin/bash
# Publishing script for mcp-web-extractor

set -e  # Exit on error

echo "MCP Trafilatura Publishing Script"
echo "=================================="
echo ""

# Check if version argument provided
if [ -z "$1" ]; then
    echo "Usage: ./publish.sh <version> [--test]"
    echo "Example: ./publish.sh 0.1.0 --test"
    exit 1
fi

VERSION=$1
TEST_MODE=${2:-""}

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check Python and required tools
echo "Checking prerequisites..."
if ! command -v python &> /dev/null; then
    print_error "Python is not installed"
    exit 1
fi
print_status "Python found: $(python --version)"

# Install/upgrade build tools
echo ""
echo "Installing/upgrading build tools..."
pip install -U pip build twine > /dev/null 2>&1
print_status "Build tools ready"

# Update version in pyproject.toml
echo ""
echo "Updating version to $VERSION..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/^version = \".*\"/version = \"$VERSION\"/" pyproject.toml
else
    # Linux/Windows Git Bash
    sed -i "s/^version = \".*\"/version = \"$VERSION\"/" pyproject.toml
fi
print_status "Version updated in pyproject.toml"

# Clean previous builds
echo ""
echo "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info src/*.egg-info 2>/dev/null || true
print_status "Clean build environment"

# Build the package
echo ""
echo "Building package..."
python -m build
print_status "Package built successfully"

# Check the package
echo ""
echo "Verifying package..."
twine check dist/*
print_status "Package verification passed"

# List built files
echo ""
echo "Built files:"
ls -la dist/

# Handle test vs production publishing
if [ "$TEST_MODE" == "--test" ]; then
    echo ""
    print_warning "TEST MODE - Publishing to TestPyPI"
    echo ""
    
    if [ -z "$TESTPYPI_TOKEN" ]; then
        print_warning "TESTPYPI_TOKEN not set. You'll need to enter credentials manually."
        echo "Get your token from: https://test.pypi.org/manage/account/token/"
    else
        export TWINE_USERNAME="__token__"
        export TWINE_PASSWORD="$TESTPYPI_TOKEN"
    fi
    
    echo "Uploading to TestPyPI..."
    twine upload -r testpypi dist/*
    
    echo ""
    print_status "Published to TestPyPI!"
    echo ""
    echo "Test installation with:"
    echo "  pip install -i https://test.pypi.org/simple/ mcp-web-extractor==$VERSION \\"
    echo "    --extra-index-url https://pypi.org/simple"
    echo ""
    echo "Or with uvx:"
    echo "  uvx --index-url https://test.pypi.org/simple/ mcp-web-extractor"
    
else
    echo ""
    print_warning "PRODUCTION MODE - Publishing to PyPI"
    echo ""
    
    # Confirmation prompt
    read -p "Are you sure you want to publish v$VERSION to PyPI? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Publishing cancelled"
        exit 1
    fi
    
    if [ -z "$PYPI_TOKEN" ]; then
        print_warning "PYPI_TOKEN not set. You'll need to enter credentials manually."
        echo "Get your token from: https://pypi.org/manage/account/token/"
    else
        export TWINE_USERNAME="__token__"
        export TWINE_PASSWORD="$PYPI_TOKEN"
    fi
    
    echo ""
    echo "Uploading to PyPI..."
    twine upload dist/*
    
    echo ""
    print_status "Published to PyPI!"
    echo ""
    echo "Package available at: https://pypi.org/project/mcp-web-extractor/$VERSION/"
    echo ""
    echo "Install with:"
    echo "  pip install mcp-web-extractor"
    echo ""
    echo "Or run directly with:"
    echo "  uvx mcp-web-extractor"
    echo ""
    echo "Don't forget to:"
    echo "  1. Create a git tag: git tag -a v$VERSION -m 'Release version $VERSION'"
    echo "  2. Push the tag: git push origin v$VERSION"
    echo "  3. Create a GitHub release"
fi

echo ""
print_status "Publishing complete!"