# 0004. Data Quality, Profiling, Cleaning, and Quarantine Pipeline — Scope

This document defines the functional boundaries, acceptance criteria, component breakdown, and dependency mapping for the Data Quality, Profiling, Cleaning, and Quarantine subsystem.

---

## 1. Feature Context and Scope Placement

- **Epic**: Data (`docs/scope/data.md`)
- **Feature Name**: Feature 6: Data quality and cleaning pipeline
- **Direct Predecessors**:
  - Feature 4: Domain schemas and database migrations (Spec 0002)
  - Feature 5: Dataset contract and synthetic generation engine (Spec 0003)
- **Direct Successors**:
  - Feature 7: Apache Spark ingestion and feature engineering (`packages/pipeline_spark`)
  - Feature 8: Independent Python data science feature engineering (`packages/pipeline_python`)

---

## 2. Scope Boundaries

### In Scope
1. **Raw Snapshot Consumption**: Ingestion of raw columnar Parquet tables generated in `data/snapshots/<snapshot_id>/` without modifying source files.
2. **Comprehensive Profiling Engine**:
   - Table level row counting and schema verification.
   - Column level null rate profiling and uniqueness checking.
   - Cross table foreign key referential integrity analysis across all eleven domain entities.
   - Summary statistics (min, max, mean, quantiles) for numeric monetary and quantity fields.
3. **Data Quality Rules Engine**:
   - Explicit registration of quality rules categorized by Schema, Completeness, Integrity, Temporal, and Validity.
   - Classification of rules into Critical, Error, Warning, and Info severity levels.
4. **Data Cleaning and Defect Quarantine**:
   - Identification and deduplication of repeated business keys (`source_order_id`, `source_order_item_id`).
   - Range validation isolating negative prices and zero quantities.
   - Future timestamp detection isolating orders with dates beyond the generation cutoff.
   - Cascading quarantine isolating orphaned order item lines whose parent order was quarantined.
   - Appending diagnostic audit attributes (`quarantine_reason`, `quarantined_at`) to quarantined records.
5. **Clean Parquet Export**: Writing clean, defect free tables to `data/cleaned/<snapshot_id>/` with identical schema contract guarantees.
6. **Temporal Split Preservation**: Copying `split_manifest.json` to the cleaned snapshot directory to maintain authoritative train, validation, test, and unseen comparison windows.
7. **Quality Reporting**: Producing an automated, machine readable JSON audit report (`quality_report.json`) documenting row counts, quarantine breakdown, and cleanliness percentages.
8. **Command Line Interface & Test Automation**:
   - CLI commands (`profile`, `clean`) in `packages/common/quality/cli.py`.
   - Comprehensive unit test suite in `tests/unit/test_data_quality.py`.

### Out of Scope (Deferred or Prohibited)
1. **In Place Raw Data Modification**: Overwriting or deleting files in `data/snapshots/` is strictly prohibited.
2. **Distributed Spark Cluster Cleaning (Deferred to Phase 7)**: Distributed multi node PySpark cleaning for multi gigabyte streaming streams is deferred to the Spark pipeline milestone.
3. **Relational Database Bulk Staging**: Direct bulk ingestion of all 1.3 million rows into PostgreSQL tables is out of scope for the analytical Parquet mart workflow.
4. **Machine Learning Feature Engineering**: Feature transformations (RFM calculations, rolling lag windows, one hot encoding) belong in downstream pipelines, not in the cleaning layer.
5. **Dashboard Presentation Logic**: UI visualization of quality metrics is deferred to the web application dashboard milestone.

---

## 3. Detailed Component Breakdown

| Component | File Path | Primary Responsibility |
|---|---|---|
| **Quality Rules** | `packages/common/quality/rules.py` | Declares quality rule dataclasses, categories, severities, and the registry of active rules. |
| **Profiler Engine** | `packages/common/quality/profiler.py` | Inspects raw tables via PyArrow, computing nullability, duplicates, distributions, and referential integrity. |
| **Cleaner Engine** | `packages/common/quality/cleaner.py` | Executes cleaning filters, routes defects to quarantine, exports clean Parquet, and writes the quality report. |
| **CLI Entrypoint** | `packages/common/quality/cli.py` | Provides command line execution interface for running profiling and cleaning on specified snapshots. |
| **Package Interface** | `packages/common/quality/__init__.py` | Exports public classes (`DataQualityProfiler`, `DataQualityCleaner`, `QualityRule`, `RuleCategory`, `RuleSeverity`). |
| **Unit Test Suite** | `tests/unit/test_data_quality.py` | Automated pytest verification of profiler, cleaner, quarantine mechanics, and report schema. |

---

## 4. Acceptance Criteria & Verification Mapping

| AC ID | Acceptance Criteria | Implementation Mechanism | Verification Test / Evidence |
|---|---|---|---|
| **AC-1** | Immutable raw inputs | Read only PyArrow table access in `profiler.py` and `cleaner.py` | Source timestamps in `data/snapshots/` remain unchanged after cleaning. |
| **AC-2** | Full table profiling | `DataQualityProfiler.profile_all()` | `test_data_quality.py::test_data_quality_profiler_and_cleaner_workflow` |
| **AC-3** | Isolated quarantine with reasons | `DataQualityCleaner._write_quarantine_table()` | `test_data_quality.py::test_quarantine_metadata_and_reasons` |
| **AC-4** | Clean Parquet export | `pq.write_table()` to `data/cleaned/<snapshot_id>/` | 11 clean Parquet files verified on disk; schema validation passes. |
| **AC-5** | Exact lineage reconciliation | Lineage equality verified in cleaner and tests | $1,302,220 \text{ clean} + 9,044 \text{ quarantine} = 1,311,264 \text{ raw}$. |
| **AC-6** | Preservation of valid states | Cancelled & voided orders preserved in clean orders | 3,500+ cancelled orders retained in `cleaned/orders.parquet`. |
| **AC-7** | Temporal split preservation | `split_manifest.json` copied to cleaned snapshot | 4 split windows verified with 66.66% / 16.61% / 8.23% / 8.49% orders. |
| **AC-8** | Machine readable report | `quality_report.json` generated with full statistics | `quality_report.json` verified with 99.31% cleanliness status. |

---

## 5. Dependencies and Traceability

- **Upstream Dependencies**:
  - `packages/core/contracts/dataset_contract.py`: Provides authoritative PyArrow schemas, regex identifier patterns, and financial formulas.
  - `data/snapshots/<snapshot_id>/`: Raw input snapshot generated by `packages/common/generator/`.
- **Downstream Consumers**:
  - `packages/pipeline_spark`: Ingests clean Parquet tables for Spark SQL marts and MLlib models.
  - `packages/pipeline_python`: Ingests clean Parquet tables for Pandas feature engineering and scikit-learn models.
  - `apps/api/routers/analytics.py`: Exposes analytical marts computed from the clean data.
