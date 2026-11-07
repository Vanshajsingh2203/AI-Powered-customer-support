
import pytest_asyncio
import asyncio

if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )
from httpx import ASGITransport, AsyncClient

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.main import app as fastapi_app
from app.config import settings
from app.database.base import Base
from app.database.session import get_db

# Import all models so SQLAlchemy knows about every table.
import app.models


# Make sure tests have their own database.
if not settings.TEST_DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL is missing from backend/.env"
    )


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    # Create all tables before the test.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Remove tables and close the engine after the test.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    async with test_engine.connect() as connection:

        # Start an outer transaction.
        outer_transaction = await connection.begin()

        # Create a session that uses savepoints.
        TestingSessionLocal = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            join_transaction_mode="create_savepoint",
        )

        async with TestingSessionLocal() as session:
            yield session

        # Undo everything performed during the test,
        # including changes committed by API endpoints.
        await outer_transaction.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=fastapi_app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as test_client:
        yield test_client

    fastapi_app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Reusable test helpers
# ---------------------------------------------------------------------------
import pytest
from app.models.user import User
from app.core.security import hash_password, create_access_token


@pytest_asyncio.fixture
async def user_factory(db_session):
    """Create users with CUSTOMER, AGENT, or ADMIN roles directly in the test DB."""
    async def make_user(
        role="CUSTOMER",
        email=None,
        full_name=None,
        is_active=True,
        password="StrongPassword123",
    ):
        import uuid

        unique = uuid.uuid4().hex[:10]
        user = User(
            full_name=full_name or f"Test {role.title()}",
            email=email or f"{role.lower()}-{unique}@example.com",
            password_hash=hash_password(password),
            role=role,
            is_active=is_active,
        )
        db_session.add(user)
        await db_session.flush()
        return user

    return make_user


@pytest.fixture
def auth_headers():
    """Build a Bearer header for a persisted test user."""
    def make_headers(user):
        token = create_access_token(str(user.id), user.role)
        return {"Authorization": f"Bearer {token}"}
    return make_headers


@pytest_asyncio.fixture
async def ticket_factory(client, user_factory, auth_headers):
    """Create a ticket through the public API as a customer."""
    async def make_ticket(customer=None, category_id=None, title="Test support ticket"):
        customer = customer or await user_factory(role="CUSTOMER")
        payload = {
            "title": title,
            "description": "This is a sufficiently detailed test ticket description.",
        }
        if category_id is not None:
            payload["category_id"] = str(category_id)
        response = await client.post(
            "/api/v1/tickets/",
            json=payload,
            headers=auth_headers(customer),
        )
        assert response.status_code == 201, response.text
        return customer, response.json()

    return make_ticket
