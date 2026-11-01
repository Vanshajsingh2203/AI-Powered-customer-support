from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.config import settings
from app.database.session import get_db


app = FastAPI(title = "Customer Support AI",
              description="AI powered customer support and ticket management system",
              version= "1.0.0")

@app.get('/health')
def health_check():
    return {
        "status": "healthy",
        "message": "Customer support API is running"
    }
    
@app.get('/db_check')
async def database_check(db : AsyncSession = Depends(get_db)):
    result = await db.execute(text('SELECT 1'))
    
    return {
        "database": "connected",
        "result": result.scalar_one()
    }