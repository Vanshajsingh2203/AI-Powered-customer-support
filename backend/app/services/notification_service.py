
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationService:

    # 1. Create a notification
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

    # 2. Retrieve all notifications belonging to a user
    async def get_user_notifications(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> list[Notification]:

        result = await db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )

        return list(result.scalars().all())

    # 3. Get unread notification count
    async def get_unread_count(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> int:

        result = await db.execute(
            select(func.count(Notification.id))
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )

        return result.scalar_one()

    # 4. Mark one notification as read
    async def mark_as_read(
        self,
        db: AsyncSession,
        notification_id: UUID,
        user_id: UUID,
    ) -> Notification | None:

        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )

        notification = result.scalar_one_or_none()

        if notification is None:
            return None

        # Avoid changing read_at if it was already read
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)

            await db.flush()

        return notification

    # 5. Mark all unread notifications as read
    async def mark_all_as_read(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> int:

        current_time = datetime.now(timezone.utc)

        result = await db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(
                is_read=True,
                read_at=current_time,
            )
            .execution_options(synchronize_session=False)
        )

        return result.rowcount or 0


notification_service = NotificationService()
