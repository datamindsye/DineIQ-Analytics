# 0001. Architecture and Technology Stack

**Date**: 2026-09-24
**Status**: In Progress

## Summary

This specification establishes the system architecture and technology stack for the DineIQ Analytics platform. The system uses a modular monolith design with a React and TypeScript frontend, a FastAPI backend, PostgreSQL for application metadata, and Apache Spark with PySpark alongside an independent Python pipeline for analytics. Large analytical datasets and feature marts are stored in Parquet files, keeping heavy processing in background jobs so web queries remain fast. This design provides clear boundaries between layers and delivers an explainable platform suitable for competitive evaluation and production readiness.

## Decision

**Chosen option**: Option 1: Modular Monolith with Dual Independent Analytics Pipelines (PySpark and Python Data Science), FastAPI, React, PostgreSQL, and Parquet analytical storage.

**Implementation skills**: `architect` (`skills/architect/`)

## Proposed stack

| Layer | Choice | Reason |
|---|---|---|
| Frontend Framework | React with TypeScript | Provides a type safe component hierarchy, high developer ergonomics, and native integration with interactive charting libraries. |
| Backend Framework | FastAPI (Python) | Offers high performance asynchronous routing, automatic OpenAPI documentation, and native Pydantic validation. |
| Application Database | PostgreSQL | Delivers robust ACID compliance, relational integrity, JSON support, and metadata management for users, jobs, models, and audit logs. |
| Analytical Storage | Apache Parquet | Columnar compressed format ideal for scans, aggregations, and versioned feature marts on datasets with millions of rows. |
| Big Data Analytics | Apache Spark, PySpark, Spark SQL | Handles distributed data cleaning, large joins across historical tables, feature engineering, and Spark MLlib models. |
| Python Data Science | Pandas, NumPy, scikit-learn | Provides an independent data science pipeline with diverse statistical and machine learning algorithms for validation. |
| Visualization | Plotly | Generates interactive and publication ready exploratory charts with responsive client side interaction. |
| Authentication | JWT with Role Based Access Control | Enables stateless secure authentication with fine grained permission enforcement across distinct user personas. |
| Testing | pytest with Spark local testing | Delivers comprehensive automated unit, integration, and pipeline validation across both Python and Spark layers. |
| Configuration | Pydantic Settings with env files | Enforces strict validation of environment variables and operational thresholds without hard coding values. |
| Version Control | Git and GitHub | Ensures traceable code history, branch collaboration, and reproducible release management. |

## System architecture and component boundaries

The system is organized as a modular monolith. This architecture avoids the operational overhead of microservices while maintaining strict structural boundaries between modules.

```
+-----------------------------------------------------------------------------------+
|                                 React Frontend                                    |
|       (TypeScript, Component Views, Plotly Visualizations, Filter State)         |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          | HTTPS / REST (JSON)
                                          v
+-----------------------------------------------------------------------------------+
|                              FastAPI Backend Core                                 |
|                                                                                   |
|  +--------------------+  +--------------------+  +-----------------------------+  |
|  |   API Endpoints    |  |  Security & RBAC   |  |   Background Job Service    |  |
|  | (Auth, Marts, Ops) |  |   (JWT Validation) |  | (Async Task Queue / Status) |  |
|  +---------+----------+  +---------+----------+  +--------------+--------------+  |
|            |                       |                            |                 |
|            v                       v                            v                 |
|  +-----------------------------------------------------------------------------+  |
|  |                             Core Domain Services                            |  |
|  |  (Mart Readers, Recommendation Engine, What If Simulator, Report Exporters) |  |
|  +---------------------------------+-------------------------------------------+  |
+------------------------------------+----------------------------------------------+
                                     |
             +-----------------------+-----------------------+
             |                                               |
             v                                               v
+--------------------------+                   +------------------------------------+
|  PostgreSQL Database     |                   |  Parquet Analytical Marts Storage  |
|  - Users and Roles       |                   |  - Raw and Clean Snapshots         |
|  - Job Execution Status  |                   |  - Spark Feature Marts             |
|  - Model Registry Meta   |                   |  - Python Feature Marts            |
|  - Recommendations Audit |                   |  - Model Predictions and Metrics   |
|  - Audit Log Trails      |                   |  - Comparison Evaluation Marts     |
+--------------------------+                   +------------------+-----------------+
                                                                  ^
                                                                  | Writes Marts
                               +----------------------------------+
                               |
            +------------------+------------------+
            |                                     |
+-----------+---------------------+ +-------------+----------------------+
|     Spark Analytics Pipeline    | |   Python Data Science Pipeline     |
| (PySpark, Spark SQL, Spark ML)  | |  (Pandas, NumPy, scikit-learn)     |
| - Ingestion and Data Quality    | | - Independent Preprocessing        |
| - Menu and Wastage Aggregations | | - Independent Feature Engineering  |
| - Spark ML Training & Inference | | - scikit-learn Training & Inference|
+---------------------------------+ +------------------------------------+
```

