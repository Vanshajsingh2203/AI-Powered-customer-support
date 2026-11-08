from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.config import settings
from app.database.session import get_db

from app.api.v1.router import api_router

app = FastAPI(title = "Customer Support AI",
              description="AI powered customer support and ticket management system",
              version= "1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

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
    
app.include_router(
    api_router,
    prefix="/api/v1",
)
