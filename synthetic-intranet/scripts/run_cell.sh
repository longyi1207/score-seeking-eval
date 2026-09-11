#!/usr/bin/env bash
# run_cell.sh — run one factorial condition cell.
#
# Real (model-driven) mode uses Inspect:
#   scripts/run_cell.sh contained      --model openai/gpt-4o-mini
#   scripts/run_cell.sh pressure_soft  --model azureai/<deployment>
# (model can also come from the INSPECT_EVAL_MODEL env var.)
#
# Wiring-smoke mode (no model / no key) drives the scripted mock agent through the
# same cell so you can confirm the stack + labels for that cell:
#   scripts/run_cell.sh contained     --mock honest
#   scripts/run_cell.sh pressure_soft --mock seek
#
# Cells are defined in packs/northstar/configs/<cell>.env .
set -euo pipefail

CELL="${1:?usage: run_cell.sh <cell> [--model M | --mock seek|honest]}"; shift || true
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACK="$HERE/packs/northstar"
ENVF="$PACK/configs/$CELL.env"
[ -f "$ENVF" ] || { echo "no such cell config: $ENVF"; exit 1; }
# shellcheck disable=SC1090
set -a; source "$ENVF"; set +a

MODE="model"; MODEL="${INSPECT_EVAL_MODEL:-}"; MOCKAGENT="seek"
while [ $# -gt 0 ]; do
  case "$1" in
    --model) MODEL="$2"; shift 2;;
    --mock)  MODE="mock"; MOCKAGENT="${2:-seek}"; shift 2;;
    *) echo "unknown arg $1"; exit 1;;
  esac
done

PY="$HERE/.venv/bin/python"; [ -x "$PY" ] || PY="python3"

echo "=== cell: $CELL ==="
echo "  scope=$SCOPE tier=$TASK_TIER vuln_mask=$VULN_MASK topology=$TOPOLOGY_LABEL clue=$CLUE step_limit=$STEP_LIMIT"

if [ "$MODE" = "mock" ]; then
  echo "  (wiring-smoke via mock agent: $MOCKAGENT)"
  "$PY" "$HERE/inspect_eval/mock_run.py" --mode "$MOCKAGENT" \
    --vuln-mask "$VULN_MASK" --tier "$TASK_TIER" --scope "$SCOPE" --seed "${SEED:-1337}"
  exit 0
fi

if [ -z "$MODEL" ]; then
  cat >&2 <<MSG
No model set. Either:
  * export INSPECT_EVAL_MODEL=... (or pass --model ...), e.g. an Azure OpenAI
    deployment per repo policy (docs/AZURE.md), then re-run; or
  * run the wiring smoke without a model:  scripts/run_cell.sh $CELL --mock $MOCKAGENT
MSG
  exit 3
fi

cd "$HERE/inspect_eval"
exec "$PY" -m inspect_ai eval northstar.py \
  --model "$MODEL" \
  -T scope="$SCOPE" -T egress="$EGRESS" -T topology_label="$TOPOLOGY_LABEL" \
  -T clue="$CLUE" -T vuln_mask="$VULN_MASK" -T task_tier="$TASK_TIER" \
  -T step_limit="$STEP_LIMIT" -T seed="${SEED:-1337}"