### 1. Component responsibilities

The platform consists of seven core components:

1. **Frontend (`apps/web`)**: Implements user interfaces in React and TypeScript. Responsible for page layout, dashboard presentation, interactive filter controls, Plotly chart rendering, and API communication. It contains zero business logic.
2. **Backend API (`apps/api`)**: Built with FastAPI. Provides REST endpoints, JWT authentication, role based access control, request validation with Pydantic, metadata queries against PostgreSQL, analytical queries against precomputed Parquet marts, and background job dispatch.
3. **Core Domain (`packages/core`)**: Contains shared domain entities, schema definitions, evaluation contracts, target definitions, and calculation rules for business metrics.
4. **Database Access Layer (`packages/db`)**: Manages PostgreSQL database connections, SQLAlchemy ORM models, and Alembic schema migrations.
5. **Spark Pipeline (`packages/pipeline_spark`)**: Implements large scale data ingestion, multi table data quality validation, data cleaning, relational joins, feature engineering, and Spark MLlib modeling. Outputs partitioned Parquet analytical marts.
6. **Python Pipeline (`packages/pipeline_python`)**: Implements an independent data processing workflow using Pandas, NumPy, and scikit-learn. Reads the same raw snapshot, performs independent data transformations, trains scikit-learn models, and outputs partitioned Parquet marts.
7. **Comparison Engine (`packages/comparison`)**: Ingests predictions and metrics from both Spark and Python pipelines, applies the unified evaluation contract, calculates comparative scores, and writes comparison summaries to PostgreSQL and Parquet marts.

### 2. Repository and module boundaries

The codebase is organized in a clear modular repository structure:

