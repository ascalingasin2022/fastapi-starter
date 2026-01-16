"""
Unified Authorization API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.authorization import (
    UnifiedAuthorizationRequest,
    UnifiedAuthorizationResponse
)
from app.services.authorization_service import AuthorizationService

router = APIRouter()


@router.post("/check", response_model=UnifiedAuthorizationResponse)
async def check_unified_authorization(
    check_request: UnifiedAuthorizationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check permission across all authorization models (RBAC, ABAC, ReBAC)
    Returns detailed information about which models granted access
    """
    # Get the user to check
    result = await db.execute(
        select(User).where(User.username == check_request.username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check permissions across all models
    service = AuthorizationService(db)
    has_permission, granted_by, results = await service.check_permission(
        user=user,
        resource=check_request.resource,
        action=check_request.action,
        resource_type=check_request.resource_type,
        resource_id=check_request.resource_id
    )
    
    return UnifiedAuthorizationResponse(
        username=check_request.username,
        resource=check_request.resource,
        action=check_request.action,
        has_permission=has_permission,
        granted_by=granted_by,
        results=results
    )
