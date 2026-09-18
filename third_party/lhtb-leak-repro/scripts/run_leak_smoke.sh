#!/usr/bin/env bash
# One shared-verifier task with continue_until_timeout under LEAKY harbor.
# Greps the trial trajectory for filesystem / feedback leak indicators.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${ROOT}/.venv"
CONFIG="${ROOT}/configs/leak_smoke.yaml"
JOBS_DIR="${ROOT}/jobs"

if [[ ! -d "${VENV}" ]]; then
  echo "Run scripts/setup_leaky_harbor.sh first." >&2
  exit 1
fi
if [[ ! -d "${ROOT}/upstream/tasks" ]]; then
  echo "Run scripts/setup.sh first." >&2
  exit 1
fi

# shellcheck disable=SC1091
source "${VENV}/bin/activate"

echo "Running leak smoke job (requires Docker; oracle agent needs no API keys) ..."
set +e
(cd "${ROOT}" && harbor jobs start -c "${CONFIG}" --jobs-dir "${JOBS_DIR}")
job_status=$?
set -e

TRAJ="$(find "${JOBS_DIR}" -path '*/agent/trajectory.json' 2>/dev/null | head -1 || true)"
if [[ -z "${TRAJ}" ]]; then
  echo "No trajectory.json found under ${JOBS_DIR} (job exit=${job_status})." >&2
  exit "${job_status:-1}"
fi

echo "Trajectory: ${TRAJ}"
PATTERN='/logs/verifier|pytest-of-root|cp -a /tests|/tests/test_|VERIFICATION FAILED'
if grep -E "${PATTERN}" "${TRAJ}" >/dev/null; then
  echo "LEAK_INDICATORS: matched in trajectory (harness may be leaky or agent probed grader paths)."
  grep -E "${PATTERN}" "${TRAJ}" | head -20
else
  echo "No leak grep hits in trajectory (oracle may not probe; inspect manually)."
fi

exit "${job_status}"
