"""Core Pydantic schemas for DineIQ Analytics."""

from packages.core.schemas.audit import AuditEventCreate, AuditEventResponse
from packages.core.schemas.auth import (
    LoginRequest,
    PermissionResponse,
    RoleResponse,
    TokenPayload,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from packages.core.schemas.common import (
    DataEnvelope,
    ErrorDetail,
    ErrorEnvelope,
    ErrorPayload,
    HealthStatus,
)
from packages.core.schemas.jobs import (
    JobRunResponse,
    JobRunStatusUpdate,
    JobRunTrigger,
)
from packages.core.schemas.ml_metadata import (
    ModelVersionCreate,
    ModelVersionResponse,
    PredictionMetadataCreate,
    PredictionMetadataResponse,
)
from packages.core.schemas.recommendations import (
    RecommendationCreate,
    RecommendationResponse,
    RecommendationStatusUpdate,
)

__all__ = [
    "DataEnvelope",
    "ErrorDetail",
    "ErrorEnvelope",
    "ErrorPayload",
    "HealthStatus",
    "LoginRequest",
    "TokenResponse",
    "TokenPayload",
    "UserResponse",
    "UserCreate",
    "RoleResponse",
    "PermissionResponse",
    "JobRunTrigger",
    "JobRunResponse",
    "JobRunStatusUpdate",
    "ModelVersionCreate",
    "ModelVersionResponse",
    "PredictionMetadataCreate",
    "PredictionMetadataResponse",
    "RecommendationCreate",
    "RecommendationStatusUpdate",
    "RecommendationResponse",
    "AuditEventCreate",
    "AuditEventResponse",
]
