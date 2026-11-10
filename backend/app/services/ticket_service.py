from uuid import UUID
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime , timezone
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate, TicketResponse, TicketUpdate, TicketAgentUpdate
from app.models.user import User
from app.services.audit_service import audit_service
from app.models.category import Category

class TicketService:
    async def create_ticket(
    self,
    db: AsyncSession,
    ticket_data: TicketCreate,
    current_user: User
) -> Ticket:

        category = None

        if ticket_data.category_id is not None:
            result = await db.execute(
                select(Category).where(
                    Category.id == ticket_data.category_id
                )
            )

            category = result.scalar_one_or_none()

            if category is None:
                raise ValueError("Invalid category ID")

        new_ticket = Ticket(
            title=ticket_data.title,
            description=ticket_data.description,
            customer_id=current_user.id,
            category_id=category.id if category else None,
            priority="MEDIUM",
            status="OPEN",
        )

        db.add(new_ticket)

        await db.flush()

        return new_ticket
    
    async def get_ticket(
    self,
    db: AsyncSession,
    current_user: User,
    category_id: UUID | None = None,
    status: str | None = None,
):
        query = (
            select(Ticket)
            .options(selectinload(Ticket.category))
            .where(Ticket.customer_id == current_user.id)
        )

        if category_id is not None:
            query = query.where(Ticket.category_id == category_id)

        if status is not None:
            query = query.where(Ticket.status == status.upper())

        query = query.order_by(Ticket.created_at.desc())

        result = await db.execute(query)

        return result.scalars().all()

    async def get_ticket_by_id(self, db:AsyncSession, ticket_id:UUID, current_user: User):
        query = (
        select(Ticket)
        .options(selectinload(Ticket.category),
                 selectinload(Ticket.assigned_agent),
                 selectinload(Ticket.customer)
        )
        .where(Ticket.id == ticket_id)
    )

        
        # Customers can access only their own tickets.
        if current_user.role == "CUSTOMER":
            query = query.where(
                Ticket.customer_id == current_user.id
        )
            
            # Agents can access only tickets assigned to them.
        elif current_user.role == "AGENT":
            query = query.where(
                Ticket.assigned_agent_id == current_user.id
        )
            
        # Admins can access all tickets.
        elif current_user.role != "ADMIN":
            return None
        
        result = await db.execute(query)
        
        return result.scalar_one_or_none()
    
    async def update_ticket(self, db:AsyncSession, ticket_id, ticket_data: TicketUpdate, current_user):
        ticket = await self.get_ticket_by_id(db, ticket_id, current_user)
        
        if ticket is None:
            return None
        
        update_data = ticket_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is None:
                raise ValueError(f"{field} cannoy be null")
            
            setattr(ticket, field, value)
            
        await db.flush()
        
        return ticket
    
    async def update_ticket_by_agent(
        self,
        db: AsyncSession,
        ticket_id: UUID,
        update_data: TicketAgentUpdate,
        current_user: User,
    ):
        result = await db.execute(
            select(Ticket)
            .options(selectinload(Ticket.category))
            .where(Ticket.id == ticket_id)
            .with_for_update()
        )
    
        ticket = result.scalar_one_or_none()
    
        if ticket is None:
            return None
    
        # Check assignment permission.
        if (
            current_user.role == "AGENT"
            and ticket.assigned_agent_id != current_user.id
        ):
            return None
    
        if current_user.role not in ("AGENT", "ADMIN"):
            raise ValueError(
                "You do not have permission to update this ticket"
            )
    
        changes = update_data.model_dump(exclude_unset=True)
    
        if not changes:
            raise ValueError("At least one field must be provided")
    
        for field, value in changes.items():
            if value is None:
                raise ValueError(f"{field} cannot be null")
    
        allowed_transitions = {
            "OPEN": ["IN_PROGRESS"],
            "IN_PROGRESS": ["WAITING_ON_CUSTOMER", "RESOLVED"],
            "WAITING_ON_CUSTOMER": ["IN_PROGRESS"],
            "RESOLVED": ["IN_PROGRESS", "CLOSED"],
            "CLOSED": [],
        }
    
        # Validate status transition.
        if "status" in changes:
            new_status = changes["status"]
    
            if new_status != ticket.status:
                allowed = allowed_transitions.get(ticket.status, [])
    
                if new_status not in allowed:
                    raise ValueError(
                        f"Cannot change status from {ticket.status} to {new_status}"
                    )
    
        # Capture old and new values before modifying the ticket.
        old_value = {}
        new_value = {}
    
        for field, new_val in changes.items():
            old_val = getattr(ticket, field)
    
            if old_val != new_val:
                old_value[field] = old_val
                new_value[field] = new_val
    
        # Apply changes.
        if "status" in changes:
            ticket.status = changes["status"]
    
        if "priority" in changes:
            ticket.priority = changes["priority"]
    
        # Update closure timestamp.
        if ticket.status == "CLOSED":
            if ticket.closed_at is None:
                ticket.closed_at = datetime.now(timezone.utc)
    
        elif "status" in changes:
            ticket.closed_at = None
    
        # Create audit record only if something actually changed.
        if old_value:
            await audit_service.create_log(
                db=db,
                user_id=current_user.id,
                ticket_id=ticket.id,
                action="TICKET_UPDATED",
                old_value=old_value,
                new_value=new_value,
            )
    
        await db.flush()
    
        return ticket
            
    def to_ticket_response(self, ticket: Ticket) -> TicketResponse:
        return TicketResponse(
        id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        status=ticket.status,
        priority=ticket.priority,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        category_id=ticket.category_id,
        category_name=ticket.category.name if ticket.category else None,
        customer_name=ticket.customer.full_name,
        customer_email=ticket.customer.email,
        assigned_agent_id=ticket.assigned_agent_id,
        assigned_agent_name=(
            ticket.assigned_agent.full_name
            if ticket.assigned_agent
            else None
        ),
        
    )
            
    async def list_tickets(
    self,
    db: AsyncSession,
    current_user: User,
    category_id: UUID | None = None,
    status: str | None = None,
    priority: str | None = None,
    search: str | None = None,
    assigned_agent_id: UUID | None = None,
    page: int = 1,
    limit: int = 10,
    sort_order: str = "desc",
):
        query = select(Ticket).options(
            selectinload(Ticket.category),
            selectinload(Ticket.assigned_agent),
            selectinload(Ticket.customer),
        )

        conditions = []

        # Role-based access restrictions
        if current_user.role == "CUSTOMER":
            conditions.append(Ticket.customer_id == current_user.id)

        elif current_user.role == "AGENT":
            conditions.append(
                Ticket.assigned_agent_id == current_user.id
            )

        elif current_user.role != "ADMIN":
            raise ValueError("Invalid user role")

        # Filters
        if category_id is not None:
            conditions.append(Ticket.category_id == category_id)

        if status is not None:
            conditions.append(Ticket.status == status.upper())

        if priority is not None:
            conditions.append(Ticket.priority == priority.upper())

        if search:
            search_term = f"%{search.strip()}%"
            conditions.append(
                Ticket.title.ilike(search_term)
                | Ticket.description.ilike(search_term)
            )

        if assigned_agent_id is not None:
            if current_user.role != "ADMIN":
                raise ValueError(
                    "Only admins can filter by assigned agent"
                )

            conditions.append(
                Ticket.assigned_agent_id == assigned_agent_id
            )

        # Apply conditions to the query
        query = query.where(*conditions)

        # Get total matching records before pagination
        count_query = (
            select(func.count(Ticket.id))
            .where(*conditions)
        )

        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # Sorting
        if sort_order.lower() == "asc":
            query = query.order_by(Ticket.created_at.asc())
        else:
            query = query.order_by(Ticket.created_at.desc())

        # Pagination
        offset = (page - 1) * limit

        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        tickets = result.scalars().all()

        total_pages = (total + limit - 1) // limit

        return {
            "items": tickets,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        }
        
    async def get_ticket_with_category(
    self,
    db: AsyncSession,
    ticket_id: UUID
):
        result = await db.execute(
        select(Ticket)
        .options(selectinload(Ticket.category))
        .where(Ticket.id == ticket_id)
        )

        return result.scalar_one_or_none()