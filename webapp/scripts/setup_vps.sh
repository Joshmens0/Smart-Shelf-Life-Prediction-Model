#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
# Smart Shelf Life Predictor — Production VPS Initial Setup Script
# Supported OS: Ubuntu 22.04 LTS / 24.04 LTS / Debian 12
# ══════════════════════════════════════════════════════════════════

set -euo pipefail

# Text colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}  Smart Shelf Life — Automated VPS Setup Script       ${NC}"
echo -e "${CYAN}======================================================${NC}"

# Check root privileges
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR] Please run this script as root or with sudo.${NC}"
    exit 1
fi

# 1. Update system packages
echo -e "\n${YELLOW}[1/6] Updating system packages...${NC}"
apt-get update -y && apt-get upgrade -y
apt-get install -y --no-install-recommends \
    curl \
    git \
    ufw \
    fail2ban \
    ca-certificates \
    gnupg \
    lsb-release \
    htop \
    tar \
    gzip

# 2. Configure Firewall (UFW)
echo -e "\n${YELLOW}[2/6] Configuring UFW Firewall (Ports: 22, 80, 443)...${NC}"
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw --force enable
ufw status verbose

# 3. Configure Fail2Ban for SSH protection
echo -e "\n${YELLOW}[3/6] Starting Fail2Ban service...${NC}"
systemctl enable fail2ban
systemctl start fail2ban

# 4. Install Docker & Docker Compose Plugin
echo -e "\n${YELLOW}[4/6] Installing Docker Engine & Docker Compose...${NC}"
if ! command -v docker &> /dev/null; then
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable docker
    systemctl start docker
    echo -e "${GREEN}[OK] Docker installed successfully.${NC}"
else
    echo -e "${GREEN}[OK] Docker is already installed.${NC}"
fi

# 5. Setup Project Directory & Environment
echo -e "\n${YELLOW}[5/6] Checking project environment configuration...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"

if [ ! -f ".env" ]; then
    echo -e "${CYAN}Creating .env from .env.example with secure random secrets...${NC}"
    cp .env.example .env
    RANDOM_SECRET=$(openssl rand -hex 32)
    RANDOM_DB_PASS=$(openssl rand -hex 16)
    
    sed -i "s/generate-a-secure-random-secret-key-for-production/${RANDOM_SECRET}/g" .env
    sed -i "s/choose_a_strong_password_here/${RANDOM_DB_PASS}/g" .env
    echo -e "${GREEN}[OK] Generated new .env file with secure secrets.${NC}"
else
    echo -e "${GREEN}[OK] .env file already exists.${NC}"
fi

# 6. Verify Model Artifacts
echo -e "\n${YELLOW}[6/6] Verifying trained model checkpoint...${NC}"
if [ ! -f "model/checkpoints/best_model.pt" ]; then
    echo -e "${YELLOW}[WARNING] Checkpoint model/checkpoints/best_model.pt not found!${NC}"
    echo -e "${YELLOW}Please ensure your trained checkpoint is present before launching.${NC}"
else
    echo -e "${GREEN}[OK] Model checkpoint confirmed.${NC}"
fi

echo -e "\n${CYAN}======================================================${NC}"
echo -e "${GREEN}  VPS Setup Completed Successfully!                   ${NC}"
echo -e "${CYAN}======================================================${NC}"
echo -e "Next steps to launch the application:"
echo -e "  1. Review and edit ${YELLOW}.env${NC} if you wish to configure your domain name."
echo -e "  2. Run deployment: ${CYAN}bash webapp/scripts/deploy.sh${NC}"
echo -e "  3. Access the web application at http://YOUR_VPS_IP"
echo -e "======================================================"
