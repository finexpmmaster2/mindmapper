#!/usr/bin/env python3
"""
Mind Mapper — OpenClaw Workspace Mind Map
Search, visualize, and edit all .md files across all agents.
Port: 8081
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import re
import glob
import json
import socket
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import uvicorn

app = FastAPI(title="Mind Mapper — OpenClaw")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WORKSPACE_ROOT = "/home/snork/.openclaw/workspace"
PORT = int(os.environ.get("MINDMAPPER_PORT", 8081))

# Security: binds to localhost only by default.
# Mind Mapper has full read/write access to your workspace files — do not
# expose it to the network unless you understand the risk.
# To enable LAN access explicitly: MINDMAPPER_HOST=0.0.0.0 python3 app.py
# Or use start.sh --lan
BIND_HOST = os.environ.get("MINDMAPPER_HOST", "127.0.0.1")

# ── Backup configuration ─────────────────────────────────────────────────────
# Default: hidden folder inside workspace (excluded from scanner automatically)
# Override: MINDMAPPER_BACKUP_DIR=/your/path python3 app.py
BACKUP_ROOT = os.environ.get(
    "MINDMAPPER_BACKUP_DIR",
    os.path.join(WORKSPACE_ROOT, ".mindmapper_backups")
)
# Keep backups for this many days before auto-pruning
BACKUP_RETENTION_DAYS = int(os.environ.get("MINDMAPPER_BACKUP_DAYS", 7))

_backup_enabled = False   # set to True at startup if dir is writable


def _init_backup() -> bool:
    """Create backup directory and verify it is writable. Returns True on success."""
    global _backup_enabled
    try:
        os.makedirs(BACKUP_ROOT, exist_ok=True)
        test = os.path.join(BACKUP_ROOT, ".write_test")
        with open(test, "w") as f:
            f.write("ok")
        os.remove(test)
        _backup_enabled = True
        print(f"  Backups  →  {BACKUP_ROOT}  (retain {BACKUP_RETENTION_DAYS} days)")
        return True
    except Exception as e:
        print(f"  ⚠️  Backup dir not writable: {BACKUP_ROOT} — {e}")
        print(f"     Set MINDMAPPER_BACKUP_DIR to a writable path to enable backups.")
        _backup_enabled = False
        return False


def _prune_old_backups():
    """Delete backup folders older than BACKUP_RETENTION_DAYS."""
    if not _backup_enabled:
        return
    try:
        cutoff = (datetime.now() - timedelta(days=BACKUP_RETENTION_DAYS)).date()
        for entry in os.scandir(BACKUP_ROOT):
            if entry.is_dir():
                try:
                    folder_date = datetime.strptime(entry.name, "%Y-%m-%d").date()
                    if folder_date < cutoff:
                        shutil.rmtree(entry.path)
                        print(f"  Pruned backup: {entry.name}")
                except ValueError:
                    pass  # non-date folder — skip
    except Exception as e:
        print(f"  ⚠️  Backup prune failed: {e}")


def backup_file(abs_path: str) -> Optional[str]:
    """
    Copy abs_path to BACKUP_ROOT/YYYY-MM-DD/HH-MM-SS__<flat-relative-path>.
    Returns backup path on success, None on failure or if backup is disabled.
    """
    if not _backup_enabled or not os.path.isfile(abs_path):
        return None
    try:
        rel       = os.path.relpath(abs_path, WORKSPACE_ROOT)
        flat_rel  = rel.replace(os.sep, "__")
        now       = datetime.now()
        date_str  = now.strftime("%Y-%m-%d")
        time_str  = now.strftime("%H-%M-%S")
        bdir      = os.path.join(BACKUP_ROOT, date_str)
        os.makedirs(bdir, exist_ok=True)
        dst = os.path.join(bdir, f"{time_str}__{flat_rel}")
        shutil.copy2(abs_path, dst)
        return dst
    except Exception as e:
        print(f"  ⚠️  Backup failed for {abs_path}: {e}")
        return None


def backup_batch(abs_paths: List[str], label: str = "propagate") -> Dict[str, Optional[str]]:
    """
    Back up multiple files into a single timestamped batch folder.
    BACKUP_ROOT/YYYY-MM-DD/<label>_HH-MM-SS/<flat-relative-path>
    Returns dict of abs_path → backup_path.
    """
    results: Dict[str, Optional[str]] = {}
    if not _backup_enabled:
        return results
    try:
        now      = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S")
        bdir     = os.path.join(BACKUP_ROOT, date_str, f"{label}_{time_str}")
        os.makedirs(bdir, exist_ok=True)
        for abs_path in abs_paths:
            if os.path.isfile(abs_path):
                rel      = os.path.relpath(abs_path, WORKSPACE_ROOT)
                flat_rel = rel.replace(os.sep, "__")
                dst      = os.path.join(bdir, flat_rel)
                try:
                    shutil.copy2(abs_path, dst)
                    results[abs_path] = dst
                except Exception as e:
                    print(f"  ⚠️  Batch backup failed for {abs_path}: {e}")
                    results[abs_path] = None
    except Exception as e:
        print(f"  ⚠️  Batch backup failed: {e}")
    return results


def get_local_ip() -> str:
    """Best-effort detection of the machine's LAN IP."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# Agent hierarchy derived from openclaw.json
