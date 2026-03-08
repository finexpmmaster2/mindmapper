# 🗺️ Mind Mapper

**Visual workspace explorer for OpenClaw multi-agent systems.**  
Search, navigate, edit, and propagate changes across all your agent files — in a single browser window.

---

## What It Does

Mind Mapper scans your entire OpenClaw workspace and renders every Markdown file as a visual node on an interactive map. Files are grouped by agent, connected by their real relationships, color-coded by type, and fully editable — all without leaving the browser.

It was built for teams running multiple OpenClaw agents who need to understand how their workspace is structured, find information quickly, and push consistent changes across agents without touching files one by one.

---

## Key Benefits

### 🧭 Understand your workspace at a glance
See all agents, their files, and how they relate — in a single interactive diagram. No more grepping through folders or guessing what belongs where.

### 🔍 Search that shows context
Type a keyword and every matching file lights up on the map. Click any result to open the full file with your search term highlighted and jump directly to matching lines.

### ✏️ Edit any file, right there
Click a node, hit Edit, make your change, save. No terminal, no text editor, no path hunting. The file is written to disk instantly.

### 📡 Propagate changes across agents
Have a section that needs to exist in every agent's `SOUL.md`? Select the source file, click Propagate, choose your targets, write the section once — and it lands in all of them. Smart dedup: if the section already exists in a target, it's updated in place rather than duplicated.

### 🔗 See real connections, not just folders
Two types of visual links:
- **Config links** — the actual hierarchy from your `openclaw.json` (who owns what)
- **Semantic links** — cross-agent references discovered by reading file content (name mentions, markdown links, wiki links)

### 🎛️ Filter noise away
Working only on `memory/` files? Filter out everything else with one click. The map clears, the edges disappear, and you focus on what matters.

### 🌐 Optional LAN access
Mind Mapper defaults to `localhost` only. You can explicitly opt in to LAN access when you need it — for example to view the map from a tablet on the same desk.

---

## Feature Overview

| Feature | Details |
|---------|---------|
| **File discovery** | Scans all `*.md` files recursively; excludes hidden dirs, backups, license files |
| **Agent hierarchy** | Reads `openclaw.json` to build the real agent tree |
| **Semantic detection** | Cross-agent name mentions, `[markdown links]()`, `[[wiki links]]` |
| **File type icons** | 15 types: soul 🧠, heartbeat 💓, memory 📅, tools 🔧, identity 🪪, and more |
| **Three edge layers** | Hierarchy (cyan), Ownership (blue), Semantic (purple dashed) — each toggleable |
| **Type filter** | Click any legend item to show/hide that file type; edges hide automatically |
| **Select/Deselect all** | One-click to show everything or hide all files |
| **Search** | Full-text across all files; line-level results with context |
| **Inline editor** | Edit any file directly in the sidebar; Save/Cancel with dirty tracking |
| **Propagation by type** | Click a file → propagate to all same-type files across all agents |
| **Propagation by agent** | Right-click an agent → propagate to all its files |
| **Smart merge** | Detects existing sections; updates in place rather than duplicating |
| **Sticky drag** | All nodes (including agents) are draggable; stays where you drop them |
| **Reset layout** | One click returns to clean radial cluster layout |
| **Resizable sidebar** | Drag the sidebar edge to any width you need |
| **LAN access** | Opt-in via `--lan` flag or `MINDMAPPER_HOST` env var (see Security section) |
| **Launcher page** | `/launcher` — central link page for all tools with local + network URLs |

---

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

```bash
# Clone or copy the mindmapper/ directory into your workspace
cd /path/to/your/workspace/tools/mindmapper

# Install dependencies
pip install fastapi uvicorn

# Start (localhost only — default)
bash start.sh

# OR: enable LAN access explicitly (see Security section below)
bash start.sh --lan
```

On startup you'll see:

```
========================================================
  🗺️  Mind Mapper — OpenClaw Workspace
========================================================
  Local   →  http://localhost:8081/
  Network →  localhost only (default, secure)
  To enable LAN: MINDMAPPER_HOST=0.0.0.0 python3 app.py
========================================================
```

Open your browser at `http://localhost:8081/`.

---

## Security

