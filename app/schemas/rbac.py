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
    resource_type: str
    resource_id: str
    parent_resource_type: str
    parent_resource_id: str
    relationship_type: str


class ResourceRelationshipResponse(BaseModel):
    id: int
    resource_type: str
    resource_id: str
    parent_resource_type: str
    parent_resource_id: str
    relationship_type: str
    
    class Config:
        from_attributes = True