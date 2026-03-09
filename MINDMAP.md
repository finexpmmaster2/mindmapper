# Mind Mapper — Project File

**Tool:** Mind Mapper — Workspace Visualizer & Editor  
**Port:** 8081  
**Location:** `agents/developer/tools/mindmapper/`  
**GitHub:** `finexpmmaster2/mindmapper` (private — designed for OpenClaw)  
**Started:** 2026-03-07  
**Status:** Active — portable, installable on any OpenClaw machine  
**Latest commit:** `07ce326`

---

## ⚠️ DESIGN PRINCIPLES — READ BEFORE EVERY CHANGE

**Mind Mapper is designed for OpenClaw and intended for public release.**

All fixes, features, and design decisions MUST consider portability:

- **No hardcoded paths** — use environment variables, `~/.openclaw/openclaw.json`, or auto-detect
- **No hardcoded agent names** — read from `openclaw.json` or auto-detect from `agents/*/`
- **No private tokens, keys, or credentials** in code or commits
- **No internal team references** in user-facing strings
- **Graceful defaults** — if no OpenClaw config exists, scan the workspace and create reasonable defaults
- **Minimal dependencies** — `fastapi` + `uvicorn` only
- **Auto-venv** — `start.sh` creates `.venv` on first run (no system pip needed)

**Before merging any PR, ask:** "Would this work for someone who just cloned the repo and ran `bash start.sh` on their own OpenClaw instance?"

---

## Purpose

Visual interactive mind map + file editor for OpenClaw workspaces. Scans all `.md` files, shows agent hierarchy, file ownership, and cross-references.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python · FastAPI · Uvicorn |
| Frontend | Vanilla JS · D3.js v7 · CSS |
| Graph layout | D3 force simulation (radial cluster, sticky drag) |
| File I/O | Native Python filesystem |
| Network | Configurable bind host (default `127.0.0.1`) |
| Dependencies | `fastapi`, `uvicorn` (2 packages) |

---

## Workspace & Agent Detection

### Detection Priority (workspace root)

1. `MINDMAPPER_WORKSPACE` env var (explicit override)
2. `mindmapper.json` config file (local or app directory)
3. `OPENCLAW_WORKSPACE` env var
4. **`~/.openclaw/`** — auto-detected if `openclaw.json` exists there
5. Current working directory (fallback for standalone use)

### Agent Discovery Priority

1. `mindmapper.json` → `"agents"` array (full control)
2. **`~/.openclaw/openclaw.json`** → `agents.list` (hierarchy from config)
3. Auto-detect from `agents/*/` subdirectories + `SOUL.md` name extraction

### How It Works

- **Hierarchy** (agent → sub-agent): read from `~/.openclaw/openclaw.json`
- **Ownership** (file → agent): determined by matching file paths to agent workspace directories
- **Semantic links** (file → agent): detected from cross-agent mentions in file content

---

## File Structure

```
tools/mindmapper/
├── app.py                  # FastAPI backend — scan, search, save, propagate
├── requirements.txt        # fastapi, uvicorn
├── start.sh                # Launch script — auto-venv, localhost/LAN modes
├── README.md               # Installation & usage docs
├── MINDMAP.md              # This project file
├── mindmapper.example.json # Example config for custom setups
├── .gitignore              # Excludes .venv, __pycache__, mindmapper.json
└── static/
    ├── index.html          # Self-contained frontend (D3.js + CSS + JS)
    └── launcher.html       # Landing page with connection info
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Mind Mapper UI |
| GET | `/launcher` | Landing page with server info |
| GET | `/api/graph` | Full graph: nodes + hierarchy/ownership/semantic edges |
| GET | `/api/file?path=` | Read file content |
| POST | `/api/file` | Save file `{path, content}` |
| GET | `/api/search?q=` | Full-text search with line numbers |
| POST | `/api/propagate` | Smart-merge content to multiple files |
| POST | `/api/rescan` | Force re-discovery of agents and files |
| GET | `/api/backups` | Backup status and history |
| GET | `/api/info` | Server info (IP, port, workspace, agent count) |

---

## Graph Data Model

### Nodes
- **Agent nodes** — one per agent; `type: "agent"`, `group: "agent"`, `id: "agent__<id>"`
- **File nodes** — one per `.md` file; `type: <file_type>`, `group: "file"`, `id: <hash>`

### Edge Types

| Layer | Color | Connects | Toggle |
|-------|-------|----------|--------|
| Hierarchy | cyan thick | agent → sub-agent | ⬡ Hierarchy button |
| Ownership | blue medium | agent → its files | 📂 Ownership button |
| Semantic | purple dashed | file → agent node | ~ Semantic button |

---

## File Type System

| Type | Icon | Color | Detection |
|------|------|-------|-----------|
| agent | 🤖 | `#ffffff` | Config node |
| soul | 🧠 | `#ffd700` | Filename has `SOUL` |
| heartbeat | 💓 | `#ff4466` | Filename has `HEARTBEAT` |
| agents | 🤝 | `#ff66aa` | Filename has `AGENTS` |
| bootstrap | 🚀 | `#00ff88` | Filename has `BOOTSTRAP` |
| tools | 🔧 | `#ff8800` | Filename has `TOOLS` |
| user | 👤 | `#88aaff` | Filename has `USER` |
| identity | 🪪 | `#ff66cc` | Filename has `IDENTITY` |
| comms | 📡 | `#aaffaa` | Filename has `COMMS` |
| memory | 📅 | `#6688cc` | In `memory/` folder or has `MEMORY` |
| draft | 📝 | `#cc9944` | In `drafts/` folder or has `DRAFT` |
| brand | 🎨 | `#cc44ff` | Filename has `BRAND` |
| task | ✅ | `#ffaa44` | Filename has `TASK` |
| readme | 📖 | `#44ddaa` | Filename has `README` |
| document | 📄 | `#667788` | Everything else |

