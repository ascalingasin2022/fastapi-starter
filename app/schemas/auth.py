from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    level: Optional[int] = None
    location: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    department: Optional[str] = None
    level: int = 1
    location: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    department: Optional[str] = None
    level: int
    location: Optional[str] = None
    
    class Config:
        from_attributes = True