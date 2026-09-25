"""Database models package exporting all operational and metadata tables."""

from packages.db.base import Base
from packages.db.models.audit import AuditEvent
from packages.db.models.auth import Permission, Role, User, role_permissions, user_roles
from packages.db.models.domain import (
    Customer,
    Inventory,
    MenuCategory,
    MenuItem,
    Order,
    OrderItem,
    PricingHistory,
    Promotion,
    Rating,
    Restaurant,
    Wastage,
)
from packages.db.models.jobs import JobRun
from packages.db.models.ml_metadata import ModelVersion, PredictionMetadata
from packages.db.models.recommendations import Recommendation

__all__ = [
    "Base",
    "User",
    "Role",
    "Permission",
    "role_permissions",
    "user_roles",
    "JobRun",
    "ModelVersion",
    "PredictionMetadata",
    "Recommendation",
    "AuditEvent",
    "Customer",
    "Restaurant",
    "MenuCategory",
    "MenuItem",
    "PricingHistory",
    "Promotion",
    "Order",
    "OrderItem",
    "Rating",
    "Inventory",
    "Wastage",
]
