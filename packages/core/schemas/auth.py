"""Authentication and authorization schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """User login credential payload."""

    username: str = Field(..., min_length=3, max_length=60)
    password: str = Field(..., min_length=6)


class PermissionResponse(BaseModel):
    """Permission detail schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None


class RoleResponse(BaseModel):
    """Role detail schema with associated permissions."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    permissions: list[PermissionResponse] = Field(default_factory=list)


class UserResponse(BaseModel):
    """Authenticated user profile schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: str | None = None
    is_active: bool
    is_superuser: bool
    roles: list[RoleResponse] = Field(default_factory=list)
    created_at: datetime


class TokenResponse(BaseModel):
    """JWT bearer token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenPayload(BaseModel):
    """Decoded JWT claims payload."""

    sub: str
    user_id: int
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    exp: int | None = None


class UserCreate(BaseModel):
    """Administrative user registration payload."""

    username: str = Field(..., min_length=3, max_length=60)
    email: str = Field(..., min_length=5, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=8)
    full_name: str | None = None
    roles: list[str] = Field(default_factory=lambda: ["Cashier"])
