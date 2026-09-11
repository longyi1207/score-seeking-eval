#!/usr/bin/env bash
# smoke_docker.sh — one-command Docker verification of the Northstar stack.
#
# 1) egress containment (network internal + runtime check)
# 2) end-to-end seek run  (vulns on)  -> expect score_seek_success / P_GOLD
# 3) end-to-end honest run (vulns off) -> expect honest_solve
# 4) aggregate dashboard
#
# Works on the docker-compose stack directly (does NOT use Inspect's docker
# provider, which needs Engine >= 24.0.6 — see IMPL_NOTES.md).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$HERE/.venv/bin/python"; [ -x "$PY" ] || PY="python3"

bash "$HERE/scripts/assert_no_egress.sh"
echo
"$PY" "$HERE/inspect_eval/mock_run.py" --mode seek   --vuln-mask all --tier hard     --scope soft
echo
"$PY" "$HERE/inspect_eval/mock_run.py" --mode honest --vuln-mask 0   --tier hard     --scope hard
echo
"$PY" "$HERE/inspect_eval/results.py"
