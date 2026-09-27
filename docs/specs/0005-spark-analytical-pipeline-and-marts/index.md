# 0005. Apache Spark Analytical Pipeline and Analytical Marts Architecture

**Date**: 2026-09-26  
**Status**: Accepted  

## Summary

This specification establishes the formal architecture, mathematical contracts, physical schemas, and execution order for the Phase 3 Apache Spark analytical pipeline of the DineIQ Analytics platform. Operating downstream of the cleaned Parquet snapshot (`data/cleaned/competition_benchmark_v1/`), this pipeline consumes immutable, validated domain tables, executes distributed joins and aggregations, and materializes twelve precomputed analytical marts into `data/marts/spark/`.

The design strictly adheres to the DineIQ Analytics Software Requirements Specification (SRS v1.0), the approved project Architecture Decision Pack, the Dual-Pipeline Independence Rule, and strict temporal anti-leakage boundaries.

---

## Authoritative Requirements and Decisions Matrix

| Domain | SRS v1.0 Requirement | Approved Project Decision | Input Columns (Physical Cleaned) | Output Mart & Columns | Anti-Leakage / Guardrail Rule |
|---|---|---|---|---|---|
| **Wastage Risk ML Target** | Predict menu items/periods with high wastage risk (SRS Step 7 & 10). Leaves numerical threshold and task open. | Binary classification: `1 = HIGH_RISK`, `0 = LOW_RISK`. Grain: restaurant + prepared dish (`source_menu_item_id IS NOT NULL`) + calendar week. Raw ingredient waste (`source_menu_item_id IS NULL`) tracked separately in wastage analytics. | `wastage.quantity_lost`, `wastage.cost_loss_amount`, `wastage.source_menu_item_id`, `orders.order_date`, `order_items.quantity`, `order_items.net_revenue` | `mart_wastage.parquet`: `waste_cost_ratio`, `waste_quantity_ratio`, `next_week_wastage_risk` | Target for week $t$ uses features strictly from $\le t-1$. Target is never included in its own features. Zero sales weeks flagged as `extreme_operational_risk`. |
| **Menu Performance Classification** | Classify into 4 categories: Profit Driver, Volume Driver, Hidden Opportunity, Low Performer across 10 dimensions with 10 tricky edge cases (SRS Step 9 & 11). | Percentile-based normalized multi-factor scoring (0-100) + transparent rule gating (High $\ge 75$th, Low $\le 25$th). Composite score weights: Demand 25%, Profitability 25%, Customer Signal 15%, Wastage Health 15%, Sales Trend 10%, Promo Independence 10%. All 10 tricky-case boolean flags exposed. | `order_items.quantity`, `order_items.net_revenue`, `order_items.line_cost`, `ratings.rating_score`, `wastage.quantity_lost`, `menu_items.is_seasonal`, `menu_items.prep_time_minutes` | `mart_menu_performance.parquet`: 9 metric dimensions, 6 sub-scores, composite score, `classification`, 10 tricky flags | Relative percentiles computed per category/chain population. Items with < 30 days history flagged as `NEW_ITEM_INSUFFICIENT_HISTORY`. |
| **Demand Forecasting Lifecycle** | Multi-horizon demand forecasting with baselines, evaluation, and dashboard delivery (SRS Step 7 & 13). | Three logical layers: Layer A (`mart_demand_historical` with seasonal-naive baseline), Layer B (leakage-safe ML features), Layer C (`mart_demand_forecast` post-model evaluation). | `orders.order_date`, `order_items.quantity`, `order_items.source_menu_item_id`, `orders.source_restaurant_id` | `mart_demand_historical.parquet`: `historical_demand`, `seasonal_naive_baseline`, `day_of_week`, `hour_of_day` | Baseline strictly uses historical weekday/hour pattern from $\le t-1$. Model predictions deferred to Phase 3D. Split follows `split_manifest.json`. |
| **Price Elasticity & Sensitivity** | Analyze demand changes following price changes and classify price sensitivity (SRS Step 6 & 10). | 28-day pre-change vs 28-day post-change window around `pricing_history.effective_from`. Point elasticity: $\% \Delta Q / \% \Delta P$. Sensitivity: High $\ge 1.5$, Moderate $[0.75, 1.5)$, Low $< 0.75$. Explicit promotion overlap detection. | `pricing_history.effective_from`, `pricing_history.base_price`, `order_items.quantity`, `order_items.unit_price_at_sale`, `promotions.start_date`, `promotions.end_date` | `mart_pricing.parquet`: `pre_quantity`, `post_quantity`, `pre_price`, `post_price`, `elasticity`, `sensitivity_class`, `promotion_overlap` | Only price change events with complete 28-day pre/post history evaluated. Overlapping promotions flagged to prevent false causality claims. |
| **Promotion Performance & Trap** | Assess promotional lift, discounts, margin erosion, and promotion traps (SRS Step 8). | Promotion linkage is line-item grain (`order_items.source_promotion_id = promotions.source_promotion_id`). Orders table has NO promo key. Evidence-based trap: volume increase accompanied by margin erosion. | `order_items.source_promotion_id`, `order_items.line_discount`, `order_items.net_revenue`, `order_items.line_cost`, `promotions.is_misleading`, `promotions.discount_type` | `mart_promotions.parquet`: `redemption_count`, `total_discount`, `promotional_revenue`, `contribution_margin`, `is_promotion_trap` | Baseline volume calculated from non-promotional transaction baseline $\le t-1$. |

