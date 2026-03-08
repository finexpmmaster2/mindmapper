# Mind Mapper — Project File

**Tool:** Memory & Mind Mapper  
**Port:** 8081  
**Location:** `agents/developer/tools/mindmapper/`  
**GitHub:** `finexpmmaster2/openclaw-ge` (private)  
**Started:** 2026-03-07  
**Status:** Active — in testing  
**Latest commit:** `d67e1dd`

---

## Purpose

Replace the old memory-base search tool with a visual interactive mind map + editor for all `.md` files in the OpenClaw workspace. Designed for multi-agent OpenClaw deployments.

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

## File Structure

```
tools/mindmapper/
├── app.py              # FastAPI backend — scan, search, save, propagate, semantic
├── requirements.txt    # fastapi, uvicorn
├── start.sh            # Launch script — localhost default, --lan flag for LAN
├── README.md           # Public-ready documentation
├── MINDMAP.md          # This project file
└── static/
    ├── index.html      # Self-contained frontend (D3.js + CSS + JS)
    └── launcher.html   # Tool landing page with local + LAN links
```

---

## Agent Hierarchy (from `openclaw.json`)

```
main       (Zaza)   /home/snork/.openclaw/workspace
├── researcher (Nino)   .../agents/researcher
├── developer  (Devi)   .../agents/developer
├── social     (Soso)   .../agents/social
└── maro       (Maro)   .../agents/maro
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Mind Mapper UI |
| GET | `/launcher` | Tool landing page (local + LAN links) |
| GET | `/api/graph` | Full graph: nodes, hierarchy/ownership/semantic edges |
| GET | `/api/file?path=` | Read file content |
| POST | `/api/file` | Save file `{path, content}` |
| GET | `/api/search?q=` | Full-text search, returns matches with line numbers |
| POST | `/api/propagate` | Propagate section `{source_path, target_paths[], section}` |
| GET | `/api/info` | LAN IP + tool URLs |

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

**Semantic edge rule:** source = actual file containing the cross-agent mention (file node); target = agent node of the mentioned agent. Edges hide when source file type is filtered. Target is always an agent node so it's never hidden by file-type filters.

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

LAN mode shows a `⚠️ WARNING` on startup. No authentication — rely entirely on network trust. Never expose to untrusted networks.

---

## Semantic Edge Detection

Cross-agent only. One edge per `(src_file_type, src_agent, tgt_agent)` ordered triple — so SOUL.md and AGENTS.md from the same agent can each contribute their own edge to the same target.

**Sources scanned:**
1. Agent name mentions (`\bNino\b`, etc.) → source file → target agent node
2. Markdown links `[text](file.md)` → source file → target file's agent node
3. Wiki links `[[file]]` → source file → target file's agent node

**Key design decisions:**
- Target is always an AGENT NODE (not a file) — so semantic edges don't vanish when specific target file types are filtered
- Source is the ACTUAL file containing the mention — so edges hide correctly when that file type is filtered
- Dedup key includes source file type — prevents SOUL.md from claiming all agent pairs before AGENTS.md can register its own edges

---

## Smart Merge / Propagation Logic

```python
def smart_merge(existing: str, section: str) -> str:
    # Take first non-empty line of section as key
    # If key found in existing → find that paragraph, replace in-place
    # If not found → append to end of file
