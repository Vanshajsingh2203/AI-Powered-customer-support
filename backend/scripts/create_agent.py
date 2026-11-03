import asyncio
import sys
from getpass import getpass

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password


async def create_agent():
    full_name = input("Enter agent name: ")
    email = input("Enter agent email: ").strip().lower()
    password = input("Enter agent password: ")

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(User).where(User.email == email)
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print("A user with this email already exists.")
                return

            agent = User(
                full_name=full_name,
                email=email,
                password_hash=hash_password(password),
                role="AGENT",
                is_active=True,
            )

            db.add(agent)
            await db.commit()

            print("Agent account created successfully!")

        except Exception:
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(create_agent())