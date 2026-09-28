"""Authentication and Role Based Access Control (RBAC) route dependencies."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from apps.api.dependencies.db import get_db
from apps.api.services.auth_service import get_user_by_username
from packages.common.security import decode_access_token
from packages.core.config.settings import get_settings
from packages.db.models.auth import User

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


def get_user_from_token(token: str | None, db: Session) -> User:
    """Validate token and retrieve the corresponding active user."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(
            token=token,
            secret_key=settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    username: str | None = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_username(db, username=username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user


def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Validate Bearer token and retrieve the corresponding active user."""
    return get_user_from_token(token, db)


def get_export_user(
    token_header: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
    token_query: str | None = Query(None, alias="token"),
) -> User:
    """Validate token from Bearer header or ?token= query parameter and enforce export permissions."""
    raw_token = token_header or token_query
    user = get_user_from_token(raw_token, db)
    if user.is_superuser:
        return user

    user_role_names = {role.name for role in user.roles}
    allowed_roles = {"Admin", "StoreManager", "DataScientist"}
    if not user_role_names.intersection(allowed_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access forbidden: required role in {sorted(list(allowed_roles))}",
        )
    return user


def get_optional_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    """Retrieve user from token if present, returning None if unauthenticated."""
    if not token:
        return None
    try:
        payload = decode_access_token(
            token=token,
            secret_key=settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        username: str | None = payload.get("sub")
        if not username:
            return None
        user = get_user_by_username(db, username=username)
        if user and user.is_active:
            return user
    except Exception:
        return None
    return None


def require_roles(*allowed_roles: str) -> Callable[[User], User]:
    """Dependency factory enforcing that the authenticated user possesses at least one allowed role."""

    def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.is_superuser:
            return current_user

        user_role_names = {role.name for role in current_user.roles}
        if not user_role_names.intersection(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: required role in {list(allowed_roles)}",
            )
        return current_user

    return role_checker


def require_permissions(*required_permissions: str) -> Callable[[User], User]:
    """Dependency factory enforcing that the authenticated user possesses all specified permissions."""

    def permission_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.is_superuser:
            return current_user

        user_permissions = {perm.name for role in current_user.roles for perm in role.permissions}
        missing = set(required_permissions) - user_permissions
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: missing permissions {list(missing)}",
            )
        return current_user

    return permission_checker
