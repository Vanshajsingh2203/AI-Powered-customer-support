from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings

# Create asynchronous database engine

engine = create_async_engine(
    settings.DATABASE_URL,
    echo = settings.DEBUG,
    pool_pre_ping = True
)

# Create a factory for database sessions

AsyncSessionLocal = async_sessionmaker(
    bind = engine,
    class_ = AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session