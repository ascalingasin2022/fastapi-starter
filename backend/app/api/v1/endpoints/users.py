from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.dependencies.services import get_user_service
from app.dependencies.auth import get_current_active_user
from app.core.casbin_enforcer import casbin_enforcer
from app.models.user import User
from app.dtos.custom_response_dto import CustomResponse
from app.schemas.user import UserResponse
from app.services.user_service import UserService
from app.utils.response import create_response

router = APIRouter()

@router.get(
    "/",
    response_model=CustomResponse[List[UserResponse]],
    summary="Get all users",
    description="Get a list of users"
)
async def get_users(
    user_service: UserService = Depends(get_user_service)
) -> CustomResponse[List[UserResponse]]:
    users = await user_service.get_all_users()

    if not users:
        return create_response(
            data=None
        )
    
    return create_response(
        data=[UserResponse.from_orm(user) for user in users]
    )

@router.get(
    "/by-email",
    response_model=CustomResponse[UserResponse],
    summary="Get user by email",
    description="Get a user by their email address"
)
async def get_user_by_email(
    email: str,
    user_service: UserService = Depends(get_user_service)
) -> CustomResponse[UserResponse]:
    user = await user_service.get_by_email(email)

    if not user:
        return create_response(
            data=None
        )
    
    return create_response(
        data=UserResponse.from_orm(user)
    )

@router.get(
    "/{id}",
    response_model=CustomResponse[UserResponse],
    summary="Get user by ID",
    description="Get a user by their ID"
)
async def get_user_by_id(
    id: int,
    user_service: UserService = Depends(get_user_service)
) -> CustomResponse[UserResponse]:
    user = await user_service.get(id)

    if not user:
        return create_response(
            data=None
        )
    
    return create_response(
        data=UserResponse.from_orm(user)
    )

@router.delete(
    "/{id}",
    summary="Delete user",
    description="Delete a user account. Authorization: Admin or Self.",
    response_model=CustomResponse[UserResponse]
)
async def delete_user(
    id: int,
    soft_delete: bool = Query(True, description="Perform soft delete (deactivate) instead of hard delete"),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user)
) -> CustomResponse[UserResponse]:
    target_user = await user_service.get(id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    # Unified Authorization Check
    # Check if current user can 'delete' the 'user:{id}' resource
    # Or explicitly check: Is Admin OR Is Self
    # We use our new unified enforcement
    
    # Construct resource string or object
    resource = f"user:{target_user.username}"
    # Also pass target_user object for attribute/relationship checks
    
    is_allowed = casbin_enforcer.enforce_unified(
        user=current_user,
        resource=resource,
        action="delete",
        resource_obj=target_user
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user"
        )
    
    if soft_delete:
        deleted_user = await user_service.deactivate_user(id)
    else:
        # Hard delete - restricted to admins perhaps?
        # For now, if authorized to delete, they can choose mode.
        deleted_user = await user_service.delete(id)
        
    return create_response(
        data=UserResponse.from_orm(deleted_user)
    )
