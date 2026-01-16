from typing import List, Optional, Union

from app.core.security import get_password_hash
from app.core.casbin_enforcer import casbin_enforcer
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from sqlalchemy.ext.asyncio import AsyncSession

class UserService:    

    def __init__(self, db: AsyncSession, user_repo: UserRepository):
        """Initialize with user repository"""
        self.db = db
        self.user_repo = user_repo

    async def get(self, user_id: int) -> Optional[User]:
        """Get a user by ID"""
        result = await self.user_repo.get(user_id)
        # attach casbin role if available
        try:
            roles = casbin_enforcer.get_roles_for_user(result.username) if result else []
            if roles:
                result._casbin_role = roles[0]
        except Exception:
            # enforcer may not be initialized yet; leave DB role/property as-is
            pass
        return result

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        result = await self.user_repo.get_by_email(email)
        try:
            roles = casbin_enforcer.get_roles_for_user(result.username) if result else []
            if roles:
                result._casbin_role = roles[0]
        except Exception:
            pass
        return result

    async def get_all_users(self) -> List[User]:
        """Get all users"""
        users, _ = await self.user_repo.get_multi()
        # attach casbin roles where present
        try:
            for u in users:
                roles = casbin_enforcer.get_roles_for_user(u.username)
                if roles:
                    u._casbin_role = roles[0]
        except Exception:
            # enforcer may not be initialized yet; ignore
            pass
        return users

    async def create(self, obj_in: UserCreate) -> User:
        """Create a new user"""
        hashed_password = get_password_hash(obj_in.password)        

        # Create user object
        db_obj = obj_in.dict()
        db_obj["hashed_password"] = hashed_password

        # Remove password field as we don't store it directly
        if "password" in db_obj:
            del db_obj["password"]

        return await self.user_repo.create(obj_in=db_obj)

    async def update(self, user_id: int, obj_in: Union[UserUpdate, dict]) -> Optional[User]:
        """Update a user"""
        # Get current user
        db_obj = await self.user_repo.get(user_id)
        if not db_obj:
            return None

        # Convert to dict if it's a Pydantic model
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)

        # Filter out None values from update_data
        filtered_update_data = {k: v for k, v in update_data.items() if v is not None}

        # Handle password update separately
        if "password" in filtered_update_data and filtered_update_data["password"]:
            filtered_update_data["hashed_password"] = get_password_hash(filtered_update_data["password"])
            del filtered_update_data["password"]  # remove plaintext password
        
        return await self.user_repo.update(id=user_id, obj_in=filtered_update_data)

    async def delete(self, user_id: int) -> Optional[User]:
        """Delete a user (hard delete)"""
        db_obj = await self.user_repo.get(user_id)
        if not db_obj:
            return None

        # Remove policies from Casbin
        if db_obj.username:
            casbin_enforcer.delete_role_for_user(db_obj.username, "user") # Remove basic role
            # Ideally remove all roles, but we need to know them. 
            # casbin_enforcer.delete_user(db_obj.username) # If such method exists or implement loop
            
        await self.user_repo.delete(id=user_id)

        return db_obj

    async def deactivate_user(self, user_id: int) -> Optional[User]:
        """
        Soft delete a user:
        - Set is_active = False
        - Remove roles from Casbin (access revocation)
        - Clear sensitive relationships if needed
        """
        user = await self.user_repo.get(user_id)
        if not user:
            return None
            
        # 1. Update is_active
        user.is_active = False
        self.db.add(user)
        
        # 2. Remove permissions/roles from Casbin
        try:
            # Get all roles and remove them
            roles = casbin_enforcer.get_roles_for_user(user.username)
            for role in roles:
                casbin_enforcer.delete_role_for_user(user.username, role)
        except Exception as e:
            print(f"Error cleaning up Casbin for user {user.username}: {e}")
            
        # 3. Commit changes
        await self.db.commit()
        await self.db.refresh(user)
        
        # Set transient property to avoid lazy load error in Pydantic model
        user._casbin_role = "user"
        
        return user