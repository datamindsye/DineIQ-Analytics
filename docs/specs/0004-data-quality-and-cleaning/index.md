# 0004. Data Quality, Profiling, Cleaning, and Quarantine Pipeline

**Date**: 2026-09-25  
**Status**: Accepted  

## Summary

This specification establishes the formal architecture, operational rules, and technical implementation for the data quality, profiling, cleaning, and quarantine subsystem of the DineIQ Analytics platform. Operating between raw synthetic snapshot generation and downstream machine learning pipelines, this subsystem enforces mathematical correctness, schema conformance, referential integrity, and temporal feasibility across all eleven core business domain tables.

The subsystem adopts the immutable raw snapshot principle. Raw generated records are treated as write once and read only historical assets. All data quality defects, whether naturally occurring or intentionally injected to test enterprise resilience, are identified, measured, and quarantined into dedicated audit Parquet files. Clean records are exported to dedicated clean Parquet storage alongside an automated machine readable quality report and the authoritative four window chronological split manifest. Both downstream processing engines, Apache Spark and Python Data Science, consume this clean snapshot independently without sharing intermediate state.

## Requirements

The data quality and cleaning subsystem satisfies the following formal acceptance criteria:

- **AC-1 (Immutable Raw Input)**: Raw snapshot files in `data/snapshots/<snapshot_id>/` must never be modified, overwritten, or trimmed in place during profiling or cleaning operations.
- **AC-2 (Comprehensive Profiling)**: Profiling routines must inspect all eleven domain tables and calculate record counts, column null rates, primary key uniqueness rates, numeric distribution bounds, and cross table foreign key validity rates without mutating source data.
- **AC-3 (Deterministic Defect Isolation)**: Identified defects (duplicate identifiers, negative prices, zero quantities, future timestamps, and orphaned child references) must be isolated into `data/quarantine/<snapshot_id>/` with explicit reason tags and quarantine timestamps.
- **AC-4 (Clean Parquet Export)**: Defect free records must be exported to `data/cleaned/<snapshot_id>/` in columnar Parquet format using snappy compression, preserving full schema contract fidelity.
- **AC-5 (Exact Lineage Reconciliation)**: Total records processed must mathematically equal clean records exported plus quarantined records isolated ($\text{Raw} = \text{Cleaned} + \text{Quarantine}$) with zero unaccounted data loss.
- **AC-6 (Preservation of Valid Business States)**: Cancelled and voided orders must be preserved in cleaned tables as legitimate business states rather than treated as data quality defects.
- **AC-7 (Chronological Split Preservation)**: The four window temporal split manifest (`split_manifest.json`) must be copied directly into the clean snapshot directory to ensure downstream feature engineering and ML training adhere strictly to time aware horizons.
- **AC-8 (Machine Readable Quality Audit)**: A structured JSON audit report (`quality_report.json`) must be generated recording processing totals, table level row counts, quarantine reason breakdowns, and overall pass or fail status.

## Decision

**Chosen architecture**: Local PyArrow based streaming profiler and cleaner in `packages/common/quality/` for primary snapshot processing, combined with formal quality rules in `rules.py` and deferred distributed Spark SQL cleaning for multi node scale out in Phase 7.

**Implementation skills**: `architect` (`skills/architect/`), `develop` (`skills/develop/`)

---

## Data Quality and Cleaning Architecture

### 1. Purpose and Scope

The data quality subsystem bridges raw synthetic snapshot storage (`data/snapshots/`) and downstream analytical pipelines (`packages/pipeline_spark`, `packages/pipeline_python`). Its primary responsibilities are:
1. Validating source Parquet tables against the formal dataset contracts defined in `packages/core/contracts/dataset_contract.py`.
2. Measuring and reporting data anomalies, completeness rates, and referential integrity across all eleven business entities.
3. Filtering out defective records into an isolated quarantine storage layer while appending actionable root cause audit attributes.
4. Exporting pristine, analysis ready Parquet datasets into `data/cleaned/` that downstream models can ingest without further defensive sanitization.

