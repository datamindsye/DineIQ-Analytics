# DineIQ Analytics — Development Log

## Project
**DineIQ Analytics — Data Science Intelligence Arena**

A competition-ready restaurant intelligence, data science, and analytics platform designed to demonstrate dual independent big data pipelines (Apache Spark and Python Data Science), executive decision intelligence, and automated machine learning evaluation.

---

## Phase 1 — Foundation

The Phase 1 foundation established the modular monolith architecture, operational database schemas, core services, and developer tooling:

- **Repository & Foundation Setup**:
  - Organized modular monorepo structure separating application shells (`apps/web`, `apps/api`) and shared packages (`packages/core`, `packages/db`, `packages/pipeline_spark`, `packages/pipeline_python`, `packages/comparison`, `packages/common`).
  - Strict prohibited infrastructure enforcement (no Kafka, Redis, Celery, Airflow, Kubernetes, or proprietary cloud services).
  - Modern frontend foundation in React 19, TypeScript, and Vite with Plotly.js.
  - Standardized tooling configured via `pyproject.toml` (Ruff linter/formatter, pytest).
- **FastAPI Backend Application**:
  - High-performance asynchronous API application in `apps/api/main.py`.
  - Application lifecycle management with logging and CORS middleware.
  - Global standardized HTTP exception handling wrapping responses in `ErrorEnvelope`.
  - Health probe endpoints (`/api/v1/health`, `/api/v1/health/liveness`, `/api/v1/health/readiness`, `/api/v1/health/analytics`).
- **PostgreSQL Operational Database & Alembic Migrations**:
  - SQLAlchemy 2.0 declarative base and session factory in `packages/db/session.py` supporting pre-ping connection pooling.
  - Initial operational schema migration (`20260925_0aa073b72e7f_initial_operational_schema.py`) establishing 10 operational tables: `permissions`, `roles`, `users`, `role_permissions`, `user_roles`, `job_runs`, `model_versions`, `predictions_metadata`, `recommendations`, and `audit_events`.
  - Business domain tables schema migration (`20260925_1b92e8c5678a_domain_tables_schema.py`) establishing all 11 core domain tables with check constraints and foreign keys.
- **Authentication, Security, and RBAC**:
  - JWT token generation, cryptographic validation, and password hashing using bcrypt.
  - Role-Based Access Control (RBAC) supporting four authoritative roles (`Admin`, `StoreManager`, `DataScientist`, `Cashier`), granular permissions, and superuser override.
  - Production security configuration validators enforcing 32+ character secrets and prohibiting default passwords.
- **Audit Logging**:
  - Comprehensive audit trail recording user IDs, IP addresses, action types, affected resources, and JSON details in `audit_events`.
- **Job & Pipeline Integration Boundaries**:
  - Asynchronous background task launcher in `packages/core/services/pipeline_launcher.py`.
  - HTTP handlers trigger long-running jobs without blocking requests, tracking lifecycle states in PostgreSQL `job_runs`.
- **Model Registry & Recommendation Metadata**:
  - Core services for model registration, version tracking, batch prediction logging, and recommendation status transitions (`packages/core/services/`).
- **Analytical Mart Reader**:
  - Embedded columnar reader in `packages/core/services/mart_reader.py` querying precomputed Parquet marts via PyArrow with directory traversal defense.
- **Backend Test Suite**:
  - Shared in-memory SQLite fixtures and authenticated client fixtures in `tests/conftest.py`.

---

## Phase 2 — Dataset & Data Quality Foundation

Phase 2 constructed the complete synthetic data generation engine, data contract specifications, quality profiler, defect quarantine engine, and cleaned Parquet storage.

### 1. Dataset Contract
- **Authoritative Specifications**:
  - Formal contracts codified in `packages/core/contracts/dataset_contract.py`.
  - Comprehensive technical data dictionary in `docs/data-dictionary.md`.
  - Architectural specifications: `docs/specs/0003-dataset-contract-and-generation-strategy/` and `docs/specs/0004-data-quality-and-cleaning/`.
