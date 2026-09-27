# DineIQ Analytics

## Stack

- **Frontend**: React 19, TypeScript, Vite, Plotly
- **Backend API**: FastAPI, Uvicorn, Pydantic, Pydantic Settings
- **Database & Metadata**: PostgreSQL, SQLAlchemy 2.0, Alembic
- **Big Data & Query**: Apache Spark 4.2.0, PySpark, Spark SQL, Spark MLlib (planned)
- **Python Data Science**: Pandas, NumPy, scikit-learn
- **Analytical Storage**: Apache Parquet (Snappy-compressed)
- **Testing**: pytest, pytest-asyncio, FastAPI TestClient
- **Security**: JWT authentication, Role Based Access Control (RBAC), bcrypt
- **Developer Tooling**: Ruff (Python), Oxlint (TypeScript), pre-commit

## Build Approach

Tracer Bullet (prove the whole pipe works before building any part fully; each slice is a working thread through every layer from data to dashboard).

## Commands

```bash
# Backend test execution
python -m pytest tests/

# Backend development server
uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

# Database migration
alembic upgrade head

# Spark analytical pipeline execution (materializes 12 marts)
python -m packages.pipeline_spark.runner

# Dataset generation (benchmark)
python -m packages.common.generator.cli --profile competition --snapshot-id competition_benchmark_v1

# Data quality profiling & cleaning
python -m packages.common.quality.cli --snapshot-dir data/snapshots/competition_benchmark_v1 --cleaned-dir data/cleaned --quarantine-dir data/quarantine

# Code linting & formatting
ruff check .
ruff format --check .

# Frontend development server
cd apps/web && npm run dev

# Frontend build & typecheck
cd apps/web && npm run build

# Frontend linting
cd apps/web && npx oxlint
```

## Team Workflow

- **Branch Protection**: `main` is protected conceptually; all active development must be done on dedicated feature branches (e.g. `feature/phase3-spark-marts`). Never push directly to `main`.
- **Explicit Approval**: No commit or push without explicit team approval and forensic verification.
- **Code Ownership**: Every member must understand, verify, and be able to defend every line of code they submit during competition presentations and code reviews.
- **AI-Assisted Development**: AI-generated code must be independently reviewed, statically analyzed, and tested. AI is never a substitute for architectural comprehension.
- **No Fabrication**: Do not fabricate metrics, row counts, defect statistics, or analytical findings. All figures must be empirically verified from physical disk artifacts.
- **No Hard-Coded Analytical Results**: Analytical metrics and mart tables must be computed dynamically by real pipeline jobs, not hard-coded in mock dictionaries.
- **No Hidden External AI Engines**: Do not use external generative AI APIs (e.g., OpenAI, Gemini API) as a runtime decision engine for business recommendations or predictions. All decision intelligence must be driven by reproducible models and heuristics inside the codebase.
- **Dual Pipeline Independence**: Spark and Python ML pipelines must remain strictly independent.
- **Scope Discipline**: The current Phase 3 branch must NOT start implementing unrelated frontend dashboards or final ML functionality unless explicitly assigned.

## Current Phase Status

### Completed
- Repository foundation, modular monolith architecture, directory layout
- Operational database schema, SQLAlchemy 2.0 ORM, Alembic migrations
- User authentication, JWT security, Role-Based Access Control (RBAC) with 4 roles
- Synthetic dataset generator with 17 realistic business complexities (1.31M rows)
- Data quality profiling engine, defect quarantine isolation, and clean Parquet export
- Comprehensive dataset forensic inspection and technical data dictionary
- Chronological temporal split contract (TRAIN, VALIDATION, TEST, UNSEEN_COMPARISON)
- Apache Spark session initialization, schema mapping, and table loading
- Native Spark SQL / DataFrame joins across 11 business domain tables
- Feature engineering across 12 analytical domains
- 12 precomputed Spark analytical marts materialized in `data/marts/spark/*.parquet` (741,310 total records)
- Sales anomaly anti-leakage correction (`rowsBetween(-14, -1)` excluding day $t$)
- Comprehensive automated regression tests (108 passed out of 108 tests)
- Static analysis pass with Ruff (0 errors)

