# 0003. Dataset Contract and Generation Strategy

**Date**: 2026-09-24
**Status**: Proposed

## Summary

This specification establishes the formal dataset contract, statistical distribution framework, and deterministic generation strategy for the DineIQ Analytics platform. It defines how the synthetic generator will create all eleven core business domain tables matching the Software Requirements Specification scale of one million order line records, one hundred thousand orders, fifty thousand customers, one hundred fifty menu items across ten categories, twenty restaurant locations, twelve months of transactional history, one hundred thousand ratings, and fifty thousand wastage entries. The design enforces reproducible multi profile generation using fixed random seeds, embeds seventeen realistic operational complexity patterns without hard coding analytical conclusions, defines strict chronological train validation test split boundaries to prevent future data leakage, and guarantees independent dual pipeline ingestion for Apache Spark and Python data science workflows.

## Decision

**Chosen option**: Option 1: Deterministic Multi Profile Synthetic Data Generator producing Versioned Raw Snapshots with Stable Business Identifiers, Embedded Operational Complexities, and Chronological Split Manifests for Independent Dual Pipeline Ingestion.

**Implementation skills**: `architect` (`skills/architect/`)

---

## SRS Dataset Scale Targets and Cardinality

The generation engine must satisfy the following minimum scale benchmarks:

| Entity / Table | Minimum Scale Target | Generation Granularity | Cardinality & Relationship Constraints |
|---|---|---|---|
| `restaurants` | 20 locations | Root master table | 1 to many with `orders`, `inventory`, `wastage`, `pricing_history` |
| `menu_categories` | 10 categories | Root catalog table | 1 to many with `menu_items`, `promotions` |
| `menu_items` | 150 items | Catalog child of categories | Average 15 items per category (range: 10 to 25) |
| `customers` | 50,000 customers | Root customer table | 1 to many with `orders` and `ratings` |
| `promotions` | 25 campaigns | Root marketing table | Linked to orders and order lines via promo codes |
| `pricing_history` | 1,500 records | SCD Type 2 history | Average 8 to 12 historical price records per menu item |
| `orders` | 100,000 unique orders | Header transactions | Distributed across 20 locations and 365 days (avg ~274 orders/day chain wide) |
| `order_items` | 1,000,000 line items | Detail transaction grain | Target mean: 10.0 line items per order (Poisson distribution: $\lambda = 10$, min 1, max 35) |
| `ratings` | 100,000 ratings | Feedback event grain | Distributed across orders, dishes, and restaurant locations |
| `inventory` | 3,000 records | Stock balance grain | Exactly 150 tracked ingredients per restaurant across 20 locations ($150 \times 20 = 3,000$) |
| `wastage` | 50,000 discard logs | Operational loss grain | Average ~7 discard logs per restaurant per day across 365 days ($7 \times 20 \times 365 \approx 51,100$) |

---

## Realistic Data Complexity Framework

To enable robust evaluation of the data cleaning pipeline, machine learning models, and executive dashboards, the generator injects seventeen realistic business complexities. Each pattern reflects actual restaurant operations rather than synthetic random noise:

