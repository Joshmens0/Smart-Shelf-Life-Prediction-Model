import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from core.config import settings
from database import get_db
from database.models import PredictionRecord, User
from api.middleware.auth_guard import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["history"])

@router.get("/history")
async def get_history(
    current_user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves prediction history records.
    
    If REQUIRE_AUTH is True, it filters by the logged-in user.
    Otherwise, returns all records globally.
    """
    stmt = select(PredictionRecord)
    
    # Filter by user if authentication is enabled
    if settings.REQUIRE_AUTH and current_user:
        stmt = stmt.where(PredictionRecord.user_id == current_user.id)
        
    stmt = stmt.order_by(PredictionRecord.created_at.desc())
    res = await db.execute(stmt)
    records = res.scalars().all()

    items = []
    for r in records:
        items.append({
            "id": r.id,
            "item_name": r.item_name,
            "image_path": f"/uploads/{r.image_path}",
            "temperature": r.temperature,
            "humidity": r.humidity,
            "environment": r.environment,
            "days_remaining": r.days_remaining,
            "created_at": r.created_at.isoformat()
        })

    return {
        "items": items,
        "total": len(items)
    }

@router.delete("/history/{id}")
async def delete_history(
    id: str,
    current_user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deletes a specific prediction record and its associated image file."""
    # Find the record
    stmt = select(PredictionRecord).where(PredictionRecord.id == id)
    res = await db.execute(stmt)
    record = res.scalars().first()

    if not record:
        raise HTTPException(status_code=404, detail="Prediction record not found")

    # Authorize deletion
    if settings.REQUIRE_AUTH and current_user:
        if record.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this record")

    # Delete the image file if it exists
    if record.image_path:
        file_path = Path(settings.UPLOAD_DIR) / record.image_path
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info("Successfully deleted image file: %s", file_path)
        except Exception as e:
            logger.error("Failed to delete physical image file: %s", e)

    # Delete DB row
    await db.execute(delete(PredictionRecord).where(PredictionRecord.id == id))
    await db.commit()
    logger.info("Deleted prediction record ID: %s", id)

    return {"status": "ok", "message": "Prediction deleted successfully"}

@router.get("/stats")
async def get_stats(
    current_user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generates dashboard analytical metrics from prediction records."""
    # Build filter conditions
    stmt_base = select(PredictionRecord)
    if settings.REQUIRE_AUTH and current_user:
        stmt_base = stmt_base.where(PredictionRecord.user_id == current_user.id)

    # Exec total count
    stmt_total = select(func.count()).select_from(stmt_base.subquery())
    total_res = await db.execute(stmt_total)
    total_count = total_res.scalar() or 0

    if total_count == 0:
        return {
            "total_items": 0,
            "average_shelf_life": 0.0,
            "environment_distribution": {"ambient": 0, "controlled": 0},
            "status_counts": {"fresh": 0, "warning": 0, "expired": 0}
        }

    # Fetch all matching items to compute averages/distributions
    res = await db.execute(stmt_base)
    records = res.scalars().all()

    total_days = sum(r.days_remaining for r in records)
    avg_days = round(total_days / total_count, 2)

    ambient_count = sum(1 for r in records if r.environment == "ambient")
    controlled_count = sum(1 for r in records if r.environment == "controlled")

    # Status splits: Fresh (>5), Warning (2-5), Expired (<2)
    fresh_count = sum(1 for r in records if r.days_remaining > 5.0)
    warning_count = sum(1 for r in records if 2.0 <= r.days_remaining <= 5.0)
    expired_count = sum(1 for r in records if r.days_remaining < 2.0)

    return {
        "total_items": total_count,
        "average_shelf_life": avg_days,
        "environment_distribution": {
            "ambient": ambient_count,
            "controlled": controlled_count
        },
        "status_counts": {
            "fresh": fresh_count,
            "warning": warning_count,
            "expired": expired_count
        }
    }
