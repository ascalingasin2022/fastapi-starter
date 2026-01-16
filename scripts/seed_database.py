"""
Database seeding script to create initial users and RBAC policies
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal, engine
from app.db.base_class import Base
from app.models.user import User, Role
from app.core.security import get_password_hash
from app.core.casbin_enforcer import casbin_enforcer


async def create_tables():
    """Create all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created")


async def create_roles():
    """Create initial roles"""
    async with AsyncSessionLocal() as session:
        roles_data = [
            {"name": "admin", "description": "Administrator with full access"},
            {"name": "manager", "description": "Manager with elevated permissions"},
            {"name": "user", "description": "Regular user"},
            {"name": "moderator", "description": "Moderator with content management permissions"},
        ]
        
        for role_data in roles_data:
            from sqlalchemy import select
            result = await session.execute(
                select(Role).where(Role.name == role_data["name"])
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                role = Role(**role_data)
                session.add(role)
        
        await session.commit()
        print("✅ Roles created")


async def create_users():
    """Create initial users with different roles and attributes"""
    async with AsyncSessionLocal() as session:
        users_data = [
            {
                "email": "admin@example.com",
                "username": "admin",
                "password": "Admin123!",
                "full_name": "Administrator User",
                "is_superuser": True,
                "is_active": True,
                "department": "IT",
                "level": 10,
                "location": "HQ",
                "roles": ["admin"]
            },
            {
                "email": "manager@example.com",
                "username": "manager",
                "password": "Manager123!",
                "full_name": "Manager User",
                "is_superuser": False,
                "is_active": True,
                "department": "Engineering",
                "level": 7,
                "location": "US",
                "roles": ["manager"]
            },
            {
                "email": "john.doe@example.com",
                "username": "johndoe",
                "password": "User123!",
                "full_name": "John Doe",
                "is_superuser": False,
                "is_active": True,
                "department": "Engineering",
                "level": 5,
                "location": "US",
                "roles": ["user"]
            },
            {
                "email": "jane.smith@example.com",
                "username": "janesmith",
                "password": "User123!",
                "full_name": "Jane Smith",
                "is_superuser": False,
                "is_active": True,
                "department": "Sales",
                "level": 3,
                "location": "EU",
                "roles": ["user"]
            },
            {
                "email": "moderator@example.com",
                "username": "moderator",
                "password": "Moderator123!",
                "full_name": "Moderator User",
                "is_superuser": False,
                "is_active": True,
                "department": "Content",
                "level": 6,
                "location": "US",
                "roles": ["moderator"]
            },
        ]
        
        for user_data in users_data:
            roles = user_data.pop("roles", [])
            password = user_data.pop("password")
            
            # Check if user exists
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.email == user_data["email"])
            )
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                user = User(
                    **user_data,
                    hashed_password=get_password_hash(password)
                )
                session.add(user)
                await session.flush()  # Flush to get user ID
                
                # Assign roles
                if roles:
                    result = await session.execute(
                        select(Role).where(Role.name.in_(roles))
                    )
                    user_roles = result.scalars().all()
                    user.roles.extend(user_roles)
        
        await session.commit()
        print("✅ Users created")


