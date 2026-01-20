import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy import select

async def create_admin():
    async with AsyncSessionLocal() as session:
        # Check if admin exists
        result = await session.execute(
            select(User).where(User.username == "harrypotter")
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            admin = User(
                email="harrypotter@example.com",
                username="harrypotter",
                hashed_password=get_password_hash("harrypotter"),
                first_name="Harry",
                last_name="Potter",
                full_name="Harry Potter",
                department="Web Dev",
                level=5,
                location="Tower 2",
                is_superuser=True,
                is_active=True
            )
            session.add(admin)
            await session.commit()
            print("Harry Potter admin user created")
        else:
            print("Harry Potter admin user already exists")

if __name__ == "__main__":
    asyncio.run(create_admin())