```
DineIQ-Analytics/
|-- apps/
|   |-- web/                           # React + TypeScript frontend
|   |   |-- src/
|   |   |   |-- components/            # UI components and chart wrappers
|   |   |   |-- pages/                 # Dashboard views
|   |   |   |-- services/              # API client methods
|   |   |   |-- types/                 # Frontend TypeScript interfaces
|   |   |   `-- App.tsx
|   `-- api/                           # FastAPI backend application
|       |-- routers/                   # API routes (auth, analytics, jobs, etc.)
|       |-- dependencies/              # Auth and database dependencies
|       `-- main.py                    # Application entrypoint
|-- packages/
|   |-- core/                          # Domain models, contracts, and constants
|   |   |-- contracts/                 # Evaluation contracts and target definitions
|   |   |-- schemas/                   # Pydantic request and response schemas
|   |   `-- config/                    # Base configuration and thresholds
|   |-- db/                            # PostgreSQL metadata layer
|   |   |-- models/                    # SQLAlchemy models
|   |   |-- migrations/                # Alembic migration scripts
|   |   `-- session.py                 # Engine and session management
|   |-- pipeline_spark/                # Spark analytics and MLlib
|   |   |-- ingestion/                 # Raw ingestion and data quality rules
|   |   |-- marts/                     # Mart aggregation scripts (menu, customer, wastage)
|   |   |-- models/                    # Spark MLlib training and scoring
|   |   `-- session.py                 # SparkSession factory and local configuration
|   |-- pipeline_python/               # Independent Python analytics
|   |   |-- preprocessing/             # Independent cleaning and transforms
|   |   |-- features/                  # Independent feature engineering
|   |   `-- models/                    # scikit-learn training and evaluation
|   |-- comparison/                    # Cross pipeline evaluation
|   |   |-- metrics.py                 # Unified score computation
|   |   `-- evaluator.py               # Evaluator execution logic
|   `-- common/                        # Shared utilities (logging, storage, security)
|-- data/                              # Local storage directory (git ignored)
|   |-- snapshots/                     # Versioned raw and clean data snapshots
|   |-- marts/                         # Precomputed analytical outputs (Parquet)
|   `-- artifacts/                     # Model weights and serialized pipelines
|-- docs/                              # Architecture specifications and scope
`-- tests/                             # Test suites (unit, integration, pipeline)
```

### 3. Database responsibilities: PostgreSQL versus Parquet

A core architectural principle is storing data where it is most efficient:

- **PostgreSQL Responsibilities**:
  - User accounts, password hashes, roles, and session tokens.
  - System configuration and business threshold overrides.
  - Job execution registry, execution status, worker logs, and progress indicators.
  - Model registry metadata, model names, hyperparameter records, and run timestamps.
  - Evidence based recommendation records, approvals, and implementation state.
  - What if simulation run records and scenario parameters.
  - Security audit logs and user activity trails.
  - High level pipeline comparison metric summaries for instant dashboard cards.
- **Parquet Storage Responsibilities**:
  - Millions of raw and cleaned records (orders, order lines, customers, inventory logs, wastage records).
  - Versioned historical snapshots partitioned by snapshot identifier.
  - Precomputed analytical feature marts (menu profitability classification, customer RFM tables, weekly store metrics).
  - Row level machine learning predictions and risk probability scores.
  - High volume time series arrays and detailed residual distributions.

PostgreSQL must never store million row transaction logs or heavy raw analytical tables. Parquet must never store mutable application state, user credentials, or operational job locks.

### 4. API and domain boundaries

The API layer is strictly decoupled from analytical processing:

- HTTP endpoints never invoke Spark jobs, data generation, or model training directly in request handlers.
- Endpoints accept requests, authenticate credentials via JWT, authorize permissions through RBAC dependencies, and delegate data fetching to precomputed mart reader services.
- Reading analytical data uses fast columnar scanners (PyArrow or DuckDB in embedded mode) that read directly from Parquet marts with predicate pushdown and column pruning, ensuring sub 50 millisecond response times.
- Mutation endpoints that trigger dataset generation, cleaning, or model training submit a job to the background job manager and immediately return an HTTP 202 Accepted status with a job identifier.

### 5. Background job boundaries

Heavy computation runs outside the web request cycle:

- A database backed job queue model in PostgreSQL (`job_runs` table) manages asynchronous tasks without requiring external message brokers like Redis, Celery, Kafka, or RabbitMQ.
- Job states transition explicitly: `PENDING` -> `RUNNING` -> `COMPLETED` or `FAILED` or `CANCELLED`.
- Tasks run either via FastAPI `BackgroundTasks` or dedicated lightweight Python worker subprocesses.
- The web client tracks long running tasks by polling the `/api/v1/jobs/{job_id}` endpoint, which returns execution percentage, elapsed time, current processing phase, and terminal status.

### 6. Dataset, model, and snapshot versioning

Reproducibility is essential for competition validation and operational safety:

- **Dataset Snapshots**: Each generated or imported dataset receives an immutable snapshot identifier formatted as `snap_YYYYMMDD_HHMMSS`. The raw files reside in `data/snapshots/{snapshot_id}/raw/` and the validated clean files in `data/snapshots/{snapshot_id}/clean/`. Snapshot metadata is recorded in the PostgreSQL `dataset_snapshots` table.
- **Pipeline Runs**: Every pipeline run receives an identifier formatted as `run_YYYYMMDD_HHMMSS`, referencing the exact `snapshot_id`, pipeline type (`SPARK` or `PYTHON`), commit hash, and parameter payload.
- **Model Registry**: Trained models are serialized into `data/artifacts/models/{model_id}/` alongside a `manifest.json` file recording features used, training hyperparameters, dataset snapshot identifier, and evaluation scores. Model metadata is indexed in PostgreSQL for querying.

### 7. Configuration management

Configuration is decoupled from application logic:

- System configuration is managed using Pydantic Settings classes loaded from `.env` files and environment variables.
- Operational parameters have strictly typed fallbacks for local development.
- Business thresholds (such as high wastage cost percentage, high margin threshold, or popularity percentile cutoffs) are stored in PostgreSQL with system defaults defined in code.
- Hard coding business logic numbers inside SQL queries or Python routines is strictly prohibited.

### 8. Logging, error handling, audit trail, and observability

The platform enforces consistent operational monitoring:

- **Structured Logging**: All logs are emitted in JSON format containing timestamp, log level, module name, request identifier, user identifier, and message context.
- **Error Envelope**: All API error responses adhere to a standard JSON envelope:
  ```json
  {
    "error": {
      "code": "RESOURCE_NOT_FOUND",
      "message": "The requested analytical mart was not found",
      "details": []
    }
  }
  ```
- **Audit Logging**: Sensitive mutations (user logins, role assignments, threshold updates, pipeline triggers, report exports, and recommendation status changes) are written to the `audit_logs` table in PostgreSQL with user identifier, client IP address, action name, before state, and after state.
- **Health Checks**: Standard endpoints `/api/v1/health` and `/api/v1/health/ready` check API responsiveness, PostgreSQL connectivity, and data directory access.

### 9. Security boundaries and RBAC integration

The platform implements stateless, fine grained access control:

- **Authentication**: Stateless JSON Web Tokens (JWT) signed using HMAC SHA256. Passwords are encrypted with bcrypt.
- **Role Hierarchy**:
  - `Admin`: Full system access, user administration, configuration updates, pipeline execution, and audit log access.
  - `Manager`: Access to all analytical dashboards, evidence based recommendations, what if simulation tools, report exports, and job triggering.
  - `Analyst`: Access to analytics dashboards, model comparison views, feature exploration, and data mart exports.
  - `Viewer`: Read only access to standard dashboards and generated reports.
- **Route Protection**: FastAPI routes use dependency injection (`Depends(require_role([...]))`) to enforce authorization at the HTTP boundary.

### 10. Analytical outputs and API ready marts

Marts are structured for immediate presentation without ad hoc heavy computation:

- Marts are stored in partitioned Parquet directories under `data/marts/{pipeline_run_id}/{domain}/`.
- For example, `data/marts/{run_id}/menu/` contains:
  - `menu_profitability.parquet`: Menu item metrics, sales volume, contribution margin, and category classifications (Stars, Plowhorses, Puzzles, Dogs).
  - `category_performance.parquet`: Aggregated revenue, cost, and volume by category.
- FastAPI reads these files using PyArrow or DuckDB, applies requested query filters (such as location or date range), and returns ready to display JSON to the frontend.

### 11. Exports and report generation

Reporting handles both interactive and large batch formats:

- Small and medium table exports (under 50,000 rows) are generated on demand and streamed directly as CSV or Excel files.
- Comprehensive analytical reports and PDF summaries are generated as asynchronous background jobs.
- Completed report files are stored in `data/exports/{export_id}` and made available for download with audit logging.

### 12. Local development and deployment boundaries

The platform is designed to be fully runnable on a local machine without expensive or complex cloud dependencies:

- **Local Machine Requirements**: Standard 64 bit workstation (Windows, Linux, or macOS) with Python 3.10+, Java 11 or 17 (for PySpark local mode), local PostgreSQL instance (or simple single container), and Node.js 18+.
- **Zero Cloud Lock in**: The architecture does not require AWS, Azure, Google Cloud, Kafka clusters, or Kubernetes.
- **Future Container Deployment**: A simple Docker Compose configuration defines three lightweight services (`web`, `api`, `db`) with mounted data volumes.

## Dual pipeline contract and independence rules

The platform features two independent analytics and machine learning pipelines: Spark Pipeline (PySpark) and Python Pipeline (scikit-learn). To maintain genuine scientific and technical comparison, their boundaries are strictly enforced.

```
+-----------------------------------------------------------------------------------+
|                        Clean Dataset Snapshot & Manifest                          |
|         (data/snapshots/{id}/clean/  &  manifests/split_manifest.json)            |
+-----------------------------------------+-----------------------------------------+
                                          |
                 +------------------------+------------------------+
                 | Shared Input Data Only                          | Shared Input Data Only
                 v                                                 v