| Complexity Pattern | Affected Tables & Fields | Generation Mechanism & Injection Rate | Downstream Analytical & ML Use | Classification |
|---|---|---|---|---|
| **1. Missing Values** | `customers(email, phone)`, `orders(customer_id)`, `ratings(review_text)` | 10% guest orders with `customer_id = NULL`; 15% missing phone numbers; 40% blank review text | Data quality pipeline imputation and handling; guest checkout segmentation | Intentional realistic data quality condition |
| **2. Duplicate Records** | `orders(source_order_id)`, `order_items(source_order_item_id)` | 0.5% duplicate transaction rows injected with identical order identifiers and timestamps | Testing deduplication algorithms in Spark SQL and Pandas | Intentional data quality defect |
| **3. Invalid Transactions** | `order_items(unit_price_at_sale, quantity)`, `orders(order_timestamp)` | 0.2% negative unit prices, 0.1% zero quantities, 0.05% future timestamps | Testing range checks, outlier quarantine filters, and validation rules | Intentional data quality defect |
| **4. Cancelled Orders** | `orders(order_status)`, `order_items(line_net_revenue)` | 3.5% orders generated with status `'Cancelled'` or `'Voided'` | Revenue calculations exclude cancelled orders; cancellation rate prediction | Valid business operational state |
| **5. Changing Menu Prices** | `pricing_history(base_price, base_cost)`, `order_items(unit_price_at_sale)` | 30% of items experience 1 to 3 price adjustments across the 12 month timeline | Price elasticity modeling, what if scenario analysis, SCD Type 2 lookups | Valid business operational state |
| **6. Seasonal Demand** | `orders(order_timestamp, total_amount)` | Sinusoidal volume modulation: Summer (Jun-Aug) +15%, Winter Holiday (Nov-Dec) +25%, Feb post holiday -15% | Demand forecasting, seasonal menu planning, historical time series decomposition | Valid business operational pattern |
| **7. Weekend Demand Surge** | `orders(order_timestamp)` | Friday, Saturday, and Sunday generate 55% of weekly order volume (Monday-Thursday generate 45%) | Staff scheduling optimization, kitchen prep capacity planning | Valid business operational pattern |
| **8. Peak Hour Bimodal Curves** | `orders(order_timestamp)` | Bimodal Gaussian distribution: Lunch peak (12:00 to 14:00) 35% volume, Dinner peak (18:00 to 21:00) 45% volume | Hourly demand forecasting, staffing analytics, table turnover analysis | Valid business operational pattern |
| **9. Multi Location Variations** | `restaurants(dining_type)`, `orders(restaurant_id)` | Flagship urban locations generate 2.5x volume of suburban locations; urban locations feature higher average ticket size | Cross location performance benchmarking, regional menu mix intelligence | Valid business operational pattern |
| **10. Promotional Campaigns** | `promotions`, `order_items(line_discount, promotion_id)` | 20 promotional campaigns across seasonal, combo, and coupon discount types | Promotion lift analysis, coupon redemption rate modeling | Valid business operational pattern |
| **11. Customer RFM Segments** | `customers(loyalty_tier)`, `orders(customer_id)` | Pareto distribution: top 5% Champions generate 25% revenue; 20% Loyalists generate 35%; casual one off diners 40% | RFM segmentation, customer lifetime value modeling | Valid business behavioral pattern |
| **12. Churned Customers** | `customers(is_active)`, `orders(order_timestamp)` | 15% of historical customers have zero orders in the final 90 to 120 days | Customer churn prediction, win back campaign targeting | Valid business behavioral pattern |
| **13. New Customers** | `customers(registration_date)`, `orders(order_timestamp)` | Steady linear onboarding of new customers (~135 new registrations daily) | Cohort analysis, acquisition channel effectiveness | Valid business behavioral pattern |
| **14. Menu Engineering Matrix Quadrants** | `menu_items`, `order_items(quantity, line_contribution_margin)` | Item popularity and recipe cost configured to yield distinct Boston Consulting Group quadrants: 25% Stars, 25% Plowhorses, 25% Puzzles, 25% Dogs | Menu engineering matrix dashboard, dish repricing recommendations | Valid business performance pattern |
| **15. High Wastage Perishables** | `wastage(cost_loss_amount, wastage_reason)`, `menu_items` | Fresh seafood, salads, and daily soups have 4x higher spoilage rates than dry goods or frozen meats | Wastage prediction, procurement optimization, inventory shelf life alerts | Valid operational hazard pattern |
| **16. Rating and Sales Anomalies** | `ratings(rating_score)`, `orders(quantity)` | Injection of two localized rating drops (recipe change defect) and one viral sales spike (social media trend) | Anomaly detection algorithms, outlier alert triggers | Intentional business anomaly |
| **17. Promotion Trap (Misleading Deals)** | `promotions(is_misleading)`, `order_items(line_contribution_margin)` | Three promotional campaigns where deep discount (for example 45% off) drives high volume but yields negative contribution margin | Promotion trap detection, margin protection rules, discount governance | Intentional business risk pattern |

---

## Detailed Data Contract for the Eleven Tables

### Table 1: `customers`
- **Purpose**: Master customer repository for loyalty, RFM segmentation, and lifetime value modeling.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY` in PostgreSQL)
- **Stable source key**: `source_customer_id` (`VARCHAR(64)` unique, e.g. `'CUST-00042851'`)
- **Required fields**: `id`, `source_customer_id`, `registration_date`, `loyalty_tier`, `is_active`, `created_at`
- **Nullable fields**: `first_name`, `last_name`, `email`, `phone`, `preferred_channel`, `home_city`
- **Allowed values**: `loyalty_tier IN ('Bronze', 'Silver', 'Gold', 'Platinum', 'None')`; `preferred_channel IN ('Dine-in', 'Takeaway', 'Delivery Direct', 'Delivery Aggregator')`
- **Timestamp semantics**: UTC ISO 8601 (`TIMESTAMPTZ`)
- **Minimum cardinality**: 50,000 records

### Table 2: `restaurants`
- **Purpose**: Physical and operational attributes of restaurant branches for multi unit comparison.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY` in PostgreSQL)
- **Stable source key**: `source_restaurant_id` (`VARCHAR(64)` unique, e.g. `'REST-0012'`)
- **Required fields**: `id`, `source_restaurant_id`, `location_name`, `city`, `state_region`, `postal_code`, `seating_capacity`, `dining_type`, `opening_date`, `is_active`, `created_at`
- **Nullable fields**: `manager_name`, `latitude`, `longitude`
- **Allowed values**: `dining_type IN ('Fast Casual', 'Casual Dining', 'Fine Dining', 'Express Kiosk')`
- **Minimum cardinality**: 20 records

