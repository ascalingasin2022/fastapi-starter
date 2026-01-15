"""
Dependencies for RBAC, ABAC, and ReBAC authorization
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.core.casbin_enforcer import casbin_enforcer


def require_rbac(resource: str, action: str):
    """
    Dependency factory for RBAC permission checking.
    
    Usage:
        @router.get("/resource")
        async def get_resource(
            user: User = Depends(require_rbac("resource", "read"))
        ):
            ...
    """
    async def check_permission(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        # Check RBAC permission
        has_permission = await casbin_enforcer.check_rbac_permission_async(
            current_user.username,
            resource,
            action
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: cannot {action} {resource}"
            )
        
        return current_user
    
    return check_permission


def require_abac(resource: str, action: str):
    """
    Dependency factory for ABAC permission checking.
    
    Usage:
        @router.get("/resource")
        async def get_resource(
            user: User = Depends(require_abac("resource", "read"))
        ):
            ...
    """
    async def check_permission(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        # Build attributes from user
        attributes = {
            "department": current_user.department or "",
            "level": current_user.level or 1,
            "location": current_user.location or "",
            "is_superuser": current_user.is_superuser
        }
        
        # Check ABAC permission
        has_permission = await casbin_enforcer.check_abac_permission_async(
            attributes,
            resource,
            action
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions based on attributes: cannot {action} {resource}"
            )
        
        return current_user
    
    return check_permission


def require_rebac(resource: str, action: str):
    """
    Dependency factory for ReBAC permission checking.
    
    Usage:
        @router.get("/resource/{resource_id}")
        async def get_resource(
            resource_id: str,
            user: User = Depends(require_rebac("resource", "read"))
        ):
            ...
    """
    async def check_permission(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        # Check ReBAC permission
        has_permission = await casbin_enforcer.check_rebac_permission_async(
            current_user.username,
            resource,
            action
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions based on relationships: cannot {action} {resource}"
            )
        
        return current_user
    
    return check_permission


def require_superuser(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to require superuser privileges.
    
    Usage:
        @router.delete("/admin/resource")
        async def delete_resource(
            user: User = Depends(require_superuser)
        ):
            ...
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser privileges required"
        )
    
    return current_user