AGENTS = [
    {"id": "main",       "name": "Zaza",         "short": "Zaza",  "workspace": WORKSPACE_ROOT,                                          "parent": None},
    {"id": "researcher", "name": "Nino (ნინო)",   "short": "Nino",  "workspace": f"{WORKSPACE_ROOT}/agents/researcher",                   "parent": "main"},
    {"id": "developer",  "name": "Devi (დევი)",   "short": "Devi",  "workspace": f"{WORKSPACE_ROOT}/agents/developer",                    "parent": "main"},
    {"id": "social",     "name": "Soso (სოსო)",   "short": "Soso",  "workspace": f"{WORKSPACE_ROOT}/agents/social",                       "parent": "main"},
    {"id": "maro",       "name": "Maro (მარო)",   "short": "Maro",  "workspace": f"{WORKSPACE_ROOT}/agents/maro",                         "parent": "main"},
]

AGENT_BY_ID  = {a["id"]: a for a in AGENTS}
AGENT_SHORTS = [a["short"] for a in AGENTS]

# Ordered by workspace length desc so most-specific match wins
AGENTS_BY_WS = sorted(AGENTS, key=lambda a: len(a["workspace"]), reverse=True)


# ── File helpers ─────────────────────────────────────────────────────────────

FILE_TYPE_MAP = [
    ("SOUL",       "soul"),
    ("HEARTBEAT",  "heartbeat"),
    ("AGENTS",     "agents"),
    ("BOOTSTRAP",  "bootstrap"),
    ("TOOLS",      "tools"),
    ("USER",       "user"),
    ("IDENTITY",   "identity"),
    ("COMMS",      "comms"),
    ("BRAND",      "brand"),
    ("TASK",       "task"),
    ("README",     "readme"),
]


def get_file_type(filepath: str) -> str:
    name    = os.path.basename(filepath).upper().replace(".MD", "")
    parent  = os.path.basename(os.path.dirname(filepath)).lower()
    if parent == "memory":
        return "memory"
    if parent in ("drafts", "draft"):
        return "draft"
    for key, ftype in FILE_TYPE_MAP:
        if key in name:
            return ftype
    return "document"


def get_agent_for_file(filepath: str) -> Optional[str]:
    """Returns the most-specific agent whose workspace contains this file."""
    for agent in AGENTS_BY_WS:
        ws = agent["workspace"]
        if filepath.startswith(ws + os.sep) or filepath == ws:
            return agent["id"]
    return None


def scan_files() -> List[Dict]:
    files = []
    pattern = os.path.join(WORKSPACE_ROOT, "**", "*.md")
    for path in glob.glob(pattern, recursive=True):
        # Skip hidden dirs WITHIN the workspace only (not parent path like .openclaw)
        rel      = os.path.relpath(path, WORKSPACE_ROOT)
        rel_parts = Path(rel).parts
        if any(p.startswith(".") for p in rel_parts):
            continue
        # Skip backups folder
        if rel_parts and rel_parts[0].lower() in ("backups", "backup", ".backups"):
            continue
        # Skip license / changelog / legal files
        basename_up = os.path.basename(path).upper()
        if any(basename_up.startswith(x) for x in ("LICENSE", "LICENCE", "CHANGELOG", "COPYING", "NOTICE")):
            continue
        node_id  = re.sub(r"[^a-zA-Z0-9_]", "_", rel)
        agent_id = get_agent_for_file(path)
        ftype    = get_file_type(path)
        try:
            stat = os.stat(path)
            size = stat.st_size
        except Exception:
            size = 0
        files.append({
            "id":       node_id,
            "path":     rel,
            "abs_path": path,
            "name":     os.path.basename(path),
            "type":     ftype,
            "agent_id": agent_id,
            "size":     size,
        })
    return files