### 2. Immutable Raw Snapshot Principle

To satisfy enterprise auditability and ensure scientific reproducibility across competition evaluation runs, all files in `data/snapshots/` are strictly immutable:
- Ingestion routines open raw Parquet files with read only flags.
- No cleaning script or database migration may execute `UPDATE`, `DELETE`, or in place overwrites on files residing within `data/snapshots/`.
- Every cleaning run produces a completely separate directory hierarchy under `data/cleaned/<snapshot_id>/` and `data/quarantine/<snapshot_id>/`.
- If cleaning rules are modified in future iterations, raw snapshots can be reprocessed from scratch with full mathematical reproducibility.

### 3. Profiling Architecture

The profiling engine is implemented in `packages/common/quality/profiler.py` via the `DataQualityProfiler` class:
- **Scan Strategy**: Employs PyArrow columnar scanners to read table metadata and selected column chunks efficiently without loading entire tables into uncompressed Python memory.
- **Per Table Metrics**:
  - Total record count and physical byte size.
  - Column null counts and nullability percentages.
  - Unique count and duplicate rate on surrogate and business keys (`source_*_id`).
  - Min, max, mean, and quantile statistics for numeric monetary columns (`unit_price_at_sale`, `total_amount`, `cost_loss_amount`).
  - Earliest and latest timestamp bounds for all temporal fields.
- **Cross Table Referential Integrity**:
  - Extracts distinct key sets for parent entities (`restaurants`, `menu_items`, `customers`, `orders`, `promotions`).
  - Evaluates child foreign key columns against parent key sets, calculating exact match rates and identifying orphaned keys.
- **Output Structure**: Returns a structured Python dictionary serialization ready for JSON export or dashboard display.

### 4. Quality Rules Framework

Quality rules are formally registered in `packages/common/quality/rules.py` through the `QualityRule` data model:
- **Rule Categories**:
  - `RuleCategory.SCHEMA`: Data type compatibility, required column presence, PyArrow schema conformance.
  - `RuleCategory.COMPLETENESS`: Disallowed null values in mandatory fields.
  - `RuleCategory.INTEGRITY`: Uniqueness of identifiers and referential integrity across parent child relationships.
  - `RuleCategory.TEMPORAL`: Logical chronological progression and prevention of future dated records.
  - `RuleCategory.VALIDITY`: Value range boundaries, positive monetary constraints, and enumeration membership.
- **Rule Severities**:
  - `RuleSeverity.CRITICAL`: Pipeline blocking defects (missing essential primary key column, schema corruption).
  - `RuleSeverity.ERROR`: Record level defect requiring quarantine (duplicate business key, negative price, future timestamp).
  - `RuleSeverity.WARNING`: Acceptable operational condition requiring informational logging (negative contribution margin on promotions, high wastage rate).
  - `RuleSeverity.INFO`: Expected business nuance (guest checkout with null customer identifier).

### 5. Null and Uniqueness Checks

The cleaning pipeline applies precise discrimination between defective nulls and legitimate business nulls:
- **Disallowed Nulls (Quarantined if violated)**:
  - `orders.source_order_id`, `orders.order_timestamp`, `orders.total_amount`
  - `order_items.source_order_item_id`, `order_items.unit_price_at_sale`, `order_items.quantity`
  - `customers.source_customer_id`, `customers.registration_date`
  - `menu_items.source_menu_item_id`, `menu_items.current_base_price`
- **Permissible Nulls (Preserved in clean dataset)**:
  - `orders.customer_id`: Exactly 10% of orders represent guest checkouts where diners order without registering an account. These are legitimate transactions and remain in clean orders.
  - `customers.phone` and `customers.email`: Up to 15% of customer accounts lack contact details.
  - `ratings.review_text`: Approximately 40% of customer ratings provide numerical star scores without written reviews.
  - `pricing_history.effective_to`: Active price records carry null end dates to designate currently effective menu prices.