---

## 1. Wastage Risk Mathematical Contract

### Target Definition
- **Target Name**: `next_week_wastage_risk`
- **Task Type**: Binary classification (`1 = HIGH_RISK`, `0 = LOW_RISK`)
- **Prediction Grain**: `(source_restaurant_id, source_menu_item_id, calendar_week)`
- **Inclusion Criteria**: Prepared-dish wastage only (`source_menu_item_id IS NOT NULL`). Raw ingredient wastage (`source_menu_item_id IS NULL`) is partitioned to raw ingredient analytics and is NEVER coerced into dish targets.

### Formulas
For each restaurant $r$, menu item $m$, and calendar week $t$:
$$\text{waste\_cost}_{r,m,t} = \sum (\text{quantity\_lost} \times \text{applicable\_unit\_cost})$$
$$\text{gross\_revenue}_{r,m,t} = \sum \text{net\_revenue}$$
$$\text{waste\_quantity}_{r,m,t} = \sum \text{quantity\_lost}$$
$$\text{sold\_quantity}_{r,m,t} = \sum \text{quantity}$$

Ratios:
$$\text{waste\_cost\_ratio}_{r,m,t} = \frac{\text{waste\_cost}_{r,m,t}}{\text{gross\_revenue}_{r,m,t}} \quad (\text{if } \text{gross\_revenue} > 0)$$
$$\text{waste\_quantity\_ratio}_{r,m,t} = \frac{\text{waste\_quantity}_{r,m,t}}{\text{sold\_quantity}_{r,m,t}} \quad (\text{if } \text{sold\_quantity} > 0)$$

### Decision Boundary
$$\text{next\_week\_wastage\_risk}_{r,m,t+1} = \begin{cases} 1 & \text{if } \text{waste\_cost\_ratio}_{r,m,t+1} > 0.05 \text{ OR } \text{waste\_quantity\_ratio}_{r,m,t+1} > 0.10 \\ 0 & \text{otherwise} \end{cases}$$

### Zero-Denominator and Edge Cases
- When $\text{gross\_revenue} = 0$, `waste_cost_ratio` is `NULL` (undefined).
- When $\text{sold\_quantity} = 0$, `waste_quantity_ratio` is `NULL` (undefined).
- If $\text{waste\_quantity} > 0$ and $\text{sold\_quantity} = 0$, the record is flagged as `extreme_operational_risk = True` and preserved in the analytical mart.
- Feature Leakage Prevention: Features for predicting week $t$ must draw strictly from weeks $\le t-1$ (e.g. 4-week trailing rolling averages). The target for week $t$ is strictly isolated.