# ── Semantic link detection ───────────────────────────────────────────────────

def detect_semantic_links(files: List[Dict]) -> List[Dict]:
    """
    Semantic edges:
      source = the ACTUAL file that contains the cross-agent mention (file node)
      target = the AGENT NODE of the mentioned agent (never filtered by type)

    This means: edge hides only when the source file type is filtered.
    e.g. AGENTS.md mentions Zaza → edge hides when 'agents' is off,
    NOT when 'soul' is off.

    Dedup: one edge per (src_agent, tgt_agent) ordered pair.
    Scan order: soul > agents > comms > ... so the most meaningful
    source file type registers the edge first.
    """
    TYPE_PRIORITY = ["soul","agents","comms","heartbeat","tools","user",
                     "identity","bootstrap","memory","draft","brand","task","readme","document"]

    links     = []
    by_name   = {f["name"].lower(): f for f in files}
    # Dedup key includes src file TYPE so each file type gets its own edge per agent pair.
    # e.g. soul→main and agents→main are different edges — both can exist.
    # This ensures AGENTS.md edges aren't swallowed by higher-priority SOUL.md.
    pair_seen = set()   # (src_file_type, src_agent_id, tgt_agent_id)

    def add_sem(src_file, tgt_agent_id, ltype, label):
        src_aid  = src_file.get("agent_id")
        src_type = src_file.get("type", "")
        if not src_aid or src_aid == tgt_agent_id:
            return
        key = (src_type, src_aid, tgt_agent_id)
        if key in pair_seen:
            return
        pair_seen.add(key)
        links.append({
            "source": src_file["id"],           # actual file (respects type filter on source)
            "target": f"agent__{tgt_agent_id}",  # agent node (never hidden by file-type filter)
            "type":   ltype,
            "label":  label,
        })

    for src in files:
        try:
            text = open(src["abs_path"], "r", encoding="utf-8", errors="ignore").read()
        except Exception:
            continue

        # 1. Cross-agent name mentions
        for agent in AGENTS:
            if agent["id"] == src.get("agent_id"):
                continue
            short = agent["short"]
            if short and len(short) > 2 and re.search(r"\b" + re.escape(short) + r"\b", text, re.IGNORECASE):
                add_sem(src, agent["id"], "semantic_name", f"mentions {short}")

        # 2. Markdown links [text](file.md) — cross-agent → target agent node
        for _, href in re.findall(r"\[([^\]]*)\]\(([^)]+\.md[^)]*)\)", text):
            bkey = os.path.basename(href).lower().split("?")[0].split("#")[0]
            if bkey in by_name:
                tgt_f = by_name[bkey]
                if tgt_f.get("agent_id") and tgt_f["agent_id"] != src.get("agent_id"):
                    add_sem(src, tgt_f["agent_id"], "semantic_link", f"→ {tgt_f['name']}")

        # 3. Wiki links [[file]] — cross-agent → target agent node
        for wl in re.findall(r"\[\[([^\]]+)\]\]", text):
            wkey = wl.lower()
            if not wkey.endswith(".md"):
                wkey += ".md"
            if wkey in by_name:
                tgt_f = by_name[wkey]
                if tgt_f.get("agent_id") and tgt_f["agent_id"] != src.get("agent_id"):
                    add_sem(src, tgt_f["agent_id"], "semantic_wiki", f"[[{tgt_f['name']}]]")

    return links


# ── API routes ────────────────────────────────────────────────────────────────

