#!/bin/bash
# Double-click in Finder to update n3n OS from upstream, rebrand, sync wiki and push to GitHub.
cd "$(dirname "$0")" || exit 1
bash "bin/n3n-update.sh"
echo ""
echo "Nhấn phím bất kỳ để đóng cửa sổ này..."
read -n 1 -s
