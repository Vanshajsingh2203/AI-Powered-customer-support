from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, status, HTTPException
from app.models.user import User
from app.services.admin_service import admin_service
from app.schemas.admin import AgentCreate, AgentResponse, AgentStatusUpdate
from app.schemas.auth import UserResponse
from app.database.session import get_db
from app.core.permissions import require_roles
from app.services.admin_service import admin_service
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category_service import category_service

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
    
@router.get('/agents')
async def get_agents(db:AsyncSession = Depends(get_db), current_user = Depends(require_roles("ADMIN"))):
    result = await admin_service.get_agents(db)
    
    return result

@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent_by_id(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN"))
):
    agent = await admin_service.get_agent_by_id(
        db=db,
        agent_id=agent_id
    )

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    return agent

@router.patch('/agents/{agent_id}/status', response_model=AgentResponse)
async def update_agent_status(
    agent_id: UUID,
    status_data: AgentStatusUpdate,
    db:AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN"))
):
    agent = await admin_service.update_user_status(db, agent_id, role = "AGENT",is_active=status_data.is_active)
    
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
        
    await db.commit()
    await db.refresh(agent)
    
    return agent

@router.get("/customers", response_model=list[UserResponse])
async def get_customers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN"))
):
    return await admin_service.get_customers(db=db)

@router.get("/customers/{customer_id}", response_model=UserResponse)
async def get_customer_by_id(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN"))
):
    customer = await admin_service.get_customer_by_id(
        db=db,
        customer_id=customer_id
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    return customer

@router.patch(
    "/customers/{customer_id}/status",
    response_model=UserResponse
)
async def update_customer_status(
    customer_id: UUID,
    status_data: AgentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN"))
):
    customer = await admin_service.update_user_status(
        db=db,
        user_id=customer_id,
        role="CUSTOMER",
        is_active=status_data.is_active
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    await db.commit()
    await db.refresh(customer)

    return customer

@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN"))
):
    try:
        category = await category_service.create_category(
            db=db,
            category_data=category_data
        )

        await db.commit()
        await db.refresh(category)

        return category

    except ValueError as exc:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc)
        )

    except Exception:
        await db.rollback()
        raise
    
@router.get(
    "/categories",
    response_model=list[CategoryResponse]
)
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN"))
):
    return await category_service.get_categories(db=db)

@router.get(
    "/categories/{category_id}",
    response_model=CategoryResponse
)
async def get_category_by_id(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN"))
):
    category = await category_service.get_category_by_id(
        db=db,
        category_id=category_id
    )

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    return category

@router.patch(
    "/categories/{category_id}",
    response_model=CategoryResponse
)
async def update_category(
    category_id: UUID,
    category_data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN"))
):
    try:
        category = await category_service.update_category(
            db=db,
            category_id=category_id,
            category_data=category_data
        )

        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        await db.commit()
        await db.refresh(category)

        return category

    except ValueError as exc:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )

    except Exception:
        await db.rollback()
        raise
    
@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN"))
):
    try:
        result = await category_service.delete_category(
            db=db,
            category_id=category_id
        )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        await db.commit()

        return {"message": "Category deleted successfully"}

    except ValueError as exc:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc)
        )

    except Exception:
        await db.rollback()
        raise