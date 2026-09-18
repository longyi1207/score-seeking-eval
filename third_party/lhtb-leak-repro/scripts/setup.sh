#!/usr/bin/env bash
# Clone LHTB at the pinned commit (no full LFS pull).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SHA="$(tr -d '[:space:]' < "${ROOT}/UPSTREAM_SHA.txt")"
UPSTREAM="${ROOT}/upstream"

if command -v git-lfs >/dev/null 2>&1; then
  git lfs install >/dev/null 2>&1 || true
fi

if [[ -d "${UPSTREAM}/.git" ]]; then
  current="$(git -C "${UPSTREAM}" rev-parse HEAD)"
  if [[ "${current}" != "${SHA}" ]]; then
    echo "upstream/ exists at ${current}; expected ${SHA}. Remove upstream/ or reset manually." >&2
    exit 1
  fi
  echo "LHTB upstream already at ${SHA}"
else
  echo "Cloning LHTB @ ${SHA} into upstream/ ..."
  git clone --depth 1 https://github.com/zli12321/LHTB.git "${UPSTREAM}"
  git -C "${UPSTREAM}" fetch --depth 1 origin "${SHA}"
  git -C "${UPSTREAM}" checkout "${SHA}"
fi

echo "upstream HEAD: $(git -C "${UPSTREAM}" rev-parse HEAD)"
