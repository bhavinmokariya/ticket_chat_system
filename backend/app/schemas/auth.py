from pydantic import BaseModel, EmailStr, Field
from typing import Optional,List
from datetime import datetime

#auth request schema

class CustomerRegisterRequest(BaseModel):
    name: str = Field(...,min_length=2,max_length=100,description="full name")
    email: EmailStr = Field(...,description="valid email address")
    password : str = Field(...,min_length=6,description="min 6 char")



class LoginRequest(BaseModel):
    email : EmailStr
    password : str

class RefreshTokenRequest(BaseModel):
    refresh_token : str

#auth response schema

class TokenResponse(BaseModel):
    access_token : str
    refresh_token : str
    token_type : str = "bearer"
    role : str
    name : str

class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str

#customer schema

class CustomerResponse(BaseModel):
    customer_id: int
    name: str
    email: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    role: str = "customer"

# Support Engineer Schemas

class SupportEngineerResponse(BaseModel):
    support_id: int
    name: str
    email: str
    role_id: int
    department: str
    is_active: bool
    is_online: bool
    last_seen: Optional[datetime] = None
    created_at: datetime

class CreateSupportEngineerRequest(BaseModel):
    """Schema for creating a new support engineer by admin."""
    name: str = Field(..., min_length=2, max_length=100, description="Full name")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, description="Minimum 6 characters")
    department: str = Field(..., min_length=2, max_length=100, description="Department name")
    role_id: int = Field(2, description="Role ID: 1=admin, 2=support")

# Role Schemas
class RoleResponse(BaseModel):
    role_id: int
    role_name: str
    permissions: List[str]