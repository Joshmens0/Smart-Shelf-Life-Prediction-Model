#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
# Smart Shelf Life Predictor — Local Development Launcher
# Starts both Backend (FastAPI :8000) and Frontend (Vite :5173).
# ══════════════════════════════════════════════════════════════════

set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${REPO_ROOT}"

echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}  Launching FreshTrack in Development Mode            ${NC}"
echo -e "${CYAN}======================================================${NC}"

# Find python interpreter
PYTHON_BIN="${REPO_ROOT}/model/.venv/bin/python"
if [ ! -f "${PYTHON_BIN}" ]; then
    PYTHON_BIN="$(command -v python3 || command -v python)"
fi

# 1. Kill any existing processes on ports 8000 & 5173
fuser -k 8000/tcp 5173/tcp 2>/dev/null || true

# 2. Launch FastAPI Backend
echo -e "\n${YELLOW}[1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...${NC}"
PYTHONPATH="webapp/backend/src" "${PYTHON_BIN}" -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# 3. Launch Vite Frontend
echo -e "${YELLOW}[2/2] Starting React + Vite Frontend on http://127.0.0.1:5173 ...${NC}"
(cd webapp/frontend && npm run dev -- --host 127.0.0.1 --port 5173) &
FRONTEND_PID=$!

echo -e "\n${GREEN}[SUCCESS] Both services are running in development mode!${NC}"
echo -e "  - Frontend UI    : ${CYAN}http://127.0.0.1:5173/${NC}"
echo -e "  - Backend API    : ${CYAN}http://127.0.0.1:8000/api/health${NC}"
echo -e "  - API Swagger Docs: ${CYAN}http://127.0.0.1:8000/docs${NC}"
echo -e "\nPress CTRL+C to stop both dev servers."

# Trap SIGINT / SIGTERM to cleanly kill background processes
trap "echo -e '\nStopping dev servers...'; kill ${BACKEND_PID} ${FRONTEND_PID} 2>/dev/null || true; exit 0" INT TERM
wait
