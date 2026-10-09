#!/bin/bash
# Talos: one script to set up, run and install as a macOS background service.
#   ./scripts/talos.sh setup      install everything (Python 3.11 venv, models deps, UI build)
#   ./scripts/talos.sh start      run in the foreground
#   ./scripts/talos.sh dev        backend with reload + React dev server (port 3000)
#   ./scripts/talos.sh install    run always in background (launchd, starts at login)
#   ./scripts/talos.sh uninstall  remove the background service
#   ./scripts/talos.sh logs       follow the service logs
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
VENV="$ROOT/.venv"
LABEL="com.talos.assistant"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG_DIR="$ROOT/data/logs"

port() {
  local p
  p=$(grep -E '^API_PORT=' "$ROOT/.env" 2>/dev/null | cut -d= -f2 | cut -d'#' -f1 | tr -d ' ')
  echo "${p:-8000}"
}

setup() {
  echo "==> System packages (ffmpeg for audio, espeak-ng for Spanish voice)"
  if command -v brew >/dev/null; then
    brew list ffmpeg >/dev/null 2>&1 || brew install ffmpeg
    brew list espeak-ng >/dev/null 2>&1 || brew install espeak-ng
    command -v python3.11 >/dev/null || brew install python@3.11
  fi

  echo "==> Python environment"
  [ -d "$VENV" ] || python3.11 -m venv "$VENV"
  "$VENV/bin/pip" install -q --upgrade pip
  "$VENV/bin/pip" install -q -r "$ROOT/backend/requirements.txt"

  echo "==> Native audio player (media keys: ⏯ pauses Talos)"
  build_player || echo "   (skipped: Talos will use afplay, without media-key control)"

  echo "==> Frontend build"
  (cd "$ROOT/frontend" && npm install --no-audit --no-fund && npm run build)

  if [ ! -f "$ROOT/.env" ]; then
    cp "$ROOT/.env.example" "$ROOT/.env"
    sed -i '' "s|^CLAUDE_BIN=claude |CLAUDE_BIN=$(command -v claude || echo claude) |" "$ROOT/.env"
    echo "==> Created .env — add your TOTALGPT_API_KEY there"
  fi
  echo "==> Done. Run: ./scripts/talos.sh start"
}

build_player() {
  command -v swiftc >/dev/null || return 1
  mkdir -p "$ROOT/bin"
  swiftc -O "$ROOT/native/TalosPlayer.swift" -o "$ROOT/bin/talos-player" 2>/dev/null && return 0
  # Command Line Tools sometimes ship a duplicate SwiftBridging modulemap; hide it via a VFS overlay
  local tmp; tmp=$(mktemp -d)
  : > "$tmp/empty.modulemap"
  printf '{"version":0,"case-sensitive":"false","roots":[{"type":"file","name":"%s","external-contents":"%s"}]}' \
    "$(xcode-select -p)/usr/include/swift/bridging.modulemap" "$tmp/empty.modulemap" > "$tmp/overlay.yaml"
  swiftc -O -vfsoverlay "$tmp/overlay.yaml" -Xcc -ivfsoverlay -Xcc "$tmp/overlay.yaml" \
    "$ROOT/native/TalosPlayer.swift" -o "$ROOT/bin/talos-player"
}

start() {
  cd "$ROOT/backend"
  exec "$VENV/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port "${1:-$(port)}"
}

dev() {
  cd "$ROOT/backend"
  "$VENV/bin/python" -m uvicorn app.main:app --reload --port 8000 &
  trap 'kill %1' EXIT
  cd "$ROOT/frontend" && npm start
}

install_service() {
  mkdir -p "$LOG_DIR" "$(dirname "$PLIST")"
  cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>$ROOT/scripts/talos.sh</string><string>start</string></array>
  <key>WorkingDirectory</key><string>$ROOT</string>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string></dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$LOG_DIR/talos.log</string>
  <key>StandardErrorPath</key><string>$LOG_DIR/talos.log</string>
</dict>
</plist>
EOF
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$PLIST"
  echo "Talos running in background: http://localhost:$(port)  (logs: ./scripts/talos.sh logs)"
}

uninstall_service() {
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  rm -f "$PLIST"
  echo "Service removed"
}

case "$1" in
  setup) setup ;;
  start) start "$2" ;;
  dev) dev ;;
  install) install_service ;;
  uninstall) uninstall_service ;;
  logs) tail -f "$LOG_DIR/talos.log" ;;
  build-player) build_player && echo "built $ROOT/bin/talos-player" ;;
  *) sed -n '2,9p' "$0" | sed 's/^# //'; exit 1 ;;
esac
