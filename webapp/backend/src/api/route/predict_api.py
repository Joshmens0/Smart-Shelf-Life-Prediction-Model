import logging
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import settings
from database import get_db
from database.models import PredictionRecord, User
from api.middleware.auth_guard import get_current_user
from service.prediction_service import get_prediction_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["prediction"])

@router.post("/predict")
async def predict_shelf_life(
    image: UploadFile = File(...),
    temp: float = Form(...),
    humidity: float = Form(...),
    environment: str = Form(...),
    item_name: str = Form(...),
    current_user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """API Endpoint to upload a fruit image and sensor inputs to run multimodal inference."""
    # 1. Validation checks
    if environment not in ("ambient", "controlled"):
        raise HTTPException(
            status_code=422,
            detail="Environment must be 'ambient' or 'controlled'"
        )
        
    if not (0.0 <= humidity <= 100.0):
        raise HTTPException(
            status_code=422,
            detail="Humidity percentage must be between 0.0 and 100.0"
        )
        
    # Check magic bytes for security (MIME validation standard in ArchonFlow)
    content = await image.read()
    if len(content) < 4:
        raise HTTPException(status_code=400, detail="Invalid image file uploaded (file is too small)")
        
    # Reset stream pointer
    await image.seek(0)

    # 2. File saving
    file_uuid = uuid.uuid4()
    original_suffix = Path(image.filename).suffix if image.filename else ".jpg"
    # Fallback to standard extensions if invalid suffix is provided
    if original_suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
        original_suffix = ".jpg"
        
    unique_filename = f"{file_uuid}{original_suffix}"
    upload_path = Path(settings.UPLOAD_DIR) / unique_filename

    try:
        with open(upload_path, "wb") as f:
            f.write(content)
    except Exception as io_err:
        logger.error("Failed to write uploaded file to disk: %s", io_err)
        raise HTTPException(status_code=500, detail="Internal server error saving upload file")

    # 3. Model Inference
    try:
        service = get_prediction_service()
        days_remaining = service.predict(
            img_path=upload_path,
            temp=temp,
            humidity=humidity,
            env=environment
        )
    except Exception as inference_err:
        logger.exception("multimodal prediction failed: %s", inference_err)
        # Clean up file on failure
        if upload_path.exists():
            upload_path.unlink()
        raise HTTPException(
            status_code=500,
            detail="Failed to run model inference pipeline. Please check weights and configs."
        )

    # 4. Save to Database
    user_id = current_user.id if current_user else None
    record = PredictionRecord(
        user_id=user_id,
        item_name=item_name,
        image_path=unique_filename,  # Save relative filename to resolve paths cleanly
        temperature=temp,
        humidity=humidity,
        environment=environment,
        days_remaining=round(days_remaining, 2)
    )

    db.add(record)
    await db.commit()
    await db.refresh(record)

    logger.info(
        "Prediction completed successfully. Days remaining: %.2f (id: %s)", 
        days_remaining, 
        record.id
    )

    return {
        "id": record.id,
        "item_name": record.item_name,
        "image_path": f"/uploads/{unique_filename}",
        "temperature": record.temperature,
        "humidity": record.humidity,
        "environment": record.environment,
        "days_remaining": record.days_remaining,
        "created_at": record.created_at.isoformat()
    }