- **Uniqueness Validation**:
  - Primary business keys (`source_customer_id`, `source_restaurant_id`, `source_order_id`, `source_order_item_id`, etc.) are checked for exact uniqueness. Duplicate records are detected and isolated.

### 6. Duplicate Detection and Resolution

- **Detection Mechanism**: The cleaner maintains in memory hash sets of observed business identifiers (`source_order_id`, `source_order_item_id`) during batch processing.
- **Resolution Strategy**: When a duplicate identifier is encountered:
  1. The first occurrence is treated as the original authoritative record and accepted into the clean dataset.
  2. Any subsequent occurrence sharing that identifier is immediately diverted into the quarantine table.
  3. The duplicate is tagged with reason code `DUPLICATE_ORDER_ID` or `DUPLICATE_ORDER_ITEM_ID`.
- **Benchmark Evidence**: In the competition benchmark dataset, this caught 508 duplicate orders (0.505% injection rate) and 5,027 duplicate order items (0.500% injection rate), matching the configured generator rates.

### 7. Invalid Value and Outlier Detection

- **Price and Cost Positivity**:
  - Menu item sales prices must be strictly non negative (`unit_price_at_sale >= 0.00`).
  - Records with negative unit prices (intentional data defect injected at 0.2% rate) are quarantined under `INVALID_NEGATIVE_PRICE`.
- **Quantity Positivity**:
  - Order line quantities must be strictly positive integers (`quantity > 0`).
  - Records with zero quantity (injected defect at 0.1% rate) are quarantined under `INVALID_ZERO_QUANTITY`.
- **Rating Score Bounds**:
  - Ratings must fall strictly within the inclusive integer range 1 to 5 (`rating_score BETWEEN 1 AND 5`).
  - Out of range ratings are quarantined or clamped depending on severity.
- **Inventory Bounds**:
  - Ingredient stock levels must not be negative (`current_stock_quantity >= 0.00`). Minor sensor drift or inventory count errors are clamped to zero and flagged for audit.

### 8. Timestamp and Future Date Validation

- **Generation Cutoff Rule**: For any snapshot generated at timestamp $T_{\text{snapshot}}$, all historical event timestamps must satisfy:
  $$t_{\text{event}} \le T_{\text{snapshot}}$$
- **Future Timestamp Quarantine**:
  - Point of sale clocks occasionally desynchronize, or simulated data may contain future timestamps.
  - The cleaner checks each `order_timestamp` against the snapshot cutoff datetime.
  - Any order dated after the generation cutoff is diverted to quarantine under `FUTURE_TIMESTAMP`.
- **Benchmark Evidence**: Identified and quarantined 46 future dated orders (0.046% rate) containing timestamps ranging from May 2026 to May 2027.

### 9. Referential Integrity and Cascading Quarantine

- **Parent Child Integrity**:
  - `order_items.source_order_id` must reference an existing record in `orders`.
  - `order_items.source_menu_item_id` must reference an existing record in `menu_items`.
  - `orders.source_restaurant_id` must reference an existing record in `restaurants`.
- **Cascading Quarantine Rule**:
  - If a parent order is quarantined (due to a duplicate identifier or a future timestamp), its associated order line items can no longer be linked to a valid clean order header.
  - Rather than leaving orphaned records in the clean order items table, all child lines belonging to a quarantined order are automatically quarantined under reason code `ORPHANED_ORDER_PARENT`.
- **Benchmark Evidence**: Quarantining 554 orders resulted in the cascading isolation of 475 child order items, ensuring that 100% of line items in `data/cleaned/` join seamlessly to clean orders.

### 10. Financial Consistency Verification

The cleaning pipeline validates financial invariants across transaction records:
- **Line Level Revenue**:
  $$\text{line\_net\_revenue} = (\text{quantity} \times \text{unit\_price\_at\_sale}) - \text{line\_discount}$$
- **Line Level Contribution Margin**:
  $$\text{line\_contribution\_margin} = \text{line\_net\_revenue} - (\text{quantity} \times \text{unit\_cost\_at\_sale})$$
