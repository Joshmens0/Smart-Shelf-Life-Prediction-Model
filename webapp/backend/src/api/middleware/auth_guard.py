import jwt
import logging
from fastapi import Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.config import settings
from database import get_db
from database.models import User

logger = logging.getLogger(__name__)

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User | None:
    """FastAPI Dependency that extracts the authenticated user.
    
    Checks 'Authorization: Bearer <token>' header first, falling back to the 
    'access_token' cookie. If settings.REQUIRE_AUTH is False, it returns None 
    as a mock/anonymous session wrapper.
    """
    # 1. Bypassed globally
    if not settings.REQUIRE_AUTH:
        return None

    # 2. Dual token extraction (Header -> Cookie)
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    else:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=401, 
            detail="Authentication credentials missing (Bearer header or access_token cookie required)"
        )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token claims payload")
        
        # Safe SQLAlchemy selection query format (.is_)
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=401, detail="User session not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token signature expired")
    except jwt.PyJWTError as jwt_err:
        logger.warning("JWT verification failed: %s", jwt_err)
        raise HTTPException(status_code=401, detail="Invalid or corrupt session token")
