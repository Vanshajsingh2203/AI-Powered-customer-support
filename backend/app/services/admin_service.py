from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.admin import AgentCreate
from app.core.security import hash_password

class AdminService:
    async def create_agent(self, db:AsyncSession, agent_data:AgentCreate)->User:
        
        # 1. Check whether email already exists
        result = await db.execute(
            select(User).where(
                User.email == agent_data.email
            )
        )
        
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise ValueError("Email is already registered")
        
        # 2. Hash the password
        hashed_password = hash_password(agent_data.password)
        
        # 3. Create the agent
        agent = User(
            full_name=agent_data.full_name,
            email=agent_data.email,
            password_hash=hashed_password,
            role="AGENT",
            is_active=True
        )
        
        # 4. Add agent to database session
        db.add(agent)
        await db.flush()

        return agent
    
    async def get_agents(self, db:AsyncSession):
        result = await db.execute(
            select(User)
            .where(User.role=="AGENT")
            .order_by(User.created_at.desc())
        )
        
        return result.scalars().all()
    
    async def get_agent_by_id(self, db: AsyncSession, agent_id: UUID):
        result = await db.execute(
        select(User).where(
            User.id == agent_id,
            User.role == "AGENT"
            )
        )

        return result.scalar_one_or_none()
    
    async def update_user_status(
    self,
    db: AsyncSession,
    user_id: UUID,
    role: str,
    is_active: bool
):
        result = await db.execute(
            select(User).where(
                User.id == user_id,
                User.role == role
            )
        )
    
        user = result.scalar_one_or_none()
    
        if user is None:
            return None
    
        user.is_active = is_active
    
        await db.flush()
    
        return user
    
    async def get_customers(self, db: AsyncSession):
        result = await db.execute(
        select(User)
        .where(User.role == "CUSTOMER")
        .order_by(User.created_at.desc())
        )

        return result.scalars().all()
    
    async def get_customer_by_id(
    self,
    db: AsyncSession,
    customer_id: UUID
):
        result = await db.execute(
        select(User).where(
            User.id == customer_id,
            User.role == "CUSTOMER"
            )
        )

        return result.scalar_one_or_none()
    
    
    
admin_service = AdminService()            