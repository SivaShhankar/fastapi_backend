from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    pan_number: Optional[str] = None
    aadhar_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    annual_income: Optional[int] = None
    employment_type: Optional[str] = None
    employer_name: Optional[str] = None


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    is_verified: bool
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    pan_number: Optional[str] = None
    aadhar_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    annual_income: Optional[int] = None
    employment_type: Optional[str] = None
    employer_name: Optional[str] = None
    profile_image: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v
