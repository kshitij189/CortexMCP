"""Pydantic schemas for authentication endpoints."""

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_user(cls, user):
        return cls(id=str(user.id), email=user.email, username=user.username)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
