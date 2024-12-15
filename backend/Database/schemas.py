from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

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
    user_type: str

    class Config:
        from_attributes = True

class UserRead(BaseModel):
    userid: UUID
    firstname: str
    lastname: str
    email: EmailStr
    user_type: str
    # signup_timestamp: datetime

    class Config:
        from_attributes = True

# class UserLogRead(BaseModel):
#     userid: UUID
#     total_logins: int
#     input_tokens_used: int
#     output_tokens_used: int
#     last_login_date: Optional[datetime]

#     class Config:
#         from_attributes = True

# class UserLogUpdate(BaseModel):
#     total_logins: Optional[int]
#     input_tokens_used: Optional[int]
#     output_tokens_used: Optional[int]
#     last_login_date: Optional[datetime]

# class ActivityLogCreate(BaseModel):
#     userid: UUID
#     ip_address: str


# class ChatLogCreate(BaseModel):
#     chat_id: str
#     user_id: UUID
#     tokens_used: int
#     created_at: datetime

    