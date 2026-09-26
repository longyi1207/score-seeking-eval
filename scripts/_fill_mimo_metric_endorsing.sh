#!/usr/bin/env bash
# Fill MiMo metric endorsing × n=5 (heatmap-comparable arm).
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a
LOG=runs/logs/mimo_metric_endorsing.log
mkdir -p runs/logs
: >"$LOG"

run_one() {
  local i=$1
  local out="runs/metric_mimo_endorsing_r${i}.json"
  if [[ -s "$out" ]]; then
    echo "[skip] $out"
    return 0
  fi
  echo "[START] $out"
  if .venv/bin/python tasks/metric_redef/run_metric.py \
      --scope none --precedent endorsing --monitoring control \
      --model-key mimo --out "$out" >>"$LOG" 2>&1; then
    echo "[OK] $out"
  else
    echo "[FAIL] $out"
    tail -8 "$LOG" || true
    return 1
  fi
}

fails=0
for i in 1 2 3 4 5; do
  run_one "$i" &
  while [[ "$(jobs -r | wc -l | tr -d ' ')" -ge 2 ]]; do sleep 2; done
done
wait || true
for i in 1 2 3 4 5; do
  out="runs/metric_mimo_endorsing_r${i}.json"
  if [[ ! -s "$out" ]]; then
    echo "[MISSING] $out"
    fails=$((fails + 1))
  fi
done
echo "DONE_METRIC fails=$fails"
exit "$fails"