### Table 3: `menu_categories`
- **Purpose**: Culinary classification groupings for category level margin and demand analysis.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY` in PostgreSQL)
- **Stable source key**: `source_category_id` (`VARCHAR(64)` unique, e.g. `'CAT-004'`)
- **Required fields**: `id`, `source_category_id`, `category_name`, `display_order`, `is_active`, `created_at`
- **Nullable fields**: `description`
- **Allowed values**: Exactly 10 canonical categories: `'Appetizers'`, `'Entrees'`, `'Seafood Specialties'`, `'Pasta & Noodles'`, `'Sandwiches & Burgers'`, `'Side Dishes'`, `'Desserts'`, `'Non-Alcoholic Beverages'`, `'Bar & Cocktails'`, `'Chef Specials'`
- **Minimum cardinality**: 10 records

### Table 4: `menu_items`
- **Purpose**: Active dish offerings, benchmark retail prices, standard recipe ingredient costs, and preparation tags.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY` in PostgreSQL)
- **Stable source key**: `source_menu_item_id` (`VARCHAR(64)` unique, e.g. `'DISH-0128'`)
- **Foreign keys**: `category_id` references `menu_categories(id)` (`source_category_id` in files)
- **Required fields**: `id`, `source_menu_item_id`, `category_id`, `item_name`, `current_base_price`, `current_base_cost`, `prep_time_minutes`, `is_seasonal`, `is_active`, `spiciness_level`, `created_at`
- **Nullable fields**: `description`, `allergens`
- **Currency & units**: USD fixed decimal `DECIMAL(10,2)`; prep time in minutes; spiciness `0` to `4`
- **Minimum cardinality**: 150 records

### Table 5: `pricing_history`
- **Purpose**: Slowly Changing Dimension Type 2 tracking price and recipe cost modifications over time.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY` in PostgreSQL)
- **Stable source key**: `source_pricing_history_id` (`VARCHAR(64)` unique, e.g. `'PRC-001094'`)
- **Foreign keys**: `menu_item_id` references `menu_items(id)`; `restaurant_id` references `restaurants(id)` (nullable)
- **Required fields**: `id`, `source_pricing_history_id`, `menu_item_id`, `base_price`, `base_cost`, `effective_from`, `change_reason`, `created_at`
- **Nullable fields**: `restaurant_id`, `effective_to` (null indicates active current price)
- **Timestamp semantics**: UTC ISO 8601; `effective_to > effective_from` when populated
- **Minimum cardinality**: 1,500 records

### Table 6: `promotions`
- **Purpose**: Marketing discount programs, coupon codes, and duration windows for campaign lift and trap analysis.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY` in PostgreSQL)
- **Stable source key**: `source_promotion_id` (`VARCHAR(64)` unique, e.g. `'PROMO-0018'`)
- **Foreign keys**: `applicable_category_id`, `applicable_menu_item_id` (both nullable)
- **Required fields**: `id`, `source_promotion_id`, `campaign_name`, `discount_type`, `discount_value`, `start_date`, `end_date`, `minimum_order_amount`, `is_active`, `is_misleading`, `created_at`
- **Nullable fields**: `promo_code`, `applicable_category_id`, `applicable_menu_item_id`, `applicable_channel`
- **Allowed values**: `discount_type IN ('Percentage', 'Fixed Amount', 'Buy One Get One', 'Combo Bundle')`
- **Minimum cardinality**: 25 campaigns

