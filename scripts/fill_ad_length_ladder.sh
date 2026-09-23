#!/usr/bin/env bash
# fill_ad_length_ladder.sh — run the AD honest-path length ladder (Phase 0 pilot / Phase 1 n=5).
#
# One fleet (reuses the enterprise range), rungs run SERIALLY (each rung re-plants a different
# chain depth, so L1 and L5 cannot coexist). Within a rung, trials run in parallel (PAR).
# For each rung: configure_length -> assert_length (must be green) -> N DeepSeek scope=none runs.
# Runs carry --ad-length / --honest-hops so aggregate.py slices seek rate by rung.
#
# Caps raised for the ladder (L5 honest ~100-120 turns): --max-steps 160 --time-limit 3600.
#
#   PILOT=1  bash scripts/fill_ad_length_ladder.sh     # Phase 0: 1 run per rung
#            bash scripts/fill_ad_length_ladder.sh     # Phase 1: n=5 per rung (25 runs)
#   RUNGS="L1 L5"  MODELS="deepseek gpt-5.4"  bash scripts/fill_ad_length_ladder.sh
#
# Prereq: enterprise fleet UP (terraform), .secrets present, AZURE_OPENAI_API_KEY set,
#         az logged in. This is real Azure spend — see docs/matrices/AD_LENGTH_LADDER.md.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HARNESS="$ROOT/platform/harness"
LADDER="$ROOT/envs/ad-length"
ENTDIR="$ROOT/envs/ad-enterprise"          # one fleet: reuse enterprise infra + ssh_key
KEY="$ENTDIR/ssh_key"
OUTDIR="$ROOT/runs/ad_panel"; mkdir -p "$OUTDIR"
LOG="$ROOT/runs/fill_ad_length_ladder.log"
log(){ echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }
# SSH keepalive/timeout so a dropped connection (e.g. laptop sleep) FAILS FAST instead of
# hanging a run forever. ServerAliveInterval*CountMax ≈ 2min to detect a dead peer.
SSHO="-o StrictHostKeyChecking=no -o ConnectTimeout=20 -o ServerAliveInterval=30 -o ServerAliveCountMax=4"

# Prefer explicit env (adopted fleet / no local terraform state); else terraform output.
RG="${RG:-$(terraform -chdir="$ENTDIR/infra" output -raw rg 2>/dev/null || echo ns-adent)}"
CTRL="${CTRL_IP:-$(terraform -chdir="$ENTDIR/infra" output -json hosts 2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin)['ctrl']['public_ip'])" 2>/dev/null || true)}"
[ -n "$CTRL" ] || { log "FATAL: no ctrl IP (set CTRL_IP=... or stand up the fleet first)."; exit 1; }

RUNGS="${RUNGS:-L1 L2 L3 L4 L5}"
MODELS="${MODELS:-deepseek}"
SCOPE="${SCOPE:-none}"          # none | forbid (forbid = shortcut declared out of scope)
N="${N:-5}"; [ "${PILOT:-0}" = "1" ] && N=1
PAR="${PAR:-2}"
MAX_STEPS="${MAX_STEPS:-160}"; TIME_LIMIT="${TIME_LIMIT:-3600}"; TOK="${TOK:-5000000}"
[ -z "${AZURE_OPENAI_API_KEY:-}" ] && { log "FATAL AZURE_OPENAI_API_KEY unset"; exit 1; }

# stage the harness + this rung's config ONCE per rung (rungs are serial), so concurrent
# trials never race on shared scp targets. Ships ad_config.json for the rung read-only.
stage_rung(){
  local rung="$1"
  ssh -i "$KEY" $SSHO "azureuser@$CTRL" 'mkdir -p ~/run'
  python3 "$LADDER/render_rung_config.py" "$rung" > "/tmp/ad_config.$rung.json"
  scp -i "$KEY" $SSHO -q "$HARNESS"/*.py "azureuser@$CTRL:~/run/"
  scp -i "$KEY" $SSHO -q "/tmp/ad_config.$rung.json" "azureuser@$CTRL:~/run/ad_config.json"
}

run_trial(){
  local rung="$1" mk="$2" t="$3" hops="$4"
  local out="$OUTDIR/ad_len_${rung}_${mk}_${SCOPE}_r${t}.json"
  if [ -f "$out" ] && [ "$(wc -c < "$out")" -gt 200 ]; then log "skip $out"; return 0; fi
  log "START $rung $mk r$t (hops=$hops) @ $CTRL"
  # UNIQUE per-trial env file on ctrl (concurrent trials must not share/rm one run.env).
  local ef="env_${rung}_${mk}_${t}"; local envf; envf=$(mktemp)
  { echo "AD_CONFIG=~/run/ad_config.json"; echo "AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}";
    echo "AZURE_AI_RESOURCE=${AZURE_AI_RESOURCE:-}"; } > "$envf"
  scp -i "$KEY" $SSHO -q "$envf" "azureuser@$CTRL:~/run/$ef"; rm -f "$envf"
  # hard wall-clock cap (> the run's own --time-limit) so a hung run can't block the panel.
  timeout "${RUN_HARD_CAP:-4200}" ssh -i "$KEY" $SSHO "azureuser@$CTRL" \
    "cd ~/run && set -a && . ./$ef && set +a && rm -f ./$ef && ~/nsvenv/bin/python adlite_run.py \
       --model-key $mk --scope $SCOPE --ad-length $rung --honest-hops $hops \
       --token-limit $TOK --max-steps $MAX_STEPS --time-limit $TIME_LIMIT \
       --out ~/run/out_${rung}_${mk}_r${t}.json" \
    >"$OUTDIR/ad_len_${rung}_${mk}_${SCOPE}_r${t}.log" 2>&1 || true
  scp -i "$KEY" $SSHO -q \
    "azureuser@$CTRL:~/run/out_${rung}_${mk}_r${t}.json" "$out" 2>/dev/null \
    && log "OK $out" || log "FAIL $rung $mk r$t (see log)"
}

log "=== AD length ladder: rungs=[$RUNGS] models=[$MODELS] N=$N PAR=$PAR caps: steps=$MAX_STEPS time=$TIME_LIMIT ==="
for rung in $RUNGS; do
  hops="$(python3 "$LADDER/render_rung_config.py" "$rung" | python3 -c "import json,sys;print(json.load(sys.stdin)['honest_hops'])")"
  log "--- configure $rung (hops=$hops) ---"
  RUNG="$rung" RG="$RG" bash "$LADDER/configure_length.sh" >>"$LOG" 2>&1 || { log "configure $rung FAILED"; continue; }
  if RUNG="$rung" SSH_KEY="$KEY" CTRL_IP="$CTRL" bash "$LADDER/assert_length.sh" >>"$LOG" 2>&1; then
    log "assert $rung GREEN"
  else
    log "assert $rung FAILED — skipping runs for $rung"; continue
  fi
  stage_rung "$rung"
  for mk in $MODELS; do
    for t in $(seq 1 "$N"); do
      run_trial "$rung" "$mk" "$t" "$hops" &
      while [ "$(jobs -r | wc -l)" -ge "$PAR" ]; do sleep 5; done
    done
    wait
  done
done
log "ladder fill done. Aggregate: python3 platform/harness/aggregate.py runs/ad_panel"
