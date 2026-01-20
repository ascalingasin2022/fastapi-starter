"""
Repository layer for form system database operations
Follows existing repository pattern in the codebase
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import joinedload
from app.models.forms import Bank, FormTemplate, FormSubmission, FormFile, SubmissionStatus
from datetime import datetime


class BankRepository:
    """Repository for Bank model CRUD operations"""
    
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> Bank:
        """Create a new bank"""
        bank = Bank(**kwargs)
        db.add(bank)
        await db.commit()
        await db.refresh(bank)
        return bank
    
    @staticmethod
    async def get_by_id(db: AsyncSession, bank_id: int) -> Optional[Bank]:
        """Get bank by ID"""
        result = await db.execute(
            select(Bank).where(and_(Bank.id == bank_id, Bank.deleted_at.is_(None)))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_code(db: AsyncSession, code: str) -> Optional[Bank]:
        """Get bank by code"""
        result = await db.execute(
            select(Bank).where(and_(Bank.code == code, Bank.deleted_at.is_(None)))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all(db: AsyncSession, include_deleted: bool = False) -> List[Bank]:
        """Get all banks"""
        query = select(Bank)
        if not include_deleted:
            query = query.where(Bank.deleted_at.is_(None))
        result = await db.execute(query.order_by(Bank.name))
        return list(result.scalars().all())
    
    @staticmethod
    async def update(db: AsyncSession, bank: Bank, **kwargs) -> Bank:
        """Update bank"""
        for key, value in kwargs.items():
            if value is not None and hasattr(bank, key):
                setattr(bank, key, value)
        await db.commit()
        await db.refresh(bank)
        return bank
    
    @staticmethod
    async def soft_delete(db: AsyncSession, bank: Bank) -> Bank:
        """Soft delete bank"""
        bank.deleted_at = datetime.utcnow()
        bank.is_active = False
        await db.commit()
        await db.refresh(bank)
        return bank


class FormTemplateRepository:
    """Repository for FormTemplate model CRUD operations"""
    
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> FormTemplate:
        """Create a new form template"""
        template = FormTemplate(**kwargs)
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template
    
    @staticmethod
    async def get_by_id(db: AsyncSession, template_id: int) -> Optional[FormTemplate]:
        """Get template by ID"""
        result = await db.execute(
            select(FormTemplate)
            .options(joinedload(FormTemplate.bank))
            .where(FormTemplate.id == template_id)
        )
        return result.unique().scalar_one_or_none()
    
    @staticmethod
    async def get_by_bank_and_type(
        db: AsyncSession, 
        bank_id: int, 
        form_type: str, 
        version: Optional[str] = None
    ) -> Optional[FormTemplate]:
        """Get template by bank, form type, and optionally version"""
        query = select(FormTemplate).where(
            and_(
                FormTemplate.bank_id == bank_id,
                FormTemplate.form_type == form_type
            )
        )
        
        if version:
            query = query.where(FormTemplate.version == version)
        else:
            # Get latest active version
            query = query.where(FormTemplate.is_active == True).order_by(FormTemplate.created_at.desc())
        
        result = await db.execute(query)
        return result.scalar_first()
    
    @staticmethod
    async def get_all_by_bank(
        db: AsyncSession, 
        bank_id: int, 
        active_only: bool = False
    ) -> List[FormTemplate]:
        """Get all templates for a bank"""
        query = select(FormTemplate).where(FormTemplate.bank_id == bank_id)
        
        if active_only:
            query = query.where(FormTemplate.is_active == True)
        
        result = await db.execute(query.order_by(FormTemplate.form_type, FormTemplate.version.desc()))
        return list(result.scalars().all())
    
    @staticmethod
    async def get_all(db: AsyncSession, active_only: bool = False) -> List[FormTemplate]:
        """Get all templates"""
        query = select(FormTemplate).options(joinedload(FormTemplate.bank))
        
        if active_only:
            query = query.where(FormTemplate.is_active == True)
        
        result = await db.execute(query.order_by(FormTemplate.bank_id, FormTemplate.form_type))
        return list(result.unique().scalars().all())
    
    @staticmethod
    async def update(db: AsyncSession, template: FormTemplate, **kwargs) -> FormTemplate:
        """Update template"""
        for key, value in kwargs.items():
            if value is not None and hasattr(template, key):
                setattr(template, key, value)
        await db.commit()
        await db.refresh(template)
        return template
    
    @staticmethod
    async def check_version_exists(
        db: AsyncSession, 
        bank_id: int, 
        form_type: str, 
        version: str
    ) -> bool:
        """Check if a specific version already exists"""
        result = await db.execute(
            select(func.count(FormTemplate.id)).where(
                and_(
                    FormTemplate.bank_id == bank_id,
                    FormTemplate.form_type == form_type,
                    FormTemplate.version == version
                )
            )
        )
        count = result.scalar()
        return count > 0


class FormSubmissionRepository:
    """Repository for FormSubmission model CRUD operations"""
    
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> FormSubmission:
        """Create a new form submission"""
        submission = FormSubmission(**kwargs)
        db.add(submission)
        await db.commit()
        await db.refresh(submission)
        return submission
    
    @staticmethod
    async def get_by_id(db: AsyncSession, submission_id: int) -> Optional[FormSubmission]:
        """Get submission by ID"""
        result = await db.execute(
            select(FormSubmission)
            .options(
                joinedload(FormSubmission.template).joinedload(FormTemplate.bank),
                joinedload(FormSubmission.files)
            )
            .where(FormSubmission.id == submission_id)
        )
        return result.unique().scalar_one_or_none()
    
    @staticmethod
    async def get_all(
        db: AsyncSession,
        submitted_by: Optional[str] = None,
        status: Optional[str] = None,
        template_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[FormSubmission]:
        """Get submissions with optional filters"""
        query = select(FormSubmission).options(
            joinedload(FormSubmission.template).joinedload(FormTemplate.bank)
        )
        
        filters = []
        if submitted_by:
            filters.append(FormSubmission.submitted_by == submitted_by)
        if status:
            filters.append(FormSubmission.status == status)
        if template_id:
            filters.append(FormSubmission.template_id == template_id)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(FormSubmission.created_at.desc()).limit(limit).offset(offset)
        
        result = await db.execute(query)
        return list(result.unique().scalars().all())
    
    @staticmethod
    async def count(
        db: AsyncSession,
        submitted_by: Optional[str] = None,
        status: Optional[str] = None,
        template_id: Optional[int] = None
    ) -> int:
        """Count submissions with optional filters"""
        query = select(func.count(FormSubmission.id))
        
        filters = []
        if submitted_by:
            filters.append(FormSubmission.submitted_by == submitted_by)
        if status:
            filters.append(FormSubmission.status == status)
        if template_id:
            filters.append(FormSubmission.template_id == template_id)
        
        if filters:
            query = query.where(and_(*filters))
        
        result = await db.execute(query)
        return result.scalar()
    
    @staticmethod
    async def update(db: AsyncSession, submission: FormSubmission, **kwargs) -> FormSubmission:
        """Update submission"""
        for key, value in kwargs.items():
            if hasattr(submission, key):
                setattr(submission, key, value)
        await db.commit()
        await db.refresh(submission)
        return submission
    
    @staticmethod
    async def delete(db: AsyncSession, submission: FormSubmission) -> None:
        """Hard delete submission (only for drafts)"""
        if submission.status != SubmissionStatus.DRAFT:
            raise ValueError("Can only delete draft submissions")
        await db.delete(submission)
        await db.commit()
    
    @staticmethod
    async def submit(db: AsyncSession, submission: FormSubmission) -> FormSubmission:
        """Mark submission as submitted"""
        submission.status = SubmissionStatus.SUBMITTED
        submission.submitted_at = datetime.utcnow()
        await db.commit()
        await db.refresh(submission)
        return submission


class FormFileRepository:
    """Repository for FormFile model CRUD operations"""
    
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> FormFile:
        """Create a new form file record"""
        file_record = FormFile(**kwargs)
        db.add(file_record)
        await db.commit()
        await db.refresh(file_record)
        return file_record
    
    @staticmethod
    async def get_by_token(db: AsyncSession, access_token: str) -> Optional[FormFile]:
        """Get file by access token"""
        result = await db.execute(
            select(FormFile).where(FormFile.access_token == access_token)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_submission(db: AsyncSession, submission_id: int) -> List[FormFile]:
        """Get all files for a submission"""
        result = await db.execute(
            select(FormFile)
            .where(FormFile.submission_id == submission_id)
            .order_by(FormFile.uploaded_at)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def delete(db: AsyncSession, file_record: FormFile) -> None:
        """Delete file record"""
        await db.delete(file_record)
        await db.commit()
