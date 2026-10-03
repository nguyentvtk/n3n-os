#!/bin/bash
# Double-click in Finder to stop n3n OS.
cd "$(dirname "$0")" || exit 1
bash "bin/n3n-stop.sh"
