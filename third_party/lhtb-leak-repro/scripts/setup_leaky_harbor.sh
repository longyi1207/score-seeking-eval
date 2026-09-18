#!/usr/bin/env bash
# Install stock Harbor 0.7.0 + ONLY the historical leaky continue-until-timeout patch.
# Do NOT pip install -e upstream/harbor (current LHTB bundle is hardened).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${ROOT}/.venv"
HARBOR_DIR="${ROOT}/.build/harbor-0.7.0-leaky"
HARBOR_SHA="$(grep -v '^#' "${ROOT}/HARBOR_SHA.txt" | tr -d '[:space:]' | head -1)"
PATCH="${ROOT}/patches/continue-until-timeout.leaky.patch"

"${ROOT}/scripts/setup.sh"

if [[ ! -f "${PATCH}" ]]; then
  echo "Missing patch: ${PATCH}" >&2
  exit 1
fi

if [[ ! -d "${HARBOR_DIR}/.git" ]]; then
  echo "Cloning harbor-framework/harbor @ v0.7.0 (${HARBOR_SHA}) ..."
  mkdir -p "${ROOT}/.build"
  git clone --depth 1 --branch v0.7.0 https://github.com/harbor-framework/harbor.git "${HARBOR_DIR}"
fi

harbor_head="$(git -C "${HARBOR_DIR}" rev-parse HEAD)"
if [[ "${harbor_head}" != "${HARBOR_SHA}" ]]; then
  echo "Warning: harbor checkout is ${harbor_head}, expected ${HARBOR_SHA} from HARBOR_SHA.txt" >&2
fi

if grep -q 'continue_until_timeout' "${HARBOR_DIR}/src/harbor/models/task/config.py" 2>/dev/null \
  && grep -q '_read_verifier_feedback' "${HARBOR_DIR}/src/harbor/trial/trial.py" 2>/dev/null; then
  echo "Leaky patch already applied — skipping."
else
  echo "Applying leaky patch (dry-run) ..."
  if ! (cd "${HARBOR_DIR}" && patch -p1 --dry-run -s < "${PATCH}"); then
    echo "Patch dry-run failed — source may already be patched or Harbor version mismatch." >&2
    exit 1
  fi
  echo "Applying leaky patch ..."
  (cd "${HARBOR_DIR}" && patch -p1 -s < "${PATCH}")
fi

if [[ ! -d "${VENV}" ]]; then
  python3 -m venv "${VENV}"
fi
# shellcheck disable=SC1091
source "${VENV}/bin/activate"
python -m pip install -U pip wheel
python -m pip install -e "${HARBOR_DIR}"

echo "Verifying continue_until_timeout field ..."
python - <<'PY'
from harbor.models.task.config import AgentConfig
assert "continue_until_timeout" in AgentConfig.model_fields
print("ok: AgentConfig.continue_until_timeout present")
PY

echo ""
echo "Leaky Harbor ready. Activate: source ${VENV}/bin/activate"
echo "Harbor source: ${HARBOR_DIR}"
echo "LHTB tasks:    ${ROOT}/upstream/tasks"
