
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.user import User

from app.services.notification_service import notification_service

from app.schemas.notification import (
    NotificationResponse,
    UnreadCountResponse,
    MarkAllReadResponse,
)


router = APIRouter(tags=["Notifications"])


# 1. Get all notifications belonging to the current user
@router.get(
    "/",
    response_model=list[NotificationResponse],
)
async def get_my_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    notifications = await notification_service.get_user_notifications(
        db=db,
        user_id=current_user.id,
    )

    return notifications


# 2. Get unread notification count
@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
)
async def get_unread_notification_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    unread_count = await notification_service.get_unread_count(
        db=db,
        user_id=current_user.id,
    )

    return {
        "unread_count": unread_count
    }


# 3. Mark one notification as read
@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
async def mark_notification_as_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    notification = await notification_service.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
    )

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    await db.commit()
    await db.refresh(notification)

    return notification


# 4. Mark all notifications as read
@router.patch(
    "/read-all",
    response_model=MarkAllReadResponse,
)
async def mark_all_notifications_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    updated_count = await notification_service.mark_all_as_read(
        db=db,
        user_id=current_user.id,
    )

    await db.commit()

    return {
        "message": "All notifications marked as read",
        "updated_count": updated_count,
    }
