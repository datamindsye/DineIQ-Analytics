# Epic: Data

Dataset generation and data quality pipeline. These feed every analytics and ML feature.

---

### 5. Dataset generation script

A reproducible script that generates realistic restaurant data at the required scale across all 11 source tables. The generated data must include realistic complexity: missing values, duplicates, invalid transactions, cancelled orders, changing prices, seasonal demand, weekend and peak patterns, location differences, promotions, high value customers, churned and new customers, popular low margin dishes, profitable low selling dishes, high wastage dishes, rating and sales anomalies, price sensitive items, and misleading promotions.

**Done when:** the script generates all 11 tables at the specified minimum scale (1M order lines, 100K orders, 50K customers, 150 menu items, 10 categories, 20 locations, 12 months history, 100K ratings, 50K wastage records); output is reproducible with a fixed seed; data contains all 17 complexity patterns listed above; output includes both relational DB inserts and Parquet files; a data dictionary document describes every column.

- [x] Design it (spec): [0003](../specs/0003-dataset-contract-and-generation-strategy/index.md)
- [x] Build it: `packages/common/generator/`
  - [x] Create generator configuration schemas and domain distributions (AC-1, AC-4)
  - [x] Implement deterministic master catalog and customer generator (AC-1, AC-3)
  - [x] Implement high volume transaction generator with metrics and complexity patterns (AC-2, AC-5, AC-7)
  - [x] Implement manifest creation and chronological split manifest exporter (AC-6, AC-8)
  - [x] Create generator CLI entrypoint and automated unit test suite (AC-1, AC-2, AC-6)
- [x] Verify it: verified against `competition_benchmark_v1` (1,311,264 raw records generated across 11 tables)
- [x] Test it: `tests/unit/test_generator.py` and `tests/unit/test_dataset_contract.py`
- [x] Document it: [docs/data-dictionary.md](../data-dictionary.md) and [docs/reports/dataset_inspection_report.md](../reports/dataset_inspection_report.md)

---

### 6. Data quality and cleaning pipeline

Detection and handling of data quality issues: missing values, duplicates, invalid transactions, type mismatches, referential integrity violations, and outlier identification. Produces a clean snapshot that both Spark and Python pipelines consume independently from the same starting point.

**Done when:** quality checks run on all 11 tables; issues are logged with counts and categories; cleaning rules are documented; the clean snapshot is exported as Parquet; both pipelines can independently load the same clean snapshot; a data quality report summarizes what was found and fixed.

- [x] Design it (spec): [0004](../specs/0004-data-quality-and-cleaning/index.md)
- [x] Build it: `packages/common/quality/` (profiler, cleaner, rules, cli)
- [x] Verify it: verified against `competition_benchmark_v1` (99.31% cleanliness, 9,044 quarantined)
- [x] Test it: `tests/unit/test_data_quality.py`
- [x] Document it: [docs/reports/dataset_inspection_report.md](../reports/dataset_inspection_report.md) and [docs/development_log.md](../development_log.md)

