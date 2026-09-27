# CLAUDE.md — Project & Agent Instructions

## Project
**DineIQ Analytics — Data Science Intelligence Arena**  
A modular monolith platform for restaurant intelligence, dual big data analytics pipelines (Apache Spark and independent Python), automated ML model comparison, executive decision intelligence, and interactive dashboards.

## Current Phase
**Phase 3 Data Engineering / Spark Analytical Pipeline completed.**

## Current Status
- **Phase 1 (Foundation & Operational Architecture)**: Completed & verified.
- **Phase 2 (Dataset Contract, Generation & Data Quality)**: Completed & verified.
- **Phase 3 (Spark Analytical Pipeline & 12 Analytical Marts)**: Implemented, verified, and materialized (741,310 Parquet rows, 108 pytest tests passed, Ruff clean).
- **Phase 4 (Machine Learning & Comparison)**: **NOT yet completed.** (Spark MLlib and independent Python ML models have NOT been trained yet).
- **Dashboards, Recommendations & What-If**: **NOT yet completed.**

---

## End-to-End Architecture

```
Raw Restaurant Data
  │
  ▼
Data Quality & Profiling
  │
  ▼
Cleaning & Defect Quarantine Isolation
  │
  ▼
Immutable Clean Parquet Snapshot (`data/cleaned/competition_benchmark_v1/`)
  │
  ▼
Spark Analytical Pipeline & Feature Engineering
  │
  ▼
12 Analytical Marts (`data/marts/spark/*.parquet`)
  │
  ├──────────────────────────────────────────────┐
  ▼                                              ▼
Spark MLlib Models                     Independent Python ML Models
(Forecasts, Wastage, Churn)            (Forecasts, Wastage, Churn)
  │                                              │
  └──────────────────────┬───────────────────────┘
                         ▼
             Dual Pipeline Model Comparison
                         │
                         ▼
        Decision Intelligence & Recommendations
                         │
                         ▼
              What-If Simulation Engine
                         │
                         ▼
                FastAPI Backend API
                         │
                         ▼
             React + Vite + Plotly Dashboards
```

---

## Current Architecture Decisions

- **Modular Monolith**: Codebase organized strictly inside `apps/` and `packages/`. No microservices, service meshes, or internal network APIs.
- **Backend**: FastAPI with asynchronous request handling, Pydantic v2 schemas, SQLAlchemy 2.0 ORM, and Uvicorn.
- **Frontend**: React 19, TypeScript, Vite, and Plotly.js for interactive visualizations.
- **Database & Metadata**: PostgreSQL for application metadata, users, roles, job tracking, and model registries via Alembic migrations.
- **Analytical Storage**: Snappy-compressed Apache Parquet for high-volume datasets and precomputed analytical marts.
- **Big Data Engine**: Apache Spark 4.2.0 / PySpark with Spark SQL and DataFrame API for distributed processing.
- **Machine Learning (Planned)**: Spark MLlib on the Spark track; Pandas, NumPy, and scikit-learn on the independent Python track.
- **Security**: JWT authentication, Role-Based Access Control (RBAC) with 4 roles (`Admin`, `StoreManager`, `DataScientist`, `Cashier`), bcrypt password hashing.
- **Testing**: Automated `pytest` test suites with in-memory fixtures.
- **Code Standards**: Ruff linter and formatter, Oxlint for TypeScript, pre-commit hooks.
- **Version Control**: Git / GitHub.

---

## Important Architectural Rule: Dual-Pipeline Independence

The Apache Spark and Python data science pipelines must remain **strictly independent**:

- **Shared Assets Only**:
  - Immutable clean raw Parquet snapshot (`data/cleaned/competition_benchmark_v1/`)
  - Chronological split manifest (`split_manifest.json`)
  - Target definitions (`packages/core/contracts/analytical_contracts.py`)
  - Evaluation contracts (`packages/core/contracts/evaluation.py`)
- **Strictly Prohibited Cross-Talk**:
  - Never share prepared feature tables or intermediate DataFrames.
  - Never share trained model artifacts or weights.
  - Never share prediction scores or inferential outputs.
  - Spark and Python models must be trained and evaluated separately against the shared unseen comparison split.

---

## Team Workflow & Operational Guardrails

1. **Feature Branches**: `main` is protected conceptually; all work must proceed through feature branches (e.g. `feature/phase3-spark-marts`). Never push directly to `main`.
2. **Explicit Approval**: No commit or push without explicit team approval and forensic verification.
3. **Comprehension & Ownership**: Every team member must fully understand, verify, and be able to defend the code they submit.
4. **AI Oversight**: All AI-assisted code must be independently reviewed, statically analyzed, and tested. AI must not be used as a black-box decision engine or to fabricate results.
5. **Zero Data/Metric Fabrication**: All reported metrics, row counts, and defect numbers must be empirically derived from physical data files on disk.
6. **Data Protection**: Bulk generated data (`data/snapshots/*`, `data/cleaned/*`, `data/quarantine/*`, `data/marts/*`, `data/artifacts/*`) is strictly excluded from Git via `.gitignore`.
7. **Secret Hygiene**: Secrets, API keys, and `.env` files must NEVER be staged or committed. Use `.env.example` as the sanitized template.
8. **Documentation Synchronization**: Project documentation must always reflect the actual current implementation truthfully. Never claim unbuilt features are complete.
