
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.user import User
from app.core.permissions import require_roles
from app.services.analytics_service import analytics_service
from app.schemas.analytics import AnalyticsOverviewResponse


router = APIRouter()


@router.get(
    "/overview",
    response_model=AnalyticsOverviewResponse,
)
async def get_analytics_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    return await analytics_service.get_overview(db=db)