### Table 7: `orders`
- **Purpose**: Order header recording transaction instant, fulfilling location, ordering channel, and settlement totals.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY` in PostgreSQL)
- **Stable source key**: `source_order_id` (`VARCHAR(64)` unique, e.g. `'ORD-00084920'`)
- **Foreign keys**: `customer_id` references `customers(id)` (nullable); `restaurant_id` references `restaurants(id)`
- **Required fields**: `id`, `source_order_id`, `restaurant_id`, `order_timestamp`, `order_channel`, `order_status`, `subtotal_amount`, `discount_amount`, `tax_amount`, `tip_amount`, `total_amount`, `payment_method`, `created_at`
- **Nullable fields**: `customer_id` (null signifies guest order)
- **Allowed values**: `order_channel IN ('Dine-in', 'Takeaway', 'Delivery Direct', 'Delivery Aggregator')`; `order_status IN ('Completed', 'Cancelled', 'Refunded', 'Voided')`; `payment_method IN ('Credit Card', 'Debit Card', 'Cash', 'Digital Wallet', 'Gift Card')`
- **Financial math**: `total_amount = subtotal_amount - discount_amount + tax_amount + tip_amount`
- **Minimum cardinality**: 100,000 records

### Table 8: `order_items`
- **Purpose**: Granular transaction line recording quantity, point in time sales price, ingredient standard cost, and line margin.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY` in PostgreSQL)
- **Stable source key**: `source_order_item_id` (`VARCHAR(64)` unique, e.g. `'ITEM-00948214'`)
- **Foreign keys**: `order_id` references `orders(id)`; `menu_item_id` references `menu_items(id)`; `promotion_id` references `promotions(id)` (nullable)
- **Required fields**: `id`, `source_order_item_id`, `order_id`, `menu_item_id`, `quantity`, `unit_price_at_sale`, `unit_cost_at_sale`, `line_discount`, `line_net_revenue`, `line_contribution_margin`, `created_at`
- **Nullable fields**: `promotion_id`, `special_instructions`
- **Financial formulas**:
  - `line_net_revenue = (quantity * unit_price_at_sale) - line_discount`
  - `line_contribution_margin = line_net_revenue - (quantity * unit_cost_at_sale)`
- **Minimum cardinality**: 1,000,000 records

### Table 9: `ratings`
- **Purpose**: Customer feedback, sentiment scores, and dish reviews supporting quality anomaly detection.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY` in PostgreSQL)
- **Stable source key**: `source_rating_id` (`VARCHAR(64)` unique, e.g. `'RAT-00078491'`)
- **Foreign keys**: `restaurant_id` references `restaurants(id)`; `order_id`, `customer_id`, `menu_item_id` (all nullable)
- **Required fields**: `id`, `source_rating_id`, `restaurant_id`, `rating_score`, `rating_timestamp`, `is_verified_purchase`, `created_at`
- **Nullable fields**: `order_id`, `customer_id`, `menu_item_id`, `food_rating`, `service_rating`, `ambiance_rating`, `review_text`
- **Allowed values**: `rating_score BETWEEN 1 AND 5`
- **Minimum cardinality**: 100,000 records

### Table 10: `inventory`
- **Purpose**: Current ingredient stock balances, procurement thresholds, and reorder levels by restaurant branch.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY` in PostgreSQL)
- **Stable source key**: `source_inventory_id` (`VARCHAR(64)` unique, e.g. `'INV-REST01-0084'`)
- **Foreign keys**: `restaurant_id` references `restaurants(id)`
- **Required fields**: `id`, `source_inventory_id`, `restaurant_id`, `ingredient_name`, `ingredient_category`, `current_stock_quantity`, `unit_of_measure`, `reorder_threshold`, `reorder_quantity`, `unit_purchase_cost`, `created_at`, `updated_at`
- **Nullable fields**: `last_restock_date`
- **Allowed values**: `unit_of_measure IN ('kg', 'g', 'L', 'ml', 'units', 'boxes')`; `ingredient_category IN ('Produce', 'Meat & Poultry', 'Dairy', 'Dry Goods', 'Beverage Supplies', 'Packaging')`
- **Minimum cardinality**: 3,000 records (150 ingredients across 20 locations)