- **Eleven Business Domain Tables**:
  `customers`, `restaurants`, `menu_categories`, `menu_items`, `pricing_history` (SCD Type 2), `promotions`, `orders`, `order_items`, `ratings`, `inventory`, `wastage`.
- **Cardinality Scale Targets**:
  Satisfies competition benchmark targets: $\ge 1\text{M}$ order lines, $\ge 100\text{k}$ orders, $\ge 50\text{k}$ customers, $\ge 150$ dishes, $\ge 10$ categories, $\ge 20$ locations, $\ge 100\text{k}$ ratings, $\ge 50\text{k}$ wastage logs, 365 days history.
- **Point-in-Time Financial Formulas**:
  $$\text{Line Net Revenue} = (\text{quantity} \times \text{unit\_price\_at\_sale}) - \text{line\_discount}$$
  $$\text{Line Contribution Margin} = \text{Line Net Revenue} - (\text{quantity} \times \text{unit\_cost\_at\_sale})$$
  $$\text{Order Total Amount} = \text{subtotal\_amount} - \text{discount\_amount} + \text{tax\_amount} + \text{tip\_amount}$$
- **Dual Pipeline Independence**:
  Clean Parquet snapshots provide the single shared read-only starting point for Apache Spark (`packages/pipeline_spark`) and Python Data Science (`packages/pipeline_python`). Pipelines never share intermediate dataframes, trained model weights, or prediction scores.

### 2. Dataset Generation
- **Generator Implementation**: Located in `packages/common/generator/` (`config.py`, `catalogs.py`, `transactions.py`, `engine.py`, `cli.py`).
- **Deterministic Reproducibility**: Governed by master random seed `42` with dedicated sub-generators for each entity.
- **Physical Competition Benchmark Snapshot**:
  Generated and stored at `data/snapshots/competition_benchmark_v1/`:
  - `seed`: 42
  - `start_date`: 2025-01-01 (365 calendar days horizon)
  - `generation_duration_seconds`: 1,434.75 s
  - `customers`: 50,000 records
  - `restaurants`: 20 locations
  - `menu_categories`: 10 categories
  - `menu_items`: 150 items
  - `pricing_history`: 1,500 records
  - `promotions`: 25 campaigns
  - `orders`: 100,508 records
  - `order_items`: 1,006,051 records
  - `ratings`: 100,000 records
  - `inventory`: 3,000 records
  - `wastage`: 50,000 records

### 3. Data Quality & Cleaning Subsystem
- **Engine Implementation**: Located in `packages/common/quality/` (`rules.py`, `profiler.py`, `cleaner.py`, `cli.py`).
- **Core Capabilities**:
  - Columnar profiling computing nullability, uniqueness, numeric ranges, and referential integrity without mutating source data.
  - Quality rule registry spanning 5 categories (Schema, Completeness, Integrity, Temporal, Validity) and 4 severity levels (Critical, Error, Warning, Info).
  - Deduplication retaining first occurrence and isolating subsequent duplicate IDs.
  - Value range filtering isolating negative unit prices and zero line quantities.
  - Generation cutoff verification isolating future dated timestamps.
  - Cascading quarantine isolating orphaned order lines whose parent order was quarantined.
  - Schema enrichment appending `quarantine_reason` and `quarantined_at` to quarantined Parquet tables.
  - Clean Parquet export with snappy compression to `data/cleaned/competition_benchmark_v1/`.
  - Machine-readable audit report generated at `data/cleaned/competition_benchmark_v1/quality_report.json`.

### 4. Verified Results

- **Authoritative Total Raw Records**: **1,311,264**
- **Clean Records Output**: **1,302,220**
- **Quarantined Records Isolated**: **9,044**
- **Mathematical Lineage Reconciliation**:
  $$1,311,264 \text{ raw} = 1,302,220 \text{ clean} + 9,044 \text{ quarantined} \quad [0 \text{ variance}]$$
