
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.category import CategoryResponse
from app.services.category_service import category_service

router = APIRouter()


@router.get("/", response_model=list[CategoryResponse])
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve available ticket categories.

    Any authenticated user can view categories.
    Only admins can create, update, or delete categories.
    """
    return await category_service.get_categories(db=db)
