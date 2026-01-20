"""
Pydantic schemas for form system API requests and responses
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid


# ============================================================================
# Bank Schemas
# ============================================================================

class BankBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Bank name")
    code: str = Field(..., min_length=1, max_length=50, description="Bank code (unique identifier)")
    description: Optional[str] = Field(None, description="Bank description")
    is_active: bool = Field(True, description="Whether the bank is active")


class BankCreate(BankBase):
    """Schema for creating a new bank"""
    pass


class BankUpdate(BaseModel):
    """Schema for updating a bank"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class BankResponse(BankBase):
    """Schema for bank response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Form Template Schemas
# ============================================================================

class FormTemplateBase(BaseModel):
    bank_id: int = Field(..., description="Bank ID this template belongs to")
    form_type: str = Field(..., min_length=1, max_length=100, description="Type of form (e.g., customer_survey)")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$", description="Semantic version (e.g., 1.0.0)")
    json_schema: Dict[str, Any] = Field(..., description="JSONSchema for validation")
    ui_schema: Optional[Dict[str, Any]] = Field(None, description="UI rendering hints")
    title: Optional[str] = Field(None, max_length=255, description="Form title")
    description: Optional[str] = Field(None, description="Form description")
    is_active: bool = Field(True, description="Whether this template version is active")


class FormTemplateCreate(FormTemplateBase):
    """Schema for creating a new form template"""
    created_by: Optional[str] = Field(None, description="Username of creator")


class FormTemplateUpdate(BaseModel):
    """Schema for updating a form template"""
    json_schema: Optional[Dict[str, Any]] = None
    ui_schema: Optional[Dict[str, Any]] = None
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class FormTemplateResponse(FormTemplateBase):
    """Schema for form template response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Form Submission Schemas
# ============================================================================

class FormSubmissionBase(BaseModel):
    template_id: int = Field(..., description="Form template ID")
    submitted_by: str = Field(..., min_length=1, max_length=100, description="Username or agent ID")
    submission_data: Dict[str, Any] = Field(..., description="Form data (must match template schema)")


class FormSubmissionCreate(FormSubmissionBase):
    """Schema for creating a new form submission"""
    status: Optional[str] = Field("draft", description="Submission status")


class FormSubmissionUpdate(BaseModel):
    """Schema for updating a form submission (draft only)"""
    submission_data: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class FormSubmissionResponse(FormSubmissionBase):
    """Schema for form submission response"""
    id: int
    status: str
    validation_errors: Optional[Dict[str, Any]] = None
    is_valid: bool
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# File Schemas
# ============================================================================

class FileUploadResponse(BaseModel):
    """Schema for file upload response"""
    file_id: int
    field_name: str
    original_filename: str
    stored_filename: str
    file_size: int
    mime_type: str
    access_token: uuid.UUID
    uploaded_at: datetime
    message: str = "File uploaded successfully"


class FormFileResponse(BaseModel):
    """Schema for form file metadata"""
    id: int
    submission_id: Optional[int] = None
    field_name: str
    original_filename: str
    stored_filename: str
    file_size: int
    mime_type: str
    access_token: uuid.UUID
    uploaded_at: datetime
    uploaded_by: str
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Validation Schemas
# ============================================================================

class ValidationError(BaseModel):
    """Schema for a  single validation error"""
    field: str = Field(..., description="Field path that failed validation")
    message: str = Field(..., description="Error message")
    constraint: Optional[str] = Field(None, description="Constraint that was violated")


class ValidationResult(BaseModel):
    """Schema for validation result"""
    is_valid: bool
    errors: List[ValidationError] = Field(default_factory=list)
    message: str


class ValidateSubmissionRequest(BaseModel):
    """Schema for submission validation request"""
    template_id: int
    submission_data: Dict[str, Any]


# ============================================================================
# List/Filter Schemas
# ============================================================================

class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    total: int
    page: int
    page_size: int
    data: List[Any]


class BankListResponse(BaseModel):
    """Schema for bank list response"""
    total: int
    data: List[BankResponse]


class FormTemplateListResponse(BaseModel):
    """Schema for form template list response"""
    total: int
    data: List[FormTemplateResponse]


class FormSubmissionListResponse(BaseModel):
    """Schema for form submission list response"""
    total: int
    page: int
    page_size: int
    data: List[FormSubmissionResponse]