+------------------------------------+           +----------------------------------+
|      Spark Analytics Pipeline      |           |     Python Analytics Pipeline    |
| - PySpark Feature Engineering      |           | - Pandas & NumPy Transformations |
| - Spark ML VectorAssembler         |           | - scikit-learn Preprocessing     |
| - Spark GBT / RF Classifier        |           | - HistGradientBoosting Classifier|
| - Spark ML Test Predictions        |           | - scikit-learn Test Predictions  |
+------------------+-----------------+           +-----------------+----------------+
                   |                                               |
                   | Independent Predictions                       | Independent Predictions
                   v                                               v
+-----------------------------------------------------------------------------------+
|                            Unified Comparison Engine                              |
|           (Reads Both Output Marts, Evaluates Contract Metrics, Logs Diff)        |
+-----------------------------------------------------------------------------------+
```

### Shared inputs (strictly permitted)

The two pipelines are permitted to share only:
1. The raw or cleaned dataset snapshot files (`data/snapshots/{snapshot_id}/clean/`).
2. Entity identifiers (`customer_id`, `order_id`, `item_id`, `location_id`, `date`, `week_id`).
3. The exact target definition and threshold rules.
4. The chronological split manifest (`split_manifest.json`) defining exact train, validation, and test date ranges.
5. The unified evaluation contract specifying calculation formulas and metrics.

### Isolation rules (strictly prohibited)

The two pipelines must NEVER share:
1. Prepared feature tables or intermediate dataframes.
2. Trained model weights, parameters, or pipelines.
3. Prediction outputs or predicted probabilities.
4. Feature selection results or transformation rules.

### Initial comparison target: Next week wastage risk

The primary machine learning benchmark evaluates wastage risk per menu item, location, and calendar week:

- **Prediction Entity**: Tuple of `(item_id, location_id, week_id)`.
- **Target Variable**: Binary risk flag `wastage_risk_flag` in `{0, 1}`.
- **Target Formal Definition**:
  For an item and location in week `t + 1`, `wastage_risk_flag = 1` if:
  `(wastage_cost_{t+1} / total_sales_revenue_{t+1}) >= wastage_cost_threshold` (default 0.05, representing 5 percent)
  OR
  `(wasted_quantity_{t+1} / prepared_quantity_{t+1}) >= wastage_quantity_ratio_threshold` (default 0.10, representing 10 percent).
  Otherwise `wastage_risk_flag = 0`.
- **Chronological Split Manifest**:
  - Training Period: Weeks 1 through 40 (earliest 10 months).
  - Validation Period: Weeks 41 through 46 (subsequent 6 weeks).
  - Testing Period: Weeks 47 through 52 (final 6 weeks).
- **Anti Leakage and Feature Availability Rule**:
  To compute features for predicting week `t + 1`, a pipeline may utilize data from timestamp zero up to the final second of week `t`. It is strictly prohibited to include same week sales, future wastage, contemporaneous customer ratings, or future promotional calendars.
- **Evaluation Contract Metrics**:
  Both pipelines must produce predictions scored against the exact same test split using:
  1. Precision, Recall, and F1 Score (evaluated at risk threshold probability 0.50 and optimal F1 threshold).
  2. Receiver Operating Characteristic Area Under Curve (ROC AUC).
  3. Precision Recall Area Under Curve (PR AUC).
  4. Brier Score (measuring probability calibration quality).
  5. Training wall clock runtime (seconds) and batch inference throughput (predictions per second).

## Data flow and lifecycle

The platform processes data through six distinct lifecycle stages:

1. **Generation and Import**: Realistic restaurant data representing 11 relational tables is generated or imported into `data/snapshots/{snapshot_id}/raw/`.
2. **Data Quality and Cleaning (PySpark)**: Spark validates schema consistency, null thresholds, referential integrity, and negative values. Clean records are saved to `data/snapshots/{snapshot_id}/clean/`.
3. **Split Manifest Generation**: A deterministic chronological split manifest is written to `data/snapshots/{snapshot_id}/manifests/split_manifest.json`.
4. **Dual Pipeline Execution**:
   - The Spark pipeline reads the clean snapshot, builds Spark feature marts, trains a Spark MLlib model, and writes test predictions to `data/marts/{run_id}/spark/`.
   - The Python pipeline reads the clean snapshot, builds Pandas feature sets, trains a scikit-learn model, and writes test predictions to `data/marts/{run_id}/python/`.
5. **Comparison and Verification**: The comparison engine compares predictions, verifies metric agreement, and records benchmark metrics in PostgreSQL and Parquet.
6. **API Delivery and Dashboard Consumption**: FastAPI serves precomputed marts to the React frontend. Users inspect dashboards, filter views, run scenarios, and review recommendations.

## Value sourcing

Every value displayed or computed across API endpoints traces to an unambiguous source:

| Action / Endpoint | Value Produced or Displayed | Concrete Source |
|---|---|---|
| `GET /api/v1/analytics/menu/profitability` | Item unit cost, price, sales volume, margin percentage | Precomputed Parquet mart `menu_profitability.parquet` |
| `GET /api/v1/analytics/menu/classification` | Menu category (Star, Plowhorse, Puzzle, Dog) | Derived in mart aggregation using median margin and volume |
| `GET /api/v1/analytics/wastage/risk` | Wastage risk probability, predicted risk class | Model predictions in Parquet mart `predictions_wastage.parquet` |
| `GET /api/v1/comparison/summary` | Precision, Recall, F1, ROC AUC, runtime diff | Computed by comparison engine in `pipeline_comparisons` table |
| `GET /api/v1/jobs/{job_id}` | Job status, progress percentage, error message | PostgreSQL table `job_runs` |
| `GET /api/v1/recommendations` | Observation, evidence, recommendation, priority | PostgreSQL table `recommendations` derived from marts |
| `POST /api/v1/auth/login` | Access token, token expiry, user role permissions | Generated JWT signed by backend using secret key and DB role |
| `POST /api/v1/scenarios/simulate` | Projected revenue and margin under price shift | Computed by domain service from precomputed elasticity matrix |

## Tracer bullet implementation specification

The initial implementation slice (Tracer Bullet) proves the entire system pathway end to end before implementing every analytics domain.

The Tracer Bullet proves this complete sequence:
```
Raw Restaurant Data (CSV / Parquet)
      |
      v
