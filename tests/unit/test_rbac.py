"""Unit tests verifying Role Based Access Control (RBAC) authorization rules."""

import pytest
from fastapi import HTTPException

from apps.api.dependencies.auth import require_permissions, require_roles
from packages.db.models.auth import Permission, Role, User


def create_user_with_roles(roles: list[str], is_superuser: bool = False) -> User:
    """Helper creating an in-memory user instance with attached roles."""
    user = User(
        id=1,
        username="test_user",
        email="test@dineiq.local",
        hashed_password="hashed_placeholder",
        is_active=True,
        is_superuser=is_superuser,
    )
    user.roles = [Role(id=i + 1, name=role_name) for i, role_name in enumerate(roles)]
    return user


def test_require_roles_allows_matching_role():
    """Verify require_roles passes when user possesses an authorized role."""
    user = create_user_with_roles(["DataScientist"])
    checker = require_roles("Admin", "DataScientist")
    result = checker(user)
    assert result.username == "test_user"


def test_require_roles_blocks_unauthorized_role():
    """Verify require_roles raises 403 Forbidden when user lacks required role."""
    user = create_user_with_roles(["Cashier"])
    checker = require_roles("Admin", "DataScientist")
    with pytest.raises(HTTPException) as exc_info:
        checker(user)
    assert exc_info.value.status_code == 403
    assert "Access forbidden" in exc_info.value.detail


def test_require_roles_superuser_bypass():
    """Verify superuser bypasses specific role restrictions."""
    superuser = create_user_with_roles([], is_superuser=True)
    checker = require_roles("DataScientist")
    result = checker(superuser)
    assert result.is_superuser is True


def test_require_permissions_checking():
    """Verify fine grained permission checks on user roles."""
    perm = Permission(id=1, name="models:delete")
    role = Role(id=1, name="CustomRole", permissions=[perm])
    user = User(
        id=1,
        username="perm_user",
        email="perm@dineiq.local",
        hashed_password="pw",
        is_active=True,
        is_superuser=False,
        roles=[role],
    )

    perm_checker = require_permissions("models:delete")
    assert perm_checker(user).username == "perm_user"

    failing_checker = require_permissions("models:delete", "users:purge")
    with pytest.raises(HTTPException) as exc_info:
        failing_checker(user)
    assert exc_info.value.status_code == 403
