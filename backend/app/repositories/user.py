from typing import Optional, Tuple, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    """Repository for user-related database operations"""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with database session.
        
        Args:
            db: SQLAlchemy async session
        """
        super().__init__(db, User)

    async def get(self, id: int) -> Optional[User]:
        """Get a user by ID with roles eagerly loaded"""
        query = select(User).options(selectinload(User.roles)).where(User.id == id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            email: User email address
            
        Returns:
            User if found, None otherwise
        """
        # Perform a query to find the user by email
        # make case insensitive        
        query = select(User).options(selectinload(User.roles)).where(func.lower(User.email) == email.lower())
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_multi(self, *, skip: int = 0, limit: int = 100, filters: dict = None) -> Tuple[List[User], int]:
        """Get multiple users with roles eagerly loaded"""
        # reuse BaseRepository.get_multi logic but ensure roles are selectinloaded
        query = select(User).options(selectinload(User.roles))

        if filters:
            for field, value in filters.items():
                if field.endswith("_contains") and value:
                    field_name = field.replace("_contains", "")
                    if hasattr(User, field_name):
                        column = getattr(User, field_name)
                        search_pattern = f"%{value}%"
                        query = query.where(func.lower(column).like(func.lower(search_pattern)))
                elif hasattr(User, field) and value is not None:
                    filter_value = value.value if hasattr(value, 'value') else value
                    if isinstance(filter_value, bool):
                        query = query.where(getattr(User, field) == filter_value)
                    elif isinstance(filter_value, list):
                        query = query.where(getattr(User, field).in_(filter_value))
                    else:
                        query = query.where(getattr(User, field) == filter_value)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total = total.scalar_one()

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total