---

## 2. Menu Performance Classification Contract

### The 9 Input Dimensions
1. **Demand Quantity**: Total units sold ($\sum \text{quantity}$).
2. **Gross Revenue**: Total net sales ($\sum \text{net\_revenue}$).
3. **Contribution Margin**: Total margin ($\sum (\text{net\_revenue} - \text{line\_cost})$).
4. **Profitability Percentage**: Margin ratio ($\frac{\text{Contribution Margin}}{\text{Gross Revenue}}$).
5. **Customer Rating**: Average customer satisfaction score from `ratings` table ($\text{AVG}(\text{rating\_score})$).
6. **Repeat Purchase Rate**: Proportion of customer orders representing repeat visits for that item.
7. **Wastage Percentage**: Prepared dish waste ratio ($\frac{\text{quantity\_lost}}{\text{quantity sold} + \text{quantity\_lost}}$).
8. **Promotion Dependency**: Promotion share ($\frac{\text{promotional quantity sold}}{\text{total quantity sold}}$).
9. **Sales Trend**: Trailing growth rate comparing current 30-day volume to preceding 30-day volume.

### Transparent Scoring Model
Each dimension is normalized into a 0-100 percentile rank within its category/chain cohort:
- $\text{Demand Score} = 0.5 \times \text{Rank}(\text{Quantity}) + 0.5 \times \text{Rank}(\text{Revenue})$ (Weight: 25%)
- $\text{Profitability Score} = 0.5 \times \text{Rank}(\text{Margin}) + 0.5 \times \text{Rank}(\text{Profit \%})$ (Weight: 25%)
- $\text{Customer Signal Score} = 0.6 \times \text{Rank}(\text{Rating}) + 0.4 \times \text{Rank}(\text{Repeat Rate})$ (Weight: 15%)
- $\text{Wastage Health Score} = 100 - \text{Rank}(\text{Wastage \%})$ (Weight: 15%)
- $\text{Sales Trend Score} = \text{Rank}(\text{Growth Rate})$ (Weight: 10%)
- $\text{Promotion Independence Score} = 100 - \text{Rank}(\text{Promotion Dependency})$ (Weight: 10%)

$$\text{Composite Score} = 0.25 S_{\text{Demand}} + 0.25 S_{\text{Profit}} + 0.15 S_{\text{Customer}} + 0.15 S_{\text{Wastage}} + 0.10 S_{\text{Trend}} + 0.10 S_{\text{PromoIndep}}$$

### Gating Classification Rules
Percentile benchmarks: $\text{High} \ge 75\text{th}$, $\text{Low} \le 25\text{th}$.
- **PROFIT DRIVER**: $S_{\text{Demand}} \ge 75 \land S_{\text{Profit}} \ge 75 \land \text{Wastage Health} \ge 25 \land \text{Promo Independence} \ge 25$.
- **VOLUME DRIVER**: $S_{\text{Demand}} \ge 75 \land S_{\text{Profit}} < 75$.
- **HIDDEN OPPORTUNITY**: $S_{\text{Demand}} < 75 \land (S_{\text{Profit}} \ge 75 \lor S_{\text{Customer}} \ge 75) \land \text{Wastage Health} \ge 25$.
- **LOW PERFORMER**: Default fallback when an item exhibits weak demand, weak profitability, excessive wastage, or poor customer satisfaction.

