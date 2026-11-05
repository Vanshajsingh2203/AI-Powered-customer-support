
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationService:

    async def create_notification(
        self,
        db: AsyncSession,
        user_id: UUID,
        ticket_id: UUID | None,
        title: str,
        message: str,
        notification_type: str,
    ) -> Notification:

        notification = Notification(
            user_id=user_id,
            ticket_id=ticket_id,
            title=title,
            message=message,
            notification_type=notification_type,
            is_read=False,
        )

        db.add(notification)

        await db.flush()

        return notification


notification_service = NotificationService()
