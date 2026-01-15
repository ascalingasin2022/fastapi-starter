import casbin
from casbin_sqlalchemy_adapter import Adapter, CasbinRule
from sqlalchemy import create_engine
from app.core.config import settings
import asyncio

class CasbinEnforcer:
    def __init__(self):
        self.rbac_enforcer = None
        self.abac_enforcer = None
        self.rebac_enforcer = None
        
    async def initialize(self):
        """Initialize all Casbin enforcers with PostgreSQL adapter"""
        try:
            # Run in thread pool since Casbin operations are synchronous
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._initialize_sync)
            
        except Exception as e:
            print(f"❌ Error initializing Casbin enforcer: {e}")
            # Try fallback approach
            await self._initialize_fallback()
    
    def _initialize_sync(self):
        """Synchronous initialization of Casbin enforcers"""
        try:
            # Database connection - use sync URL
            sync_database_url = settings.DATABASE_URL.replace('+asyncpg', '+psycopg2')
            if not sync_database_url.startswith('postgresql+psycopg2'):
                sync_database_url = sync_database_url.replace('postgresql://', 'postgresql+psycopg2://')
            
            engine = create_engine(sync_database_url, pool_pre_ping=True)
            
            # Use default CasbinRule for all enforcers (simpler approach)
            CasbinRule.metadata.create_all(engine)
            
            # Create separate adapters for each enforcer with different table names
            # For now, use default adapter - policies will be separated by ptype
            rbac_adapter = Adapter(engine)
            self.rbac_enforcer = casbin.Enforcer(
                'app/casbin/rbac_model.conf',
                rbac_adapter
            )
            # Set auto-save
            self.rbac_enforcer.enable_auto_save(True)
            self.rbac_enforcer.load_policy()
            
            # ABAC Enforcer
            abac_adapter = Adapter(engine)
            self.abac_enforcer = casbin.Enforcer(
                'app/casbin/abac_model.conf',
                abac_adapter
            )
            self.abac_enforcer.enable_auto_save(True)
            self.abac_enforcer.load_policy()
            
            # ReBAC Enforcer  
            rebac_adapter = Adapter(engine)
            self.rebac_enforcer = casbin.Enforcer(
                'app/casbin/rebac_model.conf',
                rebac_adapter
            )
            self.rebac_enforcer.enable_auto_save(True)
            self.rebac_enforcer.load_policy()
            
            print("✅ All Casbin enforcers initialized successfully")
            
        except Exception as e:
            print(f"❌ Error in sync initialization: {e}")
            raise
    
    async def _initialize_fallback(self):
        """Fallback initialization using single adapter"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._initialize_fallback_sync)
        except Exception as e:
            print(f"❌ Fallback initialization also failed: {e}")
            raise
    
    def _initialize_fallback_sync(self):
        """Synchronous fallback initialization"""
        try:
            # Try with psycopg2
            sync_database_url = settings.DATABASE_URL.replace('+asyncpg', '+psycopg2')
            if not sync_database_url.startswith('postgresql+psycopg2'):
                sync_database_url = sync_database_url.replace('postgresql://', 'postgresql+psycopg2://')
            
            engine = create_engine(sync_database_url, pool_pre_ping=True)
            
            # Use default adapter (single table for all)
            CasbinRule.metadata.create_all(engine)
            adapter = Adapter(engine)
            
            # Initialize all enforcers with same adapter
            self.rbac_enforcer = casbin.Enforcer('app/casbin/rbac_model.conf', adapter)
            self.abac_enforcer = casbin.Enforcer('app/casbin/abac_model.conf', adapter)
            self.rebac_enforcer = casbin.Enforcer('app/casbin/rebac_model.conf', adapter)
            
            # Enable auto-save
            self.rbac_enforcer.enable_auto_save(True)
            self.abac_enforcer.enable_auto_save(True)
            self.rebac_enforcer.enable_auto_save(True)
            
            # Load policies
            self.rbac_enforcer.load_policy()
            self.abac_enforcer.load_policy()
            self.rebac_enforcer.load_policy()
            
            print("✅ Casbin enforcers initialized with fallback method")
            
        except Exception as e:
            print(f"❌ Fallback sync initialization failed: {e}")
            raise
    
    def check_rbac_permission(self, user: str, resource: str, action: str) -> bool:
        """Check RBAC permission (sync operation)"""
        if not self.rbac_enforcer:
            raise Exception("RBAC enforcer not initialized")
        try:
            return self.rbac_enforcer.enforce(user, resource, action)
        except Exception as e:
            print(f"Error checking RBAC permission: {e}")
            return False
    
    async def check_rbac_permission_async(self, user: str, resource: str, action: str) -> bool:
        """Check RBAC permission (async wrapper)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.check_rbac_permission, user, resource, action)
    
    def check_abac_permission(self, attributes: dict, resource: str, action: str) -> bool:
        """Check ABAC permission with attributes (sync operation)"""
        if not self.abac_enforcer:
            raise Exception("ABAC enforcer not initialized")
        try:
            # For ABAC, we need to create a subject object from attributes
            # The matcher will evaluate these attributes
            # Create a simple object-like structure for evaluation
            class Subject:
                def __init__(self, attrs):
                    for k, v in attrs.items():
                        setattr(self, k, v)
                    # Ensure boolean is set properly
                    if hasattr(self, 'is_superuser'):
                        self.is_superuser = bool(self.is_superuser)
                    # Ensure level is integer
                    if hasattr(self, 'level'):
                        self.level = int(self.level) if self.level else 1
            
            subject = Subject(attributes)
            return self.abac_enforcer.enforce(subject, resource, action)
        except Exception as e:
            print(f"Error checking ABAC permission: {e}")
            # If ABAC check fails, fall back to superuser check
            if attributes.get('is_superuser'):
                return True
            return False
    
    async def check_abac_permission_async(self, attributes: dict, resource: str, action: str) -> bool:
        """Check ABAC permission (async wrapper)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.check_abac_permission, attributes, resource, action)
    
    def check_rebac_permission(self, user: str, resource: str, action: str) -> bool:
        """Check ReBAC permission (relationship-based) (sync operation)"""
        if not self.rebac_enforcer:
            raise Exception("ReBAC enforcer not initialized")
        try:
            return self.rebac_enforcer.enforce(user, resource, action)
        except Exception as e:
            print(f"Error checking ReBAC permission: {e}")
            return False
    
    async def check_rebac_permission_async(self, user: str, resource: str, action: str) -> bool:
        """Check ReBAC permission (async wrapper)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.check_rebac_permission, user, resource, action)
    
    def _build_abac_rule(self, attributes: dict) -> str:
        """Build ABAC rule from attributes"""
        conditions = []
        for key, value in attributes.items():
            if isinstance(value, str):
                conditions.append(f"r.sub.{key} == '{value}'")
            else:
                conditions.append(f"r.sub.{key} == {value}")
        return " && ".join(conditions) if conditions else "true"
    
    # RBAC Management Methods (sync)
    def add_role_for_user(self, user: str, role: str) -> bool:
        """Add a role to a user"""
        if not self.rbac_enforcer:
            raise Exception("RBAC enforcer not initialized")
        result = self.rbac_enforcer.add_grouping_policy(user, role)
        if result:
            self.rbac_enforcer.save_policy()
        return result
    
    def delete_role_for_user(self, user: str, role: str) -> bool:
        """Remove a role from a user"""
        if not self.rbac_enforcer:
            raise Exception("RBAC enforcer not initialized")
        result = self.rbac_enforcer.remove_grouping_policy(user, role)
        if result:
            self.rbac_enforcer.save_policy()
        return result
    
    def get_roles_for_user(self, user: str) -> list:
        """Get all roles for a user"""
        if not self.rbac_enforcer:
            raise Exception("RBAC enforcer not initialized")
        return self.rbac_enforcer.get_roles_for_user(user)
    
    def get_users_for_role(self, role: str) -> list:
        """Get all users with a specific role"""
        if not self.rbac_enforcer:
            raise Exception("RBAC enforcer not initialized")
        return self.rbac_enforcer.get_users_for_role(role)
    
    def add_permission_for_role(self, role: str, resource: str, action: str) -> bool:
        """Add a permission to a role"""
        if not self.rbac_enforcer:
            raise Exception("RBAC enforcer not initialized")
        result = self.rbac_enforcer.add_policy(role, resource, action)
        if result:
            self.rbac_enforcer.save_policy()
        return result
    
    def delete_permission_for_role(self, role: str, resource: str, action: str) -> bool:
        """Remove a permission from a role"""
        if not self.rbac_enforcer:
            raise Exception("RBAC enforcer not initialized")
        result = self.rbac_enforcer.remove_policy(role, resource, action)
        if result:
            self.rbac_enforcer.save_policy()
        return result
    
    def get_permissions_for_role(self, role: str) -> list:
        """Get all permissions for a role"""
        if not self.rbac_enforcer:
            raise Exception("RBAC enforcer not initialized")
        return self.rbac_enforcer.get_permissions_for_user(role)
    
    # ReBAC Management Methods
    def add_resource_relationship(self, resource: str, parent_resource: str) -> bool:
        """Add a resource relationship (for ReBAC)"""
        if not self.rebac_enforcer:
            raise Exception("ReBAC enforcer not initialized")
        result = self.rebac_enforcer.add_grouping_policy(resource, parent_resource)
        if result:
            self.rebac_enforcer.save_policy()
        return result
    
    def delete_resource_relationship(self, resource: str, parent_resource: str) -> bool:
        """Remove a resource relationship"""
        if not self.rebac_enforcer:
            raise Exception("ReBAC enforcer not initialized")
        result = self.rebac_enforcer.remove_grouping_policy(resource, parent_resource)
        if result:
            self.rebac_enforcer.save_policy()
        return result
    
    async def save_policy(self):
        """Save all policies to database (async wrapper)"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._save_policy_sync)
    
    def _save_policy_sync(self):
        """Save all policies to database (sync operation)"""
        try:
            if self.rbac_enforcer:
                self.rbac_enforcer.save_policy()
            if self.abac_enforcer:
                self.abac_enforcer.save_policy()
            if self.rebac_enforcer:
                self.rebac_enforcer.save_policy()
        except Exception as e:
            print(f"Error saving policies: {e}")

# Global enforcer instance
casbin_enforcer = CasbinEnforcer()