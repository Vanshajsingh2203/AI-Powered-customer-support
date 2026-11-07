import pytest
from app.models.notification import Notification


async def add_notification(db_session, user_id, title="Test notification"):
    notification = Notification(
        user_id=user_id,
        title=title,
        message="A test notification message.",
        notification_type="TICKET_CREATED",
        is_read=False,
    )
    db_session.add(notification)
    await db_session.flush()
    return notification


@pytest.mark.asyncio
async def test_user_can_list_and_count_unread_notifications(
    client, user_factory, auth_headers, db_session
):
    user = await user_factory()
    await add_notification(db_session, user.id)
    await add_notification(db_session, user.id, "Second notification")

    headers = auth_headers(user)
    listing = await client.get("/api/v1/notifications/", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 2

    count = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count.status_code == 200
    assert count.json()["unread_count"] == 2


@pytest.mark.asyncio
async def test_user_can_mark_notification_as_read(
    client, user_factory, auth_headers, db_session
):
    user = await user_factory()
    notification = await add_notification(db_session, user.id)

    response = await client.patch(
        f"/api/v1/notifications/{notification.id}/read",
        headers=auth_headers(user),
    )
    assert response.status_code == 200, response.text
    assert response.json()["is_read"] is True

    count = await client.get(
        "/api/v1/notifications/unread-count",
        headers=auth_headers(user),
    )
    assert count.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_user_can_mark_all_notifications_as_read(
    client, user_factory, auth_headers, db_session
):
    user = await user_factory()
    await add_notification(db_session, user.id)
    await add_notification(db_session, user.id, "Another notification")

    response = await client.patch(
        "/api/v1/notifications/read-all",
        headers=auth_headers(user),
    )
    assert response.status_code == 200
    assert response.json()["updated_count"] == 2


@pytest.mark.asyncio
async def test_user_cannot_mark_another_users_notification_as_read(
    client, user_factory, auth_headers, db_session
):
    owner = await user_factory()
    other = await user_factory()
    notification = await add_notification(db_session, owner.id)

    response = await client.patch(
        f"/api/v1/notifications/{notification.id}/read",
        headers=auth_headers(other),
    )
    assert response.status_code == 404