- **Overall Cleanliness Rate**: **99.31%**
- **Header Orders**: 100,508 raw = 99,954 clean + 554 quarantined
- **Order Line Items**: 1,006,051 raw = 997,561 clean + 8,490 quarantined
- **Remaining 9 Tables**: 0 quarantined rows, 100% clean pass-through

### 5. Temporal Split
Verified against the 99,954 clean orders spanning calendar year 2025:

| Split Window | Date Range | Cleaned Orders | Volume Share % | Purpose |
|---|---|---|---|---|
| **TRAIN** | `2025-01-01` → `2025-08-31` | 66,631 | 66.66% | Historical training & baseline feature engineering |
| **VALIDATION** | `2025-09-01` → `2025-10-31` | 16,605 | 16.61% | Hyperparameter tuning & model selection |
| **TEST** | `2025-11-01` → `2025-11-30` | 8,230 | 8.23% | Out-of-time pre-deployment model evaluation |
| **UNSEEN_COMPARISON** | `2025-12-01` → `2025-12-31` | 8,488 | 8.49% | Isolated cross-pipeline evaluation (Spark vs Python) |

The final month (December 2025) is strictly reserved as an unseen evaluation horizon. Models will be evaluated on these 8,488 orders without having seen them during training or validation, enabling an unbiased competition comparison between Spark MLlib and scikit-learn.

### 6. Data Quality Findings & Complexities Confirmed
- **Permissible Business Nulls (Preserved)**:
  - 10,070 guest checkout orders (10.02% null `customer_id`) preserved in clean orders.
  - 7,524 customer accounts (15.05%) with missing phone or email preserved in clean customers.
  - 39,945 ratings (39.95%) with null `review_text` preserved in clean ratings.
- **Valid Operational States (Preserved)**:
  - 3,497 Cancelled orders (3.50%) and 509 Voided orders (0.51%) retained in clean orders for operational efficiency and churn risk modeling.
- **Defects Quarantined**:
  - 508 duplicate orders isolated under `DUPLICATE_ORDER_ID`.
  - 5,027 duplicate order items isolated under `DUPLICATE_ORDER_ITEM_ID`.
  - 46 future dated orders (dates in 2026/2027) isolated under `FUTURE_TIMESTAMP`.
  - 1,964 order items with negative prices isolated under `INVALID_NEGATIVE_PRICE`.
  - 1,024 order items with zero quantities isolated under `INVALID_ZERO_QUANTITY`.
  - 475 order items whose parent order was quarantined isolated under `ORPHANED_ORDER_PARENT`.
- **Referential Integrity**: 100% key matching across all clean tables (0 orphaned child records).
- **Financial Consistency**: 100% adherence to revenue, margin, and settlement formulas (maximum error $2.27 \times 10^{-13}$, 0 mismatches exceeding $\$0.01$).
- **Realistic Injected Patterns**:
  - Intraday meal peaks: Lunch Rush (28.20%), Dinner Rush (48.22%).
  - Day of week surge: Weekend orders account for 42.48% of volume.
  - Customer Pareto spend: Top 5% generate 21.17% revenue; Top 20% generate 51.02%.
  - Customer churn: 19,412 customers (55.07%) have 0 orders in the final 90 days.
  - Boston Consulting Group menu matrix: 32 Stars, 43 Plowhorses, 43 Puzzles, 32 Dogs.
  - Recipe rating collapse: Localized collapse detected on `DISH-0008` (3.75 avg) and `DISH-0004` (3.76 avg).
  - Promotion traps: 3 campaigns (`PROMO-0001`, `PROMO-0002`, `PROMO-0003`) yielding 9,471 negative margin lines.

### 7. Verification Results
- **Automated Pytest Suite**: `python -m pytest tests/`
  - **79 passed**, 0 failed, 0 skipped, 1 warning (11.42s).
