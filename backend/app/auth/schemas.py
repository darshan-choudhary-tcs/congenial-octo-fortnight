"""
Pydantic schemas for authentication
"""
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    company: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    company: Optional[str] = None
    preferred_llm: Optional[str] = None
    explainability_level: Optional[str] = None

class UserInDB(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    roles: List[str] = []
    preferred_llm: str
    explainability_level: str

    class Config:
        from_attributes = True

class UserResponse(UserInDB):
    permissions: List[str] = []

class AdminOnboardRequest(BaseModel):
    """Schema for onboarding a new admin user by super admin"""
    email: EmailStr
    company: str = Field(..., min_length=2, max_length=200)
    name: str = Field(..., min_length=2, max_length=100)

class AdminOnboardResponse(BaseModel):
    """Response after admin onboarding with auto-generated password"""
    id: int
    username: str
    email: EmailStr
    name: str
    company: str
    password: str  # Auto-generated password
    roles: List[str]
    message: str

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleResponse(RoleBase):
    id: int
    permissions: List[str] = []

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

class AdminSetupRequest(BaseModel):
    """Schema for admin first-time setup with company profile"""
    industry: str = Field(..., description="Industry type: ITeS, Manufacturing, or Hospitality")
    location: str = Field(..., min_length=2, max_length=200)
    sustainability_target_kp1: int = Field(..., description="Target year for zero non-renewable energy", gt=2024, lt=2100)
    sustainability_target_kp2: float = Field(..., description="Percentage increase in renewable mix", ge=0, le=100)
    budget: float = Field(..., description="Budget amount", gt=0)
    historical_data_filename: Optional[str] = Field(None, description="Filename of uploaded CSV file")

    class Config:
        json_schema_extra = {
            "example": {
                "industry": "ITeS",
                "location": "Mumbai, India",
                "sustainability_target_kp1": 2030,
                "sustainability_target_kp2": 75.0,
                "budget": 1000000.0,
                "historical_data_filename": "historical_data.csv"
            }
        }

class ProfileResponse(BaseModel):
    """Response schema for company profile"""
    id: int
    user_id: int
    industry: str
    location: str
    sustainability_target_kp1: int
    sustainability_target_kp2: float
    budget: float
    historical_data_path: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SetupCompleteResponse(BaseModel):
    """Response after completing admin setup"""
    message: str
    profile: ProfileResponse
    company_database: str
