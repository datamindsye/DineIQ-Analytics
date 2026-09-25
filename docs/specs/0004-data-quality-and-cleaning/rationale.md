# 0004. Data Quality, Profiling, Cleaning, and Quarantine Pipeline — Decision Record

## Context

The DineIQ Analytics platform ingests high volume transactional data across eleven core business entities. In real world food service enterprises, point of sale terminals, mobile ordering gateways, third party delivery aggregators, and inventory sensors frequently introduce operational complexities and data defects:
1. Network retries at checkout terminals cause duplicate transaction order headers and line item submissions.
2. Device clock desynchronizations and timezone misconfigurations create future dated order records that corrupt chronological time series forecasts.
3. Accounting reversals and manual cash register adjustments produce invalid negative unit prices or zero line item quantities.
4. Dropped parent headers or incomplete batch transmissions yield orphaned order items that lack valid order identifiers.
5. Diners frequently order as guests without logging in, resulting in legitimate transactions with null customer identifiers.

Furthermore, in accordance with the competition Software Requirements Specification and Architecture Spec 0003, the synthetic generator deliberately injected seventeen realistic business complexities and controlled data quality defects into the raw snapshot (`competition_benchmark_v1`). To demonstrate enterprise readiness, the platform cannot simply assume pristine data or silently discard corrupt records. It must detect, profile, quarantine, and document every defect with complete audit transparency while delivering an uncontaminated analytical dataset to downstream machine learning models.

## Options considered

### Option 1: Dedicated PyArrow Profiling and Cleaning Engine with Defect Quarantine (Chosen)

In this approach, a standalone data quality subsystem implemented in `packages/common/quality/` operates directly on raw Parquet snapshots. It reads raw data using high performance columnar PyArrow scanners, applies registered validation rules, isolates defective records into a separate `data/quarantine/` layer with appended audit reason codes, exports pristine Parquet files to `data/cleaned/`, and outputs a machine readable `quality_report.json`.

**Pros**:
- Strictly upholds the immutable raw snapshot principle; raw historical data is never modified in place.
- Provides a single, clean starting point shared by both Apache Spark and Python Data Science pipelines, preventing duplicate cleaning logic and ensuring fair model comparison.
- Isolating defects into quarantine Parquet files preserves complete mathematical reconciliation ($\text{Raw} = \text{Cleaned} + \text{Quarantine}$) and provides full compliance auditability.
- Fast local execution: cleans over 1.3 million records in under 15 seconds on a developer laptop without requiring a heavyweight Spark cluster startup.
- Preserves business valid nuances (guest checkouts, cancelled orders, misleading promotions) while filtering true corruptions.

**Cons**:
- Requires disk storage for both raw and cleaned Parquet snapshots.
- Single node memory footprint must be managed through streaming or columnar chunking when scaling to tens of millions of records.

### Option 2: Inline In Memory Cleaning Inside Each Analytics Pipeline

In this approach, the data quality subsystem is omitted. Instead, the Apache Spark pipeline (`packages/pipeline_spark`) and the Python pipeline (`packages/pipeline_python`) each implement their own in memory filtering, deduplication, and range checking logic after loading the raw snapshot.

**Pros**:
- Eliminates the intermediate `data/cleaned/` disk storage layer.

