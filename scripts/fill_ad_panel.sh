#!/usr/bin/env bash
# Fill AD present panel: kimi / gpt-5.4 / claude × n=5 × scope=none on ad-corp + ad-enterprise.
# DeepSeek + gpt-4o already have historical n=5–6 (results/). Re-run only missing models.
#
# Prereq: VMs running (az vm start), AZURE_OPENAI_API_KEY + ANTHROPIC_API_KEY in env.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SUITE="$ROOT/platform/suite"
HARNESS="$ROOT/platform/harness"
OUTDIR="$ROOT/runs/ad_panel"
mkdir -p "$OUTDIR" "$ROOT/runs"
LOG="$ROOT/runs/fill_ad_panel.log"
log(){ echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

need_key(){ [ -n "${AZURE_OPENAI_API_KEY:-}" ] || { echo "set AZURE_OPENAI_API_KEY"; exit 1; }; }
need_key

run_cell(){
  local env="$1" mk="$2" trial="$3" scope="${4:-none}"
  local out="$OUTDIR/${env}_${mk}_${scope}_r${trial}.json"
  if [ -f "$out" ] && [ "$(wc -c < "$out")" -gt 200 ]; then
    log "skip $out"; return 0
  fi
  local envdir="$ROOT/envs/$env"
  local KEY="$envdir/ssh_key"
  local CTRL
  CTRL="$(terraform -chdir="$envdir/infra" output -json hosts 2>/dev/null \
    | python3 -c "import sys,json;print(json.load(sys.stdin)['ctrl']['public_ip'])")"
  [ -n "$CTRL" ] || { log "no ctrl for $env"; return 1; }
  log "START $env $mk $scope r$trial @ $CTRL"
  ssh -i "$KEY" -o StrictHostKeyChecking=no "azureuser@$CTRL" 'mkdir -p ~/run'
  scp -i "$KEY" -o StrictHostKeyChecking=no -q \
    "$HARNESS"/*.py "$envdir/ad_config.json" "azureuser@$CTRL:~/run/"
  # Claude needs Anthropic key on the box
  local EXTRA=""
  if [ "$mk" = "claude" ]; then
    EXTRA="ANTHROPIC_API_KEY='${ANTHROPIC_API_KEY:-}' ANTHROPIC_MODEL='${ANTHROPIC_MODEL:-claude-sonnet-4-5-20250929}'"
  fi
  ssh -i "$KEY" -o StrictHostKeyChecking=no "azureuser@$CTRL" \
    "cd ~/run && AD_CONFIG=~/run/ad_config.json AZURE_OPENAI_API_KEY='$AZURE_OPENAI_API_KEY' \
     AZURE_AI_RESOURCE='${AZURE_AI_RESOURCE:-}' $EXTRA \
     ~/nsvenv/bin/python adlite_run.py --model-key $mk --scope $scope \
     --token-limit 5000000 --time-limit 1200 --out ~/run/out_${mk}_${scope}_r${trial}.json" \
    >"$OUTDIR/${env}_${mk}_${scope}_r${trial}.log" 2>&1 || true
  scp -i "$KEY" -o StrictHostKeyChecking=no -q \
    "azureuser@$CTRL:~/run/out_${mk}_${scope}_r${trial}.json" "$out" 2>/dev/null \
    && log "OK $out" || log "FAIL $env $mk r$trial (see log)"
}

configure_env(){
  local env="$1"
  log "configure $env"
  RG="$(terraform -chdir="$ROOT/envs/$env/infra" output -raw rg 2>/dev/null || true)"
  RG="${RG:-ns-${env//-/}}"
  RG="$RG" bash "$ROOT/envs/$env/configure.sh" >>"$LOG" 2>&1 || log "configure $env rc=$?"
  bash "$ROOT/envs/$env/assert.sh" >>"$LOG" 2>&1 && log "assert $env OK" || log "assert $env FAILED"
}

# Optional: only missing models for the 11-col heatmap
MODELS=(kimi gpt-5.4 claude)
ENVS=(ad-corp)
# enterprise if state exists
if terraform -chdir="$ROOT/envs/ad-enterprise/infra" output -json hosts >/dev/null 2>&1; then
  ENVS+=(ad-enterprise)
fi

for env in "${ENVS[@]}"; do
  if [ "${SKIP_CONFIGURE:-0}" = "1" ]; then
    log "SKIP_CONFIGURE=1 — assert only $env"
    bash "$ROOT/envs/$env/assert.sh" >>"$LOG" 2>&1 && log "assert $env OK" || { log "assert $env FAILED"; exit 1; }
  else
    configure_env "$env"
  fi
done

PAR="${PAR:-2}"
for env in "${ENVS[@]}"; do
  for mk in "${MODELS[@]}"; do
    for t in 1 2 3 4 5; do
      run_cell "$env" "$mk" "$t" none &
      while [ "$(jobs -r | wc -l)" -ge "$PAR" ]; do sleep 5; done
    done
  done
done
wait
log "AD panel fill done"
