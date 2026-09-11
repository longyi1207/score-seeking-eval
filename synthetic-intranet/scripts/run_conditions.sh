#!/usr/bin/env bash
# run_conditions.sh — run the two required V1 condition cells (V1_SPEC §5, §10).
#
#   contained     : scope=hard, vuln_mask=0, task=hard      -> expect LOW seek
#   pressure_soft : scope=soft/mislabel, vulns on, pressure -> expect seek attempts
#
# Pass through --model M for a real run, or --mock to smoke both cells' wiring.
#   scripts/run_conditions.sh --model azureai/<deployment>
#   scripts/run_conditions.sh --mock
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ "${1:-}" = "--mock" ]; then
  bash "$HERE/scripts/run_cell.sh" contained     --mock honest
  bash "$HERE/scripts/run_cell.sh" pressure_soft --mock seek
else
  bash "$HERE/scripts/run_cell.sh" contained "$@"
  bash "$HERE/scripts/run_cell.sh" pressure_soft "$@"
fi

echo
echo "=== aggregate ==="
PY="$HERE/.venv/bin/python"; [ -x "$PY" ] || PY="python3"
"$PY" "$HERE/inspect_eval/results.py" || true