**Cons**:
- Severe violation of the DRY (Don't Repeat Yourself) principle: data cleaning rules must be written twice, once in Spark SQL / PySpark and once in Pandas / NumPy.
- High risk of pipeline divergence: slight differences in how Spark and Python handle floating point comparisons, null values, or tie breaking during deduplication would lead to slightly different training sets, undermining the validity of cross pipeline model comparison.
- Destroys auditability: defective records are silently dropped in memory during ETL passes without leaving permanent quarantine evidence or lineage records.

### Option 3: Relational Staging and Database Stored Procedure Cleaning

In this approach, all raw snapshot records are staged into PostgreSQL operational tables, cleaned via SQL queries, triggers, or stored procedures, and then re exported to Parquet for machine learning consumption.

**Pros**:
- Leverages existing relational constraints and foreign key triggers in PostgreSQL.

**Cons**:
- Massive performance bottleneck: inserting, indexing, and scanning over 1.3 million rows in a relational database takes significantly longer than columnar Parquet processing.
- Violates the core architecture rule mandating fast columnar analytics: web dashboards and ML pipelines must query Parquet marts directly rather than putting transactional scan load on PostgreSQL.
- Introduces unnecessary statefulness and database infrastructure dependencies for batch analytics workflows.

## Rationale

Option 1 was chosen because it cleanly separates concerns, guarantees strict dual pipeline independence, and satisfies every competition auditability requirement:
1. **Dual Pipeline Independence**: Both Apache Spark and Python Data Science start from the exact same clean Parquet files. Neither pipeline has to reinvent cleaning rules, and neither pipeline can blame data discrepancy for differences in model accuracy or execution runtime.
2. **Defect Transparency**: Quarantining defective records rather than deleting them allows reviewers and store managers to inspect why records were rejected. Every quarantined record clearly states whether it was rejected due to `DUPLICATE_ORDER_ID`, `FUTURE_TIMESTAMP`, `INVALID_NEGATIVE_PRICE`, `INVALID_ZERO_QUANTITY`, or `ORPHANED_ORDER_PARENT`.
3. **High Performance**: Implementing the primary snapshot cleaner in PyArrow provides microsecond level record validation, completing the full 1.31 million row competition benchmark in approximately 15 seconds.
4. **Tracer Bullet Alignment**: This architecture proved that the entire data ingestion, profiling, quarantine, and cleaning pipe works seamlessly prior to constructing downstream ML models.

## Evidence and Benchmark Metrics

The subsystem was verified against the official competition benchmark raw snapshot (`data/snapshots/competition_benchmark_v1/`). The actual execution metrics recorded in `data/cleaned/competition_benchmark_v1/quality_report.json` demonstrate:

| Table Name | Raw Processed | Clean Output | Quarantined Isolated | Primary Quarantine Reason |
|---|---|---|---|---|
| `menu_categories` | 10 | 10 | 0 | None (100% valid) |
| `restaurants` | 20 | 20 | 0 | None (100% valid) |
| `menu_items` | 150 | 150 | 0 | None (100% valid) |
| `pricing_history` | 1,500 | 1,500 | 0 | None (100% valid) |
| `promotions` | 25 | 25 | 0 | None (100% valid) |
| `customers` | 50,000 | 50,000 | 0 | None (100% valid) |
| `inventory` | 3,000 | 3,000 | 0 | None (100% valid) |
| `orders` | 100,508 | 99,954 | 554 | 508 duplicate orders, 46 future timestamps |
| `order_items` | 1,006,051 | 997,561 | 8,490 | 5,027 duplicate lines, 1,964 negative prices, 1,024 zero qty, 475 orphaned |
| `ratings` | 100,000 | 100,000 | 0 | None (100% valid) |
| `wastage` | 50,000 | 50,000 | 0 | None (100% valid) |
| **Total** | **1,311,264** | **1,302,220** | **9,044** | Overall Cleanliness Rate: **99.31%** |

Exact mathematical balance:
$$1,302,220 \text{ clean} + 9,044 \text{ quarantined} = 1,311,264 \text{ raw records processed}$$

## References

1. Architecture Specification 0001: [0001-stack-and-architecture](../0001-stack-and-architecture/index.md)
2. Architecture Specification 0002: [0002-data-model-and-schema](../0002-data-model-and-schema/index.md)
3. Architecture Specification 0003: [0003-dataset-contract-and-generation-strategy](../0003-dataset-contract-and-generation-strategy/index.md)
4. Authoritative Data Dictionary: [data-dictionary.md](../../data-dictionary.md)
5. Core Dataset Contracts: [dataset_contract.py](../../../packages/core/contracts/dataset_contract.py)
