import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )
from getpass import getpass

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password

async def create_admin():
    full_name = input("Enter Yourr name: ")
    email = input("Enter admin email: ").strip().lower()
    password = input("Enter admin password: ")
    
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(User).where(User.email== email)
            )        
            
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print("A user with this email already exists")
                
            admin = User(
                full_name=full_name,
                email=email,
                password_hash=hash_password(password),
                role="ADMIN",
                is_active=True,
            )
            
            db.add(admin)
            await db.commit()
            
            print("Admin account created successfully")
            
        except Exception:
            await db.rollback()
            raise
        
if __name__ =="__main__" :
    asyncio.run(create_admin())