### Not Completed Yet
- Spark MLlib model training (demand forecasting, wastage risk, churn)
- Independent Python scikit-learn model training
- Model evaluation and performance scoring
- Spark vs Python cross-pipeline comparison engine
- Final demand forecasting predictions
- Wastage prediction ML model
- Customer churn risk ML model
- Recommendation and decision intelligence engine
- What-if scenario analysis engine
- Final FastAPI analytical query endpoints
- Interactive React + Vite + Plotly BI dashboards
- Analytical export and executive reporting tools
- Production containerization, deployment, and competition submission package

## Architectural Rules

- **Modular Monolith**: Keep all code inside organized directories (`apps/` and `packages/`). Never introduce microservices, network-separated internal APIs, or distributed service meshes.
- **Architectural Boundary Separation**: Frontend handles presentation only. FastAPI routes handle HTTP serialization and authentication only. Business logic belongs in domain services. Database operations belong in `packages/db`.
- **Dual Pipeline Independence**: Spark and Python pipelines must remain strictly independent. They may share only clean dataset snapshots, entity identifiers, target definitions, chronological split manifests, and evaluation contracts. They must never share prepared feature dataframes, trained model artifacts, or prediction scores.
- **Asynchronous Heavy Processing**: HTTP request handlers must never run heavy Spark jobs, model training, or million-row table scans synchronously. All heavy analytics must execute as asynchronous background jobs tracked via the PostgreSQL `job_runs` table.
- **Fast Analytical Queries**: Web dashboards query precomputed Parquet analytical marts directly using embedded columnar scanners (PyArrow or DuckDB).
- **Time-Aware Modeling & Anti-Leakage**: Models and feature engineering must strictly prevent future data leakage. Features for week $t$ may draw only from historical data recorded up to week $t-1$. Rolling window statistics must strictly exclude day $t$.
- **Configuration and Secrets**: Manage configuration through environment variables loaded via Pydantic Settings. Never hard-code database credentials, JWT secrets, or business threshold numbers in code. Never commit `.env` files.
- **Prohibited Infrastructure**: Do not install or introduce Kafka, Redis, Celery, Airflow, Kubernetes, or proprietary cloud services unless explicitly approved by the project owner.
- **Testing Standard**: Every new domain service, router, or pipeline module must be covered by automated pytest tests verifying happy paths, edge cases, and failure modes.
- **Git Expectations**: Write clear commit messages. Keep generated dataset files (`data/snapshots/*`), analytical marts (`data/marts/*`), and model weights (`data/artifacts/*`) out of version control.
- **Documentation Expectations**: Maintain architecture specifications in `docs/specs/` and keep setup instructions in `README.md` accurate. Never leave architecture decisions undocumented.
- **Coding Conventions**: Use explicit type annotations in Python and TypeScript. Avoid broad exception catches that hide unexpected system errors.

## Context Files

- [apps/web/AGENTS.md](apps/web/AGENTS.md): Frontend React and TypeScript conventions
- [apps/api/AGENTS.md](apps/api/AGENTS.md): Backend FastAPI router and dependency conventions
- [packages/db/AGENTS.md](packages/db/AGENTS.md): Database models, sessions, and Alembic migrations
- [packages/pipeline_spark/AGENTS.md](packages/pipeline_spark/AGENTS.md): Spark ingestion, data quality, and MLlib rules
- [packages/pipeline_python/AGENTS.md](packages/pipeline_python/AGENTS.md): Independent Python data science rules
- [packages/comparison/AGENTS.md](packages/comparison/AGENTS.md): Cross pipeline evaluation and contract rules
- [docs/specs/0005-spark-analytical-pipeline-and-marts/index.md](docs/specs/0005-spark-analytical-pipeline-and-marts/index.md): Phase 3 Spark analytical pipeline specification