---

## Security Model

**Default:** binds to `127.0.0.1` — localhost only. No network access.

**LAN mode (explicit opt-in only):**
```bash
bash start.sh --lan
# or
MINDMAPPER_HOST=0.0.0.0 python3 app.py
```

⚠️ No authentication — rely entirely on network trust. Never expose to untrusted networks.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MINDMAPPER_WORKSPACE` | auto-detect | Root directory to scan |
| `MINDMAPPER_HOST` | `127.0.0.1` | Bind address |
| `MINDMAPPER_PORT` | `8081` | Server port |
| `MINDMAPPER_BACKUP_DIR` | `<workspace>/.mindmapper_backups` | Backup location |
| `MINDMAPPER_BACKUP_DAYS` | `7` | Backup retention days |
| `OPENCLAW_WORKSPACE` | — | OpenClaw workspace override |

---

## Scanner Rules

Scans all `*.md` files under workspace root recursively.

**Always excluded:**
- Hidden directories (`.git`, `.cache`, etc.)
- `backups/`, `backup/`, `.backups/`, `.mindmapper_backups/`
- `node_modules/`, `__pycache__/`, `venv/`, `.venv/`
- `dist/`, `build/`, `_site/`
- Files: `LICENSE*`, `LICENCE*`, `CHANGELOG*`, `COPYING*`, `NOTICE*`

**Configurable exclusions** via `mindmapper.json` → `"skip_dirs": [...]`

---

## Semantic Edge Detection

Cross-agent only. One edge per `(src_file_type, src_agent, tgt_agent)` triple.

**Sources scanned:**
1. Agent name mentions (`\bNino\b`, etc.) → source file → target agent node
2. Markdown links `[text](file.md)` → source file → target file's agent node
3. Wiki links `[[file]]` → source file → target file's agent node

**Key design decisions:**
- Target is always an AGENT NODE (not a file)
- Source is the ACTUAL file containing the mention
- Dedup key includes source file type — prevents one type from claiming all pairs

---

## Installation (any OpenClaw machine)

```bash
git clone https://github.com/finexpmmaster2/mindmapper.git
cd mindmapper
bash start.sh
```

`start.sh` auto-creates a `.venv`, installs deps, detects `~/.openclaw/`, and starts the server.

**Prerequisites:** Python 3.8+, `python3-venv` package (Ubuntu: `sudo apt install python3-venv`)

---

## Bugs Fixed

| # | Bug | Root Cause | Fix |
|---|-----|-----------|-----|
| 1 | 0 files shown | Hidden-dir check on absolute path | Check only relative path |
| 2 | Emoji icons blank | SVG `<text>` can't render emoji | `<foreignObject>` + HTML |
| 3 | Semantic edges hide wrong | Source forced to SOUL.md | Source = actual file |
| 4 | 140 semantic edges | No dedup | Dedup per `(src_type, src_agent, tgt_agent)` |
| 5 | AGENTS.md edges swallowed | SOUL.md claimed all pairs first | Include src_file_type in key |
| 6 | Filtered nodes had edges | Edge opacity only in `tick()` | Standalone `applyEdgeFilter()` |
| 7 | agents type invisible | Same color as hierarchy edges | Changed to pink/magenta |
| 8 | Backups folder indexed | No exclusion | Added to SKIP_DIRS |
| 9 | LAN on by default | `0.0.0.0` hardcoded | Default `127.0.0.1`, `--lan` flag |
| 10 | Agent node not editable | No edit action | ✏️ Edit button, click → SOUL.md |
| 11 | Hardcoded agent list | Agents in code constants | Auto-detect from `openclaw.json` / `agents/*/` |
| 12 | Broken venv on first run | `python3-venv` not installed | Detect broken venv, clear error msg |
| 13 | Wrong workspace on other machines | Hardcoded `/home/snork/...` | Read from `~/.openclaw/openclaw.json` |

---

## Roadmap

- [ ] Config-driven file type system (custom types beyond OpenClaw defaults)
- [ ] File watcher — auto-refresh graph when workspace files change
- [ ] Minimap for large graphs (100+ nodes)
- [ ] Collapse/expand agent subtrees
- [ ] Export graph as PNG or SVG
- [ ] Token-based auth for LAN mode
- [ ] Export / Import workspace bundles

---

## Git Log (significant commits)

| Hash | Description |
|------|-------------|
| `09f70a6` | Initial build |
| `3b79dba` | Scanner fix + UX rewrite |
| `d67e1dd` | Semantic dedup key includes src file type |
| `1e3215c` | Universal workspace support — auto-detect agents |
| `6b8b673` | Remove OpenClaw branding from UI |
| `3e13477` | Auto-create venv on first run |
| `f8033f4` | Auto-detect OpenClaw workspace from ~/.openclaw |
| `feb2e29` | Read agents from openclaw.json |
| `07ce326` | Scan from ~/.openclaw/ root |

---

*Last updated: 2026-03-09 by Devi*
