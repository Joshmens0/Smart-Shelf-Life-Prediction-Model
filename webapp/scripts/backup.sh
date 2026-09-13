#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
# Smart Shelf Life Predictor — Automated Backup Script
# Dumps PostgreSQL database and archives uploaded fruit images.
# ══════════════════════════════════════════════════════════════════

set -euo pipefail

BACKUP_DIR="/var/backups/smart-shelf-life"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
KEEP_DAYS=14

mkdir -p "${BACKUP_DIR}"

echo "[INFO] Starting Smart Shelf Life backup at ${TIMESTAMP}..."

# 1. Backup PostgreSQL Database
if docker ps | grep -q "smart_shelf_postgres"; then
    echo "[INFO] Exporting PostgreSQL database..."
    docker exec smart_shelf_postgres pg_dump -U shelfuser shelflife | gzip > "${BACKUP_DIR}/db_${TIMESTAMP}.sql.gz"
    echo "[OK] Database backup saved to ${BACKUP_DIR}/db_${TIMESTAMP}.sql.gz"
fi

# 2. Backup Uploaded Fruit Images
if docker volume inspect smart-shelf-life_backend_uploads &>/dev/null; then
    echo "[INFO] Archiving image uploads volume..."
    docker run --rm -v smart-shelf-life_backend_uploads:/uploads -v "${BACKUP_DIR}":/backup alpine \
        tar -czf "/backup/uploads_${TIMESTAMP}.tar.gz" -C /uploads .
    echo "[OK] Uploads archive saved to ${BACKUP_DIR}/uploads_${TIMESTAMP}.tar.gz"
fi

# 3. Clean up backups older than KEEP_DAYS
echo "[INFO] Pruning backups older than ${KEEP_DAYS} days..."
find "${BACKUP_DIR}" -type f -name "*.gz" -mtime +${KEEP_DAYS} -delete

echo "[SUCCESS] Backup completed successfully."
