# 0002. Data Model and Relational Schema Architecture — Decision Record

## Context

The DineIQ Analytics platform requires an analytical and operational foundation capable of supporting both day to day administrative tasks and heavy enterprise scale data science workloads. The Software Requirements Specification mandates a minimum dataset consisting of one million order line items, one hundred thousand unique orders, fifty thousand customers, one hundred fifty menu items across ten categories, twenty restaurant locations, twelve months of transaction history, one hundred thousand ratings, and fifty thousand wastage entries.

This dataset must support dual independent analytics pipelines (Apache Spark with PySpark and Python with Pandas, NumPy, and scikit-learn), multi location comparison, price elasticity, menu engineering classifications, customer lifetime value segmentation, demand forecasting, and wastage prediction. Furthermore, the dataset must reflect the messy operational reality of restaurant point of sale systems, including missing customer records during guest checkout, duplicate submissions, cancelled orders, changing seasonal prices, and promotional discounts.

Without a well designed schema and data tier architecture, two primary failure modes threaten the system:
1. Operational database degradation: attempting to perform complex multi table joins and analytical aggregations on millions of rows inside PostgreSQL while concurrently handling web queries can saturate connection pools, evict cached pages, and cause high query latency.
2. Historical financial drift: if dish retail prices or ingredient costs are joined dynamically against current catalog prices rather than captured immutably at the instant of transaction, historical financial reports will retroactively alter whenever catalog prices change, destroying auditability and invalidating model predictions.

This specification addresses these forces by formalizing the relational structure for all eleven required business entities and delineating the operational, raw, and analytical data tiers.

## Project Owner Decisions

The following authoritative architectural decisions were confirmed by the project owner and are formally established in this specification:

1. **PostgreSQL Primary Keys (`BIGINT GENERATED ALWAYS AS IDENTITY`)**:
   - Every table in PostgreSQL uses standard sixty four bit auto incrementing identity integers (`id BIGINT GENERATED ALWAYS AS IDENTITY`).
   - This provides optimal index density (eight bytes per entry versus sixteen bytes for UUID), eliminates page fragmentation during inserts, and aligns with standard SQLAlchemy 2.0 and PostgreSQL best practices.

2. **Stable Source and Business Identifiers (`source_*_id`)**:
   - To bridge the gap between file based data science pipelines and the operational database, every business entity carries a stable source identifier (for example `source_order_id VARCHAR(64) UNIQUE NOT NULL`).
   - Generated raw snapshots, cleaned Parquet tables, feature sets, and model predictions all preserve this identifier.
   - This prevents pipeline code from depending on volatile, auto incremented relational sequence numbers, ensuring that analytics remain fully reproducible and auditable across separate environments.

3. **PostgreSQL Transaction Table Retention Policy (No Mirroring of One Million Rows)**:
   - The complete one million plus order line dataset will not be mirrored into PostgreSQL tables.
   - PostgreSQL is reserved for master catalog data, user security, job metadata, recommendations, audit logs, and an optional small operational demonstration slice (5,000 to 10,000 recent transactions).
   - High volume transactions remain exclusively in immutable raw snapshots (`data/snapshots/`) and precomputed columnar Parquet marts (`data/marts/`).
   - Rationale: Mirroring 1,000,000+ transaction lines into PostgreSQL produces 400MB to 600MB of unnecessary table and index bloat, creates connection pool contention during background analytics, and violates the architectural rule prohibiting heavy table scans in web request handlers.

4. **Exclusion of DuckDB as a Hard Dependency**:
   - DuckDB is not introduced as a required architectural platform component.
   - The system architecture remains lean and centered on approved core technologies: PostgreSQL, PySpark and Spark SQL, Parquet, Python data science (Pandas, NumPy, scikit-learn), FastAPI, and React.
   - PyArrow is used strictly as a lightweight, embedded columnar file parser in Python services rather than a dedicated database server.

5. **Preservation of Core Architectural Contracts**:
   - Transaction line point in time pricing and costing (`unit_price_at_sale`, `unit_cost_at_sale`).
   - Slowly Changing Dimension (SCD Type 2) tracking for menu prices in `pricing_history`.
   - UTC timezone standard (`TIMESTAMPTZ`).
   - Chronological modeling boundaries with explicit lag rules to prevent future data leakage.
   - Strict independence between Spark and Python data science pipelines.
   - Support for realistic dirty data in raw snapshots while enforcing strong analytical contracts.
   - Explicit mathematical separation between contribution margin and net profit.

## Options considered

### Option 1: Hybrid Multi Tier Architecture with Dual Key Identifiers (Chosen)

