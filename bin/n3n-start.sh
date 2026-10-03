#!/bin/bash
set -u
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${N3N_PORT:-7777}"
URL="http://127.0.0.1:${PORT}"
LOG="${APP_DIR}/server/n3n.log"
PIDF="${APP_DIR}/server/n3n.pid"
PY="${APP_DIR}/.venv/bin/python"

export PATH="${HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:${PATH}"

if curl -sf -o /dev/null "${URL}/" 2>/dev/null; then
  open "${URL}"
  exit 0
fi

if [ ! -x "${PY}" ]; then
  osascript -e 'display alert "n3n OS" message "Chưa cài môi trường. Chạy .venv trước."' 2>/dev/null || true
  echo "Missing venv at ${PY}" >&2
  exit 1
fi

cd "${APP_DIR}/server" || exit 1
JAVIS_STATE_DIR="${APP_DIR}/server" nohup "${PY}"   -m uvicorn main:app --host 127.0.0.1 --port "${PORT}" > "${LOG}" 2>&1 &
echo $! > "${PIDF}"

for _ in $(seq 1 30); do
  sleep 1
  if curl -sf -o /dev/null "${URL}/" 2>/dev/null; then break; fi
done
open "${URL}"
