import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

# Add backend directory to Python's import path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Configure Windows event loop before creating async connections
if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )

from app.database.session import engine


async def test_connection():
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            print("Database result:", result.scalar())

    finally:
        await engine.dispose()


asyncio.run(test_connection())