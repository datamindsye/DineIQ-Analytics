# Database and Metadata Package

## Overview

Database persistence layer managing PostgreSQL connections, SQLAlchemy DeclarativeBase models, and Alembic database schema migrations.

## Key files

| File | Owns |
|---|---|
| `base.py` | SQLAlchemy 2.0 DeclarativeBase class |
| `session.py` | Engine, sessionmaker, and connectivity test helpers |
| `models/` | Relational model definitions for users, jobs, and metadata |
| `migrations/env.py` | Alembic runtime environment script |

## Commands

```bash
# Generate a new migration revision
alembic revision --autogenerate -m "create_initial_schema"

# Apply pending migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

## Conventions

- Use SQLAlchemy 2.0 syntax (Mapped, mapped_column, select).
- Keep million row transaction tables out of PostgreSQL; store analytical datasets in Apache Parquet.
- Always run migrations through Alembic rather than calling `Base.metadata.create_all()` in production code.

_Drafted by /audit from the repo, worth a quick human pass. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
