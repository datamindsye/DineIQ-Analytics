# Epic: Data

Dataset generation and data quality pipeline. These feed every analytics and ML feature.

---

### 5. Dataset generation script

A reproducible script that generates realistic restaurant data at the required scale across all 11 source tables. The generated data must include realistic complexity: missing values, duplicates, invalid transactions, cancelled orders, changing prices, seasonal demand, weekend and peak patterns, location differences, promotions, high value customers, churned and new customers, popular low margin dishes, profitable low selling dishes, high wastage dishes, rating and sales anomalies, price sensitive items, and misleading promotions.

**Done when:** the script generates all 11 tables at the specified minimum scale (1M order lines, 100K orders, 50K customers, 150 menu items, 10 categories, 20 locations, 12 months history, 100K ratings, 50K wastage records); output is reproducible with a fixed seed; data contains all 17 complexity patterns listed above; output includes both relational DB inserts and Parquet files; a data dictionary document describes every column.

- [x] Design it (spec): [0003](../specs/0003-dataset-contract-and-generation-strategy/index.md)
- [ ] Build it: `/develop dataset generation script`
  - [ ] Create generator configuration schemas and domain distributions (AC-1, AC-4)
  - [ ] Implement deterministic master catalog and customer generator (AC-1, AC-3)
  - [ ] Implement high volume transaction generator with metrics and complexity patterns (AC-2, AC-5, AC-7)
  - [ ] Implement manifest creation and chronological split manifest exporter (AC-6, AC-8)
  - [ ] Create generator CLI entrypoint and automated unit test suite (AC-1, AC-2, AC-6)
- [ ] Verify it: `/check verify dataset generation script`
- [ ] Test it: `/test dataset generation script`
- [ ] Review it (fresh model): `/check review dataset generation script`
- [ ] Document it: `/document dataset generation script`

---

### 6. Data quality and cleaning pipeline · needs a decision

Detection and handling of data quality issues: missing values, duplicates, invalid transactions, type mismatches, referential integrity violations, and outlier identification. Produces a clean snapshot that both Spark and Python pipelines consume independently from the same starting point.

**Done when:** quality checks run on all 11 tables; issues are logged with counts and categories; cleaning rules are documented; the clean snapshot is exported as Parquet; both pipelines can independently load the same clean snapshot; a data quality report summarizes what was found and fixed.

- [ ] Design it (spec): `/architect data quality and cleaning pipeline`
