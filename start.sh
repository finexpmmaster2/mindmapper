#!/bin/bash
# Mind Mapper — start script
#
# Usage:
#   bash start.sh                              → localhost only (default, secure)
#   bash start.sh --lan                        → expose on local network
#   MINDMAPPER_WORKSPACE=/path bash start.sh   → scan a specific directory
#
# Auto-creates a Python virtual environment on first run.

set -e
cd "$(dirname "$0")"

# Kill existing process on port 8081
lsof -ti:8081 | xargs -r kill -9 2>/dev/null || true
sleep 0.5

# ── Virtual environment setup ────────────────────────────────────────────────
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "📦 Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
  echo "📦 Installing dependencies..."
  "$VENV_DIR/bin/pip" install -q -r requirements.txt
  echo "✅ Setup complete."
fi

# Use venv Python
PYTHON="$VENV_DIR/bin/python3"

# Check deps are installed in venv
if ! "$PYTHON" -c "import fastapi, uvicorn" 2>/dev/null; then
  echo "📦 Installing missing dependencies..."
  "$VENV_DIR/bin/pip" install -q -r requirements.txt
fi

# ── LAN flag ─────────────────────────────────────────────────────────────────
if [[ "$1" == "--lan" ]]; then
  export MINDMAPPER_HOST=0.0.0.0
  LAN_IP=$("$PYTHON" -c "import socket; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(('8.8.8.8',80)); print(s.getsockname()[0]); s.close()" 2>/dev/null || echo "?")
  echo ""
  echo "⚠️  LAN mode enabled — full file read/write access will be"
  echo "   exposed on your local network at http://$LAN_IP:8081/"
  echo "   Only use this on trusted networks."
  echo ""
else
  export MINDMAPPER_HOST=127.0.0.1
fi

"$PYTHON" app.py