Spark Ingestion and Quality Validation
      |
      v
Clean Data Snapshot & Split Manifest
      |
      +--------------------------------+
      |                                |
      v                                v
Spark Menu Analytics Mart       Python Menu Analytics Mart
(PySpark & Spark SQL)           (Pandas & NumPy)
      |                                |
      +----------------+---------------+
                       |
                       v
         Dual Pipeline Comparison Check
                       |
                       v
              FastAPI REST Endpoint
          (/api/v1/analytics/menu/mart)
                       |
                       v
            React Frontend Dashboard
       (Plotly Menu Profitability Matrix)
```

### Minimum architecture required for Tracer Bullet

1. **Data Layer**:
   - Synthetic data generation for at least 4 core tables: `restaurants`, `menu_categories`, `menu_items`, `orders`, and `order_items`.
   - Local directory structure for `data/snapshots/` and `data/marts/`.
2. **Spark Processing**:
   - Local PySpark session creation.
   - Spark ingestion and schema validation script.
   - Spark Menu Analytics aggregation calculating revenue, cost, sales volume, and classification for each menu item.
3. **Python Processing**:
   - Independent Python script reading the same clean data files.
   - Independent calculation of menu metrics and classification using Pandas.
4. **Comparison Execution**:
   - Automated script comparing Spark versus Python menu classification outputs.
   - Validation that classification agreement is 100 percent and revenue calculation differences are within rounding tolerance.
5. **FastAPI Application**:
   - FastAPI app with CORS middleware and health route.
   - Endpoint `GET /api/v1/analytics/menu` reading the generated Parquet mart and returning JSON.
6. **React Dashboard**:
   - React app with TypeScript and Plotly library.
   - Menu Intelligence view displaying a 4 quadrant scatter plot (Profit Margin vs Sales Volume) and data table.

## Consequences

**Positive**:
- Eliminates heavy cluster and cloud infrastructure dependencies, allowing the entire application to be developed, run, and demonstrated on a local computer.
- Guarantees fast web dashboard response times because all analytical computations are precomputed into Parquet marts rather than executed inside HTTP handlers.
- Preserves genuine dual pipeline independence, satisfying competition evaluation requirements.
- Modular monolith structure keeps code organized, type safe, and easy for student developers to understand and modify.

**Negative / tradeoffs**:
- Local PySpark requires a Java Runtime Environment (JRE 11 or 17) on the developer machine.
- Background jobs managed via database tables lack advanced workflow features (like dynamic DAG dependencies) present in dedicated orchestrators like Airflow.
- Dual pipelines require maintaining two distinct analytics codebases that calculate equivalent business metrics.

**Neutral**:
- Parquet files stored locally must be tracked and cleaned up periodically to manage disk space.
- Schema migrations in PostgreSQL must be managed using Alembic migration scripts.

## Follow-up

- [ ] Verify local Java runtime environment compatibility for PySpark on team machines.
- [ ] Confirm PostgreSQL local instance setup and create initial database.
- [ ] Implement data generation script and data quality pipeline for the Tracer Bullet slice.

## Rationale

Reasoning, options considered, and references: see [rationale.md](rationale.md).
