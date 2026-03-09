# 🗺️ Mind Mapper

Interactive mind map visualizer and editor for markdown workspaces.

Built for multi-agent AI setups (like [OpenClaw](https://github.com/openclaw/openclaw)), but works with **any directory of `.md` files**.

![Python](https://img.shields.io/badge/python-3.8+-blue) ![Dependencies](https://img.shields.io/badge/deps-2_packages-green) ![License](https://img.shields.io/badge/license-MIT-brightgreen)

## Features

- 🔍 **Visual graph** — D3.js force-directed mind map of all markdown files
- ✏️ **Inline editor** — Click any file to view and edit
- 🔎 **Full-text search** — Search across all files with line-level results
- 🤖 **Agent detection** — Auto-discovers agents from `agents/*/` directories
- 🔗 **Semantic links** — Detects cross-references between files (mentions, links, wiki-links)
- 📋 **Propagate** — Push content sections across multiple files with smart merge
- 💾 **Auto-backup** — Backs up files before every write
- 🔒 **Secure by default** — Localhost only; explicit opt-in for LAN access

## Quick Start

```bash
# Clone
git clone https://github.com/finexpmmaster2/mindmapper.git
cd mindmapper

# Option 1: One command (auto-creates venv, installs deps, starts server)
bash start.sh

# Option 2: Manual setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Open `http://localhost:8081` in your browser.

### Point at your workspace
```bash
MINDMAPPER_WORKSPACE=/path/to/your/project bash start.sh
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MINDMAPPER_WORKSPACE` | current directory | Root directory to scan for `.md` files |
| `MINDMAPPER_HOST` | `127.0.0.1` | Bind address (`0.0.0.0` for LAN access) |
| `MINDMAPPER_PORT` | `8081` | Server port |
| `MINDMAPPER_BACKUP_DIR` | `<workspace>/.mindmapper_backups` | Backup storage location |
| `MINDMAPPER_BACKUP_DAYS` | `7` | Days to retain backups |

### Config File (optional)

Create `mindmapper.json` next to `app.py` or in your workspace root:

```json
{
  "workspace": "/path/to/your/project",
  "skip_dirs": ["build", "vendor", "custom_output"],
  "agents": [
    {"id": "main", "name": "Coordinator", "short": "Coord", "workspace": ".", "parent": null},
    {"id": "writer", "name": "Writer Agent", "short": "Writer", "workspace": "agents/writer", "parent": "main"},
    {"id": "reviewer", "name": "Reviewer", "short": "Rev", "workspace": "agents/reviewer", "parent": "main"}
  ]
}
```

**Without a config file**, Mind Mapper auto-detects:
- Workspace root → `main` agent
- Any `agents/*/` subdirectories → child agents
- Agent names from `SOUL.md` files (if present), otherwise directory name

### Skipped Directories

These directories are always excluded from scanning:
`backups`, `node_modules`, `__pycache__`, `venv`, `.venv`, `dist`, `build`, `_site`

Add custom exclusions via `mindmapper.json` → `"skip_dirs": [...]`

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Mind Mapper UI |
| `GET` | `/launcher` | Landing page with connection info |
| `GET` | `/api/graph` | Full graph (nodes + edges) |
| `GET` | `/api/file?path=<rel>` | Read file content |
| `POST` | `/api/file` | Save file `{"path": "...", "content": "..."}` |
| `GET` | `/api/search?q=<query>` | Full-text search |
| `POST` | `/api/propagate` | Smart-merge content to multiple files |
| `POST` | `/api/rescan` | Force re-discovery of agents |
| `GET` | `/api/backups` | Backup status and history |
| `GET` | `/api/info` | Server info (IP, port, workspace) |

## Use Cases

### Standalone (any markdown project)
```bash
cd ~/my-notes
MINDMAPPER_WORKSPACE=. python3 /path/to/mindmapper/app.py
```

### Multi-agent AI workspace
```bash
# With auto-detection (agents in agents/*/)
MINDMAPPER_WORKSPACE=/path/to/openclaw/workspace python3 app.py

# With explicit config
cp mindmapper.json /path/to/workspace/
python3 app.py
```

### LAN access (e.g., view from phone/tablet)
```bash
MINDMAPPER_HOST=0.0.0.0 MINDMAPPER_WORKSPACE=/path/to/project python3 app.py
```

⚠️ **Warning:** LAN mode exposes full read/write file access. Use only on trusted networks.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python · FastAPI · Uvicorn |
| Frontend | Vanilla JS · D3.js v7 (CDN) · CSS |
| Dependencies | `fastapi`, `uvicorn` |

## Security

- **Default:** Binds to `127.0.0.1` — no network access
- **LAN mode:** Explicit opt-in via `MINDMAPPER_HOST=0.0.0.0`
- **No authentication** — relies on network trust
- **Path traversal protection** — all file operations validated against workspace root

## License

MIT