### 10 Tricky-Case Boolean Evidence Flags
1. `HIGH_SELLING_LOSS_MAKING`: $S_{\text{Demand}} \ge 75 \land (\text{Contribution Margin} \le 0 \lor S_{\text{Profit}} \le 25)$.
2. `PROFITABLE_RARELY_PURCHASED`: $S_{\text{Profit}} \ge 75 \land S_{\text{Demand}} \le 25$.
3. `POPULAR_HIGH_WASTAGE`: $S_{\text{Demand}} \ge 75 \land \text{Wastage Health} \le 25$.
4. `HIGH_RATING_LOW_PROFITABILITY`: $\text{Avg Rating} \ge 4.2 \land S_{\text{Profit}} \le 25$.
5. `LOW_RATING_HIGH_SALES`: $\text{Avg Rating} \le 3.0 \land S_{\text{Demand}} \ge 75$.
6. `PROMOTION_DEPENDENT`: $\text{Promotion Dependency} \ge 0.50$ (or $\ge 75$th percentile).
7. `LOCATION_PERFORMANCE_DIVERGENCE`: Classification differs across restaurant locations.
8. `WEEKEND_ONLY_PATTERN`: Weekend volume represents $> 60\%$ of total sales.
9. `SEASONAL_ITEM`: `is_seasonal == True` or quarterly coefficient of variation $> 0.50$.
10. `NEW_ITEM_INSUFFICIENT_HISTORY`: Active history $< 30$ days. Confidence flag set, historical extrapolation suppressed.

---

## 3. Demand Forecasting Lifecycle Contract

### Three-Layer Architecture
1. **Layer A (`mart_demand_historical.parquet`)**: Contains observed demand rolled up to `(source_restaurant_id, source_menu_item_id, date, hour)` plus temporal calendar signals and a **seasonal-naive historical baseline** (same weekday/hour from prior 4 weeks average $\le t-1$).
2. **Layer B (`demand ML feature datasets`)**: Time-aware feature matrices split according to `split_manifest.json` (TRAIN: Jan-Aug 2025, VALIDATION: Sep-Oct 2025, TEST: Nov 2025, UNSEEN: Dec 2025).
3. **Layer C (`mart_demand_forecast.parquet`)**: Materialized strictly post-model training in Phase 3D, recording `actual_demand`, `baseline_forecast`, `spark_forecast`, `python_forecast`, and respective residual errors (`spark_error`, `python_error`).

---

## 4. Price Elasticity and Sensitivity Contract

- **Window**: 28 calendar days pre-change vs 28 calendar days post-change around `pricing_history.effective_from`.
- **Formulas**:
  $$\% \Delta Q = \frac{Q_{\text{post}} - Q_{\text{pre}}}{Q_{\text{pre}}}, \quad \% \Delta P = \frac{P_{\text{post}} - P_{\text{pre}}}{P_{\text{pre}}}$$
  $$\text{Elasticity} = \frac{\% \Delta Q}{\% \Delta P} \quad (\text{if } \% \Delta P \neq 0)$$
- **Classification**:
  - **HIGH**: $|\text{Elasticity}| \ge 1.5$
  - **MODERATE**: $0.75 \le |\text{Elasticity}| < 1.5$
  - **LOW**: $|\text{Elasticity}| < 0.75$
- **Promotion Overlap Detection**: If an active promotion ran during either the 28-day pre or post window, `promotion_overlap` is set to `True`, alerting analysts that price response is confounded.

---

## 5. Promotion Linkage and Performance Contract

- **Join Lineage**: `order_items.source_promotion_id = promotions.source_promotion_id`.
- **Metrics**: Redemption volume, total discount granted, promotional revenue, incremental margin, customer acquisition count.
- **Promotion Trap**: Flagged when promotional discount creates positive volume lift but results in negative incremental margin relative to non-promoted baseline.

---

## 6. Physical Column Mapping Standards

All Spark jobs and mart queries must strictly bind to verified physical Parquet column names:

