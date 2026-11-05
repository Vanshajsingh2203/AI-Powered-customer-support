from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, status, HTTPException
from app.models.user import User
from app.services.admin_service import admin_service
from app.schemas.admin import AgentCreate, AgentResponse

from app.database.session import get_db
from app.core.permissions import require_roles
from app.services.admin_service import admin_service

router = APIRouter()

@router.post('/agents', response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate, 
    db:AsyncSession = Depends(get_db),
    current_user:User =  Depends(require_roles("ADMIN"))
):
    try:
        agent = await admin_service.create_agent(db, agent_data)
        
        await db.commit()
        await db.refresh(agent)
        
        return agent
    
    except ValueError as exc:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    except Exception:
        await db.rollback()
        raise