@app.get("/api/graph")
def get_graph():
    files = scan_files()

    # Agent nodes
    nodes = []
    for agent in AGENTS:
        nodes.append({
            "id":       f"agent__{agent['id']}",
            "label":    agent["name"],
            "short":    agent["short"],
            "type":     "agent",
            "agent_id": agent["id"],
            "group":    "agent",
        })

    # File nodes
    for f in files:
        nodes.append({
            "id":       f["id"],
            "label":    f["name"],
            "type":     f["type"],
            "agent_id": f["agent_id"],
            "path":     f["path"],
            "group":    "file",
        })

    # Hierarchy edges: agent → agent
    hierarchy_edges = []
    for agent in AGENTS:
        if agent["parent"]:
            hierarchy_edges.append({
                "source": f"agent__{agent['parent']}",
                "target": f"agent__{agent['id']}",
                "type":   "hierarchy",
            })

    # Ownership edges: agent → owned files
    ownership_edges = []
    for f in files:
        if f["agent_id"]:
            ownership_edges.append({
                "source": f"agent__{f['agent_id']}",
                "target": f["id"],
                "type":   "ownership",
            })

    semantic_edges = detect_semantic_links(files)

    return {
        "nodes":           nodes,
        "hierarchy_edges": hierarchy_edges,
        "ownership_edges": ownership_edges,
        "semantic_edges":  semantic_edges,
        # legacy combined (kept for compatibility)
        "config_edges":    hierarchy_edges + ownership_edges,
    }


@app.get("/api/file")
def read_file(path: str):
    abs_path = os.path.normpath(os.path.join(WORKSPACE_ROOT, path))
    if not abs_path.startswith(os.path.abspath(WORKSPACE_ROOT)):
        raise HTTPException(403, "Access denied")
    if not os.path.isfile(abs_path):
        raise HTTPException(404, "File not found")
    content = open(abs_path, "r", encoding="utf-8", errors="ignore").read()
    return {"path": path, "content": content}


class SaveRequest(BaseModel):
    path:    str
    content: str


@app.post("/api/file")
def save_file(req: SaveRequest):
    abs_path = os.path.normpath(os.path.join(WORKSPACE_ROOT, req.path))
    if not abs_path.startswith(os.path.abspath(WORKSPACE_ROOT)):
        raise HTTPException(403, "Access denied")
    backed_up = backup_file(abs_path)   # backup BEFORE write
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(req.content)
    return {"ok": True, "path": req.path, "backup": backed_up}


@app.get("/api/search")
def search_files(q: str = ""):
    if len(q) < 2:
        return {"results": [], "query": q}
    files = scan_files()
    results = []
    for f in files:
        try:
            lines = open(f["abs_path"], "r", encoding="utf-8", errors="ignore").readlines()
        except Exception:
            continue
        matches = []
        for i, line in enumerate(lines):
            if q.lower() in line.lower():
                matches.append({
                    "line_num": i + 1,
                    "line":     line.rstrip(),
                    "before":   lines[i - 1].rstrip() if i > 0 else "",
                    "after":    lines[i + 1].rstrip() if i < len(lines) - 1 else "",
                })
        if matches:
            results.append({
                "file_id":    f["id"],
                "path":       f["path"],
                "name":       f["name"],
                "type":       f["type"],
                "agent_id":   f["agent_id"],
                "matches":    matches,
                "match_count": len(matches),
            })
    return {"query": q, "results": results}


def smart_merge(existing: str, section: str) -> str:
    """
    Append section to file, or update in-place if its heading already exists.
    Dedup logic: if first non-empty line of section exists verbatim in existing,
    find that paragraph and replace it. Otherwise append.
    """
    stripped = section.strip()
    if not stripped:
        return existing

    first_line = next((l.strip() for l in stripped.splitlines() if l.strip()), "")

    if first_line and first_line in existing:
        # Replace the paragraph that contains first_line
        paras = re.split(r"\n{2,}", existing)
        new_paras = []
        replaced = False
        for para in paras:
            if first_line in para and not replaced:
                new_paras.append(stripped)
                replaced = True
            else:
                new_paras.append(para)
        if not replaced:
            new_paras.append(stripped)
        return "\n\n".join(new_paras).rstrip() + "\n"
    else:
        return existing.rstrip() + "\n\n" + stripped + "\n"


class PropagateRequest(BaseModel):
    source_path:  str
    target_paths: List[str]
    section:      str


