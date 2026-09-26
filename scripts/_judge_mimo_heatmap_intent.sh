#!/usr/bin/env bash
# Judge intent on MiMo present-heatmap cells that lack a row in cot_contemplate_codes.jsonl.
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a
LOG=runs/logs/mimo_intent_judge.log
mkdir -p runs/logs
: >"$LOG"

LIST=$(mktemp)
.venv/bin/python - <<'PY' >"$LIST"
from pathlib import Path
import importlib.util, json
spec = importlib.util.spec_from_file_location("h", "scripts/render_task_heatmap.py")
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
by = {
    json.loads(l)["file"]
    for l in Path("docs/matrices/cot_contemplate_codes.jsonl").read_text().splitlines()
    if l.strip()
}
for _short, tid in h.TASKS:
    for p in h.cell_files(tid, "mimo"):
        if p.name in by:
            continue
        d = json.loads(p.read_text())
        ij = d.get("intent_judge") or {}
        if isinstance(ij, dict) and ij.get("judge_model") and not ij.get("dry_run"):
            continue
        tr = d.get("transcript") or d.get("messages")
        if not tr:
            print(f"NO_TR {p}", flush=True)
            continue
        print(p)
PY

n=0; ok=0; fail=0
while IFS= read -r f; do
  [[ -z "$f" || "$f" == NO_TR* ]] && continue
  n=$((n + 1))
  echo "[$n] JUDGE $f" | tee -a "$LOG"
  if .venv/bin/python scripts/judge_cot_contemplate.py \
      --run "$f" --write-back --append --skip-existing >>"$LOG" 2>&1; then
    ok=$((ok + 1))
    echo "[OK] $f"
  else
    fail=$((fail + 1))
    echo "[FAIL] $f"
    tail -5 "$LOG" || true
  fi
done <"$LIST"
rm -f "$LIST"
echo "DONE_INTENT n=$n ok=$ok fail=$fail"
exit "$fail"
