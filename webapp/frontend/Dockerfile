# ══════════════════════════════════════════════════════════════════
# Stage 1: Build Frontend Assets
# ══════════════════════════════════════════════════════════════════
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package manifests first for optimal Docker layer caching
COPY webapp/frontend/package.json webapp/frontend/package-lock.json* ./

RUN npm ci

# Copy frontend source code
COPY webapp/frontend/ ./

# Build production bundle (Vite outputs to /app/dist)
RUN npm run build

# ══════════════════════════════════════════════════════════════════
# Stage 2: Production Web Server
# ══════════════════════════════════════════════════════════════════
FROM nginx:1.27-alpine AS runner

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx configuration for SPA routing
COPY webapp/frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
