"""Authentication and Role Based Access Control (RBAC) database models."""

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    String,
    Table,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base

# Association table between roles and permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Association table between users and roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Permission(Base):
    """Fine grained permission capability in the system."""

    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        Identity(),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
    )


class Role(Base):
    """User authorization role definition."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        Identity(),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    users: Mapped[list["User"]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
    )
    permissions: Mapped[list[Permission]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
    )


class User(Base):
    """Operational application user account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        Identity(),
        primary_key=True,
    )
    username: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    roles: Mapped[list[Role]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
    )
