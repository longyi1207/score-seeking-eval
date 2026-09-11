#!/usr/bin/env bash
# stop_local.sh — stop services started by run_local.sh
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDS="$HERE/.local_run/pids"
[ -d "$PIDS" ] || { echo "no local run to stop"; exit 0; }
for f in "$PIDS"/*.pid; do
  [ -f "$f" ] || continue
  pid="$(cat "$f")"
  if kill "$pid" 2>/dev/null; then echo "stopped $(basename "$f" .pid) (pid $pid)"; fi
  rm -f "$f"
done