> ⚠️ **Mind Mapper has full read and write access to your workspace files.**
> Treat it with the same caution as a terminal with access to those files.

### Default: localhost only
By default, Mind Mapper binds to `127.0.0.1`. It is only accessible from the machine it runs on. This is the safe default and should be kept for most use cases.

### LAN access: explicit opt-in only
If you need to access Mind Mapper from another device (e.g. a tablet on the same desk):

```bash
# Option 1 — flag
bash start.sh --lan

# Option 2 — environment variable
MINDMAPPER_HOST=0.0.0.0 python3 app.py

# Option 3 — custom port
MINDMAPPER_HOST=0.0.0.0 MINDMAPPER_PORT=9090 python3 app.py
```

When LAN mode is active, the startup output shows a clear warning and the network URL.

**Only enable LAN access on networks you fully control.** There is no authentication — anyone on the network can read, edit, or overwrite your workspace files.

### What's exposed
| Capability | Accessible when |
|------------|----------------|
| Read any `.md` file in workspace | Always (by design) |
| Write/overwrite any `.md` file | Always (by design) |
| Network access | Only when explicitly enabled with `--lan` |
| Authentication | None — rely on network trust |

---

## Configuration

Mind Mapper reads your workspace structure automatically from two sources:

**1. Directory structure** — any `*.md` file found under the workspace root is indexed.

**2. `openclaw.json`** — the agent list and their workspace paths define the hierarchy. Example:

```json
{
  "agents": {
    "list": [
      { "id": "main",       "workspace": "/workspace",           "identity": { "name": "Zaza" } },
      { "id": "developer",  "workspace": "/workspace/agents/dev", "identity": { "name": "Devi" } }
    ]
  }
}
```

To change the workspace path, edit `WORKSPACE_ROOT` at the top of `app.py`.

### Excluded paths (built-in)
- Hidden directories (`.git`, `.cache`, etc.)
- `backups/` and `backup/` folders
- `LICENSE*`, `CHANGELOG*`, `COPYING*`, `NOTICE*` files

---

## Usage Guide

### Navigating the map
- **Scroll** to zoom in/out
- **Click and drag** the background to pan
- **Click and drag any node** to reposition it (sticky — stays where you drop)
- **↺ Reset** to restore the original radial layout

### Understanding the layout
- The **main agent** starts at the center
- **Sub-agents** are arranged in a ring around it
- Each agent's **files** fan out in an arc from their agent node

### Edge types
| Color | Type | Meaning |
|-------|------|---------|
| ── cyan, thick | **⬡ Hierarchy** | Agent → Sub-agent relationship |
| ── blue, medium | **📂 Ownership** | Agent → its files |
| ╌╌ purple, dashed | **~ Semantic** | Cross-agent content reference |

Toggle each layer on/off with the buttons in the header.

### Searching
1. Type in the search bar (minimum 2 characters)
2. Matching file nodes glow **orange**; non-matching nodes dim
3. The sidebar opens with a grouped list of all matching files
4. Click a file header to expand its matching lines
5. Click any line to open that file in the editor, scrolled to that position

### Editing a file
1. Click any file node on the map
2. The sidebar opens with the full file content
3. Click **✏️ Edit** to unlock the editor
4. Make your changes
5. Click **💾 Save** — file is written to disk immediately
6. Click **Cancel** to revert all changes

### Filtering by type
- The **Legend** panel (bottom left) lists all file types
- Click any type to **hide** it (node + all its edges disappear)
- Click again to show it again
- **✓ All** — show everything
- **✗ Files off** — hide all file types, show only agent nodes

### Propagating changes

#### By file type (recommended)
Best for: pushing the same section to the same role file across all agents (e.g. all `SOUL.md` files).

1. Click any file node (e.g. `SOUL.md`)
2. Click **📡 Propagate same type** in the sidebar
3. All same-type files across all agents are highlighted (green) and pre-selected
4. Deselect any targets you want to skip (click on map or in sidebar list)
5. Type the section to propagate in the text area
6. Click **📡 Propagate**

#### By agent
Best for: pushing a shared section to all files owned by one agent.

