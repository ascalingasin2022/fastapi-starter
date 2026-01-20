"""
ABAC (Attribute-Based Access Control) models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class UserAttribute(Base):
    """Store additional attributes for users beyond the core User model"""
    __tablename__ = "user_attributes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    attribute_key = Column(String, nullable=False)
    attribute_value = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to User
    user = relationship("User", back_populates="attributes")


class ResourceAttribute(Base):
    """Store attributes for resources (documents, projects, etc.)"""
    __tablename__ = "resource_attributes"

    id = Column(Integer, primary_key=True, index=True)
    resource_type = Column(String, nullable=False)  # e.g., "document", "project"
    resource_id = Column(String, nullable=False)    # e.g., "doc_123", "proj_456"
    attribute_key = Column(String, nullable=False)  # e.g., "sensitivity", "department"
    attribute_value = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ABACPolicy(Base):
    """ABAC policy definitions with JSON rules"""
    __tablename__ = "abac_policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String)
    rules = Column(JSON, nullable=False)
    # Rules structure example:
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
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
