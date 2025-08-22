# How it works

1. Look for an existing `trafilatura` on `PATH`.
2. If missing, pick a cache dir (e.g., `~/.cache/trafilatura-mcp/venv` or `%LOCALAPPDATA%\trafilatura-mcp\venv`).
3. Create a venv (`python -m venv`), upgrade pip, `pip install trafilatura`.
4. Return the absolute path to the CLI (`venv/bin/trafilatura` or `venv\Scripts\trafilatura.exe`).
5. Use that path in your tool.

You can pin the version via `TRAFILATURA_VERSION=1.9.*` (or whatever you like) and choose the Python binary via `TRAFILATURA_PYTHON`.

---

# Drop-in code (TypeScript, Node MCP)

**`src/ensureTrafilatura.ts`**

```ts
import os from "os";
import path from "path";
import { promises as fs } from "fs";
import { execa } from "execa";

function isWin() { return process.platform === "win32"; }

function cacheHome(): string {
  if (process.env.TRAFILATURA_MCP_HOME) return process.env.TRAFILATURA_MCP_HOME;
  if (isWin()) return path.join(process.env.LOCALAPPDATA || path.join(os.homedir(), "AppData", "Local"), "trafilatura-mcp");
  const xdg = process.env.XDG_CACHE_HOME || path.join(os.homedir(), ".cache");
  return path.join(xdg, "trafilatura-mcp");
}

async function exists(p: string): Promise<boolean> {
  try { await fs.access(p); return true; } catch { return false; }
}

async function which(cmd: string): Promise<string | null> {
  try {
    const { stdout } = await execa(isWin() ? "where" : "which", [cmd]);
    const first = stdout.split(/\r?\n/).map(s => s.trim()).filter(Boolean)[0];
    return first || null;
  } catch { return null; }
}

function venvPaths(venvDir: string) {
  const binDir = path.join(venvDir, isWin() ? "Scripts" : "bin");
  return {
    binDir,
    python: path.join(binDir, isWin() ? "python.exe" : "python3"),
    pip: path.join(binDir, isWin() ? "pip.exe" : "pip"),
    trafilatura: path.join(binDir, isWin() ? "trafilatura.exe" : "trafilatura"),
  };
}

async function pickSystemPython(): Promise<string | null> {
  // Allow override
  if (process.env.TRAFILATURA_PYTHON) return process.env.TRAFILATURA_PYTHON;
  // Common candidates
  for (const c of ["python3", "python", "py"]) {
    const p = await which(c);
    if (p) return c === "py" ? "py" : p; // 'py' launcher on Windows
  }
  return null;
}

export async function ensureTrafilatura(): Promise<string> {
  // 1) If already on PATH, use it.
  const onPath = await which("trafilatura");
  if (onPath) return onPath;

  // 2) Bootstrap venv
  const home = cacheHome();
  const venvDir = path.join(home, "venv");
  const { python, pip, trafilatura } = venvPaths(venvDir);

  // Simple idempotent lock to avoid races
  const lock = path.join(home, "install.lock");
  await fs.mkdir(home, { recursive: true });

  // If CLI exists, return it.
  if (await exists(trafilatura)) return trafilatura;

  // Acquire lock (best-effort)
  let haveLock = false;
  try {
    const fd = await fs.open(lock, "wx"); await fd.close(); haveLock = true;
  } catch { /* someone else is installing */ }

  try {
    // If someone else is installing, wait briefly up to ~30s
    if (!haveLock) {
      for (let i = 0; i < 60; i++) {
        if (await exists(trafilatura)) return trafilatura;
        await new Promise(r => setTimeout(r, 500));
      }
      // Timeout; continue to try ourselves.
    }

    const sysPy = await pickSystemPython();
    if (!sysPy) throw new Error("No Python found. Install Python 3.9+ or set TRAFILATURA_PYTHON to a python executable.");

    // Create venv if missing
    if (!(await exists(python))) {
      if (isWin() && sysPy === "py") {
        await execa("py", ["-3", "-m", "venv", venvDir], { stdio: "inherit" });
      } else {
        await execa(sysPy, ["-m", "venv", venvDir], { stdio: "inherit" });
      }
    }

    // Upgrade pip + wheel + setuptools
    await execa(python, ["-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], { stdio: "inherit" });

    // Install Trafilatura (pin optionally via env)
    const version = process.env.TRAFILATURA_VERSION?.trim();
    const pkg = version ? `trafilatura==${version}` : "trafilatura";
    await execa(python, ["-m", "pip", "install", "--upgrade", pkg], { stdio: "inherit" });

    if (!(await exists(trafilatura))) {
      throw new Error(`Trafilatura CLI missing after install: ${trafilatura}`);
    }
    return trafilatura;
  } finally {
    if (haveLock) {
      try { await fs.unlink(lock); } catch {}
    }
  }
}
```

**Integrate into your server** (replace the earlier hardcoded `"trafilatura"`):

**`src/server.ts`** (only the changed parts)

```ts
import { execa } from "execa";
import { ensureTrafilatura } from "./ensureTrafilatura";

// inside your handler:
const bin = await ensureTrafilatura();
if (url) {
  child = execa(bin, ["-u", url, ...cliArgs], { timeout: timeoutMs });
} else {
  child = execa(bin, cliArgs, { timeout: timeoutMs, input: html, stdin: "pipe" });
}
```

---

## Env knobs you can expose

* `TRAFILATURA_VERSION` → pin to a specific version (e.g., `1.9.*`) for reproducibility.
* `TRAFILATURA_PYTHON` → absolute path to a specific Python (useful behind corp IT images).
* `TRAFILATURA_MCP_HOME` → where to create/cache the venv.

---

## Notes, gotchas, and the no-nonsense bits

* **Cold start latency:** first call pays the pip install cost. If that’s not acceptable, run `ensureTrafilatura()` once at server startup.
* **JS-rendered sites:** Trafilatura doesn’t run JS. If you need it, prerender with Playwright, then pipe HTML into the tool. Keep this optional so you don’t drag Chromium into every install.
* **Proxies/SSL MITM:** pip respects `HTTPS_PROXY`, `HTTP_PROXY`, `PIP_INDEX_URL`, and cert envs. If you’re behind a corporate proxy/CA, pass these through your MCP server’s env.
* **Licensing:** you’re invoking a GPLv3 tool as a subprocess (cleaner boundary). If redistribution is a concern, you can switch to Readability+Turndown later without touching the client surface.

If you want, I can add a **preflight** command (e.g., `setup_trafilatura`) so you can warm the venv explicitly, plus a health check tool that returns the resolved binary path and version.
