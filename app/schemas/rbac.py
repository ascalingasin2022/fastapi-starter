from pydantic import BaseModel
from typing import Optional, List

class RoleAssignment(BaseModel):
    username: str
    role: str


class PermissionAssignment(BaseModel):
    role: str
    resource: str
    action: str


class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class PermissionResponse(BaseModel):
    id: int
    role_id: int
    resource: str
    action: str
    
    class Config:
        from_attributes = True


class ResourceRelationshipCreate(BaseModel):
    subject_type: str  # "user", "role", "resource"
    subject_id: str    # username, role name, or resource identifier
    resource_type: str
    resource_id: str
    parent_resource_type: str
    parent_resource_id: str
    relationship_type: str  # e.g., "owner_of", "member_of", "parent_of", "manages"


class ResourceRelationshipResponse(BaseModel):
    id: int
    subject_type: str
    subject_id: str
    resource_type: str
    resource_id: str
    parent_resource_type: str
    parent_resource_id: str
    relationship_type: str
    
    class Config:
        from_attributes = True


class REBACCheckRequest(BaseModel):
    """Schema for checking ReBAC permission"""
    username: str
    resource: str  # Can be "resource_type:resource_id" format
    action: str


class REBACCheckResponse(BaseModel):
    """Schema for ReBAC permission check response"""
    username: str
    resource: str
    action: str
    has_permission: bool
    relationship_path: Optional[List[str]] = None  # Shows the path of relationships that granted access
    reason: Optional[str] = None