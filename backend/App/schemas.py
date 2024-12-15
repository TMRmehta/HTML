from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum

class UserType(str, Enum):
    PATIENT = "PATIENT"
    RESEARCHER = "RESEARCHER"

class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"

# Request Schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str

    class Config:
        from_attributes = True

class UserFind(BaseModel):
    email: EmailStr
    password: str

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    firstname: str
    lastname: str
    email: EmailStr
    password: str
    user_type: UserType

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isalpha() for char in v):
            raise ValueError('Password must contain at least one letter')
        return v

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[EmailStr] = None
    user_type: Optional[UserType] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isalpha() for char in v):
            raise ValueError('Password must contain at least one letter')
        return v

    class Config:
        from_attributes = True

# Response Schemas
class UserRead(BaseModel):
    userid: UUID
    firstname: str
    lastname: str
    email: EmailStr
    user_type: UserType
    is_active: bool
    is_verified: bool
    signup_timestamp: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserProfile(BaseModel):
    userid: UUID
    firstname: str
    lastname: str
    email: EmailStr
    user_type: UserType
    is_verified: bool
    signup_timestamp: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    user_type: Optional[UserType] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

# Activity Log Schemas
class ActivityLogCreate(BaseModel):
    ip_address: str
    user_agent: Optional[str] = None
    action: str = "LOGIN"

class ActivityLogRead(BaseModel):
    log_id: int
    userid: UUID
    ip_address: str
    login_timestamp: datetime
    user_agent: Optional[str] = None
    action: str

    class Config:
        from_attributes = True

# User Log Schemas
class UserLogRead(BaseModel):
    userid: UUID
    total_logins: int
    input_tokens_used: int
    output_tokens_used: int
    last_login_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserLogUpdate(BaseModel):
    total_logins: Optional[int] = None
    input_tokens_used: Optional[int] = None
    output_tokens_used: Optional[int] = None
    last_login_date: Optional[datetime] = None

    class Config:
        from_attributes = True

# Email Verification Schemas
class EmailVerificationRequest(BaseModel):
    token: str

class EmailVerificationResponse(BaseModel):
    message: str
    verified: bool

class ResendVerificationRequest(BaseModel):
    email: str

class ResendVerificationResponse(BaseModel):
    message: str
    sent: bool

# Password Reset Schemas
class ForgotPasswordRequest(BaseModel):
    email: str

class ForgotPasswordResponse(BaseModel):
    message: str
    sent: bool

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ResetPasswordResponse(BaseModel):
    message: str
    success: bool

# Error Schemas
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None

class ValidationErrorResponse(BaseModel):
    detail: List[dict]
    error_code: str = "VALIDATION_ERROR"