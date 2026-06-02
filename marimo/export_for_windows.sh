#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  export_for_windows.sh /path/to/destination

Copies the runtime bundle needed by a colleague on Windows:
  - data/
  - src/
  - notebooks/
  - README.md
  - requirements.txt

The destination is created if needed. Existing files are updated in place.
EOF
}

if [[ $# -ne 1 ]]; then
  usage
  exit 1
fi

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="$1"

mkdir -p "$DEST_DIR"

rsync -a --delete \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  --exclude '.pytest_cache/' \
  "$SOURCE_DIR/data" \
  "$SOURCE_DIR/src" \
  "$SOURCE_DIR/notebooks" \
  "$SOURCE_DIR/README.md" \
  "$SOURCE_DIR/requirements.txt" \
  "$DEST_DIR"/

printf 'Exported Marimo bundle to %s\n' "$DEST_DIR"