@app.post("/api/propagate")
def propagate(req: PropagateRequest):
    # Resolve + validate all target paths before touching anything
    valid_targets = []
    for tp in req.target_paths:
        abs_path = os.path.normpath(os.path.join(WORKSPACE_ROOT, tp))
        if not abs_path.startswith(os.path.abspath(WORKSPACE_ROOT)):
            valid_targets.append((tp, abs_path, "access denied"))
        elif not os.path.isfile(abs_path):
            valid_targets.append((tp, abs_path, "not found"))
        else:
            valid_targets.append((tp, abs_path, None))

    # Batch-backup ALL valid files before writing any of them
    abs_to_backup = [ap for _, ap, err in valid_targets if err is None]
    backups = backup_batch(abs_to_backup, label="propagate")

    results = []
    for tp, abs_path, err in valid_targets:
        if err:
            results.append({"path": tp, "ok": False, "error": err})
            continue
        try:
            existing = open(abs_path, "r", encoding="utf-8").read()
            merged   = smart_merge(existing, req.section)
            open(abs_path, "w", encoding="utf-8").write(merged)
            results.append({"path": tp, "ok": True, "backup": backups.get(abs_path)})
        except Exception as e:
            results.append({"path": tp, "ok": False, "error": str(e)})
    return {"results": results, "backup_count": len([b for b in backups.values() if b])}


# ── Backup info endpoint ─────────────────────────────────────────────────────

@app.get("/api/backups")
def list_backups():
    """Return summary of stored backups."""
    if not _backup_enabled:
        return {"enabled": False, "path": BACKUP_ROOT, "days": BACKUP_RETENTION_DAYS, "dates": []}
    dates = []
    try:
        for entry in sorted(os.scandir(BACKUP_ROOT), key=lambda e: e.name, reverse=True):
            if entry.is_dir():
                try:
                    datetime.strptime(entry.name, "%Y-%m-%d")  # validate date folder
                    count = sum(1 for _ in Path(entry.path).rglob("*.md"))
                    dates.append({"date": entry.name, "files": count})
                except ValueError:
                    pass
    except Exception:
        pass
    return {
        "enabled":    True,
        "path":       BACKUP_ROOT,
        "days":       BACKUP_RETENTION_DAYS,
        "dates":      dates,
        "total_days": len(dates),
    }


# ── Info / network URL ───────────────────────────────────────────────────────

@app.get("/api/info")
def get_info():
    lan_ip = get_local_ip()
    return {
        "host":      lan_ip,
        "port":      PORT,
        "tools": [
            {"name": "🗺️ Mind Mapper",     "url": f"http://{lan_ip}:{PORT}/",    "local": f"http://localhost:{PORT}/"},
            {"name": "📋 Mission Control", "url": f"http://{lan_ip}:8080/board", "local": "http://localhost:8080/board"},
        ],
    }


# ── Static files + root ───────────────────────────────────────────────────────

_static_dir = os.path.join(os.path.dirname(__file__), "static")


@app.get("/")
def root():
    return FileResponse(os.path.join(_static_dir, "index.html"))


@app.get("/launcher")
def launcher():
    return FileResponse(os.path.join(_static_dir, "launcher.html"))


app.mount("/static", StaticFiles(directory=_static_dir), name="static")


if __name__ == "__main__":
    lan_ip = get_local_ip()
    lan_enabled = BIND_HOST != "127.0.0.1"
    print("\n" + "="*56)
    print("  🗺️  Mind Mapper — OpenClaw Workspace")
    print("="*56)
    print(f"  Local   →  http://localhost:{PORT}/")
    if lan_enabled:
        print(f"  Network →  http://{lan_ip}:{PORT}/  ⚠️  LAN OPEN")
        print(f"\n  ⚠️  WARNING: Full file read/write access is exposed")
        print(f"     on the local network. Use only on trusted networks.")
    else:
        print(f"  Network →  localhost only (default, secure)")
        print(f"  To enable LAN: MINDMAPPER_HOST=0.0.0.0 python3 app.py")
    # Initialize backup system
    _init_backup()
    _prune_old_backups()
    print("="*56 + "\n")
    uvicorn.run(app, host=BIND_HOST, port=PORT, reload=False)