### Table 11: `wastage`
- **Purpose**: Food discards, expired inventory, and cooking loss tracking for wastage prediction and cost recovery.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY` in PostgreSQL)
- **Stable source key**: `source_wastage_id` (`VARCHAR(64)` unique, e.g. `'WASTE-00049182'`)
- **Foreign keys**: `restaurant_id` references `restaurants(id)`; `menu_item_id` references `menu_items(id)` (nullable)
- **Required fields**: `id`, `source_wastage_id`, `restaurant_id`, `wastage_timestamp`, `quantity_lost`, `unit_of_measure`, `cost_loss_amount`, `wastage_reason`, `created_at`
- **Nullable fields**: `menu_item_id`, `ingredient_name`, `reported_by`
- **Allowed values**: `wastage_reason IN ('Expired', 'Over-preparation', 'Cooking Error', 'Equipment Failure', 'Customer Returned', 'Spillage')`
- **Minimum cardinality**: 50,000 records

---

## Stable Business Identifier Conventions

To enable seamless lineage and auditability across file storage and the relational database, every entity uses a standardized, human readable source identifier:

| Entity | Prefix Pattern | Format Specification | Example Identifier |
|---|---|---|---|
| `customers` | `CUST-` | Zero padded 8 digit integer | `CUST-00042851` |
| `restaurants` | `REST-` | Zero padded 4 digit integer | `REST-0012` |
| `menu_categories` | `CAT-` | Zero padded 3 digit integer | `CAT-005` |
| `menu_items` | `DISH-` | Zero padded 4 digit integer | `DISH-0142` |
| `pricing_history` | `PRC-` | Zero padded 6 digit integer | `PRC-000842` |
| `promotions` | `PROMO-` | Zero padded 4 digit integer | `PROMO-0018` |
| `orders` | `ORD-` | Zero padded 8 digit integer | `ORD-00084920` |
| `order_items` | `ITEM-` | Zero padded 8 digit integer | `ITEM-00948214` |
| `ratings` | `RAT-` | Zero padded 8 digit integer | `RAT-00078491` |
| `inventory` | `INV-` | Branch code plus 4 digit integer | `INV-REST01-0084` |
| `wastage` | `WASTE-` | Zero padded 8 digit integer | `WASTE-00049182` |

**Deterministic Generation Rule**: Identifiers are assigned sequentially based on the deterministic generation loop, guaranteeing that identical seeds yield identical business identifier strings on every execution.

---

## Deterministic Generation Strategy and Multi Profile Profiles

The dataset generator is implemented as a standalone script in `packages/common/generator/` parameterized by a configuration schema.

### Configurable Scale Profiles

```
+-----------------------------------------------------------------------------------------------+
| Profile 1: Development (`dev`)                                                                |
| - Target: Fast local testing, automated pytest CI execution (< 15 seconds)                   |
| - Scale: 10,000 order lines, 1,000 orders, 500 customers, 30 items, 5 branches, 500 ratings   |
+-----------------------------------------------------------------------------------------------+
                                                 |
                                                 v
+-----------------------------------------------------------------------------------------------+
| Profile 2: Competition Minimum (`competition`) [Default]                                      |
| - Target: Full SRS compliance, benchmark evaluations, complete dashboard visual density      |
| - Scale: 1,000,000 order lines, 100,000 orders, 50,000 customers, 150 items, 20 branches      |
|          100,000 ratings, 50,000 wastage records, 12 months history                           |
+-----------------------------------------------------------------------------------------------+
                                                 |
                                                 v
