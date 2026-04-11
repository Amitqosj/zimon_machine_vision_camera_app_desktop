#!/usr/bin/env bash
# Use when Render "Root Directory" is set to `backend` (cwd = this folder).
# Do not use: uvicorn backend.api.main:app — Python needs repo root on PYTHONPATH for `backend` + `database`.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$HERE/../scripts/run-api-render.sh"