```

Prevents duplicates when propagating incrementally (re-running same propagation updates instead of duplicating).

---

## Scanner Rules

Scans all `*.md` files under `WORKSPACE_ROOT` recursively.

**Excluded:**
- Hidden directories (`.git`, `.cache`, etc.) — checked on relative path only
- `backups/`, `backup/`, `.backups/` folders
- Files: `LICENSE*`, `LICENCE*`, `CHANGELOG*`, `COPYING*`, `NOTICE*`

**Critical fix (2026-03-07):** scanner previously checked absolute path for hidden dirs — `.openclaw` in `/home/snork/.openclaw/workspace` matched and filtered out ALL files. Fixed to check relative path only.

---

## Bugs Fixed (session log)

| # | Bug | Root Cause | Fix |
|---|-----|-----------|-----|
| 1 | 0 files shown | Hidden-dir check on absolute path — `.openclaw` killed everything | Check only relative path from workspace root |
| 2 | Emoji icons blank | SVG `<text>` can't render emoji reliably | Switched to `<foreignObject>` + HTML `<div>` |
| 3 | All semantic edges hide when Soul filtered | Semantic detection forced SOUL→SOUL edges (upgraded source to SOUL.md) | Source = actual file; target = agent node |
| 4 | 140 semantic edges (too many) | Every file mentioning a name generated a separate edge | Dedup per `(src_type, src_agent, tgt_agent)` — one per file-type × agent pair |
| 5 | AGENTS.md semantic edges swallowed | SOUL.md (higher priority) claimed all `(src_agent, tgt_agent)` pairs first; AGENTS.md had nothing left | Include src_file_type in dedup key |
| 6 | Filtered nodes still had edges | Edge opacity updated only in `tick()` — stops after simulation settles | Standalone `applyEdgeFilter()` with CSS `display:none`, called on every filter change |
| 7 | agents type invisible | Color `#00f0ff` same as Hierarchy edge cyan | Changed to `#ff66aa` (pink/magenta) |
| 8 | Backups folder indexed | No exclusion | Added `backups/`, `backup/`, `.backups/` to exclusion list |
| 9 | LAN access on by default (security) | `0.0.0.0` hardcoded as bind host | Default `127.0.0.1`; `--lan` flag for opt-in |
| 10 | Agent node not editable | No obvious edit action; inline onclick had path escaping bugs | File refs stored in `window._apFiles[]`; explicit ✏️ Edit button per file; agent click opens SOUL.md directly |
| 11 | Maro AGENTS.md only connected to Soso | SOUL.md scanned first, claimed all `(maro, *)` pairs before AGENTS.md ran | Dedup key `(src_type, src_agent, tgt_agent)` — each file type gets its own slot |

---

## Parked Ideas

### 💡 Export / Import / Backup-Restore
**Status:** Parked — GG to revisit after testing

Full workspace portability system integrated into Mind Mapper:

**Export bundle** (`.zip`):
```
openclaw-backup-YYYY-MM-DD.zip
├── openclaw.json
├── agents/
│   ├── zaza/SOUL.md
│   ├── zaza/AGENTS.md
│   └── ...          ← core types: soul/agents/tools/heartbeat/identity/user/comms
└── manifest.json    ← version, timestamp, agent list, checksum
```

**Features:**
- One-click full export → download `.zip`
- Selective export: per agent + per file type checkboxes
- Import: drag & drop → validate manifest → diff preview → write files
- Auto-backup on every save: `backups/YYYY-MM-DD/HH-MM-SS_<path>.md`
- Auto-backup batch before propagation: `backups/propagate_HH-MM-SS/`

**Use cases:**
- Migrate OpenClaw to new machine in 30 seconds
- Clone agent configuration
- Share "starter packs" — publish agent personality bundles
- Point-in-time restore after bad edit
- Community agent sharing

**API additions needed:**
- `GET /api/export` → streams `.zip`
- `POST /api/import` → accepts `.zip`, returns diff
- `POST /api/restore` → applies diff after confirmation

---

## Roadmap

- [ ] Auto-backup on save and propagate (prerequisite for export feature)
- [ ] Export / Import / Backup-Restore (see Parked Ideas above)
- [ ] File watcher — auto-refresh graph when workspace files change
- [ ] Minimap for large graphs (100+ nodes)
- [ ] Collapse/expand agent subtrees
- [ ] Jump-to-line highlight inside editor on search result click
- [ ] Export graph as PNG or SVG
- [ ] Token-based auth for LAN mode (basic security layer)
- [ ] Per-agent stats: file count, total size, last modified

---

## Start / Restart

```bash
# Localhost only (default, secure)
cd /home/snork/.openclaw/workspace/agents/developer/tools/mindmapper
bash start.sh

# LAN mode (opt-in, explicit)
bash start.sh --lan

# Kill and restart manually
lsof -ti:8081 | xargs -r kill -9 && python3 app.py
```

---

## Git Log (significant commits)

| Hash | Description |
|------|-------------|
| `09f70a6` | Initial build |
| `3b79dba` | Scanner fix + UX rewrite |
| `da41b6b` | Exclude backups/ folder |
| `6782565` | Hide edges with filtered nodes; Select All / Deselect All |
| `a8d4e71` | Security: localhost default, --lan flag |
| `f2e4e0b` | Agent panel Edit buttons; click agent → opens SOUL.md |
| `0e15cf4` | Semantic edges → agent nodes (v2 attempt) |
| `b51e08c` | Semantic: file→file, exempt from filter (v3) |
| `eab5571` | Semantic: file→agent node, deduped per agent pair |
| `73fe92d` | Semantic: source = actual file, target = agent node |
| `d67e1dd` | Semantic: dedup key includes src file type — AGENTS.md no longer swallowed |

---

*Last updated: 2026-03-07 by Devi*
