#!/usr/bin/env bash
# ============================================================================
# n3n OS - Cập nhật tự động phiên bản từ upstream (blogminhquy/javis-os)
# và tự động Commit + Push lên GitHub cá nhân (nguyentvtk/n3n-os)
# ============================================================================
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

UPSTREAM_URL="https://github.com/blogminhquy/javis-os.git"
ORIGIN_URL="https://github.com/nguyentvtk/n3n-os.git"

echo "=========================================================="
echo "      🚀 BẮT ĐẦU QUÁ TRÌNH CẬP NHẬT TỰ ĐỘNG n3n OS        "
echo "=========================================================="
echo "Thư mục làm việc: $ROOT_DIR"
echo "Nguồn upstream  : $UPSTREAM_URL"
echo "Kho GitHub đích : $ORIGIN_URL"
echo ""

# 1. Đảm bảo cấu hình git remote chính xác
if ! git remote | grep -q "^upstream$"; then
    echo "==> Cấu hình remote upstream..."
    git remote add upstream "$UPSTREAM_URL" || true
fi

if ! git remote | grep -q "^origin$"; then
    echo "==> Cấu hình remote origin..."
    git remote add origin "$ORIGIN_URL" || true
fi

# 2. Cất tạm thời các thay đổi chưa lưu (nếu có)
STASHED=0
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    echo "==> Cất tạm thời các chỉnh sửa cục bộ (git stash)..."
    git stash push -m "n3n-update-backup-$(date +%s)"
    STASHED=1
fi

# 3. Kéo code mới nhất từ upstream (blogminhquy/javis-os)
echo "==> Đang tải bản cập nhật mới nhất từ $UPSTREAM_URL..."
git fetch upstream main

echo "==> Hợp nhất bản cập nhật vào n3n OS..."
if ! git merge upstream/main --no-edit -m "chore(upstream): sync latest updates from upstream javis-os [$(date +'%Y-%m-%d %H:%M')]"; then
    echo "[!] Có xung đột khi hợp nhất tự động. Đang xử lý khôi phục..."
    git merge --abort || true
    if [ "$STASHED" -eq 1 ]; then
        git stash pop || true
    fi
    echo "[X] Cập nhật chưa hoàn tất do xung đột mã nguồn. Vui lòng kiểm tra git log."
    exit 1
fi

# Khôi phục lại stash nếu có
if [ "$STASHED" -eq 1 ]; then
    echo "==> Khôi phục lại các chỉnh sửa cục bộ..."
    git stash pop || true
fi

# 4. Tái cấu trúc & Đồng bộ thương hiệu n3n OS
echo "==> Đồng bộ thương hiệu n3n OS..."
if [ -f "tools/rebrand_to_n3n.py" ]; then
    python3 tools/rebrand_to_n3n.py
fi

# 5. Đảm bảo cấu hình Ollama Local tối ưu
echo "==> Kiểm tra cấu hình Ollama Model..."
if [ -f "tools/setup_ollama_default.py" ]; then
    python3 tools/setup_ollama_default.py
fi

# 6. Cập nhật thư viện Python phụ thuộc
if [ -f "requirements.txt" ] && [ -d ".venv" ]; then
    echo "==> Kiểm tra và cài đặt thư viện Python mới..."
    ./.venv/bin/pip install -r requirements.txt -q || true
fi

# 7. Đồng bộ tri thức tự học sang thư mục Wiki
echo "==> Thu thập tri thức tự học & tạo tài liệu Wiki..."
if [ -f "tools/sync_wiki.py" ]; then
    python3 tools/sync_wiki.py || true
fi

# 8. Tự động Commit & Push toàn bộ lên GitHub (nguyentvtk/n3n-os)
echo "==> Tự động Commit & Đẩy mã nguồn lên GitHub cá nhân..."
git add -A
if [ -n "$(git status --porcelain)" ]; then
    COMMIT_MSG="feat(sync): update upstream javis-os & auto-rebrand n3n OS [$(date +'%Y-%m-%d %H:%M')]"
    git commit -m "$COMMIT_MSG"
    echo "==> Đã tạo commit: $COMMIT_MSG"
fi

echo "==> Đang đẩy dữ liệu lên GitHub ($ORIGIN_URL)..."
git push origin main || echo "[!] Đẩy lên GitHub gặp sự cố mạng hoặc quyền truy cập. Bản cập nhật cục bộ vẫn an toàn."

# 9. Khởi động lại dịch vụ n3n OS
echo "==> Đang khởi động lại dịch vụ n3n OS..."
PORT="${JAVIS_PORT:-7777}"
PIDS="$(lsof -ti tcp:"$PORT" 2>/dev/null || true)"
if [ -n "$PIDS" ]; then
    echo "==> Đang dừng tiến trình cũ (PID: $PIDS)..."
    kill $PIDS 2>/dev/null || true
    sleep 2
fi

( cd server && JAVIS_STATE_DIR="$PWD" nohup ../.venv/bin/python -m uvicorn main:app \
    --host "${JAVIS_HOST:-127.0.0.1}" --port "$PORT" > javis.log 2>&1 & )

echo ""
echo "=========================================================="
echo "    🎉 CẬP NHẬT n3n OS THÀNH CÔNG VÀ ĐÃ PUSH LÊN GITHUB!  "
echo "=========================================================="
echo "🌐 URL Repository GitHub: $ORIGIN_URL"
echo "🌐 URL Wiki Tri Thức     : https://github.com/nguyentvtk/n3n-os/wiki"
echo "💻 n3n OS Dashboard      : http://127.0.0.1:$PORT"
echo "=========================================================="
