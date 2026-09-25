"""Authentication API endpoints for login, session info, and user registration."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from apps.api.dependencies.auth import get_current_user, require_roles
from apps.api.dependencies.db import get_db
from apps.api.services.auth_service import (
    authenticate_user,
    create_user_token,
    register_user,
    serialize_user,
)
from packages.core.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from packages.core.schemas.common import DataEnvelope
from packages.db.models.auth import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=DataEnvelope[TokenResponse],
    status_code=status.HTTP_200_OK,
)
def login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> DataEnvelope[TokenResponse]:
    """Authenticate with username or email and password, issuing a JWT bearer token."""
    ip_address = request.client.host if request.client else None
    user = authenticate_user(
        db=db,
        username=payload.username,
        password=payload.password,
        ip_address=ip_address,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_response = create_user_token(user)
    return DataEnvelope(data=token_response)


@router.get(
    "/me",
    response_model=DataEnvelope[UserResponse],
    status_code=status.HTTP_200_OK,
)
def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> DataEnvelope[UserResponse]:
    """Retrieve profile and assigned roles for the currently authenticated user."""
    return DataEnvelope(data=serialize_user(current_user))


@router.post(
    "/register",
    response_model=DataEnvelope[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: UserCreate,
    current_admin: Annotated[User, Depends(require_roles("Admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> DataEnvelope[UserResponse]:
    """Register a new user account with specified roles (Admin only)."""
    try:
        new_user = register_user(db=db, payload=payload, creator_id=current_admin.id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    return DataEnvelope(data=serialize_user(new_user))