async def setup_casbin_policies():
    """Set up initial Casbin RBAC policies"""
    print("Setting up Casbin policies...")
    
    # Wait for Casbin to be initialized
    if not casbin_enforcer.rbac_enforcer:
        await casbin_enforcer.initialize()
    
    # Admin permissions - full access
    casbin_enforcer.add_permission_for_role("admin", "users", "read")
    casbin_enforcer.add_permission_for_role("admin", "users", "write")
    casbin_enforcer.add_permission_for_role("admin", "users", "delete")
    casbin_enforcer.add_permission_for_role("admin", "roles", "read")
    casbin_enforcer.add_permission_for_role("admin", "roles", "assign")
    casbin_enforcer.add_permission_for_role("admin", "roles", "revoke")
    casbin_enforcer.add_permission_for_role("admin", "permissions", "read")
    casbin_enforcer.add_permission_for_role("admin", "permissions", "assign")
    casbin_enforcer.add_permission_for_role("admin", "permissions", "check")
    
    # Manager permissions
    casbin_enforcer.add_permission_for_role("manager", "users", "read")
    casbin_enforcer.add_permission_for_role("manager", "users", "write")
    casbin_enforcer.add_permission_for_role("manager", "roles", "read")
    casbin_enforcer.add_permission_for_role("manager", "permissions", "read")
    
    # Moderator permissions
    casbin_enforcer.add_permission_for_role("moderator", "content", "read")
    casbin_enforcer.add_permission_for_role("moderator", "content", "write")
    casbin_enforcer.add_permission_for_role("moderator", "content", "moderate")
    
    # User permissions
    casbin_enforcer.add_permission_for_role("user", "profile", "read")
    casbin_enforcer.add_permission_for_role("user", "profile", "write")
    casbin_enforcer.add_permission_for_role("user", "content", "read")
    
    # Assign roles to users
    casbin_enforcer.add_role_for_user("admin", "admin")
    casbin_enforcer.add_role_for_user("manager", "manager")
    casbin_enforcer.add_role_for_user("johndoe", "user")
    casbin_enforcer.add_role_for_user("janesmith", "user")
    casbin_enforcer.add_role_for_user("moderator", "moderator")
    
    await casbin_enforcer.save_policy()
    print("✅ Casbin policies created")


