#!/usr/bin/env bash
# ============================================================================
# n3n OS - Cập nhật phiên bản từ upstream & tự động push GitHub & sync Wiki
# ============================================================================
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
exec bash "bin/n3n-update.sh" "$@"
