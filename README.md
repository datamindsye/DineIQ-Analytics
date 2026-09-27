# DineIQ Analytics — Data Science Intelligence Arena

A comprehensive restaurant analytics and decision intelligence platform designed to demonstrate dual independent analytical pipelines (Apache Spark / PySpark and Python Data Science / scikit-learn), high-scale data quality profiling, evidence-based business recommendations, what-if scenario simulations, and interactive executive dashboards.

---

## 1. Project Overview

Modern multi-unit restaurant operations face complex operational, pricing, and margin challenges:
- **Menu Profitability vs. Popularity**: High-volume dishes often conceal razor-thin or negative contribution margins, while highly profitable dishes languish without marketing support.
- **Wastage & Spoilage**: Food waste occurs at both the kitchen preparation level and the raw inventory level, driving unnecessary cost loss.
- **Promotion Cannibalization**: Misconfigured marketing campaigns can create "promotion traps" where order volumes spike while total net margin collapses.
- **Demand Fluctuation & Kitchen Bottlenecks**: Intra-day rush hours, day-of-week surges, and channel shifts (dine-in vs. delivery) strain staffing and table turn rates.
- **Customer Churn & Retention**: Identifying at-risk high-value customers requires multi-dimensional Recency, Frequency, and Monetary (RFM) modeling.

**DineIQ Analytics** addresses these challenges through an end-to-end data science and decision intelligence platform that processes raw transactional, operational, and customer data into actionable business intelligence.

---

## 2. Core Architecture

The platform follows a **Modular Monolith** pattern with strict architectural separation between layers:

