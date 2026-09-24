# DineIQ Analytics — Data Science Intelligence Arena

A restaurant analytics and intelligence platform built for high scale data quality, dual independent analytical pipelines (Apache Spark / PySpark and Python Data Science / scikit-learn), evidence based business recommendations, and interactive dashboards.

---

## Architecture Overview

DineIQ Analytics follows a **Modular Monolith** pattern:
- **Frontend (`apps/web`)**: React 19 + TypeScript + Vite + Plotly.js for interactive visualizations.
- **Backend (`apps/api`)**: FastAPI providing asynchronous REST endpoints, JWT authentication, and RBAC authorization.
- **Application Database (`packages/db`)**: PostgreSQL for application metadata, users, roles, job tracking, and model registries via SQLAlchemy 2.0 and Alembic.
- **Analytical Storage (`data/marts`)**: Apache Parquet for high volume data snapshots and precomputed feature marts.
- **Dual Analytics Pipelines**:
  - **Spark Pipeline (`packages/pipeline_spark`)**: PySpark, Spark SQL, and Spark MLlib for distributed processing.
  - **Python Pipeline (`packages/pipeline_python`)**: Pandas, NumPy, and scikit-learn for independent data science.
- **Comparison Engine (`packages/comparison`)**: Unified cross pipeline evaluation against mathematical contracts.

---

## Repository Structure

```
DineIQ-Analytics/
|-- apps/
|   |-- web/                           # React + TypeScript frontend
|   |   |-- src/
|   |   |   |-- components/            # UI components and Plotly chart wrappers
|   |   |   |-- pages/                 # Dashboard, Pipelines, and Health views
|   |   |   |-- services/              # API client methods
|   |   |   `-- types/                 # TypeScript interfaces
|   `-- api/                           # FastAPI backend application
|       |-- routers/                   # Health, analytics, and jobs routers
|       |-- dependencies/              # Dependency injection helpers
|       `-- main.py                    # Application entrypoint
|-- packages/
|   |-- core/                          # Domain models, contracts, and configuration
|   |-- db/                            # PostgreSQL metadata layer and migrations
|   |-- pipeline_spark/                # PySpark ingestion and MLlib pipeline
|   |-- pipeline_python/               # Independent Python DS pipeline
|   |-- comparison/                    # Cross pipeline evaluation runner
|   `-- common/                        # Logging, security, and shared utilities
|-- data/                              # Local storage directory (git ignored)
|   |-- snapshots/                     # Raw and clean dataset snapshots
|   |-- marts/                         # Precomputed analytical outputs (Parquet)
|   `-- artifacts/                     # Model weights and manifests
|-- docs/
|   |-- scope/                         # Project scope and feature index
|   `-- specs/                         # Architecture specifications
`-- tests/                             # Test suites
    |-- unit/                          # Unit tests (config, security, contracts)
    `-- api/                           # API smoke and health tests
```

---

## Prerequisites

1. **Python**: Version 3.10 or higher (Python 3.13 supported)
2. **Node.js**: Version 18 or higher (Node 24 supported) with `npm`
3. **Java** (Optional for local PySpark): JRE 11 or 17
4. **PostgreSQL** (Optional for initial startup, required for persistent metadata): PostgreSQL 14+

---

## Setup & Getting Started

### 1. Environment Configuration

Copy the example environment file:
```bash
cp .env.example .env
```
Default configuration values in `.env`:
```ini
ENVIRONMENT=development
DEBUG=true
APP_NAME="DineIQ Analytics API"
APP_HOST=0.0.0.0
APP_PORT=8000
DATABASE_URL=postgresql+psycopg2://dineiq_user:dineiq_password@localhost:5432/dineiq_analytics
SECRET_KEY=change-this-in-production-super-secret-key-min-32-chars
```

### 2. Backend Setup

Install Python dependencies:
```bash
pip install -r requirements.txt
```

Run database migrations (once PostgreSQL is running):
```bash
alembic upgrade head
```

Start the FastAPI backend server:
```bash
uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```
- Interactive API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### 3. Frontend Setup

Navigate to the frontend directory:
```bash
cd apps/web
npm install
npm run dev
```
Open your browser at [http://localhost:5173](http://localhost:5173).

---

## Code Quality & Developer Tooling

To ensure consistency across the 5-person team, the repository enforces automated linting, formatting, type checking, and pre-commit hooks.

### 1. Python Code Quality (Ruff)

We use **Ruff** for high-speed Python linting and formatting:
```bash
# Check code for lint errors and import order
ruff check .

# Automatically fix fixable lint errors
ruff check --fix .

# Format code according to project style
ruff format .

# Check formatting without modifying files
ruff format --check .
```

### 2. Frontend Code Quality (Oxlint & TypeScript)

From `apps/web`:
```bash
# Fast linting across frontend TypeScript files
npx oxlint

# Type checking and production bundle verification
npm run build
```

### 3. Pre-Commit Hooks

Pre-commit hooks automatically check staged files before each commit, preventing syntax errors, unformatted code, secret leaks, and accidental commits of generated datasets:

```bash
# Install git hooks into your local repository (run once)
pre-commit install

# Manually run all hooks against all files
pre-commit run --all-files
```

Active pre-commit checks:
- **Ruff Linter & Formatter**: Automatically formats and lints Python code.
- **Oxlint**: Validates frontend TypeScript components.
- **Typecheck & Build**: Verifies that frontend builds without errors.
- **Large File Protection**: Rejects files larger than 1MB (prevents accidental commits of large dataset snapshots).
- **Secret Detection**: Checks for private keys and credentials.
- **File Hygiene**: Removes trailing whitespace, ensures single newline at EOF, validates JSON/YAML.

### 4. Continuous Integration (GitHub Actions)

Every pull request and push to `main` triggers automated CI checks (`.github/workflows/ci.yml`):
1. **Backend Job**: Sets up Python 3.13, runs `ruff check`, `ruff format --check`, and executes the `pytest` test suite.
2. **Frontend Job**: Sets up Node 20, runs `npx oxlint`, and executes `npm run build` (type checking and bundling).

---

## Team Workflow & Git Conventions

1. **Branching**: Create feature branches from `main` (e.g. `feat/menu-analytics`, `feat/customer-rfm`).
2. **Never Commit Secrets or Generated Datasets**: Ensure `.env`, `data/snapshots/*`, `data/marts/*`, and `data/artifacts/*` are never added to Git.
3. **Commit Hygiene**: Run `pre-commit run --all-files` before pushing. Write clear, descriptive commit messages.
4. **Code Review**: Open a Pull Request to `main`. Ensure all CI checks pass before requesting reviews.

---

## PostgreSQL Configuration

To run PostgreSQL locally with Docker:
```bash
docker run --name dineiq-postgres -e POSTGRES_USER=dineiq_user -e POSTGRES_PASSWORD=dineiq_password -e POSTGRES_DB=dineiq_analytics -p 5432:5432 -d postgres:16
```
Or use a local native PostgreSQL installation matching the credentials in `.env`.
