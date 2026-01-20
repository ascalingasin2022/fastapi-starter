from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import get_current_active_user, get_current_superuser
from app.repositories.forms import FormTemplateRepository, BankRepository
from app.schemas.forms import FormTemplateResponse, FormTemplateCreate, FormTemplateUpdate
from app.models.user import User

router = APIRouter()

@router.get("/bank/{bank_id}", response_model=List[FormTemplateResponse])
async def read_templates_by_bank(
    bank_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve form templates for a specific bank.
    """
    bank = await BankRepository.get_by_id(db, bank_id)
    if not bank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank not found"
        )
        
    templates = await FormTemplateRepository.get_all_by_bank(db, bank_id, active_only=True)
    return templates

@router.get("/{template_id}", response_model=FormTemplateResponse)
async def read_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get a specific Form Template by ID.
    """
    template = await FormTemplateRepository.get_by_id(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form template not found"
        )
    return template

@router.post("/", response_model=FormTemplateResponse)
async def create_template(
    *,
    db: AsyncSession = Depends(get_db),
    template_in: FormTemplateCreate,
    current_user: User = Depends(get_current_superuser)
) -> Any:
    """
    Create a new Form Template.
    Only superusers can create templates.
    """
    # Check if bank exists
    bank = await BankRepository.get_by_id(db, template_in.bank_id)
    if not bank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank not found"
        )
        
    # Check if version exists
    exists = await FormTemplateRepository.check_version_exists(
        db, template_in.bank_id, template_in.form_type, template_in.version
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template with this version already exists for the bank"
        )
        
    template = await FormTemplateRepository.create(db, **template_in.model_dump())
    return template