- **Ruff Linter**: `ruff check .`
  - **All checks passed!** (0 errors, 0 warnings).
- **Ruff Formatter**: `ruff format --check .`
  - **180 files already formatted** (0 formatting issues).

---

## Evidence Chain

The repository demonstrates a verifiable and unbroken end-to-end data processing lineage:

1. **Generator**:
   - Path: `packages/common/generator/`
   - Role: Deterministic data synthesis engine with 17 realistic business complexities.
2. **Raw Parquet**:
   - Path: `data/snapshots/competition_benchmark_v1/`
   - Role: Write-once immutable snapshot containing 11 Parquet tables (1,311,264 records).
3. **Profiling**:
   - Path: `packages/common/quality/profiler.py`
   - Role: Columnar profiling measuring null rates, duplicate keys, and key set integrity.
4. **Quality Rules**:
   - Path: `packages/common/quality/rules.py`
   - Role: Formal quality definitions classified across 5 categories and 4 severities.
5. **Cleaning Pipeline**:
   - Path: `packages/common/quality/cleaner.py`
   - Role: Columnar cleaner executing deduplication, range checks, and cascading quarantine.
6. **Quarantine Storage**:
   - Path: `data/quarantine/competition_benchmark_v1/`
   - Role: Dedicated storage isolating 9,044 defective records with reason codes.
7. **Clean Parquet**:
   - Path: `data/cleaned/competition_benchmark_v1/`
   - Role: Pristine analytical dataset containing 1,302,220 validated records.
8. **Temporal Split**:
   - Path: `data/cleaned/competition_benchmark_v1/split_manifest.json`
   - Role: Manifest locking TRAIN, VAL, TEST, and UNSEEN_COMPARISON split windows.
9. **Validation & Audit**:
   - Path: `docs/reports/dataset_inspection_report.md`
   - Role: 1,750-line forensic audit report providing table-by-table schemas, samples, and invariants.

---

## Architecture / Engineering Decisions

1. **Raw Data Immutability**:
   Raw generated files in `data/snapshots/` are strictly read-only. No cleaning or ETL routine may alter or overwrite them.
2. **Columnar Parquet for Analytical Data**:
   All high-volume analytical data is stored as Snappy-compressed Apache Parquet. Web dashboards and analytical queries read Parquet directly via embedded PyArrow scanners rather than scanning relational database tables.
3. **Large Datasets Excluded from Version Control**:
   In compliance with the `.gitignore` policy, generated Parquet tables in `data/snapshots/`, `data/cleaned/`, and `data/quarantine/` are kept out of Git.
4. **Environment Isolation**:
   Local configuration and credentials reside in `.env`, which is strictly ignored by Git. `.env.example` serves as the sanitized template.
5. **Chronological ML Splits**:
   To strictly prevent future data leakage, chronological cutoff boundaries are locked prior to modeling. Features for week $t$ may only draw upon data recorded on or before week $t-1$.
6. **Dual Pipeline Independence**:
   Apache Spark and Python Data Science pipelines operate strictly independently, sharing only clean Parquet snapshots, entity identifiers, and evaluation contracts.
7. **Data Foundation Readiness**:
   Phase 2 serves as the verified data foundation. Phase 3 (Apache Spark) and Phase 4 (Python Data Science) consume the clean Parquet dataset directly.

---

## Git / Contribution Boundary

- All Phase 1 and Phase 2 implementations are currently present in the working tree and fully verified.
- The working tree remains uncommitted in accordance with the gate review protocol.
- Staging and preparing the Phase 2 commit will be executed following final gate approval.

---

## Phase Status

- **Phase 2 implementation**: **COMPLETE**
- **Phase 2 evidence**: **COMPLETE**
- **Phase 2 development log**: **COMPLETE**
- **Phase 2 commit**: **PENDING**
- **Phase 3 Spark**: **NOT STARTED**