- **Order Level Total Settlement**:
  $$\text{total\_amount} = \text{subtotal\_amount} - \text{discount\_amount} + \text{tax\_amount} + \text{tip\_amount}$$
- Any discrepancy exceeding one cent ($| \Delta | > 0.01$) due to rounding or corruption is flagged for review.

### 11. Handling Business Valid Cancelled and Voided Records

A critical distinction in the DineIQ data quality architecture is separating true data defects from valid negative business events:
- **Cancelled and Voided Orders**:
  - Approximately 3.5% of restaurant orders are cancelled prior to fulfillment, and 0.5% are voided due to customer payment or kitchen errors.
  - These records represent genuine operational activity, not data quality corruptions.
  - **Treatment**: Cancelled and voided orders are fully retained in `data/cleaned/competition_benchmark_v1/orders.parquet`.
- **Downstream Consumption Rule**:
  - Realized sales and revenue dashboards filter for `order_status == 'Completed'`.
  - Cancellation risk models and kitchen operational efficiency metrics explicitly require the cancelled records to compute historical loss ratios.

### 12. Intentional Anomaly Detection

The cleaner successfully validates the presence and proper handling of all seventeen complexity patterns generated in Spec 0003:
- **Promotion Traps**: Campaigns where high promotional volume yields negative contribution margin are preserved in clean data for downstream margin protection modeling.
- **Rating Collapse**: Localized rating drops on dishes following recipe cost reductions are preserved in clean data for anomaly detection models.
- **Seasonal and Hourly Curves**: Natural bimodal meal peaks and weekend surges pass all validity checks and remain intact.

### 13. Quarantine Strategy and Schema Enrichment

Quarantined records are isolated into dedicated Parquet files in `data/quarantine/<snapshot_id>/`:
- `orders_quarantine.parquet`
- `order_items_quarantine.parquet`
- **Schema Enrichment**: Every quarantined row is enriched with two mandatory diagnostic columns:
  1. `quarantine_reason` (string): The explicit violation code (`DUPLICATE_ORDER_ID`, `FUTURE_TIMESTAMP`, `INVALID_NEGATIVE_PRICE`, `INVALID_ZERO_QUANTITY`, `ORPHANED_ORDER_PARENT`).
  2. `quarantined_at` (timestamp with timezone UTC): The exact UTC timestamp when the record was isolated.
- This design enables compliance auditing, defect triage, and automated reporting without modifying the original raw payload schema.

### 14. Cleaned Parquet Outputs

The output of the cleaning pipeline resides in `data/cleaned/<snapshot_id>/`:
- Contains all eleven domain tables in Apache Parquet format.
- Uses snappy compression for optimal balance between read throughput and disk footprint.
- All column data types match the formal PyArrow schemas defined in `packages/core/contracts/dataset_contract.py`.
- Verified record counts for `competition_benchmark_v1`:
  - `menu_categories`: 10 rows
  - `restaurants`: 20 rows
  - `menu_items`: 150 rows
  - `customers`: 50,000 rows
  - `pricing_history`: 1,500 rows
  - `promotions`: 25 rows
  - `orders`: 99,954 rows
  - `order_items`: 997,561 rows
  - `ratings`: 100,000 rows
  - `inventory`: 3,000 rows
  - `wastage`: 50,000 rows
  - Total Clean Records: **1,302,220 rows**

### 15. Machine Readable Quality Report

The cleaner writes `quality_report.json` into the root of the cleaned snapshot directory. The report provides an authoritative, automated summary:
- `snapshot_id`: Identifier of the processed snapshot.
- `cleaning_timestamp`: ISO 8601 UTC timestamp of execution completion.
- `overall_status`: Status indicator (`PASSED_WITH_QUARANTINE` or `FAILED`).
- `totals`:
  - `raw_records_processed`: 1,311,264
  - `cleaned_records_output`: 1,302,220
  - `quarantined_records_isolated`: 9,044
  - `cleanliness_rate_pct`: 99.31%