1. **Right-click** any agent node on the map
2. All that agent's files are highlighted
3. Deselect any files you want to skip
4. Type the section and propagate

#### Smart merge behavior
- If the **first line** of your section already exists in a target file, Mind Mapper finds that paragraph and **updates it in place**
- If not found, the section is **appended** at the end
- This prevents duplicates when propagating incrementally

---

## API Reference

Mind Mapper exposes a simple REST API at `http://localhost:8081`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web UI |
| `GET` | `/launcher` | Tool launcher page |
| `GET` | `/api/graph` | Full graph: nodes, hierarchy/ownership/semantic edges |
| `GET` | `/api/file?path=` | Read file content |
| `POST` | `/api/file` | Save file `{ path, content }` |
| `GET` | `/api/search?q=` | Search all files; returns matches with line numbers |
| `POST` | `/api/propagate` | Propagate section `{ source_path, target_paths[], section }` |
| `GET` | `/api/info` | Machine LAN IP and tool URLs |

---

## File Type Reference

| Icon | Type | Detected by |
|------|------|-------------|
| 🤖 | Agent | Config node (not a file) |
| 🧠 | Soul | Filename contains `SOUL` |
| 💓 | Heartbeat | Filename contains `HEARTBEAT` |
| 🤝 | Agents | Filename contains `AGENTS` |
| 🚀 | Bootstrap | Filename contains `BOOTSTRAP` |
| 🔧 | Tools | Filename contains `TOOLS` |
| 👤 | User | Filename contains `USER` |
| 🪪 | Identity | Filename contains `IDENTITY` |
| 📡 | Comms | Filename contains `COMMS` |
| 📅 | Memory | In a `memory/` folder or name contains `MEMORY` |
| 📝 | Draft | In a `drafts/` folder or name contains `DRAFT` |
| 🎨 | Brand | Filename contains `BRAND` |
| ✅ | Task | Filename contains `TASK` |
| 📖 | Readme | Filename contains `README` |
| 📄 | Document | Everything else |

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python · FastAPI · Uvicorn |
| Frontend | Vanilla JS · D3.js v7 |
| Graph layout | D3 force simulation (radial cluster, sticky drag) |
| File I/O | Native Python filesystem (no database) |
| Network | Binds to `0.0.0.0` — LAN accessible out of the box |
| Dependencies | `fastapi`, `uvicorn` (2 packages total) |

---

## Keyboard & Interaction Reference

| Action | How |
|--------|-----|
| Pan map | Click + drag background |
| Zoom | Scroll wheel |
| Move a node | Click + drag the node |
| Reset layout | Click **↺ Reset** |
| Open file | Click any file node |
| Open agent summary | Click any agent node |
| Propagate (agent) | Right-click any agent node |
| Propagate (type) | Click file → "📡 Propagate same type" |
| Search | Type in the search bar |
| Clear search | Click × or clear the search bar |
| Toggle edge layer | Click Hierarchy / Ownership / Semantic buttons |
| Filter file type | Click type in Legend |
| Show all types | Click **✓ All** in Legend |
| Hide all file types | Click **✗ Files off** in Legend |
| Resize sidebar | Drag its left edge |
| Reload workspace | Click **↻** in header |

---

## File Structure

```
mindmapper/
├── app.py              # FastAPI backend — scanning, search, save, propagate, graph API
├── requirements.txt    # fastapi, uvicorn
├── start.sh            # Kill :8081, install deps, start server, print URLs
├── MINDMAP.md          # Internal project doc (requirements, bug log, decisions)
├── README.md           # This file
└── static/
    ├── index.html      # Single-page frontend (D3.js + CSS + JS, self-contained)
    └── launcher.html   # Tool landing page with local + LAN links
```

---

## Roadmap

- [ ] Auto-refresh graph when files change on disk (watchdog integration)
- [ ] Minimap for large workspaces (100+ nodes)
- [ ] Collapse/expand agent subtrees
- [ ] Jump-to-line highlight inside the editor
- [ ] Export graph as PNG or SVG
- [ ] Per-agent file count and size stats
- [ ] Dark/light theme toggle

---

## License

Part of the OpenClaw toolset. See the main repository for license terms.

---

*Built by Devi — OpenClaw Web Engineer*