+-----------------------------------------------------------------------------------------------+
| Profile 3: Stress Test (`stress`)                                                             |
| - Target: Distributed PySpark scale testing and execution performance benchmarking            |
| - Scale: 5,000,000 order lines, 500,000 orders, 200,000 customers, 300 items, 50 branches     |
|          500,000 ratings, 250,000 wastage records                                             |
+-----------------------------------------------------------------------------------------------+
```

### Deterministic Seed Architecture
- **Master Seed**: Configured via `--seed` (default `42`).
- **Subordinate Domain Seeds**: Derived deterministically from the master seed to isolate entity generation loops:
  - `seed_customers = master_seed + 101`
  - `seed_catalog = master_seed + 202`
  - `seed_orders = master_seed + 303`
  - `seed_ratings = master_seed + 404`
  - `seed_wastage = master_seed + 505`
- Running the generator with `--profile competition --seed 42` produces bit for bit identical CSV and Parquet files every time.

---

## Chronological Split Strategy and Future Leakage Prevention

To ensure sound econometric and machine learning modeling, transactional data spanning the 12 month horizon (2025-01-01 through 2025-12-31) is segmented into explicit, non overlapping chronological partitions:

```
+---------------------------------------------------------------------------------------------------+
| Chronological Partition Timeline (12 Months: 2025-01-01 to 2025-12-31)                            |
+------------------------------------+------------------+------------------+------------------------+
| Months 1 to 8 (Jan 1 - Aug 31)     | M9-M10 (Sep-Oct) | Month 11 (Nov)   | Month 12 (Dec 1 - 31)  |
| Training Horizon (67% time)        | Validation (17%) | Test Horizon (8%)| Unseen Comparison (8%) |
| Features & Historical Baseline     | Model Tuning     | Model Evaluation | 100+ Competition Cases |
+------------------------------------+------------------+------------------+------------------------+
```

### Time Aware Modeling Governance
1. **Feature Cutoff Rule**: For any prediction target evaluated at timestamp $T$, features may only incorporate historical data logged on or before $T - \Delta t$ (where $\Delta t$ is at least 1 day for daily demand forecasting, and at least 7 days for weekly wastage prediction).
2. **No Future Leakage Guarantee**: Aggregations such as customer historical spend, item rolling sales velocity, or store average ticket size must strictly compute over historical windows preceding the evaluation date.
3. **Unseen Comparison Slice**: The final month (December 2025) contains a designated evaluation slice with at least 100 distinct menu items, locations, and customer cohorts. Both the Spark and Python pipelines generate predictions against this exact slice without having trained on it, enabling unbiased evaluation comparison in `packages/comparison`.
4. **Split Manifest**: The split boundaries and cohort definitions are exported as `split_manifest.json` alongside the raw snapshot, locking the train, validation, test, and comparison time windows.

---

## Dual Pipeline Compatibility and Strict Independence

The architecture enforces strict decoupling between Pipeline 1 (Apache Spark) and Pipeline 2 (Python Data Science):

```
                                  +-----------------------------+
                                  |  Immutable Raw Snapshot     |
                                  | `data/snapshots/vYYYYMMDD/` |
                                  +--------------+--------------+
                                                 |
                         +-----------------------+-----------------------+
                         | (Shared Read Only)                            | (Shared Read Only)
                         v                                               v
        +--------------------------------+              +--------------------------------+
        | Pipeline 1: Apache Spark       |              | Pipeline 2: Python Data Science|
        | - `packages/pipeline_spark`    |              | - `packages/pipeline_python`   |
        | - PySpark & Spark SQL cleaning |              | - Pandas & NumPy cleaning      |
        | - Spark VectorAssembler & MLlib|              | - Scikit-learn pipelines       |
        | - Writes: `data/marts/spark/`  |              | - Writes: `data/marts/python/` |
        +----------------+---------------+              +----------------+---------------+
                         |                                               |
                         +-----------------------+-----------------------+
                                                 | (Independent Outputs)
                                                 v
                                  +-----------------------------+
                                  | Comparison Engine           |
                                  | `packages/comparison`       |
                                  | - Reads both marts          |
                                  | - Evaluates on unseen 100   |
                                  | - Computes RMSE, runtime, F1|
                                  +-----------------------------+
