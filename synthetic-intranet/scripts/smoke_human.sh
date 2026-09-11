#!/usr/bin/env bash
# smoke_human.sh — end-to-end human walkthrough proof (NO Docker required).
#
# Phase 1: bring the stack up with all vulns ON, assert every payoff channel
#          (P_GOLD x2, P_POISON, P_TOKEN) succeeds and the honest path succeeds.
# Phase 2: bring the stack up with all vulns OFF, assert every illicit channel is
#          BLOCKED while the honest path still succeeds.
#
# This is the V1_SPEC §10 "done definition" #1 and #2 check, runnable today.
#
# Usage: scripts/smoke_human.sh [seed] [tier]
set -euo pipefail

SEED="${1:-1337}"
TIER="${2:-hard}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACK="$HERE/packs/northstar"
PY="$HERE/.venv/bin/python"; [ -x "$PY" ] || PY="python3"

cleanup() { bash "$HERE/scripts/stop_local.sh" >/dev/null 2>&1 || true; }
trap cleanup EXIT

ALL_VULNS="V_IDOR,V_PREVIEW_TRAVERSAL,V_OPEN_CACHE,V_LEAKED_BOT_TOKEN"

echo "########## PHASE 1: vulns ON ##########"
bash "$HERE/scripts/run_local.sh" "$SEED" "$TIER" "$ALL_VULNS" >/dev/null
"$PY" "$HERE/scripts/smoke_walk.py" --base 127.0.0.1 \
  --fixtures "$HERE/.local_run/fixtures" --pack "$PACK" --tier "$TIER" --expect on
bash "$HERE/scripts/stop_local.sh" >/dev/null

echo
echo "########## PHASE 2: vulns OFF ##########"
bash "$HERE/scripts/run_local.sh" "$SEED" "$TIER" "0" >/dev/null
"$PY" "$HERE/scripts/smoke_walk.py" --base 127.0.0.1 \
  --fixtures "$HERE/.local_run/fixtures" --pack "$PACK" --tier "$TIER" --expect off
bash "$HERE/scripts/stop_local.sh" >/dev/null

echo
echo "########## SMOKE OK: channels open with vulns on, closed with vulns off ##########"
