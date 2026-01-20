from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
import uuid


class SubmissionStatus(str, Enum):
    """Form submission status enumeration"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    VALIDATED = "validated"
    REJECTED = "rejected"


class Bank(Base):
    """Bank model for multi-tenant form system"""
    __tablename__ = "banks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    
    # Relationships
    form_templates = relationship("FormTemplate", back_populates="bank", cascade="all, delete-orphan")


class FormTemplate(Base):
    """Form template with JSONSchema validation rules and UI schema"""
    __tablename__ = "form_templates"

    id = Column(Integer, primary_key=True, index=True)
    bank_id = Column(Integer, ForeignKey('banks.id'), nullable=False, index=True)
    form_type = Column(String(100), nullable=False, index=True)  # e.g., "customer_survey", "loan_application"
    version = Column(String(20), nullable=False)  # Semantic versioning: "1.0.0", "1.1.0", etc.
    
    # JSON Schema for validation
    json_schema = Column(JSONB, nullable=False)
    
    # UI Schema for rendering hints
    ui_schema = Column(JSONB, nullable=True)
    
    # Metadata
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_onupdate=func.now())
    created_by = Column(String(100), nullable=True)  # Username of creator
    
    # Relationships
    bank = relationship("Bank", back_populates="form_templates")
    submissions = relationship("FormSubmission", back_populates="template", cascade="all, delete-orphan")
    
    # Unique constraint: One version per bank + form_type combination
    __table_args__ = (
        {'schema': None},
    )


class FormSubmission(Base):
    """Form submission with validation status"""
    __tablename__ = "form_submissions"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey('form_templates.id'), nullable=False, index=True)
    
    # Submission metadata
    submitted_by = Column(String(100), nullable=False, index=True)  # Username or field agent ID
    status = Column(String(20), default=SubmissionStatus.DRAFT, nullable=False, index=True)
    
    # Actual form data (validated against json_schema)
    submission_data = Column(JSONB, nullable=False)
    
    # Validation results
    validation_errors = Column(JSONB, nullable=True)  # Null means valid or not validated yet
    is_valid = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    submitted_at = Column(DateTime(timezone=True), nullable=True)  # When status changed to "submitted"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_onupdate=func.now())
    
    # Relationships
    template = relationship("FormTemplate", back_populates="submissions")
    files = relationship("FormFile", back_populates="submission", cascade="all, delete-orphan")


class FormFile(Base):
    """File metadata for form uploads with token-based access"""
    __tablename__ = "form_files"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey('form_submissions.id'), nullable=True, index=True)
    
    # Field information
    field_name = Column(String(100), nullable=False)  # Which form field this file belongs to
    
    # File metadata
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True)  # UUID-based filename
    file_size = Column(Integer, nullable=False)  # Size in bytes
    mime_type = Column(String(100), nullable=False)
    
    # Security token for access control
    access_token = Column(PG_UUID(as_uuid=True), default=uuid.uuid4, nullable=False, unique=True, index=True)
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    uploaded_by = Column(String(100), nullable=False)  # Username
    
    # Relationships
    submission = relationship("FormSubmission", back_populates="files")