```

**Permitted Sharing**: Clean raw snapshots, entity business identifiers (`source_*_id`), evaluation metrics in `packages/core/contracts.py`, and the chronological split manifest (`split_manifest.json`).
**Strictly Prohibited**: Sharing intermediate cleaned dataframes, prepared feature matrices, serialized model weights, or prediction scores between pipelines.

---

## Data Quality Contract and Injection Rules

The dataset generator deliberately introduces controlled data quality anomalies to validate the cleaning capabilities of the ingestion pipelines:

| Quality Dimension | Verification Rule | Generator Injection Rate | Severity | Pipeline Resolution Strategy |
|---|---|---|---|---|
| **Referential Integrity** | Every `order_items.menu_item_id` must exist in `menu_items` | 0.05% orphaned item references | Error | Quarantined to `quarantine_records` mart; logged in DQ summary |
| **Price / Cost Positivity** | `unit_price_at_sale > 0` and `unit_cost_at_sale >= 0` | 0.2% negative unit prices | Error | Imputed from `pricing_history` active price at transaction timestamp |
| **Quantity Validity** | `quantity > 0` | 0.1% zero quantities | Warning | Excluded from financial aggregations; retained for audit log |
| **Duplicate Transactions** | `source_order_id` uniqueness | 0.5% duplicate submissions | Error | Deduplicated by retaining earliest transaction timestamp record |
| **Missing Customer Coordinates** | `orders.customer_id IS NOT NULL` | 10.0% null guest orders | Info | Flagged as `'Guest Checkout'`; valid for revenue, excluded from RFM |
| **Rating Score Bounds** | `rating_score BETWEEN 1 AND 5` | 0.1% out of range scores (0 or 6) | Error | Clipped to valid range [1, 5] or quarantined |
| **Chronological Feasibility** | `order_timestamp <= snapshot_generation_time` | 0.05% future timestamps | Error | Quarantined; excluded from time series training splits |
| **Inventory Non Negativity** | `current_stock_quantity >= 0` | 0.3% negative stock balances | Warning | Clamped to 0.00; flagged for stockout alert |

---

## Business Distribution Framework

To ensure realistic, non uniform patterns that enable downstream analytics to uncover meaningful business insights:

### 1. Restaurant Location Distribution
- Locations follow 3 dining categories:
  - 4 Flagship Urban locations: 35% of total orders (high volume, high average ticket $45).
  - 12 Casual Dining suburban locations: 50% of total orders (moderate ticket $32).
  - 4 Express Kiosks: 15% of total orders (high frequency, lower ticket $18).

### 2. Temporal Distributions
- **Hour of Day**: Bimodal distribution centered at lunch (12:00 to 14:00, 35% volume) and dinner (18:00 to 21:00, 45% volume). Off peak hours (10:00-11:30 and 14:30-17:00) account for 18% volume; late night accounts for 2%.
- **Day of Week**: Weekend surge where Friday (18%), Saturday (22%), and Sunday (15%) drive 55% of transactions. Monday through Thursday average 11.25% each.
- **Monthly Seasonality**: Base monthly volume is multiplied by seasonal factors: January (0.90), February (0.85), March (0.95), April (1.00), May (1.05), June (1.15), July (1.15), August (1.10), September (1.00), October (1.05), November (1.20), December (1.25).

### 3. Customer Purchase Frequency (Pareto Distribution)
- **Top 5% (Champions)**: Frequency of 35 to 60 orders/year; average order value $55.
- **Next 15% (Loyalists)**: Frequency of 12 to 25 orders/year; average order value $38.
- **Next 30% (Regulars)**: Frequency of 4 to 10 orders/year; average order value $30.
- **Remaining 50% (Casuals / One off)**: Frequency of 1 to 2 orders/year; average order value $22.
- **Guest Orders**: 10% of total orders lack customer link.

### 4. Menu Engineering Matrix (BCG Quadrants)
- **Stars (Profit Drivers)**: Top 25% order volume, contribution margin > $14.00 (e.g. Signature Ribeye Steak, Truffle Pasta).
- **Plowhorses (Volume Drivers)**: Top 25% order volume, contribution margin < $7.00 (e.g. Classic French Fries, House Soft Drinks).
- **Puzzles (Hidden Opportunities)**: Low 25% order volume, contribution margin > $14.00 (e.g. Artisanal Seafood Bisque, Rack of Lamb).
- **Dogs (Low Performers)**: Low 25% order volume, contribution margin < $7.00 (e.g. Cabbage Slaw, Bland Steamed Veggies).

---

## SRS Analytical Requirement Traceability Matrix

| SRS Analytical Module | Required Tables | Key Fields Traced | Generated Business Condition | Consuming Downstream Pipeline |
|---|---|---|---|---|
| **Menu Profitability & BCG Classification** | `order_items`, `menu_items` | `line_net_revenue`, `line_contribution_margin`, `quantity` | Distinct item clusters in volume and margin quadrants | Spark Menu Analytics & Python Menu Analytics |
| **Customer Segmentation & RFM** | `orders`, `customers` | `order_timestamp`, `source_customer_id`, `total_amount` | Pareto spend distribution, varying recency gaps | Python Data Science (K-Means & RFM scoring) |
| **Market Basket Analysis** | `order_items`, `orders` | `source_order_id`, `source_menu_item_id` | Affinity rules: Burgers co occur with Fries (80% confidence), Wine with Steak | Spark MLlib (FP-Growth) & Python (Apriori) |
| **Peak Period & Channel Analysis** | `orders` | `order_timestamp`, `order_channel`, `restaurant_id` | Bimodal hour peaks, channel split variations across locations | Spark SQL aggregation marts & Plotly dashboards |
| **Hourly Demand Forecasting** | `orders`, `order_items` | `order_timestamp`, `quantity`, `category_id` | Sinusoidal seasonal trend with weekend/holiday uplifts | Spark MLlib (GBTRegressor) & Python (RandomForest) |
| **Wastage Prediction & Root Cause** | `wastage`, `inventory`, `menu_items` | `wastage_timestamp`, `cost_loss_amount`, `wastage_reason` | High spoilage on fresh perishables, prep loss correlation | Python Data Science & Spark MLlib |
| **Price Elasticity & What If Simulation** | `pricing_history`, `order_items` | `unit_price_at_sale`, `quantity`, `effective_from` | Price hikes on specific items reduce volume by 25% ($\epsilon > 1.2$) | Python Econometric Modeling & FastAPI simulator |
| **Promotion Trap Detection** | `promotions`, `order_items` | `line_discount`, `line_contribution_margin`, `is_misleading` | 3 campaigns drive high volume with negative net contribution margin | Spark SQL & Python comparison marts |
| **Rating Anomaly Detection** | `ratings`, `orders` | `rating_score`, `rating_timestamp`, `source_menu_item_id` | Localized rating collapse on 2 dishes following recipe cost cut | Python isolation forest / z score anomaly detector |
| **Customer Churn Risk** | `customers`, `orders` | `registration_date`, `order_timestamp`, `is_active` | Inactivity window > 90 days for 15% of historical patrons | Python Logistic Regression / XGBoost churn model |

---

## File Organization and Storage Strategy

```
data/
├── snapshots/
│   └── v20260924_180000/
│       ├── manifest.json              # Checksums, row counts, random seed, generation config
│       ├── split_manifest.json        # Chronological train, validation, test, comparison bounds
│       ├── customers.csv              # Raw CSV format (and/or uncompressed Parquet)
│       ├── restaurants.csv
│       ├── menu_categories.csv
│       ├── menu_items.csv
│       ├── pricing_history.csv
│       ├── promotions.csv
│       ├── orders.parquet             # Stored as Parquet due to 100K+ volume
│       ├── order_items.parquet        # Stored as Parquet due to 1,000,000+ volume
│       ├── ratings.parquet
│       ├── inventory.csv
│       └── wastage.csv
├── marts/
│   ├── spark/                         # Output marts computed by Apache Spark
│   │   ├── mart_menu_performance/
│   │   ├── mart_hourly_demand/
│   │   └── mart_wastage_prediction/
│   └── python/                        # Output marts computed by Python Data Science
│       ├── mart_customer_rfm/
│       ├── mart_price_elasticity/
│       └── mart_churn_risk/
└── artifacts/
    ├── spark/                         # Serialized Spark MLlib models
    └── python/                        # Serialized scikit-learn models
