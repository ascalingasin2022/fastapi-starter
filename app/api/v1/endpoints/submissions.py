from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import get_current_active_user
from app.repositories.forms import FormSubmissionRepository, FormTemplateRepository
from app.schemas.forms import (
    ValidateSubmissionRequest, 
    ValidationResult, 
    FormSubmissionCreate, 
    FormSubmissionResponse,
    FormSubmissionListResponse
)
from app.services.form_validation import FormValidationService
from app.models.user import User

router = APIRouter()

@router.post("/validate", response_model=ValidationResult)
async def validate_submission(
    request: ValidateSubmissionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Validate a form submission against its template schema.
    Does not save to database.
    """
    template = await FormTemplateRepository.get_by_id(db, request.template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form template not found"
        )
        
    result = FormValidationService.validate_submission(request.submission_data, template.json_schema)
    return result

@router.post("/", response_model=FormSubmissionResponse)
async def create_submission(
    submission_in: FormSubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a new form submission (Draft or Final).
    """
    template = await FormTemplateRepository.get_by_id(db, submission_in.template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form template not found"
        )
        
    # Validate payload
    # Note: We allow saving invalid drafts, but we flag them
    validation_result = FormValidationService.validate_submission(submission_in.submission_data, template.json_schema)
    
    # Prepare data
    data = submission_in.model_dump()
    data["submitted_by"] = current_user.username
    data["is_valid"] = validation_result.is_valid
    # Serialize errors list to dict/json if needed or store as is if model supports it. 
    # FormSubmission model column is JSONB. Pydantic list[ValidationError] -> list[dict] automatically via model_dump?
    # ValidationError is pydantic model.
    data["validation_errors"] = [e.model_dump() for e in validation_result.errors] if validation_result.errors else []
    
    submission = await FormSubmissionRepository.create(db, **data)
    return submission

@router.get("/", response_model=FormSubmissionListResponse)
async def read_submissions(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    template_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    List form submissions.
    """
    offset = (page - 1) * page_size
    
    # TODO: Admin can see all? Regular user only sees own?
    # For now, simplistic: everyone sees their own, unless admin (not implemented check)
    # Let's enforce own only for now
    submitted_by = current_user.username
    
    submissions = await FormSubmissionRepository.get_all(
        db, 
        submitted_by=submitted_by, 
        status=status, 
        template_id=template_id,
        limit=page_size,
        offset=offset
    )
    
    total = await FormSubmissionRepository.count(
        db, 
        submitted_by=submitted_by, 
        status=status, 
        template_id=template_id
    )
    
    return {
        "data": submissions,
        "total": total,
        "page": page,
        "page_size": page_size
    }
