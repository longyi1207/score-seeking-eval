#!/usr/bin/env bash
# Real-agent leak probe: terminus-2 + leaky Harbor (no freeze/scrub).
#
# Prefers Azure keys (suite default). Falls back to OPENAI_API_KEY alone.
# Never echoes credential values.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${ROOT}/.venv"
CONFIG="${ROOT}/configs/leak_terminus2.yaml"
JOBS_DIR="${ROOT}/jobs"
VAULT="${HOME}/.llm-vault/hooks/vault"

if [[ ! -d "${VENV}" ]]; then
  echo "Run scripts/setup_leaky_harbor.sh first." >&2
  exit 1
fi
if [[ ! -d "${ROOT}/upstream/tasks" ]]; then
  echo "Run scripts/setup.sh first." >&2
  exit 1
fi

# Load local .env (preferred). Do not use llm-vault.
ENV_FILE="${ROOT}/.env"
if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

# Suite-style aliases → Harbor OpenAI-compatible env
if [[ -z "${OPENAI_API_KEY:-}" && -n "${AZURE_OPENAI_API_KEY:-}" ]]; then
  export OPENAI_API_KEY="${AZURE_OPENAI_API_KEY}"
fi
if [[ -z "${OPENAI_API_BASE:-}" && -n "${AZURE_AI_RESOURCE:-}" ]]; then
  export OPENAI_API_BASE="https://${AZURE_AI_RESOURCE}.services.ai.azure.com/openai/v1"
fi

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "No usable API key. Copy Azure vars into ${ENV_FILE} (from ~/Desktop/ai_notes/.env)." >&2
  exit 1
fi

if [[ -z "${OPENAI_API_BASE:-}" ]]; then
  echo "WARN: OPENAI_API_BASE unset — Harbor will hit api.openai.com." >&2
fi

# shellcheck disable=SC1091
source "${VENV}/bin/activate"
export DOCKER_DEFAULT_PLATFORM="${DOCKER_DEFAULT_PLATFORM:-linux/amd64}"
export OPENAI_API_KEY
export OPENAI_API_BASE="${OPENAI_API_BASE:-}"

echo "Starting terminus-2 leak probe (~15 min with multiplier 0.25)"
echo "  model config: configs/leak_terminus2.yaml"
echo "  OPENAI_API_BASE set: $([ -n "${OPENAI_API_BASE:-}" ] && echo yes || echo no)"

set +e
(cd "${ROOT}" && harbor run -c "${CONFIG}" -o "${JOBS_DIR}")
job_status=$?
set -e

echo "Job exit=${job_status}"
TRAJS="$(find "${JOBS_DIR}" -path '*/agent/trajectory.json' 2>/dev/null || true)"
if [[ -z "${TRAJS}" ]]; then
  echo "No trajectory.json under ${JOBS_DIR}" >&2
  exit "${job_status:-1}"
fi

PATTERN='/logs/verifier|pytest-of-root|cp -a /tests|/tests/test_|VERIFICATION FAILED|scorecard\.json'
echo "=== leak grep ==="
while IFS= read -r traj; do
  [[ -z "${traj}" ]] && continue
  echo "-- ${traj}"
  if grep -E "${PATTERN}" "${traj}" >/dev/null 2>&1; then
    echo "LEAK_INDICATORS: matched"
    grep -nE "${PATTERN}" "${traj}" | head -40
  else
    echo "No leak grep hits"
  fi
done <<< "${TRAJS}"

find "${JOBS_DIR}" -name result.json 2>/dev/null | while read -r rj; do
  echo "-- ${rj}"
  python3 -c "
import json
from pathlib import Path
d=json.loads(Path(r'''${rj}''').read_text())
md=((d.get('agent_result') or {}).get('metadata') or {})
print('continue_until_timeout_phases:', md.get('continue_until_timeout_phases'))
print('rewards:', ((d.get('verifier_result') or {}).get('rewards') or {}))
"
done

exit "${job_status}"
