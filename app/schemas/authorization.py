"""
Unified Authorization schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class AuthorizationModel(str, Enum):
    """Enum for authorization models"""
    RBAC = "rbac"
    ABAC = "abac"
    REBAC = "rebac"


class UnifiedAuthorizationRequest(BaseModel):
    """Schema for checking permission across all authorization models"""
    username: str = Field(..., description="Username to check")
    resource: str = Field(..., description="Resource to access")
    action: str = Field(..., description="Action to perform")
    resource_type: Optional[str] = Field(None, description="Resource type (for ABAC/ReBAC)")
    resource_id: Optional[str] = Field(None, description="Resource ID (for ABAC/ReBAC)")


class AuthorizationResult(BaseModel):
    """Individual authorization check result"""
    model: AuthorizationModel
    has_permission: bool
    reason: Optional[str] = None


class UnifiedAuthorizationResponse(BaseModel):
    """Schema for unified authorization check response"""
    username: str
    resource: str
    action: str
    has_permission: bool  # True if ANY model granted access
    granted_by: List[AuthorizationModel] = Field(default_factory=list, description="Which models granted access")
    results: List[AuthorizationResult] = Field(default_factory=list, description="Detailed results from each model")
    evaluation_order: List[AuthorizationModel] = Field(
        default_factory=lambda: [AuthorizationModel.RBAC, AuthorizationModel.ABAC, AuthorizationModel.REBAC],
        description="Order in which models were evaluated"
    )
