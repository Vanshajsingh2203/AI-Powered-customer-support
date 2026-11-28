import pytest


@pytest.mark.asyncio
async def test_customer_can_create_and_list_own_tickets(client, user_factory, auth_headers):
    customer = await user_factory()
    headers = auth_headers(customer)

    created = await client.post("/api/v1/tickets/", headers=headers, json={
        "title": "Cannot access account",
        "description": "I cannot sign in to my account after resetting my password.",
    })
    assert created.status_code == 201, created.text
    ticket = created.json()
    assert ticket["title"] == "Cannot access account"
    assert ticket["status"] == "OPEN"
    assert ticket["priority"] == "MEDIUM"

    listed = await client.get("/api/v1/tickets/", headers=headers)
    assert listed.status_code == 200, listed.text
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == ticket["id"]


@pytest.mark.asyncio
async def test_customer_can_retrieve_and_update_own_ticket(client, ticket_factory, auth_headers):
    customer, ticket = await ticket_factory()
    headers = auth_headers(customer)

    retrieved = await client.get(f"/api/v1/tickets/{ticket['id']}", headers=headers)
    assert retrieved.status_code == 200, retrieved.text

    updated = await client.patch(
        f"/api/v1/tickets/{ticket['id']}",
        headers=headers,
        json={"title": "Updated support ticket title"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["title"] == "Updated support ticket title"


@pytest.mark.asyncio
async def test_ticket_creation_rejects_invalid_category(client, user_factory, auth_headers):
    customer = await user_factory()
    response = await client.post("/api/v1/tickets/", headers=auth_headers(customer), json={
        "title": "Invalid category ticket",
        "description": "This ticket references a category that does not exist.",
        "category_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ticket_list_pagination(client, user_factory, auth_headers):
    customer = await user_factory()
    headers = auth_headers(customer)
    for number in range(3):
        response = await client.post("/api/v1/tickets/", headers=headers, json={
            "title": f"Pagination ticket {number}",
            "description": "A valid description for pagination test tickets.",
        })
        assert response.status_code == 201

    page = await client.get("/api/v1/tickets/?page=1&limit=2", headers=headers)
    assert page.status_code == 200
    data = page.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["total_pages"] == 2



@pytest.mark.asyncio
async def test_ticket_creation_with_ai_classification(
    client, user_factory, auth_headers, db_session
):
    """Ticket creation with AI classification should map category and set priority."""
    from app.services.category_service import category_service
    from app.schemas.category import CategoryCreate
    from unittest.mock import patch, AsyncMock
    from app.schemas.ai.classification import TicketClassification

    customer = await user_factory(role="CUSTOMER")
    headers = auth_headers(customer)

    cat_billing = await category_service.create_category(
        db_session, CategoryCreate(name="Billing", description="Billing issues")
    )
    await category_service.create_category(
        db_session, CategoryCreate(name="Technical", description="Technical issues")
    )
    await db_session.flush()

    expected_classification = TicketClassification(
        category="Billing",
        priority="HIGH",
        sentiment="FRUSTRATED",
        confidence=0.85,
        reasoning="Customer reports duplicate charges.",
    )

    with patch(
        "app.services.ticket_service.classify_ticket",
        new_callable=AsyncMock,
    ) as mock_classify:
        mock_classify.return_value = expected_classification

        response = await client.post(
            "/api/v1/tickets/",
            headers=headers,
            json={
                "title": "Duplicate charge on my account",
                "description": "I was charged twice for the same subscription.",
            },
        )

    assert response.status_code == 201, response.text
    ticket = response.json()
    assert ticket["category_id"] == str(cat_billing.id)
    assert ticket["priority"] == "HIGH"

    mock_classify.assert_called_once()
    call_kwargs = mock_classify.call_args[1]
    assert "available_categories" in call_kwargs
    assert "Billing" in call_kwargs["available_categories"]
    assert "Technical" in call_kwargs["available_categories"]


@pytest.mark.asyncio
async def test_ticket_creation_ai_failure_does_not_block_ticket(
    client, user_factory, auth_headers, db_session
):
    """AI classification failure must not prevent ticket creation."""
    from app.services.category_service import category_service
    from app.schemas.category import CategoryCreate
    from unittest.mock import patch, AsyncMock

    customer = await user_factory(role="CUSTOMER")
    headers = auth_headers(customer)

    await category_service.create_category(
        db_session, CategoryCreate(name="Billing", description="Billing issues")
    )
    await db_session.flush()

    with patch(
        "app.services.ticket_service.classify_ticket",
        new_callable=AsyncMock,
    ) as mock_classify:
        mock_classify.side_effect = RuntimeError("AI model invocation failed")

        response = await client.post(
            "/api/v1/tickets/",
            headers=headers,
            json={
                "title": "Cannot access account",
                "description": "I cannot sign in to my account.",
            },
        )

    assert response.status_code == 201, response.text
    ticket = response.json()
    assert ticket["status"] == "OPEN"
    assert ticket["priority"] == "MEDIUM"
    assert ticket["category_id"] is None


@pytest.mark.asyncio
async def test_ticket_creation_ai_returns_unknown_category(
    client, user_factory, auth_headers, db_session
):
    """AI returning a category not in the permitted list must not corrupt ticket creation."""
    from app.services.category_service import category_service
    from app.schemas.category import CategoryCreate
    from unittest.mock import patch, AsyncMock
    from app.schemas.ai.classification import TicketClassification

    customer = await user_factory(role="CUSTOMER")
    headers = auth_headers(customer)

    await category_service.create_category(
        db_session, CategoryCreate(name="Billing", description="Billing issues")
    )
    await db_session.flush()

    expected_classification = TicketClassification(
        category="NonExistentCategory",
        priority="MEDIUM",
        sentiment="NEUTRAL",
        confidence=0.5,
        reasoning="Test",
    )

    with patch(
        "app.services.ticket_service.classify_ticket",
        new_callable=AsyncMock,
    ) as mock_classify:
        mock_classify.return_value = expected_classification

        response = await client.post(
            "/api/v1/tickets/",
            headers=headers,
            json={
                "title": "Test ticket",
                "description": "Test description",
            },
        )

    assert response.status_code == 201, response.text
    ticket = response.json()
    assert ticket["priority"] == "MEDIUM"
    assert ticket["category_id"] is None


@pytest.mark.asyncio
async def test_ticket_creation_ai_no_categories_available(
    client, user_factory, auth_headers
):
    """When no categories exist in the DB, AI is skipped and ticket uses defaults."""
    customer = await user_factory(role="CUSTOMER")
    headers = auth_headers(customer)

    response = await client.post(
        "/api/v1/tickets/",
        headers=headers,
        json={
            "title": "No categories ticket",
            "description": "There are no categories configured.",
        },
    )

    assert response.status_code == 201, response.text
    ticket = response.json()
    assert ticket["priority"] == "MEDIUM"
    assert ticket["category_id"] is None


@pytest.mark.asyncio
async def test_ticket_creation_ai_category_case_insensitive_mapping(
    client, user_factory, auth_headers, db_session
):
    """AI category name is matched case-insensitively to the DB record."""
    from app.services.category_service import category_service
    from app.schemas.category import CategoryCreate
    from unittest.mock import patch, AsyncMock
    from app.schemas.ai.classification import TicketClassification

    customer = await user_factory(role="CUSTOMER")
    headers = auth_headers(customer)

    cat = await category_service.create_category(
        db_session, CategoryCreate(name="Technical Support", description="Tech help")
    )
    await db_session.flush()

    expected_classification = TicketClassification(
        category="technical support",
        priority="URGENT",
        sentiment="NEGATIVE",
        confidence=0.9,
        reasoning="Server is down.",
    )

    with patch(
        "app.services.ticket_service.classify_ticket",
        new_callable=AsyncMock,
    ) as mock_classify:
        mock_classify.return_value = expected_classification

        response = await client.post(
            "/api/v1/tickets/",
            headers=headers,
            json={
                "title": "Server down",
                "description": "The production server is not responding.",
            },
        )

    assert response.status_code == 201, response.text
    ticket = response.json()
    assert ticket["category_id"] == str(cat.id)
    assert ticket["priority"] == "URGENT"


@pytest.mark.asyncio
async def test_ticket_creation_ai_persists_classification_record(
    client, user_factory, auth_headers, db_session
):
    """AI classification creates ticket and TicketAIClassification record."""
    from app.services.category_service import category_service
    from app.schemas.category import CategoryCreate
    from unittest.mock import patch, AsyncMock
    from app.schemas.ai.classification import TicketClassification
    from app.models.ticket_ai_classification import TicketAIClassification
    from sqlalchemy import select

    customer = await user_factory(role="CUSTOMER")
    headers = auth_headers(customer)

    await category_service.create_category(
        db_session, CategoryCreate(name="Billing", description="Billing issues")
    )
    await category_service.create_category(
        db_session, CategoryCreate(name="Technical", description="Technical issues")
    )
    await db_session.flush()

    expected_classification = TicketClassification(
        category="Billing",
        priority="HIGH",
        sentiment="FRUSTRATED",
        confidence=0.85,
        reasoning="Customer reports duplicate charges.",
    )

    with patch(
        "app.services.ticket_service.classify_ticket",
        new_callable=AsyncMock,
    ) as mock_classify:
        mock_classify.return_value = expected_classification

        response = await client.post(
            "/api/v1/tickets/",
            headers=headers,
            json={
                "title": "Duplicate charge on my account",
                "description": "I was charged twice for the same subscription.",
            },
        )

    assert response.status_code == 201, response.text
    ticket = response.json()
    assert ticket["category_id"] is not None
    assert ticket["priority"] == "HIGH"

    # Verify classification record was persisted.
    result = await db_session.execute(
        select(TicketAIClassification).where(
            TicketAIClassification.ticket_id == ticket["id"]
        )
    )
    ai_classification = result.scalar_one_or_none()
    assert ai_classification is not None
    assert ai_classification.sentiment == "FRUSTRATED"
    assert ai_classification.confidence == 0.85
    assert ai_classification.reasoning == "Customer reports duplicate charges."
    assert ai_classification.created_at is not None


@pytest.mark.asyncio
async def test_ticket_creation_ai_failure_no_classification_record(
    client, user_factory, auth_headers, db_session
):
    """AI failure does not prevent ticket creation and creates no classification record."""
    from app.services.category_service import category_service
    from app.schemas.category import CategoryCreate
    from unittest.mock import patch, AsyncMock
    from app.models.ticket_ai_classification import TicketAIClassification
    from sqlalchemy import select

    customer = await user_factory(role="CUSTOMER")
    headers = auth_headers(customer)

    await category_service.create_category(
        db_session, CategoryCreate(name="Billing", description="Billing issues")
    )
    await db_session.flush()

    with patch(
        "app.services.ticket_service.classify_ticket",
        new_callable=AsyncMock,
    ) as mock_classify:
        mock_classify.side_effect = RuntimeError("AI model invocation failed")

        response = await client.post(
            "/api/v1/tickets/",
            headers=headers,
            json={
                "title": "Cannot access account",
                "description": "I cannot sign in to my account.",
            },
        )

    assert response.status_code == 201, response.text
    ticket = response.json()
    assert ticket["status"] == "OPEN"
    assert ticket["priority"] == "MEDIUM"
    assert ticket["category_id"] is None

    # No classification record.
    result = await db_session.execute(
        select(TicketAIClassification).where(
            TicketAIClassification.ticket_id == ticket["id"]
        )
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_ticket_creation_ai_then_auto_assignment_still_works(
    client, user_factory, auth_headers, db_session
):
    """Automatic assignment still works after AI classification."""
    from app.services.category_service import category_service
    from app.schemas.category import CategoryCreate
    from unittest.mock import patch, AsyncMock
    from app.schemas.ai.classification import TicketClassification
    from app.models.user import User
    from app.core.security import hash_password

    customer = await user_factory(role="CUSTOMER")
    headers = auth_headers(customer)

    # Create an active agent.
    agent = User(
        full_name="Test Agent",
        email="agent-test@example.com",
        password_hash=hash_password("StrongPassword123"),
        role="AGENT",
        is_active=True,
    )
    db_session.add(agent)
    await db_session.flush()

    await category_service.create_category(
        db_session, CategoryCreate(name="Billing", description="Billing issues")
    )
    await db_session.flush()

    expected_classification = TicketClassification(
        category="Billing",
        priority="HIGH",
        sentiment="FRUSTRATED",
        confidence=0.85,
        reasoning="Customer reports duplicate charges.",
    )

    with patch(
        "app.services.ticket_service.classify_ticket",
        new_callable=AsyncMock,
    ) as mock_classify:
        mock_classify.return_value = expected_classification

        response = await client.post(
            "/api/v1/tickets/",
            headers=headers,
            json={
                "title": "Duplicate charge on my account",
                "description": "I was charged twice for the same subscription.",
            },
        )

    assert response.status_code == 201, response.text
    ticket = response.json()
    assert ticket["category_id"] is not None
    assert ticket["priority"] == "HIGH"
    # Auto-assignment should have assigned the ticket to the agent.
    assert ticket["assigned_agent_id"] == str(agent.id)
    assert ticket["assignment_source"] == "AUTO"


@pytest.mark.asyncio
async def test_ticket_has_at_most_one_classification_record(
    client, user_factory, auth_headers, db_session
):
    """One-to-one relationship: a ticket has at most one classification record."""
    from app.services.category_service import category_service
    from app.schemas.category import CategoryCreate
    from unittest.mock import patch, AsyncMock
    from app.schemas.ai.classification import TicketClassification
    from app.models.ticket_ai_classification import TicketAIClassification
    from sqlalchemy import select

    customer = await user_factory(role="CUSTOMER")
    headers = auth_headers(customer)

    await category_service.create_category(
        db_session, CategoryCreate(name="Billing", description="Billing issues")
    )
    await db_session.flush()

    expected_classification = TicketClassification(
        category="Billing",
        priority="HIGH",
        sentiment="FRUSTRATED",
        confidence=0.85,
        reasoning="Customer reports duplicate charges.",
    )

    with patch(
        "app.services.ticket_service.classify_ticket",
        new_callable=AsyncMock,
    ) as mock_classify:
        mock_classify.return_value = expected_classification

        response = await client.post(
            "/api/v1/tickets/",
            headers=headers,
            json={
                "title": "Duplicate charge on my account",
                "description": "I was charged twice for the same subscription.",
            },
        )

    assert response.status_code == 201, response.text
    ticket = response.json()

    # Query classification records for this ticket.
    result = await db_session.execute(
        select(TicketAIClassification).where(
            TicketAIClassification.ticket_id == ticket["id"]
        )
    )
    records = result.scalars().all()
    assert len(records) == 1
    assert records[0].sentiment == "FRUSTRATED"
    assert records[0].confidence == 0.85
    assert records[0].reasoning == "Customer reports duplicate charges."
@pytest.mark.asyncio
async def test_ticket_creation_customer_category_skips_ai_no_classification_record(
    client, user_factory, auth_headers, db_session
):
    """Customer-provided category skips AI and creates no classification record."""
    from app.services.category_service import category_service
    from app.schemas.category import CategoryCreate
    from unittest.mock import patch, AsyncMock
    from app.models.ticket_ai_classification import TicketAIClassification
    from sqlalchemy import select

    customer = await user_factory(role="CUSTOMER")
    headers = auth_headers(customer)

    cat = await category_service.create_category(
        db_session, CategoryCreate(name="Billing", description="Billing issues")
    )
    await db_session.flush()

    with patch(
        "app.services.ticket_service.classify_ticket",
        new_callable=AsyncMock,
    ) as mock_classify:
        response = await client.post(
            "/api/v1/tickets/",
            headers=headers,
            json={
                "title": "Customer selected category",
                "description": "I chose this category myself.",
                "category_id": str(cat.id),
            },
        )

    assert response.status_code == 201, response.text
    ticket = response.json()
    assert ticket["category_id"] == str(cat.id)
    assert ticket["priority"] == "MEDIUM"

    # AI was not called.
    mock_classify.assert_not_called()

    # No classification record.
    result = await db_session.execute(
        select(TicketAIClassification).where(
            TicketAIClassification.ticket_id == ticket["id"]
        )
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_ticket_creation_no_categories_skips_ai_no_classification_record(
    client, user_factory, auth_headers, db_session
):
    """No categories in DB skips AI and creates no classification record."""
    from app.models.ticket_ai_classification import TicketAIClassification
    from sqlalchemy import select

    customer = await user_factory(role="CUSTOMER")
    headers = auth_headers(customer)

    response = await client.post(
        "/api/v1/tickets/",
        headers=headers,
        json={
            "title": "No categories ticket",
            "description": "There are no categories configured.",
        },
    )

    assert response.status_code == 201, response.text
    ticket = response.json()
    assert ticket["priority"] == "MEDIUM"
    assert ticket["category_id"] is None

    # No classification record.
    result = await db_session.execute(
        select(TicketAIClassification).where(
            TicketAIClassification.ticket_id == ticket["id"]
        )
    )
    assert result.scalar_one_or_none() is None



@pytest.mark.asyncio
async def test_ticket_summary_assigned_agent(
    client, user_factory, auth_headers, db_session
):
    """Assigned agent can generate AI summary for their assigned ticket."""
    from unittest.mock import patch, AsyncMock
    from app.services.category_service import category_service
    from app.schemas.category import CategoryCreate
    from app.schemas.ai.summary import TicketSummary
    from app.models.ticket import Ticket
    from sqlalchemy import select
    from uuid import UUID

    customer = await user_factory(role="CUSTOMER")
    agent = await user_factory(role="AGENT")

    cat = await category_service.create_category(
        db_session,
        CategoryCreate(name="Billing", description="Billing issues"),
    )
    await db_session.flush()

    response = await client.post(
        "/api/v1/tickets/",
        headers=auth_headers(customer),
        json={
            "title": "Duplicate charge on my account",
            "description": "I was charged twice for the same subscription.",
            "category_id": str(cat.id),
        },
    )

    assert response.status_code == 201, response.text
    ticket = response.json()

    # Assign the ticket directly to the test agent.
    result = await db_session.execute(
        select(Ticket).where(Ticket.id == UUID(ticket["id"]))
    )
    ticket_obj = result.scalar_one()
    ticket_obj.assigned_agent_id = agent.id
    await db_session.flush()

    expected_summary = TicketSummary(
        issue_summary="Customer reports duplicate charge on their account.",
        key_points=[
            "Customer charged twice",
            "Subscription activated 3 months ago",
        ],
        troubleshooting_steps=["Checked billing cycle dates"],
        current_situation="Customer is frustrated about duplicate charge.",
        unresolved_questions=["Is the second charge a system error?"],
    )

    with patch(
        "app.ai.services.ticket_ai_service.generate_structured",
        new_callable=AsyncMock,
    ) as mock_generate:
        mock_generate.return_value = expected_summary

        response = await client.post(
            f"/api/v1/tickets/{ticket['id']}/summary",
            headers=auth_headers(agent),
        )

    assert response.status_code == 200, response.text

    summary_data = response.json()

    assert summary_data["issue_summary"] == expected_summary.issue_summary
    assert summary_data["key_points"] == expected_summary.key_points
    assert summary_data["troubleshooting_steps"] == expected_summary.troubleshooting_steps
    assert summary_data["current_situation"] == expected_summary.current_situation
    assert summary_data["unresolved_questions"] == expected_summary.unresolved_questions

    mock_generate.assert_called_once()



@pytest.mark.asyncio
async def test_ticket_summary_admin(
    client, user_factory, auth_headers
):
    """Admin can generate AI summary for any ticket."""
    from unittest.mock import patch, AsyncMock
    from app.schemas.ai.summary import TicketSummary

    customer = await user_factory(role="CUSTOMER")
    admin = await user_factory(role="ADMIN")

    response = await client.post(
        "/api/v1/tickets/",
        headers=auth_headers(customer),
        json={
            "title": "Cannot access account",
            "description": "I cannot sign in after resetting my password.",
        },
    )

    assert response.status_code == 201, response.text
    ticket = response.json()

    expected_summary = TicketSummary(
        issue_summary="Customer cannot access their account after password reset.",
        key_points=["Customer reset password but still cannot log in"],
        troubleshooting_steps=[],
        current_situation="Customer is locked out of their account.",
        unresolved_questions=["Was the password reset email received?"],
    )

    with patch(
        "app.ai.services.ticket_ai_service.generate_structured",
        new_callable=AsyncMock,
    ) as mock_generate:
        mock_generate.return_value = expected_summary

        response = await client.post(
            f"/api/v1/tickets/{ticket['id']}/summary",
            headers=auth_headers(admin),
        )

    assert response.status_code == 200, response.text

    summary_data = response.json()

    assert summary_data["issue_summary"] == expected_summary.issue_summary
    assert summary_data["key_points"] == expected_summary.key_points
    assert summary_data["current_situation"] == expected_summary.current_situation
    assert summary_data["unresolved_questions"] == expected_summary.unresolved_questions

    mock_generate.assert_called_once()

@pytest.mark.asyncio
async def test_ticket_summary_customer_403(client, user_factory, auth_headers):
    """Customer cannot generate AI summary for any ticket."""
    from unittest.mock import patch, AsyncMock

    customer = await user_factory(role="CUSTOMER")
    headers = auth_headers(customer)

    response = await client.post(
        "/api/v1/tickets/",
        headers=headers,
        json={
            "title": "Customer ticket",
            "description": "This is a customer ticket.",
        },
    )
    assert response.status_code == 201, response.text
    ticket = response.json()

    with patch(
        "app.ai.services.llm_service.generate_structured",
        new_callable=AsyncMock,
    ) as mock_generate:
        response = await client.post(
            f"/api/v1/tickets/{ticket['id']}/summary",
            headers=headers,
        )

    assert response.status_code == 403, response.text
    mock_generate.assert_not_called()





@pytest.mark.asyncio
async def test_ticket_summary_unassigned_agent_403(
    client, user_factory, auth_headers, db_session
):
    """Unassigned agent cannot generate AI summary for another agent's ticket."""
    from unittest.mock import patch, AsyncMock
    from app.models.ticket import Ticket
    from sqlalchemy import select
    from uuid import UUID

    customer = await user_factory(role="CUSTOMER")
    assigned_agent = await user_factory(role="AGENT")
    unassigned_agent = await user_factory(role="AGENT")

    response = await client.post(
        "/api/v1/tickets/",
        headers=auth_headers(customer),
        json={
            "title": "Assigned ticket",
            "description": "This ticket is assigned to another agent.",
        },
    )

    assert response.status_code == 201, response.text
    ticket = response.json()

    # Assign the ticket to a different agent.
    result = await db_session.execute(
        select(Ticket).where(Ticket.id == UUID(ticket["id"]))
    )
    ticket_obj = result.scalar_one()
    ticket_obj.assigned_agent_id = assigned_agent.id
    await db_session.flush()

    with patch(
        "app.ai.services.ticket_ai_service.generate_structured",
        new_callable=AsyncMock,
    ) as mock_generate:
        response = await client.post(
            f"/api/v1/tickets/{ticket['id']}/summary",
            headers=auth_headers(unassigned_agent),
        )

    assert response.status_code == 403, response.text
    mock_generate.assert_not_called()
