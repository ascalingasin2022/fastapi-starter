from fastapi import APIRouter, HTTPException
from typing import List
from app.core.casbin_enforcer import casbin_enforcer
from app.schemas.rbac import (
    RoleAssignment,
    PermissionAssignment,
    RoleResponse,
    PermissionResponse
)

router = APIRouter()

@router.post("/roles/assign")
async def assign_role_to_user(assignment: RoleAssignment):
    """Assign a role to a user"""
    try:
        # Check if user already has this role
        current_roles = casbin_enforcer.get_roles_for_user(assignment.username)
        if assignment.role in current_roles:
            raise HTTPException(status_code=409, detail=f"Role '{assignment.role}' is already assigned to user '{assignment.username}'")

        success = casbin_enforcer.add_role_for_user(
            assignment.username,
            assignment.role
        )

        if success:
            return {
                "message": f"Role '{assignment.role}' assigned to user '{assignment.username}'",
                "success": True
            }

        raise HTTPException(status_code=400, detail="Failed to assign role - unknown error")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error assigning role: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.delete("/roles/revoke")
async def revoke_role_from_user(assignment: RoleAssignment):
    """Revoke a role from a user"""
    # Check whether the user actually has the role
    current_roles = casbin_enforcer.get_roles_for_user(assignment.username)
    if assignment.role not in current_roles:
        raise HTTPException(status_code=404, detail=f"Role '{assignment.role}' not assigned to user '{assignment.username}'")

    success = casbin_enforcer.delete_role_for_user(
        assignment.username,
        assignment.role
    )

    if success:
        return {
            "message": f"Role '{assignment.role}' revoked from user '{assignment.username}'",
            "success": True
        }

    raise HTTPException(status_code=500, detail="Failed to revoke role")


@router.get("/roles/user/{username}", response_model=List[str])
async def get_user_roles(username: str):
    """Get all roles for a user"""
    roles = casbin_enforcer.get_roles_for_user(username)
    return roles


@router.get("/roles/{role}/users", response_model=List[str])
async def get_role_users(role: str):
    """Get all users with a specific role"""
    users = casbin_enforcer.get_users_for_role(role)
    return users


@router.post("/permissions/assign")
async def assign_permission_to_role(assignment: PermissionAssignment):
    """Assign a permission to a role"""
    success = casbin_enforcer.add_permission_for_role(
        assignment.role,
        assignment.resource,
        assignment.action
    )
    
    if success:
        return {
            "message": f"Permission '{assignment.action}' on '{assignment.resource}' assigned to role '{assignment.role}'",
            "success": True
        }
    
    raise HTTPException(status_code=400, detail="Failed to assign permission")


@router.delete("/permissions/revoke")
async def revoke_permission_from_role(assignment: PermissionAssignment):
    """Revoke a permission from a role"""
    # Check whether the permission exists for the role
    permissions = casbin_enforcer.get_permissions_for_role(assignment.role)
    # permissions are returned as lists like [role, resource, action]
    if not any(p for p in permissions if len(p) >= 3 and p[1] == assignment.resource and p[2] == assignment.action):
        raise HTTPException(status_code=404, detail="Permission not found for role")

    success = casbin_enforcer.delete_permission_for_role(
        assignment.role,
        assignment.resource,
        assignment.action
    )

    if success:
        await casbin_enforcer.save_policy()
        return {
            "message": f"Permission revoked from role '{assignment.role}'",
            "success": True
        }

    raise HTTPException(status_code=500, detail="Failed to revoke permission")


@router.get("/permissions/role/{role}")
async def get_role_permissions(role: str):
    """Get all permissions for a role"""
    permissions = casbin_enforcer.get_permissions_for_role(role)
    return {
        "role": role,
        "permissions": permissions
    }


@router.post("/check-permission")
async def check_permission(
    username: str,
    resource: str,
    action: str
):
    """Check if user has permission (no authentication required)"""
    has_permission = await casbin_enforcer.check_rbac_permission_async(
        username,
        resource,
        action
    )
    
    return {
        "username": username,
        "resource": resource,
        "action": action,
        "has_permission": has_permission
    }