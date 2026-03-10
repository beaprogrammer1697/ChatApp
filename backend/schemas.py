from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: UUID
    fcm_token: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class FCMTokenUpdate(BaseModel):
    fcm_token: str

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None

class GroupResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    created_by: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True

class GroupMemberCreate(BaseModel):
    user_id: UUID

class MessageCreateResponse(BaseModel): # Used to serialize returned messages
    id: UUID
    sender_id: UUID
    receiver_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    content: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class MessageSend(BaseModel):
    content: str
    receiver_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
