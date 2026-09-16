#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
# Smart Shelf Life Predictor — Production Deployment Script
# Supports clean resets, no-cache builds, and health verification.
#
# Usage:
#   bash webapp/scripts/deploy.sh              # Standard deploy
#   bash webapp/scripts/deploy.sh --no-cache   # Rebuild without Docker cache
#   bash webapp/scripts/deploy.sh --reset      # Wipe containers/volumes & rebuild fresh
# ══════════════════════════════════════════════════════════════════

set -euo pipefail

# Text colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"

# Parse flags
NO_CACHE=false
RESET_ALL=false

for arg in "$@"; do
    case "$arg" in
        --no-cache)
            NO_CACHE=true
            ;;
        --reset|-r)
            RESET_ALL=true
            NO_CACHE=true
            ;;
        --help|-h)
            echo -e "${BOLD}Usage:${NC} bash webapp/scripts/deploy.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-cache    Rebuild all Docker images without using cached layers."
            echo "  --reset, -r   Complete reset: stops containers, removes volumes (-v),"
            echo "                rebuilds without cache, and starts fresh."
            echo "  --help, -h    Display this help text."
            exit 0
            ;;
        *)
            echo -e "${YELLOW}[WARNING] Unknown argument: $arg (ignoring)${NC}"
            ;;
    esac
done

echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}  Deploying Smart Shelf Life Application              ${NC}"
if [ "$RESET_ALL" = true ]; then
    echo -e "${YELLOW}  Mode: FULL RESET (Wiping old containers & volumes)  ${NC}"
elif [ "$NO_CACHE" = true ]; then
    echo -e "${YELLOW}  Mode: NO-CACHE (Rebuilding images from scratch)     ${NC}"
fi
echo -e "${CYAN}======================================================${NC}"

# Check .env
if [ ! -f ".env" ]; then
    echo -e "${RED}[ERROR] .env file not found in ${REPO_ROOT}!${NC}"
    echo -e "Copy .env.example to .env and configure it before deploying:"
    echo -e "  cp .env.example .env"
    exit 1
fi

# 1. Reset / Teardown if requested
if [ "$RESET_ALL" = true ]; then
    echo -e "\n${YELLOW}[Step] Resetting existing containers, networks, and volumes...${NC}"
    docker compose down -v --remove-orphans || true
    echo -e "${YELLOW}[Step] Pruning dangling Docker build cache...${NC}"
    docker builder prune -f || true
fi

# 2. Pull latest git updates if inside a tracking repository
if [ -d ".git" ]; then
    echo -e "\n${YELLOW}[1/4] Pulling latest repository updates...${NC}"
    git pull origin main || true
fi

# 3. Build Docker container images
echo -e "\n${YELLOW}[2/4] Building container images...${NC}"
if [ "$NO_CACHE" = true ]; then
    echo -e "  Running: ${CYAN}docker compose build --no-cache${NC}"
    if ! docker compose build --no-cache; then
        echo -e "\n${RED}[ERROR] Docker build failed during image export or compilation!${NC}"
        echo -e "${YELLOW}Common causes and fixes:${NC}"
        echo -e "  1. ${BOLD}Disk space full${NC}: Check with ${CYAN}df -h${NC}. Free space with: ${CYAN}docker system prune -a --volumes -f${NC}"
        echo -e "  2. ${BOLD}BuildKit cache error${NC}: Clear builder state with ${CYAN}docker builder prune -a -f${NC}"
        echo -e "  3. ${BOLD}Docker daemon lock${NC}: Restart docker with ${CYAN}sudo systemctl restart docker${NC}"
        exit 1
    fi
else
    if ! docker compose build; then
        echo -e "\n${RED}[ERROR] Docker build failed! Run with --no-cache or --reset to rebuild cleanly.${NC}"
        exit 1
    fi
fi

# 4. Free port 80 / 443 if bound by host services (e.g. system nginx/apache)
if command -v systemctl &>/dev/null; then
    if systemctl is-active --quiet nginx 2>/dev/null; then
        echo -e "\n${YELLOW}[Notice] Host Nginx is active. Stopping and disabling to free port 80/443 for Docker...${NC}"
        systemctl stop nginx 2>/dev/null || sudo systemctl stop nginx 2>/dev/null || true
        systemctl disable nginx 2>/dev/null || sudo systemctl disable nginx 2>/dev/null || true
    fi
    if systemctl is-active --quiet apache2 2>/dev/null; then
        echo -e "\n${YELLOW}[Notice] Host Apache2 is active. Stopping and disabling to free port 80/443 for Docker...${NC}"
        systemctl stop apache2 2>/dev/null || sudo systemctl stop apache2 2>/dev/null || true
        systemctl disable apache2 2>/dev/null || sudo systemctl disable apache2 2>/dev/null || true
    fi
fi

# 5. Ensure SSL certificates exist so Nginx can start cleanly
echo -e "\n${YELLOW}[Notice] Ensuring SSL certificates exist for Nginx...${NC}"
docker run --rm -v "smart-shelf-life_certbot_etc:/etc/nginx/ssl" alpine sh -c "
    mkdir -p /etc/nginx/ssl/live
    if [ ! -f /etc/nginx/ssl/live/fullchain.pem ] || [ ! -f /etc/nginx/ssl/live/privkey.pem ]; then
        echo 'Generating self-signed fallback SSL certificate...'
        apk add --no-cache openssl >/dev/null 2>&1
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout /etc/nginx/ssl/live/privkey.pem \
            -out /etc/nginx/ssl/live/fullchain.pem \
            -subj '/CN=localhost' >/dev/null 2>&1
    fi
" 2>/dev/null || true

# 6. Start containers
echo -e "\n${YELLOW}[3/4] Launching containers in detached mode...${NC}"
if [ "$RESET_ALL" = true ] || [ "$NO_CACHE" = true ]; then
    docker compose up -d --force-recreate --remove-orphans
else
    docker compose up -d --remove-orphans
fi

# 5. Wait for healthcheck verification
echo -e "\n${YELLOW}[4/4] Verifying service health status...${NC}"
sleep 5

MAX_RETRIES=20
COUNTER=0
HEALTHY=false

while [ $COUNTER -lt $MAX_RETRIES ]; do
    # Check if backend container is reporting healthy or responding to health endpoint
    if docker compose ps | grep -qi "backend.*healthy" || docker compose exec -T backend curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
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
    echo -e "${RED}[ERROR] Backend failed to become healthy within the allotted time.${NC}"
    echo -e "${YELLOW}── Backend Logs (last 40 lines) ──${NC}"
    docker compose logs backend --tail=40
    echo -e "\n${YELLOW}── Database Logs (last 20 lines) ──${NC}"
    docker compose logs db --tail=20 || true
    echo -e "\n${RED}Tip: To perform a 100% clean reset without cache, run:${NC}"
    echo -e "  ${CYAN}bash webapp/scripts/deploy.sh --reset${NC}"
    exit 1
fi

echo -e "\n${CYAN}======================================================${NC}"
echo -e "Useful Commands:"
echo -e "  - View live logs      : ${CYAN}docker compose logs -f${NC}"
echo -e "  - Backend logs only   : ${CYAN}docker compose logs -f backend${NC}"
echo -e "  - Stop application    : ${CYAN}docker compose down${NC}"
echo -e "  - Clean reset deploy  : ${CYAN}bash webapp/scripts/deploy.sh --reset${NC}"
echo -e "======================================================"
