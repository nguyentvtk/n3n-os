#!/bin/bash
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDF="${APP_DIR}/server/n3n.pid"
if [ -f "${PIDF}" ]; then
  PID="$(cat "${PIDF}")"
  kill "${PID}" 2>/dev/null || true
  rm -f "${PIDF}"
  echo "n3n OS (PID ${PID}) đã dừng."
else
  pkill -f "uvicorn main:app --host 127.0.0.1 --port 7777" 2>/dev/null || true
  echo "Đã dừng các tiến trình n3n OS uvicorn."
fi