```

**Git Version Control Boundary**:
- In accordance with the `.gitignore` policy and pre commit `--maxkb=1000` rule, the bulk generated files in `data/snapshots/*`, `data/marts/*`, and `data/artifacts/*` are never committed to GitHub.
- Committed repository evidence includes:
  - Generator script code in `packages/common/generator/`
  - Generator test suite in `tests/unit/test_generator.py`
  - Configuration profiles (`config/generator/profiles.yaml`)
  - A committed mini seed dataset in `tests/data/sample_dataset/` (100 rows per table)
  - Data dictionary documentation in `docs/data-dictionary.md`
  - Generation run instructions in `README.md`

---

## Build plan

The build plan follows the project Tracer Bullet approach, establishing the generator engine, configuration profiles, verification tests, and manifest generation:

1. Create generator configuration schemas and domain distributions in `packages/common/generator/config.py`, satisfies **AC-1**, **AC-4**
2. Implement deterministic master catalog and customer generator in `packages/common/generator/catalogs.py` with stable source identifiers, satisfies **AC-1**, **AC-3**
3. Implement high volume transaction generator (`orders`, `order_items`, `ratings`, `wastage`) with mathematical metric formulas and complexity patterns in `packages/common/generator/transactions.py`, satisfies **AC-2**, **AC-5**, **AC-7**
4. Implement manifest creation and chronological split manifest exporter in `packages/common/generator/manifest.py`, satisfies **AC-6**, **AC-8**
5. Create generator CLI entry point in `packages/common/generator/cli.py` and automated test suite in `tests/unit/test_generator.py` verifying row counts, math formulas, and deterministic seed reproducibility, satisfies **AC-1**, **AC-2**, **AC-6**

## Consequences

**Positive**:
- The multi profile generator allows instant local unit testing via the `dev` profile while providing full SRS scale verification via the `competition` profile.
- Embedding seventeen realistic complexity patterns enables the data quality and ML pipelines to demonstrate advanced enterprise capabilities rather than operating on clean trivial data.
- Fixed chronological split boundaries strictly prevent future data leakage, ensuring model evaluation integrity.
- Stable business identifiers (`source_*_id`) provide transparent lineage from raw CSV files to finished dashboard charts.

**Negative and Tradeoffs**:
- Generating one million order lines in Python requires memory efficient batch streaming (e.g. writing Parquet chunks in batches of 50,000 rows) to prevent out of memory errors on local laptops.
- Maintaining seventeen intentional complexity patterns requires the cleaning pipelines to implement explicit filtering rules rather than assuming pristine inputs.

**Neutral**:
- Requires disk space of approximately 150MB to 250MB for the uncompressed raw competition snapshot.

## Follow-up

- [ ] Implement the dataset generator engine during Feature 5 build execution (`/develop dataset generation script`).
- [ ] Document the data dictionary in `docs/data-dictionary.md` upon generator implementation.

## Rationale

Reasoning, alternatives considered, and architectural tradeoffs: see [rationale.md](rationale.md).
