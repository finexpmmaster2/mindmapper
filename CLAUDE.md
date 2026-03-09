# Mind Mapper

Interactive mind map visualizer and editor for markdown workspaces. Part of the OpenClaw multi-agent system, owned by Devi (developer agent).

## Architecture

- **Backend**: Python FastAPI app (`app.py`) serving REST API + static files
- **Frontend**: Vanilla JS + D3.js force-directed graph (`static/index.html`, `static/launcher.html`)
- **Dependencies**: `fastapi`, `uvicorn`, `watchdog` (see `requirements.txt`)
- **Port**: 8081 (default), configurable via `MINDMAPPER_PORT`
- **Config**: `mindmapper.json` (gitignored) for workspace path, agents, skip_dirs

## Key Files

- `app.py` — Entire backend: workspace detection, agent discovery, file scanning, API routes, backup system
- `static/index.html` — Main UI with D3 graph, editor, search
- `static/launcher.html` — Landing page with connection info
- `start.sh` — Startup script (auto-creates venv, installs deps, kills stale processes)
- `mindmapper.json` — Runtime config (gitignored, see `mindmapper.example.json` for template)

## Development

```bash
# Run locally
bash start.sh

# Or manually
source .venv/bin/activate
python3 app.py
```

## Conventions

- Single-file backend — all Python logic lives in `app.py`
- Security: binds to localhost by default, path traversal protection on all file ops
- Backups: auto-created before every file write in `.mindmapper_backups/`
- Agent discovery priority: mindmapper.json > openclaw.json > auto-detect from `agents/*/`
- Workspace detection priority: `MINDMAPPER_WORKSPACE` env > mindmapper.json > `OPENCLAW_WORKSPACE` env > `~/.openclaw/` > cwd

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/graph` | Full graph (nodes + edges) |
| GET | `/api/file?path=<rel>` | Read file |
| POST | `/api/file` | Save file |
| GET | `/api/search?q=<query>` | Full-text search |
| POST | `/api/propagate` | Smart-merge to multiple files |
| POST | `/api/rescan` | Re-discover agents |
| GET | `/api/backups` | Backup status |
| GET | `/api/info` | Server info |
