"""
ABAC Service - Attribute-Based Access Control operations
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.abac import UserAttribute, ResourceAttribute, ABACPolicy
from app.models.user import User
from app.core.casbin_enforcer import casbin_enforcer


class ABACService:
    """Service for managing ABAC policies and attributes"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # Policy Management
    async def create_policy(
        self,
        name: str,
        description: Optional[str],
        rules: Dict[str, Any],
        is_active: bool = True
    ) -> ABACPolicy:
        """Create a new ABAC policy"""
        policy = ABACPolicy(
            name=name,
            description=description,
            rules=rules,
            is_active=is_active
        )
        self.db.add(policy)
        await self.db.commit()
        await self.db.refresh(policy)
        
        # Sync to Casbin if active
        if is_active:
            await self.sync_policy_to_casbin(policy)
        
        return policy
    
    async def get_policies(self, active_only: bool = False) -> List[ABACPolicy]:
        """Get all ABAC policies"""
        query = select(ABACPolicy)
        if active_only:
            query = query.where(ABACPolicy.is_active == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_policy(self, policy_id: int) -> Optional[ABACPolicy]:
        """Get a specific policy by ID"""
        result = await self.db.execute(
            select(ABACPolicy).where(ABACPolicy.id == policy_id)
        )
        return result.scalar_one_or_none()
    
    async def delete_policy(self, policy_id: int) -> bool:
        """Delete an ABAC policy"""
        policy = await self.get_policy(policy_id)
        if not policy:
            return False
        
        await self.db.delete(policy)
        await self.db.commit()
        return True
    
    # User Attribute Management
    async def set_user_attribute(
        self,
        user_id: int,
        attribute_key: str,
        attribute_value: str
    ) -> UserAttribute:
        """Set or update a user attribute"""
        # Check if attribute exists
        result = await self.db.execute(
            select(UserAttribute).where(
                UserAttribute.user_id == user_id,
                UserAttribute.attribute_key == attribute_key
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.attribute_value = attribute_value
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            attribute = UserAttribute(
                user_id=user_id,
                attribute_key=attribute_key,
                attribute_value=attribute_value
            )
            self.db.add(attribute)
            await self.db.commit()
            await self.db.refresh(attribute)
            return attribute
    
    async def get_user_attributes(self, user_id: int) -> List[UserAttribute]:
        """Get all attributes for a user"""
        result = await self.db.execute(
            select(UserAttribute).where(UserAttribute.user_id == user_id)
        )
        return list(result.scalars().all())
    
    async def get_user_attributes_dict(self, user_id: int) -> Dict[str, str]:
        """Get user attributes as a dictionary"""
        attributes = await self.get_user_attributes(user_id)
        return {attr.attribute_key: attr.attribute_value for attr in attributes}
    
    # Resource Attribute Management
    async def set_resource_attribute(
        self,
        resource_type: str,
        resource_id: str,
        attribute_key: str,
        attribute_value: str
    ) -> ResourceAttribute:
        """Set or update a resource attribute"""
        # Check if attribute exists
        result = await self.db.execute(
            select(ResourceAttribute).where(
                ResourceAttribute.resource_type == resource_type,
                ResourceAttribute.resource_id == resource_id,
                ResourceAttribute.attribute_key == attribute_key
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.attribute_value = attribute_value
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            attribute = ResourceAttribute(
                resource_type=resource_type,
                resource_id=resource_id,
                attribute_key=attribute_key,
                attribute_value=attribute_value
            )
            self.db.add(attribute)
            await self.db.commit()
            await self.db.refresh(attribute)
            return attribute
    
    async def get_resource_attributes(
        self,
        resource_type: str,
        resource_id: str
    ) -> List[ResourceAttribute]:
        """Get all attributes for a resource"""
        result = await self.db.execute(
            select(ResourceAttribute).where(
                ResourceAttribute.resource_type == resource_type,
                ResourceAttribute.resource_id == resource_id
            )
        )
        return list(result.scalars().all())
    
    async def get_resource_attributes_dict(
        self,
        resource_type: str,
        resource_id: str
    ) -> Dict[str, str]:
        """Get resource attributes as a dictionary"""
        attributes = await self.get_resource_attributes(resource_type, resource_id)
        return {attr.attribute_key: attr.attribute_value for attr in attributes}
    
    # Policy Evaluation
    async def evaluate_policy(
        self,
        user: User,
        resource: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> tuple[bool, List[str]]:
        """
        Evaluate ABAC policies for a user
        Returns: (has_permission, matched_policy_names)
        """
        # Gather user attributes
        user_attrs = {
            "department": user.department or "",
            "level": user.level or 1,
            "location": user.location or "",
            "is_superuser": user.is_superuser
        }
        
        # Add custom attributes
        custom_attrs = await self.get_user_attributes_dict(user.id)
        user_attrs.update(custom_attrs)
        
        # Gather resource attributes if provided
        resource_attrs = {}
        if resource_type and resource_id:
            resource_attrs = await self.get_resource_attributes_dict(resource_type, resource_id)
        
        # Get active policies
        policies = await self.get_policies(active_only=True)
        matched_policies = []
        
        # Evaluate each policy
        for policy in policies:
            if self._evaluate_policy_rules(policy.rules, user_attrs, resource_attrs, resource, action):
                matched_policies.append(policy.name)
        
        # Use Casbin for final decision
        has_permission = await casbin_enforcer.check_abac_permission_async(
            user_attrs, resource, action
        )
        
        return has_permission, matched_policies
    
    def _evaluate_policy_rules(
        self,
        rules: Dict[str, Any],
        user_attrs: Dict[str, Any],
        resource_attrs: Dict[str, Any],
        resource: str,
        action: str
    ) -> bool:
        """Evaluate policy rules against attributes"""
        # Check if permissions match
        perms = rules.get("permissions", {})
        if perms.get("resource") != resource or perms.get("action") != action:
            return False
        
        # Check conditions
        conditions = rules.get("conditions", [])
        for condition in conditions:
            attr_name = condition.get("attribute")
            operator = condition.get("operator")
            expected_value = condition.get("value")
            
            # Try to get attribute from user or resource
            actual_value = user_attrs.get(attr_name) or resource_attrs.get(attr_name)
            
            if not self._compare_values(actual_value, operator, expected_value):
                return False
        
        return True
    
    def _compare_values(self, actual: Any, operator: str, expected: Any) -> bool:
        """Compare values based on operator"""
        try:
            if operator == "equals" or operator == "==":
                return str(actual) == str(expected)
            elif operator == "!=":
                return str(actual) != str(expected)
            elif operator == ">":
                return float(actual) > float(expected)
            elif operator == ">=":
                return float(actual) >= float(expected)
            elif operator == "<":
                return float(actual) < float(expected)
            elif operator == "<=":
                return float(actual) <= float(expected)
            elif operator == "in":
                return str(actual) in expected
            else:
                return False
        except (ValueError, TypeError):
            return False
    
    async def sync_policy_to_casbin(self, policy: ABACPolicy):
        """Sync policy to Casbin enforcer (if needed for complex rules)"""
        # For now, Casbin uses the matcher in abac_model.conf
        # This could be used to add specific rules to Casbin if needed
        pass
