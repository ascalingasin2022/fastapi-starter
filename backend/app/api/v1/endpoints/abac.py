"""
ABAC API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import require_superuser
from app.models.user import User
from app.schemas.abac import (
    UserAttributeCreate, UserAttributeResponse,
    ResourceAttributeCreate, ResourceAttributeResponse,
    ABACPolicyCreate, ABACPolicyResponse,
    ABACCheckRequest, ABACCheckResponse
)
from app.services.abac_service import ABACService
from sqlalchemy import select

router = APIRouter()


# Policy Management Endpoints
@router.post("/policies", response_model=ABACPolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_abac_policy(
    policy_data: ABACPolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_superuser)
):
    """Create a new ABAC policy (admin only)"""
    service = ABACService(db)
    policy = await service.create_policy(
        name=policy_data.name,
        description=policy_data.description,
        rules=policy_data.rules,
        is_active=policy_data.is_active
    )
    return policy


@router.get("/policies", response_model=List[ABACPolicyResponse])
async def list_abac_policies(
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_superuser)
):
    """List all ABAC policies (admin only)"""
    service = ABACService(db)
    policies = await service.get_policies(active_only=active_only)
    return policies


@router.get("/policies/{policy_id}", response_model=ABACPolicyResponse)
async def get_abac_policy(
    policy_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_superuser)
):
    """Get a specific ABAC policy (admin only)"""
    service = ABACService(db)
    policy = await service.get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_abac_policy(
    policy_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_superuser)
):
    """Delete an ABAC policy (admin only)"""
    service = ABACService(db)
    success = await service.delete_policy(policy_id)
    if not success:
        raise HTTPException(status_code=404, detail="Policy not found")
    return None


# User Attribute Endpoints
@router.post("/attributes/user", response_model=UserAttributeResponse, status_code=status.HTTP_201_CREATED)
async def set_user_attribute(
    attribute_data: UserAttributeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_superuser)
):
    """Set a user attribute (admin only)"""
    service = ABACService(db)
    attribute = await service.set_user_attribute(
        user_id=attribute_data.user_id,
        attribute_key=attribute_data.attribute_key,
        attribute_value=attribute_data.attribute_value
    )
    return attribute


@router.get("/attributes/user/{user_id}", response_model=List[UserAttributeResponse])
async def get_user_attributes(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all attributes for a user"""
    # Users can view their own attributes, admins can view anyone's
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to view these attributes")
    
    service = ABACService(db)
    attributes = await service.get_user_attributes(user_id)
    return attributes


# Resource Attribute Endpoints
@router.post("/attributes/resource", response_model=ResourceAttributeResponse, status_code=status.HTTP_201_CREATED)
async def set_resource_attribute(
    attribute_data: ResourceAttributeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_superuser)
):
    """Set a resource attribute (admin only)"""
    service = ABACService(db)
    attribute = await service.set_resource_attribute(
        resource_type=attribute_data.resource_type,
        resource_id=attribute_data.resource_id,
        attribute_key=attribute_data.attribute_key,
        attribute_value=attribute_data.attribute_value
    )
    return attribute


@router.get("/attributes/resource/{resource_type}/{resource_id}", response_model=List[ResourceAttributeResponse])
async def get_resource_attributes(
    resource_type: str,
    resource_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all attributes for a resource"""
    service = ABACService(db)
    attributes = await service.get_resource_attributes(resource_type, resource_id)
    return attributes


# Permission Check Endpoint
@router.post("/check", response_model=ABACCheckResponse)
async def check_abac_permission(
    check_request: ABACCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if a user has permission based on ABAC policies"""
    # Get the user to check
    from app.models.user import User as UserModel
    result = await db.execute(
        select(UserModel).where(UserModel.username == check_request.username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    service = ABACService(db)
    has_permission, matched_policies = await service.evaluate_policy(
        user=user,
        resource=check_request.resource,
        action=check_request.action,
        resource_type=check_request.resource_type,
        resource_id=check_request.resource_id
    )
    
    reason = f"Matched policies: {', '.join(matched_policies)}" if matched_policies else "No policies matched"
    
    return ABACCheckResponse(
        username=check_request.username,
        resource=check_request.resource,
        action=check_request.action,
        has_permission=has_permission,
        matched_policies=matched_policies,
        reason=reason
    )
