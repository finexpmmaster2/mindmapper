#!/bin/bash
# Mind Mapper — start script
#
# Usage:
#   bash start.sh         → localhost only (default, secure)
#   bash start.sh --lan   → expose on local network (⚠️ full file access)

cd "$(dirname "$0")"

# Kill existing process on port 8081
lsof -ti:8081 | xargs -r kill -9 2>/dev/null || true
sleep 0.5

# Install deps if needed
if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
  echo "Installing dependencies..."
  pip3 install -q fastapi uvicorn
fi

# LAN flag
if [[ "$1" == "--lan" ]]; then
  export MINDMAPPER_HOST=0.0.0.0
  LAN_IP=$(python3 -c "import socket; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(('8.8.8.8',80)); print(s.getsockname()[0]); s.close()" 2>/dev/null || echo "?")
  echo ""
  echo "⚠️  LAN mode enabled — full file read/write access will be"
  echo "   exposed on your local network at http://$LAN_IP:8081/"
  echo "   Only use this on trusted networks."
  echo ""
else
  export MINDMAPPER_HOST=127.0.0.1
fi

python3 app.py
