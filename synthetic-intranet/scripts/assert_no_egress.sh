#!/usr/bin/env bash
# assert_no_egress.sh — prove the eval has no real internet egress.
#
# Two checks:
#   (1) static: the compose network is declared `internal: true`
#   (2) runtime: from the agent sandbox (`default`), a public IP is UNREACHABLE
#       while an internal service IS reachable (positive control)
#
# Self-contained: brings the stack up if needed and tears down what it started.
#
# Usage: scripts/assert_no_egress.sh
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACK="$HERE/packs/northstar"
cd "$PACK"

export VULN_MASK="${VULN_MASK:-0}" SEED="${SEED:-1337}" TIER="${TIER:-hard}"

fail=0

echo "== (1) static: network internal: true =="
if docker compose -f compose.yaml config | grep -A3 -E 'northstar_lab:' | grep -q 'internal: true'; then
  echo "  OK: northstar_lab is internal:true"
else
  echo "  FAIL: northstar_lab is not marked internal:true"; fail=1
fi

STARTED=0
if [ -z "$(docker compose -f compose.yaml ps -q default 2>/dev/null)" ]; then
  echo "== bringing stack up for runtime check =="
  docker compose -f compose.yaml up -d >/dev/null 2>&1
  STARTED=1
  # wait for the agent sandbox to be running
  for _ in $(seq 1 30); do
    [ -n "$(docker compose -f compose.yaml ps -q default 2>/dev/null)" ] && break
    sleep 1
  done
  sleep 3
fi

echo "== (2) runtime egress checks from the agent sandbox =="
# positive control: internal service reachable
if docker compose -f compose.yaml exec -T default \
     python -c "import urllib.request;print(urllib.request.urlopen('http://grader.northstar.lab:8090/healthz',timeout=5).status)" \
     2>/dev/null | grep -q 200; then
  echo "  OK: internal grader.northstar.lab reachable from agent"
else
  echo "  FAIL: agent cannot reach internal service (positive control failed)"; fail=1
fi

# negative: public IP must be UNREACHABLE (TCP connect to 1.1.1.1:80 should fail)
if docker compose -f compose.yaml exec -T default \
     python -c "import socket,sys; s=socket.socket(); s.settimeout(5);
try:
    s.connect(('1.1.1.1',80)); print('REACHED'); sys.exit(0)
except Exception as e:
    print('blocked:', type(e).__name__); sys.exit(1)" 2>/dev/null | grep -q REACHED; then
  echo "  FAIL: agent reached a public IP (egress not contained)"; fail=1
else
  echo "  OK: public IP unreachable from agent (egress contained)"
fi

if [ "$STARTED" = "1" ]; then
  echo "== tearing down (this script started the stack) =="
  docker compose -f compose.yaml down -v >/dev/null 2>&1
fi

if [ "$fail" = "0" ]; then
  echo "ASSERT_NO_EGRESS: PASS"
else
  echo "ASSERT_NO_EGRESS: FAIL"; exit 1
fi
