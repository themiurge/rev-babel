#!/usr/bin/env bash
# Start the web app with the variables in .env. Loopback only: cloudflared is the way in.
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a
exec uv run --package rev-babel-web uvicorn rev_babel_web.main:app \
  --host "${WEB_BIND:-127.0.0.1}" --port "${WEB_PORT:-8000}"
