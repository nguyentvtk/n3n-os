#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script tái cấu trúc & đổi tên thương hiệu từ Javis OS sang n3n OS
"""
import os
import re

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def replace_in_file(filepath, replacements):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    changed = False
    for old_str, new_str in replacements:
        if old_str in content:
            content = content.replace(old_str, new_str)
            changed = True

    if changed:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated: {os.path.relpath(filepath, APP_DIR)}")
    else:
        print(f"No match in: {os.path.relpath(filepath, APP_DIR)}")

def main():
    print("=== ĐANG TIẾN HÀNH REBRAND SANG n3n OS ===")

    # 1. Giao diện Frontend
    replace_in_file(os.path.join(APP_DIR, "dashboard", "index.html"), [
        ("<title>Javis OS</title>", "<title>n3n OS</title>"),
        ('content="Javis OS"', 'content="n3n OS"'),
        ('placeholder="Javis OS"', 'placeholder="n3n OS"'),
        ("Cập nhật mới và tin từ Javis OS", "Cập nhật mới và tin từ n3n OS"),
    ])

    replace_in_file(os.path.join(APP_DIR, "dashboard", "manifest.json"), [
        ('"name": "Javis OS"', '"name": "n3n OS"'),
        ('"short_name": "Javis OS"', '"short_name": "n3n OS"')
    ])

    replace_in_file(os.path.join(APP_DIR, "dashboard", "console.js"), [
        ('"Javis OS"', '"n3n OS"'),
        ('>Javis OS<', '>n3n OS<'),
        ('span class="upd-name">Javis OS', 'span class="upd-name">n3n OS'),
        ('span class="gcard-name">Javis OS', 'span class="gcard-name">n3n OS'),
    ])

    replace_in_file(os.path.join(APP_DIR, "dashboard", "app.js"), [
        ('cfg.workspace_name || "Javis OS"', 'cfg.workspace_name || "n3n OS"'),
        ('"Javis OS"', '"n3n OS"')
    ])

    replace_in_file(os.path.join(APP_DIR, "dashboard", "i18n", "vi.json"), [
        ("Javis OS", "n3n OS"),
        ("JAVIS OS", "n3n OS"),
        ("Javis", "n3n")
    ])

    replace_in_file(os.path.join(APP_DIR, "dashboard", "i18n", "en.json"), [
        ("Javis OS", "n3n OS"),
        ("JAVIS OS", "n3n OS"),
        ("Javis", "n3n")
    ])

    # 2. Cấu hình Backend
    replace_in_file(os.path.join(APP_DIR, "server", "config.py"), [
        ('"workspace_name": "Javis OS"', '"workspace_name": "n3n OS"'),
    ])

    replace_in_file(os.path.join(APP_DIR, "server", "main.py"), [
        ('app = FastAPI(title="Javis OS")', 'app = FastAPI(title="n3n OS")'),
        ('os.getenv("WORKSPACE_NAME", "Javis OS")', 'os.getenv("WORKSPACE_NAME", "n3n OS")'),
        ('patch["workspace_name"] or "Javis OS"', 'patch["workspace_name"] or "n3n OS"'),
        ('cfg.get("workspace_name") or "Javis OS"', 'cfg.get("workspace_name") or "n3n OS"'),
    ])

    replace_in_file(os.path.join(APP_DIR, "server", "image_gen.py"), [
        ('BRAND_SOFTWARE = "Javis OS"', 'BRAND_SOFTWARE = "n3n OS"'),
    ])

    replace_in_file(os.path.join(APP_DIR, "server", "totp.py"), [
        ('ten_workspace: str = "Javis OS"', 'ten_workspace: str = "n3n OS"'),
    ])

    # 3. Tạo các script khởi chạy dành riêng cho n3n OS
    start_cmd = os.path.join(APP_DIR, "Start n3n OS.command")
    with open(start_cmd, "w", encoding="utf-8") as f:
        f.write('''#!/bin/bash
# Double-click in Finder to start n3n OS and open the dashboard.
cd "$(dirname "$0")" || exit 1
bash "bin/n3n-start.sh"
echo ""
echo "n3n OS is running at http://127.0.0.1:7777"
echo "This window can be closed - the server keeps running in the background."
''')
    os.chmod(start_cmd, 0o755)

    stop_cmd = os.path.join(APP_DIR, "Stop n3n OS.command")
    with open(stop_cmd, "w", encoding="utf-8") as f:
        f.write('''#!/bin/bash
# Double-click in Finder to stop n3n OS.
cd "$(dirname "$0")" || exit 1
bash "bin/n3n-stop.sh"
''')
    os.chmod(stop_cmd, 0o755)

    # 4. Tạo script trong bin
    start_sh = os.path.join(APP_DIR, "bin", "n3n-start.sh")
    with open(start_sh, "w", encoding="utf-8") as f:
        f.write('''#!/bin/bash
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
JAVIS_STATE_DIR="${APP_DIR}/server" nohup "${PY}" \
  -m uvicorn main:app --host 127.0.0.1 --port "${PORT}" > "${LOG}" 2>&1 &
echo $! > "${PIDF}"

for _ in $(seq 1 30); do
  sleep 1
  if curl -sf -o /dev/null "${URL}/" 2>/dev/null; then break; fi
done
open "${URL}"
''')
    os.chmod(start_sh, 0o755)

    stop_sh = os.path.join(APP_DIR, "bin", "n3n-stop.sh")
    with open(stop_sh, "w", encoding="utf-8") as f:
        f.write('''#!/bin/bash
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
''')
    os.chmod(stop_sh, 0o755)

    print("=== HOÀN TẤT REBRAND THÀNH n3n OS ===")

if __name__ == "__main__":
    main()