- `cleaned_row_counts`: Table by table clean counts.
- `quarantined_row_counts`: Table by table quarantined counts.
- `quarantine_reasons`: Detailed breakdown of defect frequencies.

### 16. Raw, Quarantine, and Cleaned Lineage

The subsystem guarantees absolute mathematical reconciliation across the lifecycle:

```
                      +-----------------------------------+
                      |      Raw Snapshot (1,311,264)     |
                      | data/snapshots/<snapshot_id>/     |
                      +-----------------+-----------------+
                                        |
                         [ Data Quality Cleaner ]
                                        |
                +-----------------------+-----------------------+
                | (99.31% Valid)                                | (0.69% Defective)
                v                                               v
+-------------------------------+               +-------------------------------+
|    Cleaned Parquet Snapshot   |               |       Quarantine Storage      |
| data/cleaned/<snapshot_id>/   |               | data/quarantine/<snapshot_id>/|
| - 1,302,220 clean records     |               | - 9,044 quarantined records   |
| - 11 defect-free tables       |               | - Diagnostic reason codes     |
| - split_manifest.json         |               | - orders_quarantine.parquet   |
| - quality_report.json         |               | - order_items_quarantine      |
+---------------+---------------+               +-------------------------------+
                |
                +-----------------------+
                | (Shared Read Only)    | (Shared Read Only)
                v                       v
+-------------------------------+ +-------------------------------+
| Pipeline 1: Apache Spark      | | Pipeline 2: Python Data Science
| packages/pipeline_spark       | | packages/pipeline_python      |
+-------------------------------+ +-------------------------------+
```

Lineage equation:
$$\text{Raw Records Processed} = \text{Clean Records Output} + \text{Quarantined Records Isolated}$$
$$1,311,264 = 1,302,220 + 9,044$$

### 17. Temporal Split Preservation

The four window chronological ML split defined in Spec 0003 is preserved throughout the cleaning process:
- The cleaning engine copies `split_manifest.json` directly from the raw snapshot directory into `data/cleaned/<snapshot_id>/split_manifest.json`.
- Analysis of cleaned orders demonstrates exact adherence to the planned temporal proportions:
  - **TRAIN** (2025-01-01 to 2025-08-31): 66,631 orders (66.66% of clean orders, 66.58% of calendar days)
  - **VALIDATION** (2025-09-01 to 2025-10-31): 16,605 orders (16.61% of clean orders, 16.71% of calendar days)
  - **TEST** (2025-11-01 to 2025-11-30): 8,230 orders (8.23% of clean orders, 8.22% of calendar days)
  - **UNSEEN_COMPARISON** (2025-12-01 to 2025-12-31): 8,488 orders (8.49% of clean orders, 8.49% of calendar days)
- Quarantined orders did not skew these proportions because duplicate orders and future timestamps were uniformly distributed or isolated beyond the 2025 calendar year.

### 18. Downstream Spark and Python Compatibility

The cleaned Parquet tables serve as the single source of truth for both analytics pipelines:
- **Strict Decoupling**: Apache Spark (`packages/pipeline_spark`) and Python Data Science (`packages/pipeline_python`) read directly from `data/cleaned/<snapshot_id>/`.
- **Zero Shared State**: Neither pipeline writes back to `data/cleaned/` or reads intermediate dataframes from the other pipeline.
- **Native Parquet Loading**: Both pipelines ingest the clean tables via native columnar readers (`spark.read.parquet()` and `pd.read_parquet()` / `pq.read_table()`) with identical column datatypes and schema guarantees.

### 19. Current Implementation vs Deferred Spark Scale Out

To maintain architectural transparency, this specification clearly delineates current capabilities from planned enhancements:
- **Implemented in Current Codebase (Phase 2 / Phase 6)**:
  - High performance Python and PyArrow single workstation cleaner and profiler in `packages/common/quality/`.
  - Processes over 1.3 million rows in approximately 15 seconds with minimal RAM usage.
  - Complete quarantine isolation, Parquet table export, CLI command interface, and automated pytest suite.
