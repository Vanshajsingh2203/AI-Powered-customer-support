from fastapi import APIRouter

from app.api.v1.endpoints import auth
from app.api.v1.endpoints import tickets
from app.api.v1.endpoints import messages
from app.api.v1.endpoints import agents
from app.api.v1.endpoints import attachments
from app.api.v1.endpoints import admin
from app.api.v1.endpoints import analytics

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix='/auth',
    tags = ['Authentication'],
)

api_router.include_router(
    tickets.router,
    prefix="/tickets",
    tags=["Tickets"],
)

api_router.include_router(
    messages.router,
    prefix="/tickets",
    tags=["Messages"],
)

api_router.include_router(
    agents.router,
    prefix="/agents",
    tags=["Agents"],
)

api_router.include_router(
    attachments.router,
    tags=["Attachments"]
)

from app.api.v1.endpoints import notifications

api_router.include_router(
    notifications.router,
    prefix="/notifications",
)

api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin"],
)

api_router.include_router(
    analytics.router,
    prefix="/admin/analytics",
    tags=["Admin Analytics"],
)