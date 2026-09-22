#!/bin/bash
# B3 bootstrap on VCF: env + download first open-weight model + serve notes.
# Submit from laptop:  ssh vcf 'bash -s' < scripts/b3_vcf_bootstrap.sh
# Or: scp + sbatch scripts/b3_vcf_serve_minimax.sbatch
set -euo pipefail
ROOT=/clusterhome/long_yi/score-seeking-b3
mkdir -p "$ROOT"/{venvs,models,logs,hf-cache}
export HF_HOME="$ROOT/hf-cache"
export TRANSFORMERS_CACHE="$ROOT/hf-cache"
cd "$ROOT"

echo "[$(date -Is)] B3 bootstrap start on $(hostname)"

if [[ ! -d venvs/vllm ]]; then
  python3 -m venv venvs/vllm
  # shellcheck disable=SC1091
  source venvs/vllm/bin/activate
  pip install -U pip wheel
  # CPU-side download tools first (GPU node for vllm later)
  pip install -U "huggingface_hub" hf_transfer
else
  # shellcheck disable=SC1091
  source venvs/vllm/bin/activate
  pip install -U "huggingface_hub" hf_transfer >/dev/null
fi

# First panel model: MiniMax-M2 (TP=4 friendly). Public weights — no HF token required for most files.
MODEL_ID="${B3_MODEL_ID:-MiniMaxAI/MiniMax-M2}"
echo "[$(date -Is)] downloading $MODEL_ID (this takes hours) ..."
hf download "$MODEL_ID" --local-dir "$ROOT/models/MiniMax-M2" \
  2>&1 | tee -a "$ROOT/logs/download_minimax.log"

echo "[$(date -Is)] download step finished (or interrupted). See logs/download_minimax.log"
echo "Next: sbatch serve job on h100-sxm-8-0 with vLLM TP=4, then point laptop:"
echo "  OPEN_WEIGHT_BASE_URL=http://<node>:8000/v1 OPEN_WEIGHT_MODEL=MiniMax-M2"
