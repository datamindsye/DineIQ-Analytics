"""Authentication, user management, and token issuance services."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from packages.common.logging import get_logger
from packages.common.security import create_access_token, get_password_hash, verify_password
from packages.core.config.settings import get_settings
from packages.core.schemas.auth import (
    PermissionResponse,
    RoleResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from packages.db.models.audit import AuditEvent
from packages.db.models.auth import Role, User

logger = get_logger("dineiq.api.auth_service")
settings = get_settings()


def get_user_by_username(db: Session, username: str) -> User | None:
    """Retrieve an active or inactive user by username with roles loaded."""
    stmt = (
        select(User)
        .options(
            selectinload(User.roles).selectinload(Role.permissions),
        )
        .where(User.username == username)
    )
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_email(db: Session, email: str) -> User | None:
    """Retrieve a user by email address."""
    stmt = (
        select(User)
        .options(
            selectinload(User.roles).selectinload(Role.permissions),
        )
        .where(User.email == email)
    )
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Retrieve a user by primary key id."""
    stmt = (
        select(User)
        .options(
            selectinload(User.roles).selectinload(Role.permissions),
        )
        .where(User.id == user_id)
    )
    return db.execute(stmt).scalar_one_or_none()


def authenticate_user(
    db: Session,
    username: str,
    password: str,
    ip_address: str | None = None,
) -> User | None:
    """Validate user credentials and return authenticated user or None."""
    user = get_user_by_username(db, username)
    if not user:
        # Also allow login with email
        user = get_user_by_email(db, username)

    if not user or not verify_password(password, user.hashed_password):
        # Audit failed login
        audit = AuditEvent(
            user_id=user.id if user else None,
            action="LOGIN_FAILURE",
            resource="auth",
            resource_id=username,
            ip_address=ip_address,
            details={"reason": "invalid_credentials"},
        )
        db.add(audit)
        try:
            db.commit()
        except Exception:
            db.rollback()
        return None

    if not user.is_active:
        audit = AuditEvent(
            user_id=user.id,
            action="LOGIN_BLOCKED_INACTIVE",
            resource="auth",
            resource_id=str(user.id),
            ip_address=ip_address,
            details={"reason": "account_deactivated"},
        )
        db.add(audit)
        try:
            db.commit()
        except Exception:
            db.rollback()
        return None

    # Audit successful login
    audit = AuditEvent(
        user_id=user.id,
        action="LOGIN_SUCCESS",
        resource="auth",
        resource_id=str(user.id),
        ip_address=ip_address,
        details={"username": user.username},
    )
    db.add(audit)
    try:
        db.commit()
    except Exception:
        db.rollback()

    return user


def serialize_user(user: User) -> UserResponse:
    """Transform ORM user model to Pydantic UserResponse schema."""
    role_responses = [
        RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            permissions=[
                PermissionResponse(
                    id=perm.id,
                    name=perm.name,
                    description=perm.description,
                )
                for perm in role.permissions
            ],
        )
        for role in user.roles
    ]

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        roles=role_responses,
        created_at=user.created_at,
    )


def create_user_token(user: User) -> TokenResponse:
    """Create JWT access token and return token response wrapper."""
    role_names = [role.name for role in user.roles]
    permission_set = {perm.name for role in user.roles for perm in role.permissions}

    token_data = {
        "sub": user.username,
        "user_id": user.id,
        "roles": role_names,
        "permissions": sorted(list(permission_set)),
        "is_superuser": user.is_superuser,
    }

    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=token_data,
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        expires_delta=expires_delta,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=serialize_user(user),
    )


def register_user(
    db: Session,
    payload: UserCreate,
    creator_id: int | None = None,
) -> User:
    """Create a new user with assigned roles and hashed password."""
    existing_username = get_user_by_username(db, payload.username)
    if existing_username:
        raise ValueError(f"Username '{payload.username}' is already registered")

    existing_email = get_user_by_email(db, payload.email)
    if existing_email:
        raise ValueError(f"Email '{payload.email}' is already registered")

    hashed_pwd = get_password_hash(payload.password)
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hashed_pwd,
        full_name=payload.full_name,
        is_active=True,
        is_superuser=False,
    )

    # Attach requested roles if they exist
    if payload.roles:
        stmt = select(Role).where(Role.name.in_(payload.roles))
        found_roles = db.execute(stmt).scalars().all()
        user.roles = list(found_roles)

    db.add(user)
    db.flush()

    audit = AuditEvent(
        user_id=creator_id or user.id,
        action="USER_REGISTERED",
        resource="users",
        resource_id=str(user.id),
        details={"username": user.username, "roles": payload.roles},
    )
    db.add(audit)
    db.commit()
    db.refresh(user)
    return user


def seed_security_defaults(db: Session) -> None:
    """Ensure standard roles and default administrator exist in database."""
    standard_roles = {
        "Admin": "System administrator with full privileges",
        "StoreManager": "Restaurant store manager with branch operational access",
        "DataScientist": "Data scientist with pipeline, model, and analytics access",
        "Cashier": "Frontline cashier with order and catalog view access",
    }

    created_roles = {}
    for role_name, description in standard_roles.items():
        stmt = select(Role).where(Role.name == role_name)
        role = db.execute(stmt).scalar_one_or_none()
        if not role:
            role = Role(name=role_name, description=description)
            db.add(role)
            db.flush()
        created_roles[role_name] = role

    # Ensure default admin account exists
    admin_user = get_user_by_username(db, settings.DEFAULT_ADMIN_USERNAME)
    if not admin_user:
        logger.info("Bootstrapping default administrator '%s'", settings.DEFAULT_ADMIN_USERNAME)
        admin_user = User(
            username=settings.DEFAULT_ADMIN_USERNAME,
            email=settings.DEFAULT_ADMIN_EMAIL,
            hashed_password=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
            full_name="Default System Administrator",
            is_active=True,
            is_superuser=True,
            roles=[created_roles["Admin"]],
        )
        db.add(admin_user)

    db.commit()
