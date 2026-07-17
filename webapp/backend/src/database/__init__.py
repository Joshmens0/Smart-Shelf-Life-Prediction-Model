import logging
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from .models import Base

logger = logging.getLogger(__name__)

# Singletons initialized via init_engine
engine = None
async_session_factory = None

def init_engine(database_url: str, echo: bool = False):
    """Initializes the database connection engine and session factory."""
    global engine, async_session_factory

    connect_args = {}
    if "sqlite" in database_url:
        connect_args["check_same_thread"] = False

    engine = create_async_engine(
        database_url,
        connect_args=connect_args,
        echo=echo,
    )

    async_session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    logger.info("Database engine initialized successfully.")

async def get_db():
    """Dependency that yields an active database session and closes it in finally block."""
    if async_session_factory is None:
        raise ValueError("Database engine has not been initialized. Call init_engine first.")
        
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

async def create_tables():
    """Initializes the database schema by auto-creating missing tables (DEV_MODE)."""
    if engine is None:
        raise ValueError("Database engine is not initialized.")
        
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema auto-created.")
