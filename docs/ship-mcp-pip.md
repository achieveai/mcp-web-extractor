Here’s the no-nonsense path to ship your MCP server to PyPI (“pip install …”).

# 0) Layout (keep it boring + standard)

```
trafilatura-mcp/
├─ src/
│  └─ trafilatura_mcp/
│     ├─ __init__.py
│     └─ server.py          # the MCP server from before
├─ pyproject.toml
├─ README.md
├─ LICENSE
└─ MANIFEST.in              # optional (see below)
```

# 1) pyproject.toml (copy/paste + tweak)

Use modern PEP 621 metadata. This example publishes a pure-Python wheel with a console entry point `trafilatura-mcp`.

```toml
[project]
name = "trafilatura-mcp"               # check name availability on TestPyPI first
version = "0.1.0"                      # bump every release (PEP 440)
description = "MCP server exposing Trafilatura as an extract_markdown tool"
readme = "README.md"
requires-python = ">=3.9"
license = { file = "LICENSE" }
keywords = ["mcp", "model context protocol", "markdown", "extraction", "trafilatura"]
authors = [{ name = "Your Name", email = "you@example.com" }]
classifiers = [
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3 :: Only",
  "License :: OSI Approved :: MIT License",
  "Intended Audience :: Developers",
  "Topic :: Internet :: WWW/HTTP",
]

# Runtime deps. If you’re shelling out to the CLI, you can either:
#   (A) depend on trafilatura so it's installed alongside, or
#   (B) omit it and document that the CLI must be present.
# Most convenient is (A):
dependencies = [
  "modelcontextprotocol>=0.1.0",
  "pydantic>=2.7.0",
  "trafilatura>=1.9.0,<2.0.0",
]

[project.scripts]
trafilatura-mcp = "trafilatura_mcp.server:main"

[project.urls]
Homepage = "https://github.com/yourorg/trafilatura-mcp"
Issues = "https://github.com/yourorg/trafilatura-mcp/issues"

[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
```

**Why MIT above?** Your server can be MIT even if it *invokes* a GPLv3 tool via subprocess. If you ever switch to importing Trafilatura’s Python API directly, reassess licensing.

# 2) README.md & LICENSE

* Keep README short, with:

  * what it is,
  * install,
  * quick start (how MCP clients register it),
  * a minimal example command.
* Put a real LICENSE (MIT/Apache-2.0/etc). The `license` field points to it.

# 3) MANIFEST.in (optional but safe)

If you want to guarantee README/LICENSE land in the sdist:

```
include README.md
include LICENSE
```

# 4) Build the distributions

Use the standard build + twine flow in a clean venv:

```bash
python -m venv .venv
. .venv/bin/activate                   # Windows: .venv\Scripts\activate
pip install -U pip build twine

# Build sdist + wheel (py3-none-any)
python -m build                        # creates dist/*.tar.gz and dist/*.whl

# Sanity checks
twine check dist/*
```

# 5) Create a PyPI API token

* Do **TestPyPI** first (recommended), then PyPI.
* In your account → “API tokens” → create a token (scoped to the project if it exists, else “entire account” for first upload).
* Export credentials for Twine:

  ```bash
  export TWINE_USERNAME="__token__"
  export TWINE_PASSWORD="pypi-AgENdGVzdHA..."   # or real PyPI token later
  ```

# 6) Upload to **TestPyPI** (dry run the whole pipeline)

```bash
twine upload -r testpypi dist/*
```

Fresh venv install test:

```bash
python -m venv /tmp/t && . /tmp/t/bin/activate
# Pull your package from TestPyPI, deps from real PyPI:
pip install -i https://test.pypi.org/simple/ trafilatura-mcp==0.1.0 \
  --extra-index-url https://pypi.org/simple

# Smoke test: will start your server (Ctrl+C to exit)
trafilatura-mcp
```

# 7) Upload to **PyPI** (real thing)

```bash
# switch TWINE_PASSWORD to your real PyPI token
twine upload dist/*
```

# 8) Versioning + re-releases

* PyPI is **immutable** per version. To fix anything, bump `version` (e.g., `0.1.1`) and rebuild/upload.
* Follow PEP 440 (e.g., `0.2.0`, `0.2.1`, `0.3.0b1` for betas).

# 9) CI (optional but worth it)

* Add a GitHub Action to build on tag and `twine upload` using a PyPI token stored as a secret.
* Keep your wheel pure-Python so you don’t need multi-arch builds.

# 10) Common pitfalls (so you don’t waste time)

* **Name already taken** → pick something unique (e.g., `mcp-trafilatura`).
* **Missing entry point** → ensure `[project.scripts]` block is correct and `server:main` exists.
* **Long description missing on PyPI** → ensure `readme = "README.md"` in `pyproject.toml`.
* **Broken install on TestPyPI** → remember `--extra-index-url https://pypi.org/simple` so dependencies resolve from main PyPI.
* **Forgot to bump version** → PyPI rejects re-uploads with same version.

That’s it. If you want, paste your current `pyproject.toml` and I’ll sanity-check it before you publish.
