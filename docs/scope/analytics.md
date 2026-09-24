# Epic: Analytics and ML

All analytical computations, ML models, and the dual pipeline infrastructure. Each analytics feature is built through both Spark and Python pipelines independently, then compared.

## Pipeline independence rule

Both pipelines work independently from the same raw/clean snapshot. They may share: raw dataset snapshot, entity IDs, target definition, chronological split manifest, evaluation contract. They must NOT share: prepared feature tables, trained models, predictions, or one pipeline's engineered features as the other's input.

## Time aware modeling rule

Forecasting and time dependent models must use chronological training, validation, and test windows. Future data leakage is explicitly prohibited. Forecasts must be compared with a simple baseline.

---

## Slice 1: Menu analytics (the tracer bullet)

The first working thread through every layer: raw data → Spark analytics → Python analytics → comparison → API → dashboard. Narrow (menu only), but real end to end.

### 7. Menu profitability and classification analytics · needs a decision

Compute menu item profitability (revenue, cost, contribution margin, profit margin) and classify each item into one of four categories: Profit Driver (high margin, high volume), Volume Driver (low margin, high volume), Hidden Opportunity (high margin, low volume), Low Performer (low margin, low volume). Include slow moving dish identification and location specific menu performance.

**Done when:** every menu item has a profitability score and a classification label; classification uses the four defined categories; results are computed per location and aggregated; slow moving dishes are flagged; output is available as both Spark DataFrame/Parquet and Python DataFrame/CSV.

- [ ] Design it (spec): `/architect menu profitability and classification analytics`

### 8. Spark menu analytics pipeline · needs a decision

The Spark implementation of menu profitability and classification using PySpark, Spark SQL, and Spark MLlib. Feature engineering, aggregation, and classification are done entirely within Spark. At least three suitable MLlib candidate algorithms must be evaluated for any ML task within this pipeline.

**Done when:** Spark SQL queries compute profitability metrics; Spark MLlib evaluates at least three candidate algorithms; results are written to Parquet; pipeline runs end to end from clean snapshot to classified output; evaluation metrics are logged.

- [ ] Design it (spec): `/architect Spark menu analytics pipeline`

### 9. Python menu analytics pipeline

The independent Python implementation of menu profitability and classification using Pandas, NumPy, Scikit learn, and XGBoost where justified. Feature engineering and classification are done entirely within Python, independently of the Spark pipeline.

**Done when:** Python computes the same profitability metrics and classification independently; feature engineering uses only the raw/clean snapshot (not Spark features); results are written to CSV/Parquet; evaluation metrics are logged using the same evaluation contract as Spark.

- [ ] `/develop Python menu analytics pipeline`

### 10. Dual pipeline comparison framework · needs a decision

The framework for comparing Spark and Python predictions on the same unseen cases. The initial shared modeling task is next week wastage risk for (item_id, location_id, week). The comparison must include at least 100 unseen cases and report: actual label, Spark result, Python result, match or difference, disagreement information, evaluation metrics, and model versions.

**Done when:** comparison runs on at least 100 unseen cases from the chronological test set; report includes all seven required columns; disagreement patterns are surfaced; aggregate evaluation metrics (accuracy, precision, recall, F1 or equivalent) are computed for both pipelines; model versions are recorded; output is persisted and API accessible.

- [ ] Design it (spec): `/architect dual pipeline comparison framework`

---

## Slice 2: Customer analytics

Adds customer intelligence to the working thread.

### 12. Customer segmentation and RFM analytics · needs a decision

Segment customers using RFM (Recency, Frequency, Monetary) analysis. Identify high value, at risk, churned, and new customer segments. Include customer churn risk scoring using both Spark and Python pipelines.

**Done when:** RFM scores are computed for all customers; segments are assigned (high value, at risk, churned, new, and other segments as appropriate); churn risk scores are produced by both pipelines; results are API accessible and dashboard ready.

- [ ] Design it (spec): `/architect customer segmentation and RFM analytics`