```
Raw Restaurant Data (11 Domain Tables)
  │
  ▼
Data Quality & Profiling Subsystem (Nulls, Duplicates, Referential Integrity, Financial Validity)
  │
  ▼
Cleaning & Defect Quarantine Isolation (quarantine reasons appended, 0 variance reconciliation)
  │
  ▼
Immutable Clean Parquet Snapshot (`data/cleaned/competition_benchmark_v1/`)
  │
  ▼
Apache Spark Analytical Pipeline & Feature Engineering
  │
  ▼
12 Precomputed Analytical Marts (`data/marts/spark/*.parquet`)
  │
  ├──────────────────────────────────────────────┐
  ▼                                              ▼
Spark MLlib Pipeline                   Independent Python ML Pipeline
(Distributed ML, Feature Prep)         (scikit-learn, Time-Series Modeling)
  │                                              │
  └──────────────────────┬───────────────────────┘
                         ▼
             Dual Pipeline Model Comparison
                         │
                         ▼
        Decision Intelligence & Recommendations
                         │
                         ▼
              What-If Scenario Simulation
                         │
                         ▼
                FastAPI Backend API
                         │
                         ▼
             React + Vite + Plotly Dashboards
```

---

## 3. Technology Stack

### Backend
- **Framework**: FastAPI (asynchronous REST endpoints, standardized `ErrorEnvelope` responses)
- **Validation & Settings**: Pydantic v2, Pydantic Settings
- **ORM & Migrations**: SQLAlchemy 2.0, Alembic
- **Database**: PostgreSQL (application metadata, users, roles, job runs, model versions, audit logs)
- **Security**: JWT authentication, Role-Based Access Control (RBAC) with 4 roles (`Admin`, `StoreManager`, `DataScientist`, `Cashier`), bcrypt password hashing

### Data Engineering
- **Big Data Engine**: Apache Spark 4.2.0 / PySpark
- **Analytical Query**: Spark SQL, PySpark DataFrame API (windowing, ranking, aggregations)
- **Columnar Engine**: PyArrow (zero-copy Parquet reading in services)
- **Storage Format**: Apache Parquet (Snappy-compressed)

### Data Science / Machine Learning
- **Python ML**: Pandas, NumPy, scikit-learn (independent pipeline)
- **Spark ML**: Spark MLlib (planned for distributed modeling)
- *Note: Machine learning models and training are scheduled for the upcoming ML track and are NOT yet trained.*

### Frontend
- **Core**: React 19, TypeScript
- **Build Tool**: Vite
- **Visualizations**: Plotly.js

### Testing & Code Quality
- **Test Runner**: pytest, pytest-asyncio, FastAPI TestClient
- **Linter & Formatter**: Ruff (Python target 3.10+)
- **Frontend Linter**: Oxlint (TypeScript)
- **Git Hooks**: pre-commit

---

## 4. Benchmark Dataset

The system includes a deterministic synthetic data generator producing realistic multi-unit restaurant transactions across 365 calendar days (year 2025).

### Verified Entity Cardinality
- **Customers**: 50,000 registered customers
- **Restaurants**: 20 multi-unit locations across 4 cities and 3 dining formats
- **Menu Categories**: 10 distinct food and beverage categories
- **Menu Items**: 150 dishes with standard recipes, prep times, and base costs
- **Pricing History**: 1,500 historical price-change records (SCD Type 2)
- **Promotions**: 25 marketing campaigns (including intentional promotion trap scenarios)
- **Raw Orders**: 100,508 orders
- **Raw Order Line Items**: 1,006,051 line items
- **Customer Ratings**: 100,000 ratings with satisfaction scores and text reviews
- **Inventory Records**: 3,000 stock tracking logs
- **Wastage Records**: 50,000 operational wastage events

### Master Record Reconciliation
- **Total Raw Records**: **1,311,264**
- **Cleaned Records Output**: **1,302,220**
- **Quarantined Defective Records**: **9,044**
- **Mathematical Lineage Reconciliation**:
  $$1,311,264 \text{ raw} = 1,302,220 \text{ clean} + 9,044 \text{ quarantined} \quad [0 \text{ variance}]$$
- **Overall Cleanliness Rate**: **99.31%**

---

## 5. Data Quality & Cleaning Subsystem

The data quality pipeline profiles every batch against 5 categories of rules without modifying raw sources:
1. **Missing Values**: Permissible business nulls (e.g., guest checkouts, missing review comments) are preserved; prohibited nulls in primary or foreign keys are quarantined.
2. **Duplicate Records**: Duplicate order IDs and duplicate line-item IDs are detected and isolated.
3. **Price & Quantity Validity**: Negative line item prices, zero order quantities, and invalid tax calculations are quarantined.
4. **Temporal Consistency**: Future-dated timestamps beyond the snapshot cutoff are quarantined.
5. **Referential Integrity**: Cascading quarantine ensures that if a parent order is quarantined, its child line items are quarantined under `ORPHANED_ORDER_PARENT`.
6. **Financial Consistency**: Line net revenue and line contribution margin adhere strictly to point-in-time pricing and cost formulas:
   $$\text{Line Net Revenue} = (\text{quantity} \times \text{unit\_price\_at\_sale}) - \text{line\_discount}$$
   $$\text{Line Contribution Margin} = \text{Line Net Revenue} - (\text{quantity} \times \text{unit\_cost\_at\_sale})$$
7. **Valid Operational States**: Cancelled and Voided orders are preserved with valid operational flags for churn and operational bottleneck analysis.

---

## 6. Phase 3 Apache Spark Analytical Pipeline

The Phase 3 analytical pipeline executes natively in Apache Spark 4.2.0, consuming the clean Parquet dataset and materializing twelve precomputed analytical marts in `data/marts/spark/*.parquet`:

| # | Mart Name | Grain | Row Count | Purpose |
| :---: | :--- | :--- | :---: | :--- |
| 1 | `mart_menu_performance` | `restaurant + item` | 3,000 | 9-dimension menu engineering, composite score, 4 classifications, 10 tricky flags. |
| 2 | `mart_customer_rfm` | `customer` | 50,000 | Recency, Frequency, Monetary quintile scoring and 7 customer loyalty segments. |
| 3 | `mart_basket_analysis` | `item_pair` | 11,175 | Support, confidence, and association lift for co-ordered menu item pairs. |
| 4 | `mart_peak_analysis` | `restaurant + day + hour` | 1,643 | Hourly and day-of-week volume distributions, rush-hour indicators. |
| 5 | `mart_location_performance` | `restaurant + month` | 253 | Store-level margins, labor efficiency, customer counts, and seat turn rates. |
| 6 | `mart_channel_performance` | `restaurant + channel + month` | 976 | Dine-in, Takeout, and Delivery revenue, commission drag, and channel shares. |
| 7 | `mart_wastage` | `restaurant + item/ingr + week` | 151,029 | Dual-level wastage tracking (prepared dish vs raw ingredient) and high-risk target. |
| 8 | `mart_pricing` | `event (item/restaurant)` | 1,500 | 28-day pre/post price change volume response and price elasticity of demand. |
| 9 | `mart_promotions` | `promotion + restaurant` | 320 | Order-item-level promotion redemption, incremental margin, and promotion traps. |
| 10 | `mart_ratings_anomalies` | `item/restaurant + week` | 61,322 | Sentiment-rating divergence and sudden customer satisfaction drops. |
| 11 | `mart_sales_anomalies` | `restaurant + day` | 7,313 | 14-day rolling baseline Z-scores, volume spikes, drops, and zero-sales exceptions. |
| 12 | `mart_demand_historical` | `restaurant + item + day` | 450,779 | Calendar aggregations, chronological split windows, and seasonal-naive baselines. |
| **TOTAL** | **12 Analytical Marts** | — | **741,310** | **100% Real Spark-Materialized Parquet Records** |

---

## 7. Analytical Intelligence Contracts

### Menu Intelligence
- **Multi-Factor Percentile Model**:
  $$\text{Composite Score} = 0.25 S_{\text{Demand}} + 0.25 S_{\text{Profit}} + 0.15 S_{\text{Customer}} + 0.15 S_{\text{Wastage}} + 0.10 S_{\text{Trend}} + 0.10 S_{\text{PromoIndep}}$$
- **Four Standard Gated Classes**:
  - `Profit Driver`: High Margin ($\ge 50$th percentile) AND High Demand ($\ge 50$th percentile)
  - `Volume Driver`: Low/Med Margin ($< 50$th percentile) AND High Demand ($\ge 50$th percentile)
  - `Hidden Opportunity`: High Margin ($\ge 50$th percentile) AND Low/Med Demand ($< 50$th percentile)
  - `Low Performer`: Low/Med Margin ($< 50$th percentile) AND Low/Med Demand ($< 50$th percentile)
- **Ten Tricky-Case Boolean Evidence Flags**:
  1. `flag_high_selling_loss_making`: High volume with unit contribution margin $\le 0$.
  2. `flag_profitable_rarely_purchased`: Top 25% margin but bottom 25% volume.
  3. `flag_popular_high_wastage`: Top 25% volume but bottom 25% wastage health.
  4. `flag_high_rating_low_profitability`: Top 25% rating but bottom 25% margin.
  5. `flag_low_rating_high_sales`: Bottom 25% rating but top 25% volume.
  6. `flag_promotion_dependent`: Organic sales ratio $< 30\%$.
  7. `flag_location_divergence`: Item classification differs across store locations.
  8. `flag_weekend_only`: $\ge 65\%$ of volume sold on Saturdays and Sundays.
  9. `flag_seasonal_item`: Marked seasonal with activity concentrated in specific calendar windows.
  10. `flag_insufficient_history`: Total active observation days $< 14$.

### Wastage Intelligence
- **Dual-Path Routing**:
  - `PREPARED_DISH`: Linked via `source_menu_item_id`; wastage ratios computed against prepared units sold.
  - `RAW_INGREDIENT`: Linked via `source_restaurant_id` + `ingredient_name`; ratios computed against inventory stock.
  - Raw ingredient waste and prepared dish waste are never blended into a single composite numerator.
- **Approved Target Definition (`next_week_wastage_risk`)**:
  $$\text{High Risk (1)} \iff (\text{waste\_cost\_ratio} > 0.05) \lor (\text{waste\_quantity\_ratio} > 0.10)$$
  - Verified distribution across 151,029 mart rows: 14,639 high risk (9.69%) and 136,390 low risk (90.31%).

### Promotion Intelligence
- **Line-Level Attribution**: Promotions are joined strictly at the order-item level (`order_items.source_promotion_id = promotions.source_promotion_id`). The header `orders` table contains no promotion foreign key.
- **Promotion Traps**: Campaigns where discounts exceed margins or where discounts reach $\ge 50\%$ with negative net contribution margin are explicitly identified (`is_promotion_trap = True`).

### Sales Anomaly Intelligence & Anti-Leakage
- **Leakage-Free Rolling Baseline**: The 14-day rolling mean and standard deviation are computed over `rowsBetween(-14, -1)`, strictly isolating prior historical observations and excluding the current day $t$ from its own baseline calculation.
- **Initial Days Handling**: Days with zero prior history evaluate to null baselines and default to normal anomaly status without synthetic distortion.

### Demand Time-Series & Chronological Splits
- **Historical Demand Mart**: `mart_demand_historical` contains calendar rollups and seasonal-naive baselines ($y_{t-1}$).
- **Anti-Leakage Note**: The historical demand mart serves as feature engineering and comparative baseline data; it is **NOT** the final ML forecast. Final model forecasts will be generated in Phase 4.
- **Chronological Split Manifest**:
  - `TRAIN`: 2025-01-01 → 2025-08-31 (300,129 item-week observations)
  - `VALIDATION`: 2025-09-01 → 2025-10-31 (75,165 item-week observations)
  - `TEST`: 2025-11-01 → 2025-11-30 (36,821 item-week observations)
  - `UNSEEN_COMPARISON`: 2025-12-01 → 2025-12-31 (38,664 item-week observations reserved for final pipeline evaluation)

---

## 8. Current Project Status

### Completed
- **Phase 1: Foundation**: Modular monolith structure, FastAPI backend, PostgreSQL operational schema, JWT/RBAC security, audit logging.
- **Phase 2: Data Foundation**: Synthetic dataset generator (1.31M rows), data quality profiling, defect quarantine isolation, clean Parquet snapshot.
- **Phase 3: Data Engineering & Spark Marts**: Spark session factory, schema mapping, joins, 12 analytical marts, rolling baseline correction, regression tests, and physical Parquet materialization (741,310 records).
- **Phase 4: Dual Machine Learning & Arena Evaluation**: Independent Spark MLlib and Python scikit-learn ML pipelines, chronological temporal split contract, zero future leakage enforcement, cross-pipeline consensus scoring (**71.52% overall agreement**), and head-to-head scorecard.
- **Phase 5: Frontend BI Dashboards & Decision Intelligence**: Complete 12-domain BI analytics platform in React 19 + TypeScript + Vite + Plotly, high-performance PyArrow columnar mart services, 14 FastAPI REST endpoints, What-If scenario simulation engine, and deterministic recommendation synthesis.

### Upcoming
- **Phase 6: Production Containerization & Deployment**: Docker Compose, production Nginx reverse proxy, CI/CD pipeline, and final competition submission package.

---

## 9. Verification & Code Quality

Current verified status of the repository:
- **Pytest Automated Tests**: **140 passed out of 140 tests** (100% pass rate in ~87s)
- **Oxlint Static Analysis (Frontend)**: **0 errors, 0 warnings** across 25 TypeScript files
- **Frontend Production Build**: `npm run build` compiles cleanly in ~1.8s
- **Ruff Static Analysis (Backend)**: **0 errors, 0 warnings** (`ruff check .` passed)
- **Ruff Code Formatting**: **217 files formatted cleanly** (`ruff format --check .` passed)

---

## 10. Execution Instructions

### 0. Quick Start (Windows Single-Click Launcher)

To launch both the FastAPI backend and React frontend concurrently with automatic browser launch:

```bat
# From repository root in cmd or PowerShell:
start.bat
```

Or simply **double-click** `start.bat` in Windows Explorer. This will:
1. Detect Python virtual environment (`.venv\Scripts\python.exe`) or system Python.
2. Launch the FastAPI backend on `http://127.0.0.1:8000` in a dedicated terminal.
3. Launch the Vite frontend on `http://localhost:5173` in a dedicated terminal.
4. Automatically open your default web browser to `http://localhost:5173/`.

---

### Application URLs & Access Links

| Service / Interface | URL | Description |
|---|---|---|
| **Frontend BI Dashboard** | [http://localhost:5173/](http://localhost:5173/) | Main interactive React 19 + Plotly BI analytics platform |
| **Backend REST API** | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) | FastAPI application root |
| **API Documentation (Swagger)** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Interactive Swagger UI testing all 14 analytical endpoints |
| **Alternative Docs (ReDoc)** | [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) | Clean OpenAPI reference documentation |
| **System Health Probe** | [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health) | API health check & operational database status |

---

### Frontend BI Dashboard Navigation (12 Domains)

Once launched, navigate through the sidebar to access all 12 SRS analytical modules:

1. **Executive Dashboard (`/`)**:
   - Boston Portfolio Matrix scatter plot (Stars, Cash Cows, Puzzles, Dogs).
   - High-level KPI cards: Total Net Revenue, Contribution Margin %, Wastage Loss, Churn Rate.
   - Quick recommendation alert teasers.
2. **Menu Intelligence (`/menu`)**:
   - 6-Factor composite scores: Profitability, Velocity, Labor, Complexity, Waste, and Feedback.
   - Filter by 10 Tricky Flags (e.g., `flag_high_waste_driver`, `flag_low_margin_trap`, `flag_weekend_only`).
   - Deep-dive dish inspection panel with pantry synergy scores.
3. **Customer Intelligence (`/customers`)**:
   - RFM customer segmentation donut chart (`Champions`, `Loyal`, `At Risk`, `Lost`).
   - Paginated customer churn risk table with ML churn probabilities, RFM scores, and loyalty tiers.
4. **Sales & Operations (`/sales`)**:
   - Hourly rush-hour velocity heatmap (Lunch: 11:00-14:00, Dinner: 18:00-21:00).
   - Dining channel revenue split (Dine-in, Takeout, Drive-Thru, Delivery Direct, Delivery Aggregator).
   - Location performance leaderboard ranked by net sales and order volume.
5. **Demand & Pricing (`/demand-pricing`)**:
   - Actual vs. Predicted daily demand time-series with ML error metrics.
   - Empirical price elasticity ($\epsilon$) vs contribution margin scatter plot.
6. **Wastage & Inventory (`/wastage`)**:
   - Root-cause loss breakdown (Spoilage, Preparation Error, Overproduction, Expired Stock).
   - Strict dual-path separation: Raw Ingredient stock loss vs. Prepared Dish kitchen scrap.
   - High-risk inventory items exceeding the $>5\%$ waste cost ratio threshold.
7. **Promotions & Basket Analysis (`/promotions`)**:
   - Promotion trap identification: campaigns driving volume spikes while net contribution margin collapses.
   - Market Basket Analysis: association rule pairings with Support, Confidence, and Lift ($Lift > 1.2$).
8. **Ratings & Anomalies (`/anomalies`)**:
   - Daily sales anomaly detector using rolling 14-day leakage-free Z-scores ($|Z| > 2.5$).
   - Real-time customer review alert stream highlighting negative sentiment and operational defect tags.
9. **Data Science Arena (`/arena`)**:
   - Consensus agreement scorecard: **71.52% overall consensus** between Spark MLlib and Python scikit-learn.
   - Head-to-head performance scorecard across Demand (RMSE/MAE), Wastage (AUC/Recall), and Churn (F1/LogLoss).
   - Side-by-side model disagreement table inspecting divergence between distributed and single-node pipelines.
10. **Actionable Recommendations (`/recommendations`)**:
    - Deterministic 5-step evidence-based recommendation cards across Menu Engineering, Wastage Prevention, and Retention.
    - Financial impact estimates, implementation effort, confidence levels, and status tracking (`Pending`, `In Progress`, `Implemented`).
11. **What-If Scenario Simulation (`/what-if`)**:
    - Interactive sensitivity sliders: Price Adjustment ($\pm 30\%$), Promotion Discount ($\pm 50\%$), and Waste Reduction ($0-80\%$).
    - Dynamic calculations using empirical price elasticity estimates and baseline margins to forecast volume, revenue, and margin deltas.
12. **Pipelines & Health (`/health`)**:
    - Columnar Parquet mart inspection verifying all 12 marts totaling 741,310 precomputed records.
    - Background pipeline launcher and operational execution history.

> [!NOTE]
> **Global Filters & Role Simulator**: Use the top header bar to filter data dynamically by restaurant location or switch simulated roles (`Admin`, `StoreManager`, `DataScientist`) to test persona-specific views.

---

### Manual CLI Execution Instructions

If you prefer to run services manually from separate terminal windows:

### 1. Environment Setup
```bash
# Install Python dependencies (including PySpark)
pip install -r requirements.txt

# Copy example environment configuration
cp .env.example .env
```

### 2. Run Automated Test Suite
```bash
# Execute full backend and analytical test suite (140 tests)
python -m pytest tests/

# Execute targeted mart tests
python -m pytest tests/unit/test_marts.py -v
```

### 3. Run Static Analysis & Formatting
```bash
# Check Python code quality with Ruff
ruff check .

# Check formatting
ruff format --check .

# Check TypeScript / React frontend code quality with Oxlint
cd apps/web && npx oxlint
```

### 4. Generate Synthetic Benchmark Dataset
```bash
# Generates 1.31M raw records under data/snapshots/competition_benchmark_v1/
python -m packages.common.generator.cli --profile competition --snapshot-id competition_benchmark_v1
```

### 5. Profile & Clean Dataset
```bash
# Profiles raw data, isolates 9,044 defects to quarantine, exports 1.30M clean rows
python -m packages.common.quality.cli --snapshot-dir data/snapshots/competition_benchmark_v1 --cleaned-dir data/cleaned --quarantine-dir data/quarantine
```

### 6. Execute Apache Spark Analytical Pipeline
```bash
# Materializes all 12 analytical marts (741,310 Parquet rows) into data/marts/spark/
python -m packages.pipeline_spark.runner
```

### 7. Run FastAPI Backend Server
```bash
# Start backend API (serves 14 analytical endpoints + operational endpoints)
uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Probe: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- Executive KPI Endpoint: [http://localhost:8000/api/v1/analytics/executive-summary](http://localhost:8000/api/v1/analytics/executive-summary)

### 8. Run React Frontend Development Server & Build
```bash
cd apps/web

# Install dependencies
npm install

# Start local Vite development server
npm run dev

# Build production bundle
npm run build
```

---

## 11. Team Workflow & Repository Rules

- **Feature Branches**: All active work must be conducted on dedicated feature branches (e.g. `feature/phase3-spark-marts`). Never push directly to `main`.
- **Meaningful Commits**: Every commit must represent a coherent, tested unit of work with clear commit messages.
- **No Secrets**: Never commit `.env` files, API keys, or database credentials.
- **No Bulk Data in Git**: All generated data folders (`data/snapshots/*`, `data/cleaned/*`, `data/quarantine/*`, `data/marts/*`, `data/artifacts/*`) are strictly excluded from Git tracking via `.gitignore`.
- **AI Usage Transparency**: All AI assistance must be disclosed and documented in `AI_USAGE.md` in accordance with competition governance rules.
- **Code Review**: Every pull request must pass automated pytest suites, Ruff linting, and human peer review before merging.
