Here’s a clean, production-ready way to expose **Trafilatura** as an MCP tool. I’m giving you a Node (TypeScript) MCP server that shells out to the Trafilatura CLI. It’s the easiest to deploy, works with any MCP-capable client, and keeps Trafilatura swappable.

---

# What you get

* An MCP server named `trafilatura-mcp`
* One tool: `extract_markdown`

  * Accepts **either** a `url` **or** raw `html` (exactly one required)
  * Optional flags: `precision`, `noComments`, `noTables`, `timeoutMs`
* Streams nothing; returns a single Markdown string
* Timeouts + robust subprocess error handling
* Optional headless prerender (Playwright) hook you can enable later if needed

---

# 1) Server (TypeScript, Node)

> Directory: `servers/trafilatura-mcp`

**`package.json`**

```json
{
  "name": "trafilatura-mcp",
  "version": "0.1.0",
  "type": "module",
  "private": true,
  "bin": {
    "trafilatura-mcp": "./dist/server.js"
  },
  "scripts": {
    "build": "tsc -p tsconfig.json",
    "start": "node dist/server.js",
    "dev": "tsx src/server.ts"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "execa": "^9.2.0",
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "tsx": "^4.19.2",
    "typescript": "^5.5.4"
  }
}
```

**`tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "Bundler",
    "strict": true,
    "outDir": "dist",
    "skipLibCheck": true
  },
  "include": ["src"]
}
```

**`src/server.ts`**

```ts
import { createServer, stdioServerTransport, ToolHandler } from "@modelcontextprotocol/sdk/server";
import { z } from "zod";
import { execa } from "execa";

// ----- Tool input schema -----------------------------------------------------
const Input = z.object({
  // Exactly one of these must be provided
  url: z.string().url().optional(),
  html: z.string().min(1).optional(),

  // Optional tuning knobs
  precision: z.boolean().default(true),
  noComments: z.boolean().default(true),
  noTables: z.boolean().default(false),

  // Timeout for the trafilatura subprocess
  timeoutMs: z.number().int().positive().max(120000).default(20000)
}).refine(
  (v) => (v.url ? !v.html : !!v.html),
  { message: "Provide exactly one of 'url' or 'html'." }
);

// ----- Tool implementation ---------------------------------------------------
const extractMarkdown: ToolHandler<typeof Input> = async (args, _ctx) => {
  const { url, html, precision, noComments, noTables, timeoutMs } = Input.parse(args);

  // Build argument list for trafilatura CLI
  const cliArgs = ["--markdown"];
  if (precision) cliArgs.push("--precision");
  if (noComments) cliArgs.push("--no-comments");
  if (noTables)   cliArgs.push("--no-tables");

  // We will either: trafilatura -u URL ...  OR  echo HTML | trafilatura ...
  let child;
  try {
    if (url) {
      child = execa("trafilatura", ["-u", url, ...cliArgs], {
        timeout: timeoutMs
      });
    } else {
      child = execa("trafilatura", cliArgs, {
        timeout: timeoutMs,
        input: html,          // piped HTML to stdin
        stdin: "pipe"
      });
    }

    const { stdout } = await child;
    const md = stdout?.trim() ?? "";

    if (!md) {
      return {
        content: [{ type: "text", text: "Trafilatura returned empty output (no main content found)." }],
        isError: true
      };
    }

    return { content: [{ type: "text", text: md }] };
  } catch (err: any) {
    const msg = [
      "Trafilatura failed.",
      err.shortMessage || err.message || String(err),
      err.stderr ? `STDERR: ${String(err.stderr).slice(0, 2000)}` : ""
    ].filter(Boolean).join("\n");

    return { content: [{ type: "text", text: msg }], isError: true };
  }
};

// ----- Optional: prerender with Playwright (for heavy JS pages) --------------
// If you need it later, uncomment and wire a boolean flag (e.g., render: true) in schema.
// async function prerenderHTML(url: string): Promise<string> {
//   const { chromium } = await import("playwright");
//   const browser = await chromium.launch({ headless: true });
//   const page = await browser.newPage();
//   await page.goto(url, { waitUntil: "networkidle" });
//   const html = await page.content();
//   await browser.close();
//   return html;
// }

// ----- Server bootstrap ------------------------------------------------------
const server = createServer(
  { name: "trafilatura-mcp", version: "0.1.0" },
  {
    tools: {
      extract_markdown: {
        description: "Extract main article content and return Markdown using Trafilatura.",
        inputSchema: Input,
        handler: extractMarkdown
      }
    }
  }
);

server.connect(stdioServerTransport());
```

> Notes:
>
> * Uses the SDK’s built-in `stdio` transport (works with most MCP clients).
> * Enforces “exactly one of `url` or `html`” at the schema level.
> * Times out the CLI to avoid hung processes.
> * Keeps Trafilatura flags focused and safe; you can add more later if you actually need them.

---

# 2) Install & run

**Prereqs**