### 13. Market basket analysis

Association rule mining across order items to identify co-purchased items. Compute support, confidence, and lift for item pairs and groups. Derive bundling and cross sell opportunities.

**Done when:** association rules are mined with support, confidence, and lift metrics; top co-purchased pairs and groups are identified per location and overall; bundling and cross sell recommendations are generated; results are API accessible.

- [ ] `/develop market basket analysis`

---

## Slice 3: Forecasting and wastage

Adds predictive analytics to the working thread.

### 15. Wastage analysis and prediction · needs a decision

Analyze historical wastage patterns by item, location, day of week, and season. Predict next week wastage risk for (item_id, location_id, week) using both Spark MLlib and Python (Scikit learn or XGBoost). This is the initial shared modeling task for the dual pipeline comparison. Chronological train, validation, and test splits are required. Forecasts must be compared with a simple baseline.

**Done when:** wastage patterns are analyzed across all dimensions; both pipelines independently predict wastage risk on the chronological test set; predictions beat a simple baseline; results feed the comparison framework (feature 10); preparation quantity recommendations are derived.

- [ ] Design it (spec): `/architect wastage analysis and prediction`

### 16. Demand forecasting · needs a decision

Forecast demand by item, location, and time period. Use chronological training, validation, and test windows. Compare forecasts against a simple baseline (e.g. same week last period average). Identify peak periods (time of day, day of week, seasonal, holiday).

**Done when:** demand forecasts are produced per item and location for the next period; peak periods are identified with statistical support; forecast accuracy is evaluated against the baseline; results are API accessible.

- [ ] Design it (spec): `/architect demand forecasting`

---

## Slice 4: Pricing, promotions, anomalies, and operational analytics

Broadens the analytics coverage across the remaining analytical areas.

### 19. Pricing and promotion analytics · needs a decision

Price intelligence: track pricing history, identify price sensitive items, measure price elasticity indicators. Promotion effectiveness: measure lift, ROI, and incremental revenue for each promotion. Promotion trap detection: identify promotions that increase volume but decrease total profit or margin.

**Done when:** pricing history is tracked per item; price sensitivity is scored; promotion effectiveness metrics (lift, ROI, incremental revenue) are computed; promotion traps are flagged with evidence; results are API accessible.

- [ ] Design it (spec): `/architect pricing and promotion analytics`

### 20. Anomaly detection (ratings, sales, promotions)

Detect anomalies in ratings (sudden drops or spikes, suspicious patterns), sales (unusual volume changes, unexpected zero days), and promotion performance (unexplained effectiveness changes). Flag anomalies with context and severity.

**Done when:** anomaly detection runs on ratings, sales, and promotion data; anomalies are flagged with severity, context, and time window; false positive rate is acceptable; results are API accessible and dashboard ready.

- [ ] `/develop anomaly detection`

### 21. Location and channel analytics

Compare performance across the 20 restaurant locations: revenue, profitability, customer mix, menu performance, wastage, and ratings. Analyze ordering channel distribution and performance. Identify location specific menu intelligence (items that perform differently by location).

**Done when:** location comparison covers all key metrics; channel analysis shows distribution and performance; location specific menu anomalies are flagged; results are API accessible.

- [ ] `/develop location and channel analytics`

### 22. Inventory intelligence

Connect inventory levels to demand forecasts, wastage predictions, and sales velocity. Flag overstocked and understocked items per location.

**Done when:** inventory status is assessed against demand and wastage predictions; overstock and understock alerts are generated per location; results are API accessible.

- [ ] `/develop inventory intelligence`

### 30. Slow moving dish and churn risk analytics

Identify slow moving dishes (low order frequency, declining trend) per location. Compute customer churn risk scores combining RFM, order recency, and behavioral signals.

**Done when:** slow moving dishes are flagged per location with trend data; churn risk scores are produced and segmented; results feed the recommendation engine and dashboards.

- [ ] `/develop slow moving dish and churn risk analytics`
