import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin
from app.core.security import hash_password, verify_password, password_needs_rehash, create_access_token

from app.config import settings

from app.core.security import generate_refresh_token,hash_refresh_token

from app.models.refresh_token import RefreshToken

class AuthService:
    
    async def create_refresh_token(self, db: AsyncSession, user_id:uuid.UUID, family_id: uuid.UUID)->str:
        
        # Generate original refresh token
        raw_token = generate_refresh_token()
        
        # Calculate token hash
        token_hash = hash_refresh_token(raw_token)
        
        # Calculate expiration time
        expires_at = datetime.now(timezone.utc)+ timedelta(
            days = settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        # Create database record
        refresh_token = RefreshToken(
            user_id= user_id,
            token_hash = token_hash,
            family_id= family_id,
            expires_at= expires_at
        )
        
        db.add(refresh_token)
        
        # Send pending changes to PostgreSQL
        await db.flush()
        
        return raw_token
    
    async def register_user(
        self,
        db: AsyncSession,
        user_data: UserRegister,
    ) -> User:

        # Check whether email already exists
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )

        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ValueError("Email is already registered")

        # Hash the password
        hashed_password = hash_password(user_data.password)

        # Create user object
        new_user = User(
            full_name=user_data.full_name,
            email=user_data.email,
            password_hash=hashed_password,
            role="CUSTOMER",
            is_active=True,
        )

        # Save user
        db.add(new_user)
        await db.flush()

        return new_user
    
    async def login_user(self, db:AsyncSession, login_data:UserLogin)->dict:
        
        result = await db.execute(
            select(User).where(login_data.email== User.email)
        )
        user = result.scalar_one_or_none()
        
        # Verify credentials
        if user is None or not verify_password(
        login_data.password,
        user.password_hash,
        ):
            raise ValueError("Incorrect email or password")
        
        # check account status
        if not user.is_active:
            raise ValueError("Incorrect email or password")
        
        # Upgrade password hash if necessary
        if password_needs_rehash(user.password_hash):
            user.password_hash = hash_password(login_data.password)
            
        # Generate access token 
        access_token = create_access_token(
            user_id=str(user.id),
            role=user.role,
        )
        # Create a nw session family for this login
        family_id = uuid.uuid4()
        
        # Generate and store refresh token
        refresh_token = await self.create_refresh_token(
            db=db,
            user_id=user.id,
            family_id=family_id,
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user  ,     
        }
        
    async def refresh_access_token(
        self,
        db: AsyncSession,
        raw_refresh_token: str,
        ) -> dict:

        # 1. Hash the incoming refresh token
        token_hash = hash_refresh_token(raw_refresh_token)

        # 2. Find the corresponding token and lock its row
        result = await db.execute(
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .with_for_update()
        )

        stored_token = result.scalar_one_or_none()

        # 3. Validate the token
        if stored_token is None:
            raise ValueError("Invalid refresh token")

        if stored_token.revoked_at is not None:

            await db.execute(
            update(RefreshToken)
            .where(
            RefreshToken.family_id == stored_token.family_id,
            RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )

            await db.flush()

            raise ValueError("Refresh token reuse detected")

        now = datetime.now(timezone.utc)

        if stored_token.expires_at <= now:
            raise ValueError("Refresh token has expired")

        # 4. Find the associated user
        user_result = await db.execute(
            select(User).where(User.id == stored_token.user_id)
        )

        user = user_result.scalar_one_or_none()

        if user is None or not user.is_active:
            raise ValueError("Invalid refresh token")

        # 5. Generate a new access token
        access_token = create_access_token(
            user_id=str(user.id),
            role=user.role,
        )

        # 6. Generate a new refresh token in the same family
        new_refresh_token = await self.create_refresh_token(
            db=db,
            user_id=user.id,
            family_id=stored_token.family_id,
        )

        # 7. Find the newly created database record
        new_token_hash = hash_refresh_token(new_refresh_token)

        new_result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == new_token_hash
            )
        )

        new_stored_token = new_result.scalar_one()

        # 8. Revoke the old token and link it to the replacement
        stored_token.revoked_at = now
        stored_token.replaced_by_token_id = new_stored_token.id

        await db.flush()

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
        
    async def logout_user(
        self,
        db:AsyncSession,
        raw_refresh_token: str,
    )->None:
        
        # Hash the incoming refresh token
        token_hash = hash_refresh_token(raw_refresh_token)
        
        # Find the corresponding token in the database
        result = await db.execute(
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .with_for_update()
        )
        
        stored_token = result.scalar_one_or_none()
        
        # Reject invalid or already-revoked tokens
        if stored_token is None or stored_token.revoked_at is not None:
            raise ValueError("Invalid or already revoked refresh token")

        # Revoke the current device session
        stored_token.revoked_at = datetime.now(timezone.utc)
        
        await db.flush()