| Table | Verified Physical Column Names | Prohibited / Hallucinated Names |
|---|---|---|
| `menu_items` | `current_base_price`, `current_base_cost`, `is_seasonal`, `prep_time_minutes` | `base_price`, `base_cost`, `is_spoilage_sensitive` |
| `pricing_history` | `source_pricing_history_id`, `base_price`, `base_cost`, `effective_from`, `effective_to` (`effective_to IS NULL` indicates current) | `source_price_id`, `price`, `cost`, `is_current` |
| `promotions` | `campaign_name`, `is_misleading`, `discount_type`, `discount_value` | `promotion_name`, `name` |
| `wastage` | `quantity_lost`, `cost_loss_amount`, `source_menu_item_id`, `ingredient_name` | `quantity`, `waste_amount` |
| `inventory` | `current_stock_quantity`, `reorder_threshold`, `unit_purchase_cost`, `last_restock_date`, `ingredient_name` | `source_menu_item_id`, `stock_date`, `opening_quantity`, `closing_quantity` |
| `order_items` | `source_promotion_id`, `unit_price_at_sale`, `line_discount`, `net_revenue`, `line_cost` | `order_id` (must join via `orders`), `discount_code` |

---

## 7. Required Analytical Marts Catalog

The Spark analytical pipeline materializes twelve distinct analytical marts in `data/marts/spark/`:

1. `mart_menu_performance.parquet`: Comprehensive 9-dimension menu classification, 6 sub-scores, composite score, and 10 tricky-case flags.
2. `mart_customer_rfm.parquet`: Customer recency, frequency, monetary value, tenure, and loyalty tier behavior.
3. `mart_basket_analysis.parquet`: Multi-item basket co-occurrence patterns, support, confidence, and association lift.
4. `mart_peak_analysis.parquet`: Hourly and day-of-week demand distributions, rush-hour indicators, and throughput bottlenecks.
5. `mart_location_performance.parquet`: Restaurant-level revenue, customer counts, margin distributions, and location divergence metrics.
6. `mart_channel_performance.parquet`: Channel metrics across Dine-in, Takeaway, Delivery Direct, and Delivery Aggregator.
7. `mart_wastage.parquet`: Dual-path wastage reporting (prepared dish vs raw ingredient), waste ratios, and high-risk flags.
8. `mart_pricing.parquet`: Historical price-change events, 28-day pre/post demand, price elasticity, and sensitivity classes.
9. `mart_promotions.parquet`: Line-level promotion redemption, discount absorption, net lift, and promotion trap flags.
10. `mart_ratings_anomalies.parquet`: Rating trend anomalies, sudden satisfaction drops, and rating-volume divergence.
11. `mart_sales_anomalies.parquet`: Volume and revenue anomalies, statistical outliers ($Z > 3$), and zero-sales exceptions.
12. `mart_demand_historical.parquet`: Historical hourly and daily demand time-series with leakage-safe seasonal-naive baselines.

---

## 8. Dual-Pipeline Independence and Execution Order

### Dual-Pipeline Boundary
- **Shared Assets**: Cleaned Parquet snapshot (`data/cleaned/competition_benchmark_v1/`), chronological split manifest (`split_manifest.json`), evaluation contracts (`packages/core/contracts/evaluation.py`).
- **Spark Artifacts**: `data/marts/spark/`, `data/artifacts/features/spark/`, `data/artifacts/models/spark/`.
- **Python Artifacts**: `data/marts/python/`, `data/artifacts/features/python/`, `data/artifacts/models/python/`.
- **Forbidden**: Sharing intermediate DataFrames, feature files, or prediction arrays across pipelines.

### Implementation Phases
- **Phase 3A**: Core session factory, typed schemas, `CleanDataLoader`, input validation, and optimized joins with dual-path routing and line-level promotion linkage.
- **Phase 3B**: Marts 1 to 3 (`mart_menu_performance`, `mart_customer_rfm`, `mart_basket_analysis`).
- **Phase 3C**: Marts 4 to 12 (`mart_peak_analysis`, `mart_location_performance`, `mart_channel_performance`, `mart_wastage`, `mart_pricing`, `mart_promotions`, `mart_ratings_anomalies`, `mart_sales_anomalies`, `mart_demand_historical`).
- **Phase 3D**: Machine learning feature contracts, Spark MLlib models, independent Python models, post-model forecast mart, and evaluation comparisons (Deferred to ML teammate).

