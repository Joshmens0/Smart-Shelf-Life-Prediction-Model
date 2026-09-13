# Production VPS Deployment Guide
## Smart Shelf Life Prediction Web Application

This document provides a comprehensive, step-by-step guide to deploying the **Smart Shelf Life Prediction System** on any Virtual Private Server (VPS) — including DigitalOcean, Hetzner, AWS EC2, Linode, Vultr, or OVH.

---

## 1. System Requirements

| Component | Minimum | Recommended |
|---|---|---|
| **OS** | Ubuntu 22.04 LTS / 24.04 LTS / Debian 12 | Ubuntu 24.04 LTS |
| **CPU** | 2 vCPU | 4 vCPU |
| **RAM** | 2 GB RAM (+ 2GB swap) | 4 GB+ RAM |
| **Disk** | 25 GB SSD | 50 GB NVMe SSD |
| **Ports** | 22 (SSH), 80 (HTTP), 443 (HTTPS) | 22, 80, 443 |

---

## 2. Architecture Overview

The deployed system runs in isolated, orchestrated Docker containers:

```
Internet (HTTPS) 
   │
   ▼
[Nginx Reverse Proxy:80/443] ──► Rate Limiting, TLS Termination, Security Headers
   │
   ├──► [/]              ──► [Frontend:80] React 18+ Vite Static SPA
   │
   ├──► [/api/*]         ──► [Backend:8000] FastAPI + PyTorch CNN-MLP Inference
   │                            │
   │                            ├──► [PostgreSQL:5432] Predictions & Auth DB
   │                            └──► [Redis:6379] Rate Limiter & Locks
   │
   └──► [/uploads/*]     ──► [Backend Uploads Volume] User Uploaded Fruit Images
```

---

## 3. Quick Start (Automated One-Click Setup)

### Step 1: Connect to your fresh VPS
```bash
ssh root@YOUR_VPS_IP
```

### Step 2: Clone the Repository
```bash
cd /opt
git clone https://github.com/Joshmens0/Smart-Shelf-Life-Prediction-Model.git smart-shelf
cd smart-shelf
```

### Step 3: Run the Automated Provisioning Script
The setup script will automatically install Docker, Docker Compose, configure UFW firewall (22, 80, 443), start Fail2Ban, and generate secure random secrets in `.env`:
```bash
bash webapp/scripts/setup_vps.sh
```

### Step 4: Configure Domain (Optional) & Launch
If you have a domain pointing to your VPS IP:
1. Open `.env` and set your domain and email:
   ```env
   DOMAIN_NAME=freshness.yourdomain.com
   CERTBOT_EMAIL=admin@yourdomain.com
   ```
2. Launch the application:
   ```bash
   bash webapp/scripts/deploy.sh
   ```

### Step 5: Verify Deployment
Open your browser and navigate to:
```
http://YOUR_VPS_IP
```
Or your configured domain name.

---

## 4. Enabling SSL / HTTPS with Let's Encrypt

Once your domain DNS A-record points to your VPS IP, obtain a free SSL certificate:

```bash
# 1. Issue certificate using certbot container
docker run -it --rm \
  -v smart-shelf-life_certbot_etc:/etc/letsencrypt \
  -v smart-shelf-life_certbot_challenge:/var/www/certbot \
  certbot/certbot certonly --webroot \
  -w /var/www/certbot \
  -d freshness.yourdomain.com \
  --email admin@yourdomain.com \
  --agree-tos --no-eff-email

# 2. Link certificate files for Nginx:
docker run --rm -v smart-shelf-life_certbot_etc:/etc/letsencrypt alpine \
  sh -c "mkdir -p /etc/letsencrypt/live && cp -rL /etc/letsencrypt/live/freshness.yourdomain.com/* /etc/letsencrypt/ssl/live/ 2>/dev/null || true"

# 3. Reload Nginx
docker compose restart nginx
```

---

## 5. Maintenance & Daily Operations

### Checking Service Health & Logs
```bash
# View all running containers
docker compose ps

# View live application logs
docker compose logs -f

# View backend logs only (with structured JSON formatting)
docker compose logs -f backend

# View Nginx access & rate limiting logs
docker compose logs -f nginx
```

### Updating to Latest Version (Zero-Downtime)
```bash
bash webapp/scripts/deploy.sh
```

### Automated Daily Backups
Set up a daily cron job to backup the PostgreSQL database and uploaded fruit images:
```bash
crontab -e
```
Add the following line (runs at 03:00 AM daily):
```cron
0 3 * * * /opt/smart-shelf/webapp/scripts/backup.sh >> /var/log/smart_shelf_backup.log 2>&1
```

---

## 6. Production Security Checklist

- [x] **Non-Root Execution**: Backend container runs under unprivileged `appuser` (UID 1000).
- [x] **Rate Limiting**: Nginx enforces 20 req/sec for `/api/` and 5 req/sec for `/api/auth/`.
- [x] **Payload Caps**: `client_max_body_size 25M` drops oversized payloads before consuming Python memory.
- [x] **Security Headers**: HSTS, CSP, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`.
- [x] **Structured Logging**: All backend requests emit JSON logs with `trace_id` and latency metrics.
- [x] **Firewall**: UFW restricts ingress strictly to ports 22 (SSH), 80 (HTTP), and 443 (HTTPS).
- [x] **Brute-Force Defense**: Fail2Ban monitors and bans malicious SSH attempts automatically.
