"""
ABAC (Attribute-Based Access Control) schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


# User Attribute Schemas
class UserAttributeCreate(BaseModel):
    """Schema for creating a user attribute"""
    user_id: int
    attribute_key: str = Field(..., description="Attribute name (e.g., 'clearance_level', 'team')")
    attribute_value: str = Field(..., description="Attribute value")


class UserAttributeResponse(BaseModel):
    """Schema for user attribute response"""
    id: int
    user_id: int
    attribute_key: str
    attribute_value: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Resource Attribute Schemas
class ResourceAttributeCreate(BaseModel):
    """Schema for creating a resource attribute"""
    resource_type: str = Field(..., description="Resource type (e.g., 'document', 'project')")
    resource_id: str = Field(..., description="Resource identifier")
    attribute_key: str = Field(..., description="Attribute name (e.g., 'sensitivity', 'owner')")
    attribute_value: str = Field(..., description="Attribute value")


class ResourceAttributeResponse(BaseModel):
    """Schema for resource attribute response"""
    id: int
    resource_type: str
    resource_id: str
    attribute_key: str
    attribute_value: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ABAC Policy Schemas
class ABACPolicyCreate(BaseModel):
    """Schema for creating an ABAC policy"""
    name: str = Field(..., description="Unique policy name")
    description: Optional[str] = Field(None, description="Policy description")
    rules: Dict[str, Any] = Field(..., description="Policy rules in JSON format")
    # Example rules structure:
    # {
    #     "conditions": [
    #         {"attribute": "department", "operator": "equals", "value": "Engineering"},
    #         {"attribute": "level", "operator": ">=", "value": 5}
    #     ],
    #     "permissions": {
    #         "resource": "documents",
    #         "action": "read"
    #     }
    # }
    is_active: bool = Field(default=True, description="Whether the policy is active")


class ABACPolicyUpdate(BaseModel):
    """Schema for updating an ABAC policy"""
    description: Optional[str] = None
    rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ABACPolicyResponse(BaseModel):
    """Schema for ABAC policy response"""
    id: int
    name: str
    description: Optional[str]
    rules: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ABAC Permission Check Schemas
class ABACCheckRequest(BaseModel):
    """Schema for checking ABAC permission"""
    username: str = Field(..., description="Username to check")
    resource: str = Field(..., description="Resource to access")
    action: str = Field(..., description="Action to perform")
    resource_type: Optional[str] = Field(None, description="Resource type (for attribute lookup)")
    resource_id: Optional[str] = Field(None, description="Resource ID (for attribute lookup)")


class ABACCheckResponse(BaseModel):
    """Schema for ABAC permission check response"""
    username: str
    resource: str
    action: str
    has_permission: bool
    matched_policies: List[str] = Field(default_factory=list, description="Names of policies that granted access")
    reason: Optional[str] = Field(None, description="Explanation of the decision")
