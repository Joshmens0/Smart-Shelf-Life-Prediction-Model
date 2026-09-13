# FreshTrack — Smart Shelf Life Prediction Web Application

A full-stack, multimodal deep learning application that accurately predicts fruit freshness and remaining shelf life using visual CNN features (EfficientNet-B0) combined with environmental sensor attributes (Temperature, Humidity, Storage Environment).

---

## 🏗️ Architecture & Technology Stack

The application strictly adheres to the **Universal App Template (Architecture, Standards & Rules)**:

```
Smart-Shelf-Life-Prediction-Model/
│
├── model/                         ← Multimodal CNN-MLP Deep Learning Pipeline
│   ├── checkpoints/best_model.pt  ← Trained PyTorch Student Model Checkpoint
│   ├── config.yaml                ← Model Hyperparameters & Architecture Config
│   └── src/                       ← PyTorch LUPI Teacher-Student Architecture
│
├── webapp/
│   ├── backend/                   ← FastAPI Production Backend (Python 3.12)
│   │   ├── src/api/               ← Routers, JSON logging middleware, CORS
│   │   ├── src/database/          ← SQLAlchemy 2 async ORM & Postgres/SQLite models
│   │   ├── src/service/           ← Multimodal PyTorch inference engine
│   │   ├── migrations/            ← Version-controlled Alembic migrations
│   │   ├── test/                  ← Async Pytest test suite
│   │   ├── Dockerfile             ← Multi-stage CPU-optimized PyTorch container
│   │   └── pyproject.toml         ← Ruff linter & Pytest project manifest
│   │
│   ├── frontend/                  ← React 18 + TypeScript + Vite SPA
│   │   ├── src/assets/tokens.css  ← Standard HSL design tokens & glassmorphism
│   │   ├── src/components/        ← Shared UI & ErrorBoundary components
│   │   ├── src/pages/             ← Predict, History, Settings, Auth pages
│   │   ├── Dockerfile             ← Multi-stage Node.js build → Nginx static server
│   │   └── nginx.conf             ← Internal SPA routing configuration
│   │
│   ├── nginx/                     ← Production Nginx Reverse Proxy
│   │   ├── nginx.conf             ← JSON access logs, rate limiting zones
│   │   └── conf.d/default.conf    ← SSL/TLS termination, proxy pass, security headers
│   │
│   ├── scripts/                   ← DevOps & VPS Automation
│   │   ├── setup_vps.sh           ← One-click Ubuntu/Debian VPS provisioning
│   │   ├── deploy.sh              ← Zero-downtime containerized deployment
│   │   └── backup.sh              ← Automated PostgreSQL & uploads backup
│   │
│   └── docs/
│       ├── DEPLOYMENT_GUIDE.md    ← Comprehensive VPS Deployment Guide
│       └── APP_TEMPLATE.md        ← Workspace architectural reference
│
├── docker-compose.yml             ← Orchestrator: Nginx, Backend, Frontend, Postgres, Redis
├── .env.example                   ← Production environment configuration template
└── .github/workflows/ci.yml       ← GitHub Actions CI pipeline
```

---

## 🚀 Running Locally (Development Mode)

### 1. Backend Setup
```bash
cd webapp/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run FastAPI dev server with auto-reload (uses SQLite in-memory / dev.db)
uvicorn src.api.main:app --reload --port 8000
```
API Documentation will be available at: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd webapp/frontend
npm install
npm run dev
```
Web application will be accessible at: `http://localhost:5173`

---

## 🌐 Deploying to a VPS (Production)

Follow the complete instructions in [`webapp/docs/DEPLOYMENT_GUIDE.md`](file:///home/joshmens/repo/Smart-Shelf-Life-Prediction-Model/webapp/docs/DEPLOYMENT_GUIDE.md):

1. **SSH to VPS**: `ssh root@YOUR_VPS_IP`
2. **Clone repo**: `git clone https://github.com/Joshmens0/Smart-Shelf-Life-Prediction-Model.git && cd Smart-Shelf-Life-Prediction-Model`
3. **Provision server**: `bash webapp/scripts/setup_vps.sh`
4. **Deploy**: `bash webapp/scripts/deploy.sh`

---

## 🧪 Testing & Code Quality

```bash
# Run backend async test suite
pytest webapp/backend/test -v

# Run Ruff linter (must pass with 0 warnings)
ruff check webapp/backend/src
```