In this architecture, PostgreSQL manages operational master dimensions (menu items, categories, restaurants, promotions, users, roles, and background job metadata) using `BIGINT IDENTITY` surrogate keys. High volume transactional events (orders, order lines, ratings, wastage) are generated into immutable versioned raw snapshots (CSV and Parquet) in `data/snapshots/` carrying stable business identifiers (`source_*_id`). Cleaned and aggregated feature sets are published to columnar Parquet analytical marts in `data/marts/` scanned by FastAPI services using PyArrow. A small operational seed slice (5,000 to 10,000 orders) is synchronized to PostgreSQL for interactive demonstration and point of sale simulation.

**Pros**:
- Preserves PostgreSQL query responsiveness and low memory footprint for administrative and dashboard requests.
- Parquet columnar compression yields five to ten times storage reduction and ten to fifty times faster aggregation scans over millions of rows compared to row oriented tables.
- Dual key design enables dual independent pipelines (Spark and Python) to ingest identical, immutable raw snapshots concurrently without lock contention or relational database coupling.
- Point in time price and cost captures on order lines guarantee immutable financial ledgers.
- Avoids introducing redundant database engines like DuckDB, keeping deployment overhead minimal.

**Cons**:
- Requires maintaining schema parity between SQLAlchemy models in PostgreSQL and Parquet dataset schemas.
- Data synchronization between Parquet analytical marts and operational views requires structured background job orchestration.

### Option 2: Monolithic PostgreSQL Relational Storage for All Data

In this architecture, all one million order lines, one hundred thousand orders, and fifty thousand wastage records are stored exclusively within PostgreSQL tables. Both the web dashboard and analytics pipelines query PostgreSQL directly via JDBC or database connection pools.

**Pros**:
- Single unified storage layer with standard SQL queries for all components.
- Simplifies initial schema deployment into a single Alembic migration.

**Cons**:
- Large table scans and aggregations over millions of rows will strain PostgreSQL memory and increase API latency.
- Spark and Python pipelines running heavy analytics jobs will compete with the web application for database resources and connection pool slots.
- Violates the approved architectural constraint prohibiting million row table scans inside HTTP request handlers.
- Rejected per Project Owner Decision 4.

### Option 3: Pure Data Lake without Relational Operational Database

In this architecture, PostgreSQL is omitted entirely or relegated solely to user authentication, with all business entities and dimensions stored exclusively as flat files or Parquet tables in object storage or local filesystems.

**Pros**:
- Eliminates database migrations and ORM maintenance.
- Maximizes data science ergonomics for batch processing scripts.

**Cons**:
- Lacks ACID transactional guarantees and foreign key referential integrity for master data management (such as updating menu items, branch details, or promotion dates).
- Web application CRUD operations become sluggish and error prone when rewriting Parquet files for single row updates.
- Incompatible with standard administrative web patterns and role based permission management.

## Rationale

Option 1 is selected because it strictly fulfills all performance, operational, and architectural requirements established in the DineIQ Analytics SRS and project owner decisions. By placing operational master records and application state in PostgreSQL, the system benefits from ACID transactions, foreign key integrity, and seamless Alembic versioning. Simultaneously, by housing the massive transactional volume in immutable Parquet snapshots and columnar marts, analytical queries across millions of rows execute in sub second time using vectorized readers (PyArrow) without loading unnecessary strain onto PostgreSQL.

Crucially, capturing `unit_price_at_sale` and `unit_cost_at_sale` directly on the `order_items` record decouples the historical sales ledger from subsequent catalog modifications, ensuring that price increases or recipe reformulations do not alter past financial metrics. Maintaining `pricing_history` as an SCD Type 2 dimension provides the historical depth necessary for econometric price elasticity calculations and what if scenario modeling.

The inclusion of stable business identifiers (`source_*_id`) across all entities solves the distributed pipeline tracking challenge. Spark and Python pipelines operate directly on stable strings without requiring live database identity generation, yet every analytical finding can be joined back to operational records or source snapshots with complete integrity.

## References

**Project sources**:
- `AGENTS.md` (root architectural rules, dual pipeline independence, and columnar Parquet mart guidelines)
- `docs/specs/0001-stack-and-architecture/index.md` (foundation architecture specification)
- `packages/db/AGENTS.md` (database conventions and Parquet analytical storage separation)
- `packages/core/contracts.py` (pipeline evaluation contract definitions)
- DineIQ Analytics SRS v1.0 (requirements for dataset scales, 11 core tables, and business analytical modules)

**Practices and standards**:
- Slowly Changing Dimensions Type 2 for historical price and cost tracking
- Boston Consulting Group and Miller Matrix for restaurant menu engineering
- Vectorized columnar execution for analytical marts
- Temporal split boundaries for time series data science without future leakage
- Dual key architecture (surrogate database keys with stable business keys) for enterprise data warehousing
