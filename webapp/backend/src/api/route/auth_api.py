import datetime
import bcrypt
import jwt
import logging
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.config import settings
from database import get_db
from database.models import User
from api.middleware.auth_guard import get_current_user
from api.scheme import UserRegisterSchema, UserLoginSchema

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

def generate_jwt_token(user_id: str) -> str:
    """Generates an HS256 JWT token for the user session."""
    payload = {
        "sub": user_id,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

@router.post("/register")
async def register(payload: UserRegisterSchema, db: AsyncSession = Depends(get_db)):
    """Registers a new user account with hashed password."""
    # Check if user already exists
    stmt = select(User).where(User.email == payload.email)
    res = await db.execute(stmt)
    if res.scalars().first():
        raise HTTPException(status_code=400, detail="Account with this email already exists")

    # Hash password
    salt = bcrypt.gensalt()
    pwd_hash = bcrypt.hashpw(payload.password.encode("utf-8"), salt).decode("utf-8")

    user = User(email=payload.email, password_hash=pwd_hash)
    db.add(user)
    await db.commit()
    logger.info("New user registered: %s", payload.email)
    return {"status": "ok", "message": "User registered successfully"}

@router.post("/login")
async def login(payload: UserLoginSchema, response: Response, db: AsyncSession = Depends(get_db)):
    """Logs in a user, returning user details and setting an httpOnly cookie."""
    stmt = select(User).where(User.email == payload.email)
    res = await db.execute(stmt)
    user = res.scalars().first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Verify password
    is_valid = bcrypt.checkpw(payload.password.encode("utf-8"), user.password_hash.encode("utf-8"))
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    token = generate_jwt_token(user.id)

    # Set httpOnly cookie (ArchonFlow style)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False,  # Set to True in HTTPS production environments
    )

    logger.info("User logged in: %s", user.email)
    return {
        "logged_in": True,
        "user_id": user.id,
        "email": user.email
    }

@router.post("/logout")
async def logout(response: Response):
    """Logs out user by clearing session cookies."""
    response.delete_cookie("access_token")
    return {"status": "ok", "message": "Logged out successfully"}

@router.get("/me")
async def me(current_user: User | None = Depends(get_current_user)):
    """Returns details of the currently authenticated user session."""
    if not settings.REQUIRE_AUTH:
        return {
            "logged_in": True,
            "user_id": "anonymous-demo-id",
            "email": "anonymous@shelf-life.internal"
        }
        
    if current_user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    return {
        "logged_in": True,
        "user_id": current_user.id,
        "email": current_user.email
    }

@router.get("/config")
async def get_config():
    """Returns system parameters configuration, such as toggleable auth state."""
    return {
        "require_auth": settings.REQUIRE_AUTH
    }
