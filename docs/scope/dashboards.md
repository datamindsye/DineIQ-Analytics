# Epic: Dashboards

Interactive dashboards providing analytical insights, predictions, and recommendations rather than only static charts. Each dashboard is a working UI connected to real analytical outputs through the API.

---

## Slice 1: Menu Intelligence Dashboard (tracer bullet)

### 11. Menu Intelligence Dashboard · needs a decision

The first real dashboard, completing the tracer bullet: raw data → analytics → API → interactive UI. Shows menu profitability, classification (Profit Driver, Volume Driver, Hidden Opportunity, Low Performer), slow moving dishes, location specific menu performance, and item level drill down.

**Done when:** dashboard renders menu profitability metrics and classification labels; items are filterable by category, location, and classification; drill down shows item level detail; slow moving dishes are highlighted; the dashboard is responsive and uses the design system; data comes from the real analytics pipeline through the API.

- [ ] Design it (spec): `/architect Menu Intelligence Dashboard`

---

## Slice 2: Customer Intelligence Dashboard

### 14. Customer Intelligence Dashboard · needs a decision

Customer segmentation view, RFM analysis visualization, churn risk indicators, and customer value distribution. Supports filtering by segment, location, and time period.

**Done when:** dashboard shows customer segments with RFM scores; churn risk is visualized; high value and at risk customers are highlighted; filtering by segment, location, and time period works; data comes from the customer analytics pipeline.

- [ ] Design it (spec): `/architect Customer Intelligence Dashboard`

---

## Slice 3: Wastage, Forecast, and Comparison Dashboards

### 17. Wastage and Forecast Dashboards · needs a decision

Two related dashboard views. Wastage Dashboard: wastage patterns by item, location, day, and season; wastage predictions; preparation quantity recommendations. Forecast Dashboard: demand forecasts by item and location; peak period visualization; forecast accuracy vs baseline; seasonal and trend decomposition.

**Done when:** wastage patterns and predictions are visualized with drill down by item and location; preparation quantity recommendations are shown; demand forecasts display actual vs predicted with baseline comparison; peak periods are highlighted; both dashboards support date range filtering.

- [ ] Design it (spec): `/architect Wastage and Forecast Dashboards`

### 18. Dual Pipeline Comparison Dashboard · needs a decision

Visualize the comparison between Spark and Python pipeline results. Show the comparison table (actual label, Spark result, Python result, match/difference), disagreement patterns, aggregate evaluation metrics, and model version information. This dashboard is a competition requirement.

**Done when:** comparison table displays all seven required columns for at least 100 unseen cases; disagreement patterns are visualized; evaluation metrics are shown side by side; model versions are displayed; the dashboard clearly communicates which pipeline is more accurate and where they diverge.

- [ ] Design it (spec): `/architect Dual Pipeline Comparison Dashboard`

---

## Slice 5: Executive Dashboard

### 25. Executive Dashboard · needs a decision

The top level overview for management. Aggregated KPIs: total revenue, total orders, average order value, overall profitability, customer counts, wastage rate, forecast accuracy. Trend lines and period over period comparisons. Quick links to deeper dashboards. Highlights top recommendations and alerts (anomalies, high wastage items, churn risk customers).

**Done when:** executive KPIs are displayed with trend lines; period over period comparison works; top recommendations and alerts surface from the analytics pipelines; drill through to detailed dashboards works; the dashboard is responsive and loads performantly from precomputed outputs.

- [ ] Design it (spec): `/architect Executive Dashboard`

---

## Additional analytical views

The broader application must also provide analytical views for pricing, promotions, locations, basket analysis, anomalies, recommendations, what if scenarios, and reports. These views are built as part of their respective analytics features (features 19 to 24) and do not each require a separate dashboard spec. They share the design system and chart components from feature 4.