* Node 18+ (or 20+ recommended)
* Python 3.9+ with Trafilatura installed

```bash
# Install trafilatura system-wide or in a venv
python -m pip install --upgrade trafilatura

# Set up the server
npm i
npm run build

# Run on stdio (MCP clients will spawn this)
trafilatura-mcp
# or
npm run start
```

**Local smoke tests (no MCP client)**

```bash
# URL mode
trafilatura -u "https://example.com" --markdown --precision | head

# HTML pipe mode
curl -s https://example.com | trafilatura --markdown --precision | head
```

---

# 3) Wire it into your MCP client

Different clients register MCP servers differently. Typical JSON entry looks like:

```json
{
  "name": "trafilatura-mcp",
  "command": "trafilatura-mcp",
  "args": []
}
```

Once registered, you’ll see a tool called **`extract_markdown`** with this signature:

```json
{
  "name": "extract_markdown",
  "input": {
    "url": "https://news.ycombinator.com/item?id=123456",
    "precision": true,
    "noComments": true,
    "noTables": false,
    "timeoutMs": 20000
  }
}
```

Or:

```json
{
  "name": "extract_markdown",
  "input": {
    "html": "<!doctype html> ...",
    "precision": true
  }
}
```

---

# 4) Docker (optional but handy)

If you want a single artifact with both Node + Trafilatura:

**`Dockerfile`**

```dockerfile
FROM node:22-slim AS base
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir trafilatura

WORKDIR /app
COPY package*.json tsconfig.json ./
COPY src ./src
RUN npm ci && npm run build

# Runtime
FROM node:22-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
RUN python3 -m pip install --no-cache-dir trafilatura
WORKDIR /app
COPY --from=base /app/dist ./dist
COPY package*.json ./
RUN npm ci --omit=dev
ENTRYPOINT ["node", "dist/server.js"]
```

Build & run:

```bash
docker build -t trafilatura-mcp:0.1.0 .
docker run -i --rm trafilatura-mcp:0.1.0
```

---

# 5) Why this shape works well for MCP

* **Simple surface area:** one tool, small schema, clear error messages.
* **Copyleft isolation:** you’re not linking Python code; you’re shelling out to a GPLv3 CLI. If licensing is a concern for distribution, this is the least-entangled approach and easy to swap later.
* **Extensible:** add a `render: true` boolean and use Playwright to prerender SPA pages, then pipe `page.content()` into Trafilatura (already scaffolded).
* **Safe defaults:** `--precision` + `--no-comments` give you clean Markdown without gutting tables by default.

---

# 6) Python MCP server (if you prefer Python)

If your whole MCP stack is Python, the core changes are just the server skeleton—your tool body still shells out to `trafilatura`:

```py
# requirements: modelcontextprotocol, trafilatura (already installed), pydantic
import asyncio, json, sys
from pydantic import BaseModel, Field, root_validator
from modelcontextprotocol.server import Server
from modelcontextprotocol.transport.stdio import stdio_transport
from asyncio.subprocess import create_subprocess_exec, PIPE

class Input(BaseModel):
    url: str | None = None
    html: str | None = None
    precision: bool = True
    noComments: bool = True
    noTables: bool = False
    timeoutMs: int = 20000

    @root_validator
    def exactly_one(cls, v):
        if bool(v.get("url")) == bool(v.get("html")):
            raise ValueError("Provide exactly one of 'url' or 'html'.")
        return v

async def run_trafilatura(i: Input) -> str:
    args = ["--markdown"]
    if i.precision: args.append("--precision")
    if i.noComments: args.append("--no-comments")
    if i.noTables: args.append("--no-tables")

    if i.url:
        cmd = ["trafilatura", "-u", i.url, *args]
        proc = await asyncio.wait_for(create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE), i.timeoutMs/1000)
        out, err = await proc.communicate()
    else:
        cmd = ["trafilatura", *args]
        proc = await asyncio.wait_for(create_subprocess_exec(*cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE), i.timeoutMs/1000)
        out, err = await proc.communicate(input=i.html.encode("utf-8"))

    if proc.returncode != 0:
        raise RuntimeError(f"Trafilatura failed: {err.decode('utf-8')[:2000]}")
    text = out.decode("utf-8").strip()
    if not text:
        raise RuntimeError("Trafilatura returned empty output.")
    return text

server = Server(name="trafilatura-mcp", version="0.1.0")

@server.tool(
    name="extract_markdown",
    description="Extract main article content and return Markdown using Trafilatura.",
    input_model=Input
)
async def extract_markdown_tool(input: dict):
    i = Input(**input)
    md = await run_trafilatura(i)
    return {"content": [{"type": "text", "text": md}]}

if __name__ == "__main__":
    server.run(stdio_transport())
```

---

If you want, tell me which runtime you’re actually deploying (Node or Python) and I’ll tailor this down further (plus add a tiny integration test that calls the tool the way your chosen MCP client will).
