import os
import casbin
from casbin_sqlalchemy_adapter import Adapter
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

# Create base class for Casbin models
CasbinBase = declarative_base()

class CasbinRBACRule(CasbinBase):
    __tablename__ = 'casbin_rbac_rule'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ptype = Column(String(255))
    v0 = Column(String(255))
    v1 = Column(String(255))
    v2 = Column(String(255))
    v3 = Column(String(255))
    v4 = Column(String(255))
    v5 = Column(String(255))

class CasbinABACRule(CasbinBase):
    __tablename__ = 'casbin_abac_rule'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ptype = Column(String(255))
    v0 = Column(String(255))
    v1 = Column(String(255))
    v2 = Column(String(255))
    v3 = Column(String(255))
    v4 = Column(String(255))
    v5 = Column(String(255))

class CasbinReBACRule(CasbinBase):
    __tablename__ = 'casbin_rebac_rule'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ptype = Column(String(255))
    v0 = Column(String(255))
    v1 = Column(String(255))
    v2 = Column(String(255))
    v3 = Column(String(255))
    v4 = Column(String(255))
    v5 = Column(String(255))

class CasbinEnforcer:
    def __init__(self):
        self.rbac_enforcer = None
        self.abac_enforcer = None
        self.rebac_enforcer = None
        
    async def initialize(self):
        """Initialize all Casbin enforcers with PostgreSQL adapter"""
        try:
            # Database connection
            sync_database_url = settings.DATABASE_URL.replace('+asyncpg', '')
            engine = create_engine(sync_database_url)
            
            # Create tables first
            CasbinBase.metadata.create_all(engine)
            
            # RBAC Enforcer
            rbac_adapter = Adapter(engine, CasbinRBACRule)
            self.rbac_enforcer = casbin.Enforcer(
                'app/casbin/rbac_model.conf',
                rbac_adapter
            )
            self.rbac_enforcer.load_policy()
            
            # ABAC Enforcer
            abac_adapter = Adapter(engine, CasbinABACRule)
            self.abac_enforcer = casbin.Enforcer(
                'app/casbin/abac_model.conf',
                abac_adapter
            )
            self.abac_enforcer.load_policy()
            
            # ReBAC Enforcer
            rebac_adapter = Adapter(engine, CasbinReBACRule)
            self.rebac_enforcer = casbin.Enforcer(
                'app/casbin/rebac_model.conf',
                rebac_adapter
            )
            self.rebac_enforcer.load_policy()
            
            print("✅ All Casbin enforcers initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing Casbin enforcer: {e}")
            # Try fallback approach
            await self._initialize_fallback()
    
    async def _initialize_fallback(self):
        """Fallback initialization using single adapter"""
        try:
            sync_database_url = settings.DATABASE_URL.replace('+asyncpg', '')
            engine = create_engine(sync_database_url)
            
            # Use default adapter (single table for all)
            from casbin_sqlalchemy_adapter import CasbinRule
            CasbinRule.metadata.create_all(engine)
            adapter = Adapter(engine)
            
            # Initialize all enforcers with same adapter
            self.rbac_enforcer = casbin.Enforcer('app/casbin/rbac_model.conf', adapter)
            self.abac_enforcer = casbin.Enforcer('app/casbin/abac_model.conf', adapter)
            self.rebac_enforcer = casbin.Enforcer('app/casbin/rebac_model.conf', adapter)
            
            # Load policies
            self.rbac_enforcer.load_policy()
            self.abac_enforcer.load_policy()
            self.rebac_enforcer.load_policy()
            
            print("✅ Casbin enforcers initialized with fallback method")
            
        except Exception as e:
            print(f"❌ Fallback initialization also failed: {e}")
            raise
    
    def check_rbac_permission(self, user: str, resource: str, action: str) -> bool:
        """Check RBAC permission"""
        if not self.rbac_enforcer:
            raise Exception("RBAC enforcer not initialized")
        return self.rbac_enforcer.enforce(user, resource, action)
    
    def check_abac_permission(self, attributes: dict, resource: str, action: str) -> bool:
        """Check ABAC permission with attributes"""
        if not self.abac_enforcer:
            raise Exception("ABAC enforcer not initialized")
        subject_rule = self._build_abac_rule(attributes)
        return self.abac_enforcer.enforce(subject_rule, resource, action)
    
    def check_rebac_permission(self, user: str, resource: str, action: str) -> bool:
        """Check ReBAC permission (relationship-based)"""
        if not self.rebac_enforcer:
            raise Exception("ReBAC enforcer not initialized")
        return self.rebac_enforcer.enforce(user, resource, action)
    
    def _build_abac_rule(self, attributes: dict) -> str:
        """Build ABAC rule from attributes"""
        conditions = []
        for key, value in attributes.items():
            if isinstance(value, str):
                conditions.append(f"r.sub.{key} == '{value}'")
            else:
                conditions.append(f"r.sub.{key} == {value}")
        return " && ".join(conditions) if conditions else "true"
    
    # RBAC Management Methods
    def add_role_for_user(self, user: str, role: str) -> bool:
        """Add a role to a user"""
        return self.rbac_enforcer.add_grouping_policy(user, role)
    
    def delete_role_for_user(self, user: str, role: str) -> bool:
        """Remove a role from a user"""
        return self.rbac_enforcer.remove_grouping_policy(user, role)
    
    def get_roles_for_user(self, user: str) -> list:
        """Get all roles for a user"""
        return self.rbac_enforcer.get_roles_for_user(user)
    
    def get_users_for_role(self, role: str) -> list:
        """Get all users with a specific role"""
        return self.rbac_enforcer.get_users_for_role(role)
    
    def add_permission_for_role(self, role: str, resource: str, action: str) -> bool:
        """Add a permission to a role"""
        return self.rbac_enforcer.add_policy(role, resource, action)
    
    def delete_permission_for_role(self, role: str, resource: str, action: str) -> bool:
        """Remove a permission from a role"""
        return self.rbac_enforcer.remove_policy(role, resource, action)
    
    def get_permissions_for_role(self, role: str) -> list:
        """Get all permissions for a role"""
        return self.rbac_enforcer.get_permissions_for_user(role)
    
    # ReBAC Management Methods
    def add_resource_relationship(self, resource: str, parent_resource: str) -> bool:
        """Add a resource relationship (for ReBAC)"""
        return self.rebac_enforcer.add_grouping_policy(resource, parent_resource)
    
    def delete_resource_relationship(self, resource: str, parent_resource: str) -> bool:
        """Remove a resource relationship"""
        return self.rebac_enforcer.remove_grouping_policy(resource, parent_resource)
    
    async def save_policy(self):
        """Save all policies to database"""
        if self.rbac_enforcer:
            self.rbac_enforcer.save_policy()
        if self.abac_enforcer:
            self.abac_enforcer.save_policy()
        if self.rebac_enforcer:
            self.rebac_enforcer.save_policy()

# Global enforcer instance
casbin_enforcer = CasbinEnforcer()