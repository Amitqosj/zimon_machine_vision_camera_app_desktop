#!/usr/bin/env bash
# Render / Linux: ensure repo root is on PYTHONPATH so `backend` and `database` import correctly.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
exec uvicorn backend.api.main:app --host 0.0.0.0 --port "${PORT:-8010}"