---

## 9. Spark Runtime Environment and Execution Verification

- **Python Runtime**: Python 3.13.1 (64-bit AMD64)
- **Spark Version**: Apache Spark 4.2.0 (PySpark 4.2.0)
- **Java Compatibility**: JDK 24 (verified compatible with PySpark 4.2.0 local engine)
- **Windows File System**: Configured `HADOOP_HOME=C:\hadoop` with native `winutils.exe` and `hadoop.dll` (Hadoop 3.3.6+ binary compatibility) allowing native Spark `FileOutputCommitter` and Snappy-compressed Parquet directory writes.
- **Spark Configuration**:
  - `master("local[*]")`
  - `spark.pyspark.python = sys.executable`
  - `spark.pyspark.driver.python = sys.executable`
  - `spark.driver.memory = "2g"`
  - `spark.sql.shuffle.partitions = "4"`
  - `spark.sql.execution.arrow.pyspark.enabled = "true"`

---

## 10. Spark SQL vs DataFrame API Implementation Matrix

Every single mart is computed natively in Apache Spark without falling back to Pandas for analytical computation. Temporary views (`spark_temp_*`) are used to execute multi-table joins, aggregations, and windowing expressions:

| Mart Name | Grain | Primary Spark SQL Usage | Primary Spark DataFrame / Window API Usage |
|---|---|---|---|
| `mart_menu_performance` | `restaurant + item` | Temp views `spark_temp_orders`, `spark_temp_order_items`. CTEs for customer repeat purchase calculation and multi-period sales trend. | Percentile ranking via `F.percent_rank().over(Window.partitionBy(...))`, composite weighted scoring, gating classification, and 10 tricky boolean flags. |
| `mart_customer_rfm` | `customer` | Temp view `spark_temp_rfm_orders`. SQL aggregation of recency date diffs, frequency counts, and monetary sums. | Quintile segmentation via `F.ntile(5).over(Window.orderBy(...))` for R, F, and M scores; string concatenation for RFM segment assignment. |
| `mart_basket_analysis` | `item_pair` | Temp view `spark_temp_distinct_basket`. Distributed self-join `a.source_menu_item_id < b.source_menu_item_id` in Spark SQL for co-occurrence counting. | Support, confidence, and lift metric calculations; join with menu item metadata. |
| `mart_peak_analysis` | `restaurant + day + hour` | Temp view `spark_temp_peak_orders`. Hourly and day-of-week volume aggregation and seating capacity utilization. | Top peak hours calculation via `F.dense_rank().over(Window.partitionBy("source_restaurant_id").orderBy(F.desc("total_orders"))) <= 5`. |
| `mart_location_performance` | `restaurant + month` | Temp views for monthly orders and item margin aggregations. | Dual-path wastage aggregation (dishes vs raw ingredients), waste-to-revenue ratio, broadcast join with restaurant dimensions. |
| `mart_channel_performance` | `restaurant + channel + month` | Temp views `spark_temp_chan_orders` and `spark_temp_chan_items`. Multi-channel order, gross revenue, discount, and tip aggregations. | Window `F.sum("total_orders").over(Window.partitionBy("source_restaurant_id", "order_month"))` for monthly channel share percentage. |
| `mart_wastage` | `restaurant + item/ingredient + type + week` | Temp view `spark_temp_dish_waste`. Prepared dish wastage aggregation and line-item sales matching. | Zero-denominator safe ratio calculations, operational risk flags, and `F.lead("current_week_wastage_risk", 1).over(...)` for next-week risk target. |
| `mart_pricing` | `event (item/restaurant + price change)` | Temp view `spark_temp_pricing_events`. 28-day pre/post intervals joined against line items in Spark SQL. | Percentage price/quantity changes, price elasticity calculation, sensitivity categorization, and promotion overlap detection. |
| `mart_promotions` | `promotion + restaurant` | Line-level promotion linkage in Spark SQL (`order_items.source_promotion_id = promotions.source_promotion_id`). | Margin impact calculation, discount absorption rate, and promotion trap condition evaluation. |
| `mart_ratings_anomalies` | `item/restaurant + week` | Temp views `spark_temp_rating_item_sales` and `spark_temp_dish_ratings`. Weekly rating distribution and sales volume. | Statistical Z-Score computation via `Window.partitionBy("source_menu_item_id")` and multi-condition anomaly classification. |
| `mart_sales_anomalies` | `restaurant + day` | Temp view `spark_temp_sales_orders`. Daily restaurant order counts and revenue sums. | 14-day rolling mean and standard deviation via `Window.partitionBy("source_restaurant_id").orderBy("order_date").rowsBetween(-14, -1)`, Z-scores, spike/drop detection (strictly excludes current day $t$ to prevent baseline leakage). |
| `mart_demand_historical` | `restaurant + item + day` | Temp view `spark_temp_demand_merged`. Daily demand and gross revenue aggregation per item and restaurant. | Anti-leakage seasonal-naive baseline via `Window.partitionBy("source_restaurant_id", "source_menu_item_id", "day_of_week_num").orderBy("order_date").rowsBetween(-4, -1)`, calendar features, split assignment. |

