Short answer: yes—writing the MCP server **in Python** is clean and makes dependency install trivial via `requirements.txt`/`pyproject.toml`. Here’s a minimal, production-ready template that:

* Installs **Trafilatura** as a normal dependency (no ad-hoc bootstrap logic).
* Exposes a single tool `extract_markdown`.
* Uses the **Trafilatura CLI** under the hood (stable flags, same behavior you get from the terminal).
* Keeps a switch to move to the **Python API** later if you want.

---

# Option A (recommended): Python MCP server that shells out to Trafilatura CLI

## `pyproject.toml`

```toml
[project]
name = "trafilatura-mcp"
version = "0.1.0"
description = "MCP server exposing Trafilatura as an extract_markdown tool"
requires-python = ">=3.9"
dependencies = [
  "modelcontextprotocol>=0.1.0",
  "pydantic>=2.7.0",
  "trafilatura>=1.9.0",
]

[project.scripts]
trafilatura-mcp = "trafilatura_mcp.server:main"

[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
```

## `src/trafilatura_mcp/server.py`

```python
import asyncio
from asyncio.subprocess import PIPE
from typing import Optional

from pydantic import BaseModel, Field, model_validator
from modelcontextprotocol.server import Server
from modelcontextprotocol.transport.stdio import stdio_transport


class Input(BaseModel):
    # Provide exactly one of these:
    url: Optional[str] = Field(default=None, description="URL to fetch")
    html: Optional[str] = Field(default=None, description="Raw HTML to parse")

    # Tuning knobs (mirrors CLI)
    precision: bool = Field(default=True, description="Favor precision over recall")
    noComments: bool = Field(default=True, description="Strip comments")
    noTables: bool = Field(default=False, description="Strip tables")
    timeoutMs: int = Field(default=20000, ge=1000, le=120000)

    @model_validator(mode="after")
    def _exactly_one(cls, values):
        if bool(values.url) == bool(values.html):
            raise ValueError("Provide exactly one of 'url' or 'html'.")
        return values


async def _run_trafilatura_cli(i: Input) -> str:
    # Build CLI args
    args = ["trafilatura", "--markdown"]
    if i.precision:
        args.append("--precision")
    if i.noComments:
        args.append("--no-comments")
    if i.noTables:
        args.append("--no-tables")

    # Either -u URL ... or stdin HTML ...
    if i.url:
        args.extend(["-u", i.url])
        proc = await asyncio.create_subprocess_exec(
            *args, stdout=PIPE, stderr=PIPE
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=i.timeoutMs / 1000)
        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError("Timed out invoking Trafilatura.")
    else:
        proc = await asyncio.create_subprocess_exec(
            *args, stdin=PIPE, stdout=PIPE, stderr=PIPE
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(input=i.html.encode("utf-8")), timeout=i.timeoutMs / 1000)
        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError("Timed out invoking Trafilatura.")

    if proc.returncode != 0:
        msg = (err or b"").decode("utf-8", errors="ignore")[:2000]
        raise RuntimeError(f"Trafilatura failed (exit {proc.returncode}). {msg}")

    md = (out or b"").decode("utf-8", errors="ignore").strip()
    if not md:
        raise RuntimeError("Trafilatura returned empty output.")
    return md


server = Server(name="trafilatura-mcp", version="0.1.0")


@server.tool(
    name="extract_markdown",
    description="Extract main article content and return Markdown using Trafilatura.",
    input_model=Input,
)
async def extract_markdown_tool(payload: dict):
    i = Input(**payload)
    md = await _run_trafilatura_cli(i)
    return {"content": [{"type": "text", "text": md}]}


def main():
    server.run(stdio_transport())


if __name__ == "__main__":
    main()
```

### Install & run

```bash
# create venv (recommended)
python -m venv .venv && . .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -U pip
pip install -e .    # installs your MCP server + trafilatura

# Run (MCP clients will typically spawn this)
trafilatura-mcp
```

Register the server in your MCP client as:

```json
{ "name": "trafilatura-mcp", "command": "trafilatura-mcp", "args": [] }
```

**Why this is the easiest path:** your deploy story is “`pip install .`”. Dependencies (including Trafilatura) are handled by standard packaging; no custom bootstrap; deterministic with version pins if you want them.

---

# Option B: Same server, but call Trafilatura’s Python API (no subprocess)

Swap `_run_trafilatura_cli` with the native API. This is a bit faster and avoids spawning a process, but make sure your flags map to API args you want.

```python
from trafilatura import fetch_url, extract

async def _run_trafilatura_api(i: Input) -> str:
    # 1) get HTML
    html = i.html
    if i.url:
        html = fetch_url(i.url)
    if not html:
        raise RuntimeError("Failed to fetch/receive HTML.")

    # 2) extract → Markdown
    # favor_recall=False ≈ precision mode; set include_tables opposite of noTables
    md = extract(
        html,
        output_format="markdown",
        include_comments=not i.noComments,
        include_tables=not i.noTables,
        favor_recall=not i.precision,
    )
    if not md:
        raise RuntimeError("Trafilatura returned empty output.")
    return md
```

Then point the tool to `_run_trafilatura_api(i)` instead.

---

## Which should you pick?

* **Internal use and you want 1:1 behavior with the CLI** → **Option A (CLI)**. It’s rock-solid and mirrors docs/examples you’ll find elsewhere.
* **You want slightly lower latency and tighter control** → **Option B (API)**.

### One caveat (licensing, told straight)

Importing Trafilatura (Option B) makes your server a combined work under **GPLv3** if you distribute it. If that’s a problem, stick to Option A + distribute your code under your preferred license, and let ops install `trafilatura` from PyPI alongside it (still fine to list it in requirements for internal deployments).

---

If you tell me which client you’re using (VS Code, Cursor, custom), I’ll add a tiny end-to-end test + a sample tool call JSON so you can smoke-test it quickly.
