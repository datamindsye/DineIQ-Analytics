# Backend API Application

## Overview

FastAPI backend application serving REST endpoints, managing CORS, validating requests via Pydantic, enforcing security with JWT and RBAC, and reading precomputed Parquet analytical marts.

## Key files

| File | Owns |
|---|---|
| `main.py` | FastAPI application factory, lifespan hooks, CORS, and route registration |
| `routers/health.py` | Liveness and readiness endpoints (`/api/v1/health`) |
| `routers/analytics.py` | Analytical marts delivery routes (`/api/v1/analytics`) |
| `routers/jobs.py` | Asynchronous job status routes (`/api/v1/jobs`) |
| `dependencies/db.py` | Database session injection dependency |

## Commands

```bash
# Run API server with hot reload
uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Conventions

- All API routes live under the `/api/v1` prefix.
- Never execute heavy Spark jobs or model training inside HTTP request handlers.
- Return standardized error responses using the `ErrorEnvelope` schema on validation or server errors.
- Wrap data payloads in `DataEnvelope` when returning collections or domain entities.
- Inject database sessions using `Depends(get_db)`.

## Gotchas

- Database readiness checks must handle PostgreSQL connection failures gracefully without crashing the API process.

_Drafted by /audit from the repo, worth a quick human pass. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
