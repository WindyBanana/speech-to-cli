#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${PROJECT_ROOT}/.venv"

cd "${PROJECT_ROOT}"

if [[ ! -d "${VENV_PATH}" ]]; then
  python3 -m venv "${VENV_PATH}"
  echo "Created virtual environment at ${VENV_PATH}"
else
  echo "Virtual environment already exists at ${VENV_PATH}"
fi

source "${VENV_PATH}/bin/activate"

pip install --upgrade pip
pip install -r requirements.txt

echo
echo "Environment ready. Activate it anytime with:"
echo "  source .venv/bin/activate"