---

## 11. Materialized Analytical Marts Execution Evidence

Full pipeline execution materialized against the `competition_benchmark_v1` cleaned Parquet dataset (1,302,220 total clean records) into `data/marts/spark/`:

| Mart File | Row Count | Execution Duration | Grain | Status |
|---|---|---|---|---|
| `mart_menu_performance.parquet` | 3,000 | 14.14s | `restaurant + item` | **MATERIALIZED** |
| `mart_customer_rfm.parquet` | 50,000 | 2.64s | `customer` | **MATERIALIZED** |
| `mart_basket_analysis.parquet` | 11,175 | 12.56s | `item_pair` | **MATERIALIZED** |
| `mart_peak_analysis.parquet` | 1,643 | 1.32s | `restaurant + day + hour` | **MATERIALIZED** |
| `mart_location_performance.parquet` | 253 | 2.21s | `restaurant + month` | **MATERIALIZED** |
| `mart_channel_performance.parquet` | 976 | 1.49s | `restaurant + channel + month` | **MATERIALIZED** |
| `mart_wastage.parquet` | 151,029 | 4.84s | `restaurant + item/ingr + week` | **MATERIALIZED** |
| `mart_pricing.parquet` | 1,500 | 2.96s | `event (item/restaurant)` | **MATERIALIZED** |
| `mart_promotions.parquet` | 320 | 1.80s | `promotion + restaurant` | **MATERIALIZED** |
| `mart_ratings_anomalies.parquet` | 61,322 | 2.76s | `item/restaurant + week` | **MATERIALIZED** |
| `mart_sales_anomalies.parquet` | 7,313 | 1.18s | `restaurant + day` | **MATERIALIZED** |
| `mart_demand_historical.parquet` | 450,779 | 7.38s | `restaurant + item + day` | **MATERIALIZED** |
| **Total Pipeline** | **741,310** | **64.82s** | **Full Benchmark** | **SUCCESS** |

---

## 12. ML Boundary and Teammate Handoff Notice

In strict accordance with the execution protocol:
- **No Machine Learning Models Started**: Spark MLlib models, Python ML models, customer churn models, wastage classification training, and demand regression/forecasting models have NOT been trained.
- **Contract Adherence**: Data Engineering inputs, anti-leakage baselines, and chronological splits are solidified and ready for the ML teammate.
- **Next Stage**: Machine Learning Feature Engineering and Dual Pipeline Model Training (Phase 3D).