async def setup_abac_examples():
    """Set up example ABAC policies and attributes"""
    from app.models.abac import ABACPolicy, UserAttribute, ResourceAttribute
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        # Create ABAC policies
        policies = [
            {
                "name": "Engineering Read Access",
                "description": "Engineers can read engineering documents",
                "rules": {
                    "conditions": [
                        {"attribute": "department", "operator": "equals", "value": "Engineering"}
                    ],
                    "permissions": {"resource": "documents", "action": "read"}
                },
                "is_active": True
            },
            {
                "name": "High Level Write Access",
                "description": "Users with level >= 7 can write documents",
                "rules": {
                    "conditions": [
                        {"attribute": "level", "operator": ">=", "value": 7}
                    ],
                    "permissions": {"resource": "documents", "action": "write"}
                },
                "is_active": True
            },
            {
                "name": "HQ Delete Access",
                "description": "Users at HQ location can delete any resource",
                "rules": {
                    "conditions": [
                        {"attribute": "location", "operator": "equals", "value": "HQ"}
                    ],
                    "permissions": {"resource": "*", "action": "delete"}
                },
                "is_active": True
            }
        ]
        
        for policy_data in policies:
            result = await session.execute(
                select(ABACPolicy).where(ABACPolicy.name == policy_data["name"])
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                policy = ABACPolicy(**policy_data)
                session.add(policy)
        
        await session.commit()
        
        # Add user attributes
        user_attributes = [
            {"user_id": 1, "attribute_key": "clearance_level", "attribute_value": "10"},  # admin
            {"user_id": 1, "attribute_key": "team", "attribute_value": "infrastructure"},
            {"user_id": 2, "attribute_key": "clearance_level", "attribute_value": "7"},   # manager
            {"user_id": 2, "attribute_key": "team", "attribute_value": "engineering-mgmt"},
            {"user_id": 3, "attribute_key": "clearance_level", "attribute_value": "5"},   # johndoe
            {"user_id": 3, "attribute_key": "team", "attribute_value": "backend"},
            {"user_id": 4, "attribute_key": "clearance_level", "attribute_value": "3"},   # janesmith
            {"user_id": 4, "attribute_key": "team", "attribute_value": "sales"},
        ]
        
        for attr_data in user_attributes:
            result = await session.execute(
                select(UserAttribute).where(
                    UserAttribute.user_id == attr_data["user_id"],
                    UserAttribute.attribute_key == attr_data["attribute_key"]
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                attribute = UserAttribute(**attr_data)
                session.add(attribute)
        
        await session.commit()
        
        # Add resource attributes
        resource_attributes = [
            {"resource_type": "document", "resource_id": "doc_001", "attribute_key": "sensitivity", "attribute_value": "high"},
            {"resource_type": "document", "resource_id": "doc_001", "attribute_key": "department", "attribute_value": "Engineering"},
            {"resource_type": "document", "resource_id": "doc_002", "attribute_key": "sensitivity", "attribute_value": "low"},
            {"resource_type": "document", "resource_id": "doc_002", "attribute_key": "department", "attribute_value": "Sales"},
            {"resource_type": "project", "resource_id": "proj_001", "attribute_key": "status", "attribute_value": "active"},
            {"resource_type": "project", "resource_id": "proj_001", "attribute_key": "department", "attribute_value": "Engineering"},
        ]
        
        for attr_data in resource_attributes:
            result = await session.execute(
                select(ResourceAttribute).where(
                    ResourceAttribute.resource_type == attr_data["resource_type"],
                    ResourceAttribute.resource_id == attr_data["resource_id"],
                    ResourceAttribute.attribute_key == attr_data["attribute_key"]
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                attribute = ResourceAttribute(**attr_data)
                session.add(attribute)
        
        await session.commit()
        print("✅ ABAC policies and attributes created")


async def setup_rebac_examples():
    """Set up example ReBAC relationships"""
    from app.models.user import ResourceRelationship
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        relationships = [
            # Admin owns Project 1
            {
                "subject_type": "user",
                "subject_id": "admin",
                "resource_type": "project",
                "resource_id": "proj_001",
                "parent_resource_type": "organization",
                "parent_resource_id": "org_001",
                "relationship_type": "owner_of"
            },
            # Project 1 contains Document 1
            {
                "subject_type": "resource",
                "subject_id": "project:proj_001",
                "resource_type": "document",
                "resource_id": "doc_001",
                "parent_resource_type": "project",
                "parent_resource_id": "proj_001",
                "relationship_type": "parent_of"
            },
            # Manager is member of Project 1
            {
                "subject_type": "user",
                "subject_id": "manager",
                "resource_type": "project",
                "resource_id": "proj_001",
                "parent_resource_type": "organization",
                "parent_resource_id": "org_001",
                "relationship_type": "member_of"
            },
            # John Doe manages Document 2
            {
                "subject_type": "user",
                "subject_id": "johndoe",
                "resource_type": "document",
                "resource_id": "doc_002",
                "parent_resource_type": "project",
                "parent_resource_id": "proj_002",
                "relationship_type": "manages"
            }
        ]
        
        for rel_data in relationships:
            result = await session.execute(
                select(ResourceRelationship).where(
                    ResourceRelationship.subject_type == rel_data["subject_type"],
                    ResourceRelationship.subject_id == rel_data["subject_id"],
                    ResourceRelationship.resource_type == rel_data["resource_type"],
                    ResourceRelationship.resource_id == rel_data["resource_id"]
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                relationship = ResourceRelationship(**rel_data)
                session.add(relationship)
        
        await session.commit()
        print("✅ ReBAC relationships created")


async def main():
    """Main seeding function"""
    print("🌱 Starting database seeding...")
    
    try:
        await create_tables()
        await create_roles()
        await create_users()
        await setup_casbin_policies()
        await setup_abac_examples()
        await setup_rebac_examples()
        
        print("\n✅ Database seeding completed successfully!")
        print("\n📋 Created users:")
        print("  1. admin@example.com / admin (Password: Admin123!) - Admin role")
        print("  2. manager@example.com / manager (Password: Manager123!) - Manager role")
        print("  3. john.doe@example.com / johndoe (Password: User123!) - User role")
        print("  4. jane.smith@example.com / janesmith (Password: User123!) - User role")
        print("  5. moderator@example.com / moderator (Password: Moderator123!) - Moderator role")
        print("\n📋 ABAC Features:")
        print("  - 3 ABAC policies created (Engineering Read, High Level Write, HQ Delete)")
        print("  - User attributes: clearance_level, team")
        print("  - Resource attributes: sensitivity, department, status")
        print("\n📋 ReBAC Features:")
        print("  - admin owns proj_001")
        print("  - proj_001 contains doc_001 (access inherited)")
        print("  - manager is member of proj_001")
        print("  - johndoe manages doc_002")
        print("\n💡 You can now use these credentials to test the API!")
        print("💡 Try the unified authorization endpoint: POST /api/v1/authorization/check")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
