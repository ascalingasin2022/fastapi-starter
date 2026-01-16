from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import verify_password
from app.core.config import settings
from app.dependencies.services import get_user_service
from app.exceptions.http_exceptions import BadRequestError, UnauthorizedError
from app.schemas.auth import UserResponse
from app.models.user import User
from app.db.session import get_db
from app.services.user_service import UserService

from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.core.security import verify_password

security = HTTPBasic()

async def get_current_user(
    credentials: HTTPBasicCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current authenticated user using Basic Auth.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Basic"},
    )
    
    # Try username
    result = await db.execute(
        select(User).where(User.username == credentials.username)
    )
    user = result.scalar_one_or_none()
    
    # If username not found, try email (optional, but good for UX)
    if not user:
        result = await db.execute(
            select(User).where(User.email == credentials.username)
        )
        user = result.scalar_one_or_none()

    if not user:
        raise credentials_exception
        
    if not verify_password(credentials.password, user.hashed_password):
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """
    Get the current active user from the token.
    Args:
        current_user: Current authenticated user (User model)
    Returns:
        Current active user (User model)
    Raises:
        HTTPException: If the user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return current_user



# Usage example:

# @router.get("/admin")
# async def read_admin_data(current_user: UserResponse = Depends(authorize(allowed_roles=["admin"]))):
#     return {"message": "Welcome, admin!"}
#

# @router.get("/user")
# async def read_user_data(current_user: UserResponse = Depends(authorize(allowed_roles=["user"]))):
#     return {"message": "Welcome, user!"}

#multiple roles
# @router.get("/admin_or_user")
# async def read_admin_or_user_data(current_user: UserResponse = Depends(authorize(allowed_roles=["admin", "user"]))):
#     return {"message": "Welcome, admin or user!"}

# @router.get("/any")
# async def read_any_data(current_user: UserResponse = Depends(authorize())):
#     return {"message": "Welcome, any authenticated user!"}

# This allows you to specify which roles are allowed to access certain endpoints.
# You can also create a route that is accessible to any authenticated user by not passing any roles to the authorize function.
def authorize(allowed_roles: Optional[List[str]] = None):
    """
    Dependency for role-based access control.
    If no roles are provided, any authenticated active user is allowed.
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        if allowed_roles:
            # Get user's role - check if they have a role in the database
            # For now, check if user has roles relationship
            user_roles = [role.name for role in current_user.roles] if current_user.roles else []
            # Also check is_superuser as admin role
            if current_user.is_superuser and "admin" not in user_roles:
                user_roles.append("admin")
            
            # Check if user has any of the allowed roles
            if not any(role in allowed_roles for role in user_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access forbidden: insufficient role"
                )
            
        return current_user

    return role_checker