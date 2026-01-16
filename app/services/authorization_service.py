"""
Unified Authorization Service - Combines RBAC, ABAC, and ReBAC
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.services.abac_service import ABACService
from app.services.rebac_service import REBACService
from app.core.casbin_enforcer import casbin_enforcer
from app.schemas.authorization import AuthorizationModel, AuthorizationResult


class AuthorizationService:
    """Unified authorization service that combines all three models"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.abac_service = ABACService(db)
        self.rebac_service = REBACService(db)
    
    async def check_permission(
        self,
        user: User,
        resource: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> tuple[bool, List[AuthorizationModel], List[AuthorizationResult]]:
        """
        Check permission across all authorization models
        Returns: (has_permission, granted_by_models, detailed_results)
        """
        results = []
        granted_by = []
        
        # 1. Check RBAC
        rbac_permission = await casbin_enforcer.check_rbac_permission_async(
            user.username, resource, action
        )
        results.append(AuthorizationResult(
            model=AuthorizationModel.RBAC,
            has_permission=rbac_permission,
            reason="Role-based access control check"
        ))
        if rbac_permission:
            granted_by.append(AuthorizationModel.RBAC)
        
        # 2. Check ABAC
        abac_permission, matched_policies = await self.abac_service.evaluate_policy(
            user, resource, action, resource_type, resource_id
        )
        reason = f"Matched policies: {', '.join(matched_policies)}" if matched_policies else "No policies matched"
        results.append(AuthorizationResult(
            model=AuthorizationModel.ABAC,
            has_permission=abac_permission,
            reason=reason
        ))
        if abac_permission:
            granted_by.append(AuthorizationModel.ABAC)
        
        # 3. Check ReBAC
        rebac_permission, relationship_path = await self.rebac_service.check_access_path(
            user.username, resource, action
        )
        path_str = " -> ".join(relationship_path) if relationship_path else "No relationship path found"
        results.append(AuthorizationResult(
            model=AuthorizationModel.REBAC,
            has_permission=rebac_permission,
            reason=path_str
        ))
        if rebac_permission:
            granted_by.append(AuthorizationModel.REBAC)
        
        # Permission granted if ANY model grants access
        has_permission = len(granted_by) > 0
        
        return has_permission, granted_by, results
