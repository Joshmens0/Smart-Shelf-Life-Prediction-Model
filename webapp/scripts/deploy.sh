#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
# Smart Shelf Life Predictor — Production Deployment Script
# Rebuilds and launches Docker Compose containers safely.
# ══════════════════════════════════════════════════════════════════

set -euo pipefail

# Text colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"

echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}  Deploying Smart Shelf Life Application              ${NC}"
echo -e "${CYAN}======================================================${NC}"

# Check .env
if [ ! -f ".env" ]; then
    echo -e "${RED}[ERROR] .env file not found! Run bash webapp/scripts/setup_vps.sh first.${NC}"
    exit 1
fi

# 1. Pull latest git code if in a git repository
if [ -d ".git" ]; then
    echo -e "\n${YELLOW}[1/4] Pulling latest repository updates...${NC}"
    git pull origin main || true
fi

# 2. Build Docker images
echo -e "\n${YELLOW}[2/4] Building production container images...${NC}"
docker compose build

# 3. Start or update containers
echo -e "\n${YELLOW}[3/4] Launching containers in detached mode...${NC}"
docker compose up -d --remove-orphans

# 4. Wait for healthcheck verification
echo -e "\n${YELLOW}[4/4] Verifying service health status...${NC}"
sleep 5

MAX_RETRIES=15
COUNTER=0
HEALTHY=false

while [ $COUNTER -lt $MAX_RETRIES ]; do
    if docker compose ps | grep -q "smart_shelf_backend.*healthy"; then
        HEALTHY=true
        break
    fi
    echo -n "."
    sleep 3
    COUNTER=$((COUNTER+1))
done
echo ""

if [ "$HEALTHY" = true ]; then
    echo -e "${GREEN}[SUCCESS] All application services are up and healthy!${NC}"
    docker compose ps
else
    echo -e "${YELLOW}[WARNING] Backend is still initializing or starting up. Check logs:${NC}"
    docker compose logs backend --tail=30
fi

echo -e "\n${CYAN}======================================================${NC}"
echo -e "Useful Commands:"
echo -e "  - View live logs    : ${CYAN}docker compose logs -f${NC}"
echo -e "  - Backend logs only : ${CYAN}docker compose logs -f backend${NC}"
echo -e "  - Stop application  : ${CYAN}docker compose down${NC}"
echo -e "  - Restart services  : ${CYAN}docker compose restart${NC}"
echo -e "======================================================"
