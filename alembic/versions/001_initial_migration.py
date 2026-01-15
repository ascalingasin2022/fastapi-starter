"""Initial migration - Users, Roles, Permissions, Casbin tables

Revision ID: 001
Revises: 
Create Date: 2026-01-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True, default=False),
        sa.Column('department', sa.String(), nullable=True),
        sa.Column('level', sa.Integer(), nullable=True, default=1),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)

    # Create permissions table
    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('resource', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create user_roles association table
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    # Create resource_relationships table for ReBAC
    op.create_table(
        'resource_relationships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=False),
        sa.Column('parent_resource_type', sa.String(), nullable=False),
        sa.Column('parent_resource_id', sa.String(), nullable=False),
        sa.Column('relationship_type', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Casbin RBAC rules table
    op.create_table(
        'casbin_rbac_rule',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ptype', sa.String(255), nullable=True),
        sa.Column('v0', sa.String(255), nullable=True),
        sa.Column('v1', sa.String(255), nullable=True),
        sa.Column('v2', sa.String(255), nullable=True),
        sa.Column('v3', sa.String(255), nullable=True),
        sa.Column('v4', sa.String(255), nullable=True),
        sa.Column('v5', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Casbin ABAC rules table
    op.create_table(
        'casbin_abac_rule',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ptype', sa.String(255), nullable=True),
        sa.Column('v0', sa.String(255), nullable=True),
        sa.Column('v1', sa.String(255), nullable=True),
        sa.Column('v2', sa.String(255), nullable=True),
        sa.Column('v3', sa.String(255), nullable=True),
        sa.Column('v4', sa.String(255), nullable=True),
        sa.Column('v5', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Casbin ReBAC rules table
    op.create_table(
        'casbin_rebac_rule',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ptype', sa.String(255), nullable=True),
        sa.Column('v0', sa.String(255), nullable=True),
        sa.Column('v1', sa.String(255), nullable=True),
        sa.Column('v2', sa.String(255), nullable=True),
        sa.Column('v3', sa.String(255), nullable=True),
        sa.Column('v4', sa.String(255), nullable=True),
        sa.Column('v5', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('casbin_rebac_rule')
    op.drop_table('casbin_abac_rule')
    op.drop_table('casbin_rbac_rule')
    op.drop_table('resource_relationships')
    op.drop_table('user_roles')
    op.drop_table('permissions')
    op.drop_index(op.f('ix_roles_id'), table_name='roles')
    op.drop_index(op.f('ix_roles_name'), table_name='roles')
    op.drop_table('roles')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')