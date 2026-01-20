"""
ReBAC Service - Relationship-Based Access Control operations
"""
from typing import List, Optional, Set, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.user import ResourceRelationship
from app.core.casbin_enforcer import casbin_enforcer


class REBACService:
    """Service for managing ReBAC relationships and permissions"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # Relationship Management
    async def create_relationship(
        self,
        subject_type: str,
        subject_id: str,
        resource_type: str,
        resource_id: str,
        parent_resource_type: str,
        parent_resource_id: str,
        relationship_type: str
    ) -> ResourceRelationship:
        """Create a new resource relationship"""
        relationship = ResourceRelationship(
            subject_type=subject_type,
            subject_id=subject_id,
            resource_type=resource_type,
            resource_id=resource_id,
            parent_resource_type=parent_resource_type,
            parent_resource_id=parent_resource_id,
            relationship_type=relationship_type
        )
        self.db.add(relationship)
        await self.db.commit()
        await self.db.refresh(relationship)
        
        # Sync to Casbin
        await self.sync_relationship_to_casbin(relationship)
        
        return relationship
    
    async def get_relationships(
        self,
        subject_type: Optional[str] = None,
        subject_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> List[ResourceRelationship]:
        """Get relationships with optional filters"""
        query = select(ResourceRelationship)
        
        if subject_type:
            query = query.where(ResourceRelationship.subject_type == subject_type)
        if subject_id:
            query = query.where(ResourceRelationship.subject_id == subject_id)
        if resource_type:
            query = query.where(ResourceRelationship.resource_type == resource_type)
        if resource_id:
            query = query.where(ResourceRelationship.resource_id == resource_id)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def delete_relationship(self, relationship_id: int) -> bool:
        """Delete a relationship"""
        result = await self.db.execute(
            select(ResourceRelationship).where(ResourceRelationship.id == relationship_id)
        )
        relationship = result.scalar_one_or_none()
        
        if not relationship:
            return False
        
        await self.db.delete(relationship)
        await self.db.commit()
        return True
    
    # Permission Checking
    async def check_access_path(
        self,
        username: str,
        resource: str,
        action: str
    ) -> tuple[bool, Optional[List[str]]]:
        """
        Check if user has access via relationship chain
        Returns: (has_permission, relationship_path)
        """
        # Parse resource if in format "type:id"
        parts = resource.split(":", 1)
        if len(parts) == 2:
            resource_type, resource_id = parts
        else:
            resource_type = "resource"
            resource_id = resource
        
        # Check direct ownership
        direct_relationships = await self.get_relationships(
            subject_type="user",
            subject_id=username
        )
        
        # Check if user owns or has direct relationship to resource
        for rel in direct_relationships:
            if rel.resource_type == resource_type and rel.resource_id == resource_id:
                if rel.relationship_type in ["owner_of", "member_of"]:
                    return True, [f"{username} -> {rel.relationship_type} -> {resource}"]
        
        # Check inherited permissions via parent resources
        path = await self._find_permission_path(username, resource_type, resource_id)
        if path:
            return True, path
        
        # Use Casbin as fallback
        has_permission = await casbin_enforcer.check_rebac_permission_async(
            username, resource, action
        )
        
        return has_permission, None
    
    async def _find_permission_path(
        self,
        username: str,
        resource_type: str,
        resource_id: str,
        visited: Optional[Set[str]] = None
    ) -> Optional[List[str]]:
        """
        Recursively find a permission path through relationships
        """
        if visited is None:
            visited = set()
        
        resource_key = f"{resource_type}:{resource_id}"
        if resource_key in visited:
            return None  # Prevent cycles
        visited.add(resource_key)
        
        # Get all relationships where this resource is involved
        relationships = await self.get_relationships(
            resource_type=resource_type,
            resource_id=resource_id
        )
        
        for rel in relationships:
            # Check if parent resource is owned by user
            parent_key = f"{rel.parent_resource_type}:{rel.parent_resource_id}"
            
            # Check direct ownership of parent
            parent_rels = await self.get_relationships(
                subject_type="user",
                subject_id=username,
                resource_type=rel.parent_resource_type,
                resource_id=rel.parent_resource_id
            )
            
            if parent_rels:
                # Found a path!
                return [
                    f"{username} -> owns -> {parent_key}",
                    f"{parent_key} -> {rel.relationship_type} -> {resource_key}"
                ]
            
            # Recurse to check parent's ancestors
            parent_path = await self._find_permission_path(
                username,
                rel.parent_resource_type,
                rel.parent_resource_id,
                visited
            )
            
            if parent_path:
                parent_path.append(f"{parent_key} -> {rel.relationship_type} -> {resource_key}")
                return parent_path
        
        return None
    
    async def get_inherited_permissions(
        self,
        username: str
    ) -> List[Dict[str, str]]:
        """Get all resources user has access to via relationships"""
        permissions = []
        
        # Get all direct relationships for user
        direct_rels = await self.get_relationships(
            subject_type="user",
            subject_id=username
        )
        
        for rel in direct_rels:
            permissions.append({
                "resource": f"{rel.resource_type}:{rel.resource_id}",
                "relationship": rel.relationship_type,
                "direct": True
            })
            
            # Get child resources
            child_rels = await self.get_relationships(
                parent_resource_type=rel.resource_type,
                parent_resource_id=rel.resource_id
            )
            
            for child in child_rels:
                permissions.append({
                    "resource": f"{child.resource_type}:{child.resource_id}",
                    "relationship": f"inherited via {rel.relationship_type}",
                    "direct": False
                })
        
        return permissions
    
    async def sync_relationship_to_casbin(self, relationship: ResourceRelationship):
        """Sync relationship to Casbin enforcer"""
        # For ReBAC, we can add grouping policy
        # Format: user/resource -> resource
        subject = f"{relationship.subject_type}:{relationship.subject_id}"
        resource = f"{relationship.resource_type}:{relationship.resource_id}"
        
        casbin_enforcer.add_resource_relationship(subject, resource)
