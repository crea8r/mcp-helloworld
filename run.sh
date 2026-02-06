#!/usr/bin/env bash
set -euo pipefail

cd /Users/hieu/Work/learning/mcp-helloworld

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export APP_HOST="${APP_HOST:-127.0.0.1}"
export APP_PORT="${APP_PORT:-8001}"
export MCP_TRANSPORT="${MCP_TRANSPORT:-streamable-http}"
export MCP_HOST="${MCP_HOST:-127.0.0.1}"
export MCP_PORT="${MCP_PORT:-8002}"
export MCP_PATH="${MCP_PATH:-/mcp}"

uvicorn app:app --host "${APP_HOST}" --port "${APP_PORT}" --reload &
APP_PID=$!

python mcp_server.py --transport "${MCP_TRANSPORT}" --host "${MCP_HOST}" --port "${MCP_PORT}" --path "${MCP_PATH}" &
MCP_PID=$!

trap 'kill ${APP_PID} ${MCP_PID}' EXIT

echo "App server running on http://${APP_HOST}:${APP_PORT}"
echo "MCP server running on ${MCP_TRANSPORT} at http://${MCP_HOST}:${MCP_PORT}${MCP_PATH}"

wait