- **Deferred to Phase 7 (Distributed Spark Pipeline)**:
  - Multi node distributed PySpark cleaning jobs for datasets exceeding tens of gigabytes or streaming message queues.
  - Distributed Spark SQL deduplication and broadcast join referential integrity validation across cluster nodes.
  - Automated scheduling of recurring cleaning jobs via the `job_runs` table in PostgreSQL.

### 20. SRS Traceability and Verification Matrix

| SRS Quality Requirement | Implemented Mechanism | Code Location | Verification Evidence |
|---|---|---|---|
| **Data Cleaning Pipeline** | `DataQualityCleaner.clean_and_quarantine()` | `packages/common/quality/cleaner.py` | Cleaned 1.302M rows to `data/cleaned/` |
| **Referential Integrity** | Parent key set validation & cascading quarantine | `cleaner.py` (lines 80-160) | Quarantined 475 orphaned items |
| **Duplicate Removal** | Seen ID hash sets & quarantine diverter | `cleaner.py` (lines 90-130) | Isolated 508 duplicate orders |
| **Outlier & Range Defense** | Negative price & zero quantity filters | `cleaner.py` (lines 140-180) | Isolated 1,964 price & 1,024 qty errors |
| **Future Date Prevention** | UTC generation cutoff timestamp check | `cleaner.py` (lines 85-110) | Quarantined 46 future orders |
| **Quality Reporting** | Automated JSON audit summary export | `cleaner.py` (lines 200-240) | `quality_report.json` generated |
| **Unit Test Coverage** | Pytest test suite for profiler & cleaner | `tests/unit/test_data_quality.py` | 14/14 data unit tests passing |

---

## Build plan

The build plan reflects the completed Tracer Bullet delivery of the data quality subsystem:

1. Formalize quality rules and severity classifications in `packages/common/quality/rules.py`.
2. Construct the data quality profiler in `packages/common/quality/profiler.py` to inspect nullability, key uniqueness, and referential integrity.
3. Build the data quality cleaner in `packages/common/quality/cleaner.py` implementing duplicate detection, value range enforcement, cascading quarantine, and clean Parquet export.
4. Provide a command line interface in `packages/common/quality/cli.py` supporting `profile` and `clean` subcommands.
5. Create automated unit tests in `tests/unit/test_data_quality.py` validating quarantine mechanics, reason codes, and report generation.
6. Execute the cleaning pipeline against `competition_benchmark_v1` raw snapshot and verify output cleanliness.

## Consequences

**Positive**:
- Guarantees pristine, validated inputs for machine learning models, eliminating silent training failures caused by future timestamps, negative prices, or orphaned lines.
- Complete auditability: every removed row is preserved in quarantine with an explicit reason code, allowing forensic inspection of data quality issues.
- Absolute data lineage: raw record count strictly equals clean record count plus quarantined count.
- Shared clean starting point enables fair and unbiased cross pipeline comparison between Apache Spark and Python Data Science.

**Negative and Tradeoffs**:
- Requires local disk space for three separate copies of transaction tables: raw snapshot (~25MB), cleaned Parquet (~22MB), and quarantine Parquet (~0.3MB).
- Cascading quarantine drops child order items when parent orders are defective, slightly reducing transaction volume (by 0.84% on order items) in exchange for perfect referential integrity.

## Follow-up

- [x] Implement the data quality profiler and cleaner engine in `packages/common/quality/`.
- [x] Execute cleaning on `competition_benchmark_v1` raw snapshot.
- [x] Verify quarantine outputs and quality report artifact.
- [ ] Connect the clean Parquet dataset to Phase 7: Apache Spark Ingestion and Feature Engineering (`packages/pipeline_spark/`).
- [ ] Connect the clean Parquet dataset to Phase 8: Independent Python Data Science Pipeline (`packages/pipeline_python/`).

## Rationale

Detailed architectural context, options evaluated, and decision tradeoffs are recorded in [rationale.md](rationale.md).
