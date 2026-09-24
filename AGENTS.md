# DineIQ Analytics

## Stack

- **Frontend**: React 19, TypeScript, Vite, Plotly
- **Backend API**: FastAPI, Uvicorn, Pydantic, Pydantic Settings
- **Database & Metadata**: PostgreSQL, SQLAlchemy 2.0, Alembic
- **Big Data & Query**: Apache Spark, PySpark, Spark SQL, Spark MLlib
- **Python Data Science**: Pandas, NumPy, scikit-learn
- **Analytical Storage**: Apache Parquet
- **Testing**: pytest, pytest-asyncio, FastAPI TestClient
- **Security**: JWT authentication, Role Based Access Control (RBAC), bcrypt

## Build approach

Tracer Bullet (prove the whole pipe works before building any part fully; each slice is a working thread through every layer from data to dashboard).

## Commands

```bash
# Backend test execution
python -m pytest tests/

# Backend development server
uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

# Database migration
alembic upgrade head

# Frontend dependency install
cd apps/web && npm install

# Frontend development server
cd apps/web && npm run dev

# Frontend build & typecheck
cd apps/web && npm run build

# Frontend linting
cd apps/web && npx oxlint
```

## Specs

Stored in `docs/specs/`. Format: `docs/specs/NNNN-title/index.md` or `docs/specs/NNNN-title.md`.

## Rules

- **Modular Monolith**: Keep all code inside organized directories (`apps/` and `packages/`). Never introduce microservices, network separated internal APIs, or distributed service meshes.
- **Architectural Boundary Separation**: Frontend handles presentation only. FastAPI routes handle HTTP serialization and authentication only. Business logic belongs in domain services. Database operations belong in `packages/db`.
- **Dual Pipeline Independence**: Spark and Python pipelines must remain strictly independent. They may share only clean dataset snapshots, entity identifiers, target definitions, chronological split manifests, and evaluation contracts. They must never share prepared feature dataframes, trained model artifacts, or prediction scores.
- **Asynchronous Heavy Processing**: HTTP request handlers must never run heavy Spark jobs, model training, or million row table scans. All heavy analytics must execute as asynchronous background jobs tracked via the PostgreSQL `job_runs` table.
- **Fast Analytical Queries**: Web dashboards query precomputed Parquet analytical marts directly using embedded columnar scanners (PyArrow or DuckDB).
- **Time Aware Modeling**: Models and feature engineering must strictly prevent future data leakage. Features for week t may draw only from historical data recorded up to week t minus one.
- **Configuration and Secrets**: Manage configuration through environment variables loaded via Pydantic Settings. Never hard code database credentials, JWT secrets, or business threshold numbers in code. Never commit `.env` files.
- **Prohibited Infrastructure**: Do not install or introduce Kafka, Redis, Celery, Airflow, Kubernetes, or proprietary cloud services unless explicitly approved by the project owner.
- **Testing Standard**: Every new domain service, router, or pipeline module must be covered by automated pytest tests verifying happy paths, edge cases, and failure modes.
- **Git Expectations**: Write clear commit messages. Keep generated dataset files (`data/snapshots/*`), analytical marts (`data/marts/*`), and model weights (`data/artifacts/*`) out of version control.
- **Documentation Expectations**: Maintain architecture specifications in `docs/specs/` and keep setup instructions in `README.md` accurate. Never leave architecture decisions undocumented.
- **Coding Conventions**: Use explicit type annotations in Python and TypeScript. Avoid broad exception catches that hide unexpected system errors.

## Context files

- [apps/web/AGENTS.md](apps/web/AGENTS.md): Frontend React and TypeScript conventions
- [apps/api/AGENTS.md](apps/api/AGENTS.md): Backend FastAPI router and dependency conventions
- [packages/db/AGENTS.md](packages/db/AGENTS.md): Database models, sessions, and Alembic migrations
- [packages/pipeline_spark/AGENTS.md](packages/pipeline_spark/AGENTS.md): Spark ingestion, data quality, and MLlib rules
- [packages/pipeline_python/AGENTS.md](packages/pipeline_python/AGENTS.md): Independent Python data science rules
- [packages/comparison/AGENTS.md](packages/comparison/AGENTS.md): Cross pipeline evaluation and contract rules

_Drafted by /audit from the repo, worth a quick human pass. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
