# 0002. Data Model and Relational Schema Architecture

**Date**: 2026-09-24
**Status**: Proposed

## Summary

This specification establishes the core relational data model and schema architecture for the DineIQ Analytics platform. It defines the structure, constraints, types, and relationships for all eleven business domain tables: customers, orders, order items, menu items, menu categories, restaurants, pricing history, promotions, ratings, inventory, and wastage. The design implements a hybrid architecture where PostgreSQL enforces structural integrity for operational master data, application state, and metadata using sixty four bit identity primary keys, while immutable, versioned Parquet snapshots and columnar analytical marts handle high volume analytical queries exceeding one million transaction records. Dual identifier semantics (surrogate database keys alongside stable business source keys) provide end to end lineage and cross pipeline traceability between operational records, raw data files, Spark and Python feature marts, and serialized model artifacts.

## Decision

**Chosen option**: Option 1: Hybrid Multi Tier Data Architecture with PostgreSQL for Operational Master Data and Metadata, Immutable Versioned Raw Snapshots for Pipeline Ingestion, and Columnar Parquet Analytical Marts for Dashboards.

**Implementation skills**: `architect` (`skills/architect/`)

## Project Owner Decisions

This specification formally incorporates the authoritative decisions provided by the project owner:

1. **PostgreSQL Primary Keys**:
   - All relational tables in PostgreSQL use `id BIGINT GENERATED ALWAYS AS IDENTITY` as the surrogate primary key.
   - Surrogate keys provide predictable, high performance clustered primary index structures, standard auto increment ergonomics in SQLAlchemy, and minimal foreign key join overhead within the operational relational database.

2. **Stable Source and Business Identifiers**:
   - Every business entity that originates from the generated raw dataset carries both a surrogate database identifier (`id`) and a stable source identifier (for example `source_order_id VARCHAR(64) UNIQUE NOT NULL`).
   - The stable source identifier originates in the dataset generator and remains invariant across all downstream artifacts: raw snapshot CSV files, cleaned Parquet tables, feature engineering datasets, Spark DataFrames, Pandas DataFrames, and prediction outputs.
   - This dual key design enables unambiguous cross layer traceability, reproducible joins between pipeline outputs and source snapshots, and transparent lineage audits without coupling pipeline logic to transient database identity sequences.

3. **Raw Dataset Source Identifier Retention**:
   - The raw and versioned dataset snapshots in `data/snapshots/` must preserve these stable business source identifiers across all eleven entities.
   - Foreign key linkages within raw files use stable source identifiers (for example `source_order_id` and `source_menu_item_id` on order item records), ensuring raw data files remain self contained and queryable independently of whether a PostgreSQL instance is running.

4. **PostgreSQL Transaction Table Retention Policy**:
   - The complete high volume transactional dataset (one million or more order line records) is strictly prohibited from being mirrored in full into PostgreSQL.
   - PostgreSQL is reserved for:
     - Operational master catalog and branch configuration data (`restaurants`, `menu_categories`, `menu_items`, `promotions`).
     - Application users, roles, password hashes, and session metadata.
     - Asynchronous background job logs (`job_runs`) and model registry metadata (`model_registry`).
     - Generated business recommendations, what if simulation templates, and security audit logs.
     - An optional, limited operational demo transaction slice (for example, the most recent 5,000 to 10,000 orders) used for live application demonstrations and administrative point of sale order entry.
   - The complete historical transactional volume remains stored in immutable raw snapshots (`data/snapshots/`), cleaned Parquet tables, and precomputed analytical Parquet marts (`data/marts/`).

5. **Dataset Scale Invariants Preserved**:
   - The data model and storage strategy support the full dataset minimums required by the SRS:
     - At least 1,000,000 order line records
     - At least 100,000 unique orders
     - At least 50,000 customers
     - At least 150 menu items
     - At least 10 categories
     - At least 20 locations
     - At least 12 months historical transaction horizon
     - At least 100,000 ratings
     - At least 50,000 wastage records

6. **Query Engine Architecture (Exclusion of DuckDB as a Hard Dependency)**:
   - DuckDB is not a required architectural dependency at this stage.
   - No new database or query engine is introduced into the stack.
   - The platform architecture remains strictly centered on the approved components:
     - PostgreSQL for operational relational data and application state
     - Apache Spark, PySpark, and Spark SQL for big data cleaning, joins, and MLlib modeling
     - Apache Parquet for columnar analytical storage and feature marts
     - Python, Pandas, NumPy, and scikit-learn for independent data science and ML modeling
     - FastAPI and Uvicorn for asynchronous backend services
     - React 19 and TypeScript for interactive user interface dashboards

7. **Lightweight Parquet Ingestion via PyArrow**:
   - PyArrow is utilized solely as a lightweight columnar reader and writer for Parquet files in Python domain services and API route handlers.
   - PyArrow does not serve as an independent database platform, but rather as an embedded format parser for scanning precomputed analytical marts.

8. **Preservation of Core Architectural Principles**:
   - Point in time transaction sales price and ingredient cost capture on order lines.
   - Slowly Changing Dimension (SCD Type 2) tracking for menu item price and cost history.
   - Strict UTC timestamp representation with timezone offset.
   - Chronological modeling boundaries with explicit lag rules to prevent future data leakage.
   - Strict independence between Spark and Python data science pipelines.
   - Support for realistic dirty data in raw snapshots while enforcing strong analytical contracts.
   - Explicit mathematical separation between contribution margin and net profit.
   - Clean modular monolith layout separating application, database, and pipeline packages.

---

## Requirements

**User stories**:
- As a restaurant executive, I want reliable transactional records with point in time price and cost captures so that menu profitability, volume driver classifications, and contribution margins reflect actual historical financial performance.
- As a data scientist on Pipeline 1 (Spark) or Pipeline 2 (Python), I want access to versioned raw snapshots with stable source identifiers and clear schema contracts so that data cleaning, feature engineering, and model training run independently without mutual dependencies.
- As an operations manager, I want inventory and wastage records linked to restaurant locations and menu items so that demand forecasting and wastage prediction models can identify root causes of spoilage.
- As a marketing analyst, I want historical promotion campaigns linked to order lines and customer profiles so that promotion effectiveness and promotion trap risks can be measured accurately.
- As an auditor or competition judge, I want clear lineage tracing each dashboard metric back through analytical marts and cleaning jobs to the original raw snapshot records.

**Acceptance criteria**:
- **AC-1**: All eleven core tables (customers, orders, order items, menu items, menu categories, restaurants, pricing history, promotions, ratings, inventory, wastage) have explicit surrogate primary keys (`id BIGINT GENERATED ALWAYS AS IDENTITY`), stable business source identifiers (`source_*_id VARCHAR(64)`), foreign keys, column types, nullability rules, check constraints, and performance indexes defined.
- **AC-2**: The transaction line schema records `unit_price_at_sale`, `unit_cost_at_sale`, and `line_discount` directly on each order item, satisfying the exact metric formula: net revenue equals quantity multiplied by unit price at sale minus line discount, and contribution margin equals net revenue minus quantity multiplied by unit cost at sale.
- **AC-3**: Price and cost fluctuations over time are tracked using a Slowly Changing Dimension (SCD Type 2) in `pricing_history` with `effective_from` and `effective_to` timestamp bounds, supporting chronological price lookup and elasticity analysis without retroactive mutation.
- **AC-4**: Ordering channels (Dine in, Takeaway, Mobile App, Aggregator Delivery) and payment methods are modeled through validated, extensible enumerations rather than hard coded business constants.
- **AC-5**: The schema architecture strictly isolates raw snapshot files (which contain realistic dirty data, nulls, duplicates, and cancelled orders) from cleaned analytical datasets and operational PostgreSQL metadata, ensuring raw data flaws do not break operational tables.
- **AC-6**: Time semantics enforce UTC timestamps (`TIMESTAMPTZ`), explicit date formats, and strict chronological partition boundaries to prevent future data leakage in feature engineering and time series modeling.
- **AC-7**: All currency fields are defined using exact fixed precision decimal types (`DECIMAL(10,2)` or `DECIMAL(12,2)`) to eliminate floating point rounding inaccuracies across analytical calculations.
- **AC-8**: Ratings are constrained to valid score ranges between one and five, with optional links to specific order items and verified purchase flags for anomaly detection.
- **AC-9**: Inventory and wastage tables define explicit units of measurement (kilograms, grams, liters, units) and normalized reason codes (expired, prep loss, cooking error, spoiled) supporting wastage prediction and recipe cost modeling.
- **AC-10**: The model supports full lineage tracing from raw snapshot identifier through data cleaning jobs, trained model artifacts, and generated analytical marts via stable source identifiers and foreign keys into job tracking metadata.

---

## Feature design

### Relational Entity Relationship Overview

The operational relational schema in PostgreSQL models eleven business domain tables. Foreign keys between tables in PostgreSQL reference the sixty four bit surrogate `id`, while stable business identifiers (`source_*_id`) provide cross layer lineage into raw snapshot files and Parquet analytical marts:

```
                              +--------------------+
                              |  menu_categories   |
                              +---------+----------+
                                        | 1 (id)
                                        |
                                        | N (category_id)
                              +---------v----------+
                              |     menu_items     |<-----------------------+
                              +----+----------+----+                        |
                                   | 1 (id)   | 1 (id)                      |
          +------------------------+          +-----------+                 |
          | N (menu_item_id)                              | N (menu_item_id)|
+---------v----------+                         +----------v---------+       |
|  pricing_history   |                         |     inventory      |       |
+--------------------+                         +----------+---------+       |
                                                          | N (ingredient)  |
                                                          |                 |
+--------------------+                         +----------v---------+       |
|    restaurants     +------------------------>|      wastage       |       |
+---+-----------+----+ 1 (id)                 N+--------------------+       |
    | 1 (id)    | 1 (id)                       (restaurant_id)              |
    |           |                                                           |
    | N         | N (restaurant_id)                                         |
    |         +-v------------------+                   +------------------+ |
    |         |       orders       |                   |    promotions    | |
    |         +---+-----------+----+                   +--------+---------+ |
    |             | 1 (id)    | 1 (id)                          | 1 (id)    |
    |             |           |                                 |           |
    |             | N         | N (order_id)                    | N         |
    |   +---------v----+    +-v------------------+              |           |
    |   |   ratings    |    |    order_items     |<-------------+           |
    |   +--------------+    +--------------------+ (promotion_id)          |
    |   (restaurant_id)                                                     |
    |                                                                       |
    | N (restaurant_id)                                                     |
+---v----------------+                                                      |
|     customers      +------------------------------------------------------+
+--------------------+ (customer_id on orders and ratings)
```

---

### Detailed Schema Specifications for the Eleven Core Tables

#### 1. `customers`
- **Purpose**: Stores customer profiles, loyalty tiers, contact coordinates, and acquisition metadata for customer lifetime value and RFM segmentation.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY`)
- **Stable source key**: `source_customer_id` (`VARCHAR(64)`, unique, required, indexed; e.g. `'CUST-00042851'`)
- **Foreign keys**: None.
- **Columns**:
  - `id`: Surrogate operational primary key, required.
  - `source_customer_id`: Stable source identifier, `VARCHAR(64)`, required, unique.
  - `first_name`: Customer given name, `VARCHAR(60)`, nullable (allows privacy opted out profiles).
  - `last_name`: Customer family name, `VARCHAR(60)`, nullable.
  - `email`: Contact email address, `VARCHAR(255)`, nullable, unique when present.
  - `phone`: Telephone contact number, `VARCHAR(30)`, nullable.
  - `registration_date`: Date account was created, `DATE`, required.
  - `loyalty_tier`: Customer tier status, `VARCHAR(20)`, required, default `'Bronze'`. Allowed values: `'Bronze'`, `'Silver'`, `'Gold'`, `'Platinum'`, `'None'`.
  - `preferred_channel`: Most frequented channel, `VARCHAR(30)`, nullable. Allowed values: `'Dine-in'`, `'Takeaway'`, `'Delivery Direct'`, `'Delivery Aggregator'`.
  - `home_city`: Primary residence city, `VARCHAR(100)`, nullable.
  - `is_active`: Account status flag, `BOOLEAN`, required, default `TRUE`.
  - `created_at`: Row creation timestamp, `TIMESTAMPTZ`, required, default `CURRENT_TIMESTAMP`.
  - `updated_at`: Row modification timestamp, `TIMESTAMPTZ`, required, default `CURRENT_TIMESTAMP`.
- **Constraints**:
  - `CHK_customers_loyalty_tier`: `loyalty_tier IN ('Bronze', 'Silver', 'Gold', 'Platinum', 'None')`
  - `CHK_customers_reg_date`: `registration_date <= CURRENT_DATE`
- **Indexes**:
  - `idx_customers_source_id` ON `customers(source_customer_id)` UNIQUE
  - `idx_customers_email` ON `customers(email)` WHERE `email IS NOT NULL`
  - `idx_customers_loyalty` ON `customers(loyalty_tier)`
  - `idx_customers_reg_date` ON `customers(registration_date)`
- **Scale expectation**: 50,000 to 100,000 customer records.

#### 2. `restaurants`
- **Purpose**: Defines physical restaurant branches, operating types, dining capacities, and regional identifiers for multi unit comparison.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY`)
- **Stable source key**: `source_restaurant_id` (`VARCHAR(64)`, unique, required, indexed; e.g. `'REST-0012'`)
- **Foreign keys**: None.
- **Columns**:
  - `id`: Surrogate operational primary key, required.
  - `source_restaurant_id`: Stable source identifier, `VARCHAR(64)`, required, unique.
  - `location_name`: Branch trade name, `VARCHAR(100)`, required, unique.
  - `city`: Operating municipality, `VARCHAR(100)`, required.
  - `state_region`: Province, state, or regional territory, `VARCHAR(100)`, required.
  - `postal_code`: Postal code, `VARCHAR(20)`, required.
  - `seating_capacity`: Total available indoor and patio seats, `INT`, required.
  - `dining_type`: Service category, `VARCHAR(40)`, required. Allowed values: `'Fast Casual'`, `'Casual Dining'`, `'Fine Dining'`, `'Express Kiosk'`.
  - `manager_name`: Branch general manager name, `VARCHAR(100)`, nullable.
  - `opening_date`: Branch opening date, `DATE`, required.
  - `latitude`: Geographical latitude, `DECIMAL(9,6)`, nullable.
  - `longitude`: Geographical longitude, `DECIMAL(9,6)`, nullable.
  - `is_active`: Active operational status, `BOOLEAN`, required, default `TRUE`.
  - `created_at`: Row creation timestamp, `TIMESTAMPTZ`, required, default `CURRENT_TIMESTAMP`.
- **Constraints**:
  - `CHK_restaurants_capacity`: `seating_capacity > 0`
  - `CHK_restaurants_dining_type`: `dining_type IN ('Fast Casual', 'Casual Dining', 'Fine Dining', 'Express Kiosk')`
- **Indexes**:
  - `idx_restaurants_source_id` ON `restaurants(source_restaurant_id)` UNIQUE
  - `idx_restaurants_city` ON `restaurants(city)`
  - `idx_restaurants_dining_type` ON `restaurants(dining_type)`
- **Scale expectation**: 20 to 50 branch locations.

#### 3. `menu_categories`
- **Purpose**: Provides category classification for menu items, enabling category level profitability, mix analysis, and menu balancing.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY`)
- **Stable source key**: `source_category_id` (`VARCHAR(64)`, unique, required, indexed; e.g. `'CAT-005'`)
- **Foreign keys**: None.
- **Columns**:
  - `id`: Surrogate operational primary key, required.
  - `source_category_id`: Stable source identifier, `VARCHAR(64)`, required, unique.
  - `category_name`: Title of category, `VARCHAR(60)`, required, unique. Examples: `'Appetizers'`, `'Main Courses'`, `'Beverages'`, `'Desserts'`, `'Side Dishes'`, `'Chef Specials'`.
  - `description`: Narrative description of category, `TEXT`, nullable.
  - `display_order`: Presentation sort order on customer menus, `INT`, required, default `0`.
  - `is_active`: Active status flag, `BOOLEAN`, required, default `TRUE`.
  - `created_at`: Creation timestamp, `TIMESTAMPTZ`, required, default `CURRENT_TIMESTAMP`.
- **Constraints**:
  - `CHK_categories_display_order`: `display_order >= 0`
- **Indexes**:
  - `idx_categories_source_id` ON `menu_categories(source_category_id)` UNIQUE
  - `idx_categories_name` ON `menu_categories(category_name)`
- **Scale expectation**: 10 to 20 categories.

#### 4. `menu_items`
- **Purpose**: Catalog of all food and beverage offerings, current active standard prices and costs, recipe attributes, and operational tags.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY`)
- **Stable source key**: `source_menu_item_id` (`VARCHAR(64)`, unique, required, indexed; e.g. `'DISH-0142'`)
- **Foreign keys**:
  - `category_id` references `menu_categories(id)` on delete restrict.
- **Columns**:
  - `id`: Surrogate operational primary key, required.
  - `source_menu_item_id`: Stable source identifier, `VARCHAR(64)`, required, unique.
  - `category_id`: Foreign key referencing `menu_categories(id)`, required.
  - `item_name`: Commercial item name, `VARCHAR(120)`, required, unique within active catalog.
  - `description`: Dish culinary description and ingredients, `TEXT`, nullable.
  - `current_base_price`: Current benchmark retail price in USD, `DECIMAL(10,2)`, required.
  - `current_base_cost`: Current standard recipe ingredient and prep cost in USD, `DECIMAL(10,2)`, required.
  - `prep_time_minutes`: Average kitchen prep and cook time, `INT`, required, default `15`.
  - `is_seasonal`: Seasonal availability indicator, `BOOLEAN`, required, default `FALSE`.
  - `is_active`: Dish active status, `BOOLEAN`, required, default `TRUE`.
  - `spiciness_level`: Heat rating, `INT`, required, default `0`. Allowed range: `0` to `4`.
  - `allergens`: Comma separated allergen tags or JSON array, `VARCHAR(255)`, nullable.
  - `created_at`: Catalog creation timestamp, `TIMESTAMPTZ`, required, default `CURRENT_TIMESTAMP`.
  - `updated_at`: Last catalog change timestamp, `TIMESTAMPTZ`, required, default `CURRENT_TIMESTAMP`.
- **Constraints**:
  - `CHK_menu_items_price`: `current_base_price > 0.00`
  - `CHK_menu_items_cost`: `current_base_cost >= 0.00`
  - `CHK_menu_items_spiciness`: `spiciness_level BETWEEN 0 AND 4`
  - `CHK_menu_items_prep_time`: `prep_time_minutes >= 0`
- **Indexes**:
  - `idx_menu_items_source_id` ON `menu_items(source_menu_item_id)` UNIQUE
  - `idx_menu_items_category` ON `menu_items(category_id)`
  - `idx_menu_items_active` ON `menu_items(is_active)`
- **Scale expectation**: 150 to 300 unique items.

#### 5. `pricing_history`
- **Purpose**: Slowly Changing Dimension (SCD Type 2) tracking all historical price and cost modifications over time across items and locations.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY`)
- **Stable source key**: `source_pricing_history_id` (`VARCHAR(64)`, unique, required, indexed; e.g. `'PRC-000842'`)
- **Foreign keys**:
  - `menu_item_id` references `menu_items(id)` on delete cascade.
  - `restaurant_id` references `restaurants(id)` on delete set null, nullable (null indicates a company wide base price).
- **Columns**:
  - `id`: Surrogate operational primary key, required.
  - `source_pricing_history_id`: Stable source identifier, `VARCHAR(64)`, required, unique.
  - `menu_item_id`: Reference to `menu_items(id)`, required.
  - `restaurant_id`: Specific restaurant branch reference, nullable (null signifies chain wide standard price).
  - `base_price`: Unit retail price in effect during window, `DECIMAL(10,2)`, required.
  - `base_cost`: Unit standard preparation cost in effect during window, `DECIMAL(10,2)`, required.
  - `effective_from`: Start timestamp of the price window, `TIMESTAMPTZ`, required.
  - `effective_to`: End timestamp of the price window, `TIMESTAMPTZ`, nullable (null indicates currently active price).
  - `change_reason`: Business justification for adjustment, `VARCHAR(100)`, required. Allowed examples: `'Annual Review'`, `'Supplier Price Surge'`, `'Promotional Alignment'`, `'Inflation Adjustment'`, `'Competitive Match'`.
  - `created_at`: Record insertion timestamp, `TIMESTAMPTZ`, required, default `CURRENT_TIMESTAMP`.
- **Constraints**:
  - `CHK_pricing_price`: `base_price > 0.00`
  - `CHK_pricing_cost`: `base_cost >= 0.00`
  - `CHK_pricing_window`: `effective_to IS NULL OR effective_to > effective_from`
- **Indexes**:
  - `idx_pricing_source_id` ON `pricing_history(source_pricing_history_id)` UNIQUE
  - `idx_pricing_lookup` ON `pricing_history(menu_item_id, restaurant_id, effective_from, effective_to)`
  - `idx_pricing_active` ON `pricing_history(menu_item_id)` WHERE `effective_to IS NULL`
- **Scale expectation**: 1,500 to 5,000 price transition records.

#### 6. `promotions`
- **Purpose**: Defines marketing campaigns, coupon discounts, combo offers, and duration windows to assess promotional uplift and identify promotion traps.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY`)
- **Stable source key**: `source_promotion_id` (`VARCHAR(64)`, unique, required, indexed; e.g. `'PROMO-SUMMER-2025'`)
- **Foreign keys**:
  - `applicable_category_id` references `menu_categories(id)` on delete set null, nullable.
  - `applicable_menu_item_id` references `menu_items(id)` on delete set null, nullable.
- **Columns**:
  - `id`: Surrogate operational primary key, required.
  - `source_promotion_id`: Stable source identifier, `VARCHAR(64)`, required, unique.
  - `campaign_name`: Marketing campaign title, `VARCHAR(120)`, required.
  - `promo_code`: Alphanumeric coupon code entered by customer or cashier, `VARCHAR(30)`, nullable, unique when present.
  - `discount_type`: Type of discount calculation, `VARCHAR(30)`, required. Allowed values: `'Percentage'`, `'Fixed Amount'`, `'Buy One Get One'`, `'Combo Bundle'`.
  - `discount_value`: Magnitude of reduction, `DECIMAL(10,2)`, required. Percentage format: 15.00 for 15 percent; Fixed format: 5.00 for five dollars off.
  - `start_date`: Beginning timestamp of promotion eligibility, `TIMESTAMPTZ`, required.
  - `end_date`: Termination timestamp of promotion eligibility, `TIMESTAMPTZ`, required.
  - `applicable_category_id`: Targeted category restriction referencing `menu_categories(id)`, nullable.
  - `applicable_menu_item_id`: Targeted dish restriction referencing `menu_items(id)`, nullable.
  - `applicable_channel`: Channel restriction, `VARCHAR(30)`, nullable. Allowed values: `'Dine-in'`, `'Takeaway'`, `'Delivery Direct'`, `'Delivery Aggregator'`, `'All'`.
  - `minimum_order_amount`: Minimum order subtotal required to qualify, `DECIMAL(10,2)`, required, default `0.00`.
  - `is_active`: Operational switch, `BOOLEAN`, required, default `TRUE`.
  - `is_misleading`: Analytical evaluation flag indicating a promotion trap where deep discounts produce high volume with negative net contribution margin, `BOOLEAN`, required, default `FALSE`.
  - `created_at`: Record creation timestamp, `TIMESTAMPTZ`, required, default `CURRENT_TIMESTAMP`.
- **Constraints**:
  - `CHK_promotions_window`: `end_date >= start_date`
  - `CHK_promotions_discount`: `discount_value >= 0.00`
  - `CHK_promotions_discount_type`: `discount_type IN ('Percentage', 'Fixed Amount', 'Buy One Get One', 'Combo Bundle')`
- **Indexes**:
  - `idx_promotions_source_id` ON `promotions(source_promotion_id)` UNIQUE
  - `idx_promotions_dates` ON `promotions(start_date, end_date)`
  - `idx_promotions_code` ON `promotions(promo_code)` WHERE `promo_code IS NOT NULL`
- **Scale expectation**: 30 to 100 promotional campaigns.

#### 7. `orders` (Operational Demo Slice in PostgreSQL; Full Volume in Parquet)
- **Purpose**: Header record for customer transactions, capturing timestamps, branch location, ordering channel, customer reference, and financial totals.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY`)
- **Stable source key**: `source_order_id` (`VARCHAR(64)`, unique, required, indexed; e.g. `'ORD-00108942'`)
- **Foreign keys**:
  - `customer_id` references `customers(id)` on delete set null, nullable (null represents unregistered guest checkouts or cash walk in patrons).
  - `restaurant_id` references `restaurants(id)` on delete restrict, required.
- **Columns**:
  - `id`: Surrogate operational primary key, required.
  - `source_order_id`: Stable source identifier, `VARCHAR(64)`, required, unique.
  - `customer_id`: Registered patron reference (`customers.id`), nullable.
  - `restaurant_id`: Restaurant branch fulfilling the order (`restaurants.id`), required.
  - `order_timestamp`: Transaction occurrence timestamp in UTC, `TIMESTAMPTZ`, required.
  - `order_channel`: Fulfillment and ordering mechanism, `VARCHAR(30)`, required. Allowed values: `'Dine-in'`, `'Takeaway'`, `'Delivery Direct'`, `'Delivery Aggregator'`.
  - `order_status`: Transaction progression state, `VARCHAR(20)`, required. Allowed values: `'Completed'`, `'Cancelled'`, `'Refunded'`, `'Voided'`.
  - `subtotal_amount`: Undiscounted sum of item line prices, `DECIMAL(10,2)`, required.
  - `discount_amount`: Total discount deducted from subtotal, `DECIMAL(10,2)`, required, default `0.00`.
  - `tax_amount`: Calculated government sales tax, `DECIMAL(10,2)`, required, default `0.00`.
  - `tip_amount`: Discretionary gratuity, `DECIMAL(10,2)`, required, default `0.00`.
  - `total_amount`: Final payable settlement amount (`subtotal - discount + tax + tip`), `DECIMAL(10,2)`, required.
  - `payment_method`: Settlement instrument, `VARCHAR(30)`, required. Allowed values: `'Credit Card'`, `'Debit Card'`, `'Cash'`, `'Digital Wallet'`, `'Gift Card'`.
  - `created_at`: Database insertion timestamp, `TIMESTAMPTZ`, required, default `CURRENT_TIMESTAMP`.
- **Constraints**:
  - `CHK_orders_channel`: `order_channel IN ('Dine-in', 'Takeaway', 'Delivery Direct', 'Delivery Aggregator')`
  - `CHK_orders_status`: `order_status IN ('Completed', 'Cancelled', 'Refunded', 'Voided')`
  - `CHK_orders_totals`: `subtotal_amount >= 0.00 AND discount_amount >= 0.00 AND total_amount >= 0.00`
- **Indexes**:
  - `idx_orders_source_id` ON `orders(source_order_id)` UNIQUE
  - `idx_orders_timestamp` ON `orders(order_timestamp)`
  - `idx_orders_restaurant_time` ON `orders(restaurant_id, order_timestamp)`
  - `idx_orders_customer` ON `orders(customer_id)` WHERE `customer_id IS NOT NULL`
  - `idx_orders_channel` ON `orders(order_channel)`
  - `idx_orders_status` ON `orders(order_status)`
- **Scale expectation**: Full historical dataset has 100,000 to 250,000 orders in raw snapshots and Parquet marts. PostgreSQL retains an operational demonstration slice of 5,000 to 10,000 recent orders.

#### 8. `order_items` (Operational Demo Slice in PostgreSQL; Full Volume in Parquet)
- **Purpose**: Granular transaction line item storing item quantity, point in time sales price, ingredient and prep cost, applied line discount, and net contribution margin.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY`)
- **Stable source key**: `source_order_item_id` (`VARCHAR(64)`, unique, required, indexed; e.g. `'ITEM-01048251'`)
- **Foreign keys**:
  - `order_id` references `orders(id)` on delete cascade, required.
  - `menu_item_id` references `menu_items(id)` on delete restrict, required.
  - `promotion_id` references `promotions(id)` on delete set null, nullable.
- **Columns**:
  - `id`: Surrogate operational primary key, required.
  - `source_order_item_id`: Stable source identifier, `VARCHAR(64)`, required, unique.
  - `order_id`: Reference to parent order header (`orders.id`), required.
  - `menu_item_id`: Reference to ordered catalog dish (`menu_items.id`), required.
  - `quantity`: Number of portions ordered, `INT`, required.
  - `unit_price_at_sale`: Unit retail price applied at transaction instant, `DECIMAL(10,2)`, required.
  - `unit_cost_at_sale`: Unit preparation and ingredient cost at transaction instant, `DECIMAL(10,2)`, required.
  - `line_discount`: Monetary discount allocated to this item line, `DECIMAL(10,2)`, required, default `0.00`.
  - `promotion_id`: Applied marketing promotion campaign (`promotions.id`), nullable.
  - `line_net_revenue`: Derived net revenue for line (`quantity * unit_price_at_sale - line_discount`), `DECIMAL(10,2)`, required.
  - `line_contribution_margin`: Derived contribution margin (`line_net_revenue - (quantity * unit_cost_at_sale)`), `DECIMAL(10,2)`, required.
  - `special_instructions`: Preparation customization note, `VARCHAR(255)`, nullable.
  - `created_at`: Insertion timestamp, `TIMESTAMPTZ`, required, default `CURRENT_TIMESTAMP`.
- **Constraints**:
  - `CHK_order_items_qty`: `quantity > 0`
  - `CHK_order_items_price`: `unit_price_at_sale >= 0.00`
  - `CHK_order_items_cost`: `unit_cost_at_sale >= 0.00`
  - `CHK_order_items_discount`: `line_discount >= 0.00`
  - `CHK_order_items_revenue_math`: `line_net_revenue = (quantity * unit_price_at_sale) - line_discount`
  - `CHK_order_items_margin_math`: `line_contribution_margin = line_net_revenue - (quantity * unit_cost_at_sale)`
- **Indexes**:
  - `idx_order_items_source_id` ON `order_items(source_order_item_id)` UNIQUE
  - `idx_order_items_order` ON `order_items(order_id)`
  - `idx_order_items_menu_item` ON `order_items(menu_item_id)`
  - `idx_order_items_promotion` ON `order_items(promotion_id)` WHERE `promotion_id IS NOT NULL`
- **Scale expectation**: Full historical dataset has 1,000,000 to 2,500,000 order lines in raw snapshots and Parquet marts. PostgreSQL retains an operational slice corresponding to the demo orders.

#### 9. `ratings`
- **Purpose**: Captures customer feedback and sentiment scores for individual dishes, overall dining experience, and service delivery, supporting rating anomaly detection.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY`)
- **Stable source key**: `source_rating_id` (`VARCHAR(64)`, unique, required, indexed; e.g. `'RAT-00084729'`)
- **Foreign keys**:
  - `order_id` references `orders(id)` on delete set null, nullable.
  - `customer_id` references `customers(id)` on delete set null, nullable.
  - `restaurant_id` references `restaurants(id)` on delete cascade, required.
  - `menu_item_id` references `menu_items(id)` on delete set null, nullable (null indicates an overall restaurant service rating rather than a dish rating).
- **Columns**:
  - `id`: Surrogate operational primary key, required.
  - `source_rating_id`: Stable source identifier, `VARCHAR(64)`, required, unique.
  - `order_id`: Verified order reference (`orders.id`), nullable.
  - `customer_id`: Submitting customer reference (`customers.id`), nullable.
  - `restaurant_id`: Restaurant branch evaluated (`restaurants.id`), required.
  - `menu_item_id`: Specific dish evaluated (`menu_items.id`), nullable.
  - `rating_score`: Composite satisfaction rating from 1 to 5, `INT`, required.
  - `food_rating`: Specific food quality score from 1 to 5, `INT`, nullable.
  - `service_rating`: Specific hospitality score from 1 to 5, `INT`, nullable.
  - `ambiance_rating`: Specific atmosphere score from 1 to 5, `INT`, nullable.
  - `review_text`: Free text review commentary, `TEXT`, nullable.
  - `rating_timestamp`: Submission timestamp in UTC, `TIMESTAMPTZ`, required.
  - `is_verified_purchase`: Whether review was linked to a completed order, `BOOLEAN`, required, default `FALSE`.
  - `created_at`: Record creation timestamp, `TIMESTAMPTZ`, required, default `CURRENT_TIMESTAMP`.
- **Constraints**:
  - `CHK_ratings_score`: `rating_score BETWEEN 1 AND 5`
  - `CHK_ratings_food`: `food_rating IS NULL OR food_rating BETWEEN 1 AND 5`
  - `CHK_ratings_service`: `service_rating IS NULL OR service_rating BETWEEN 1 AND 5`
  - `CHK_ratings_ambiance`: `ambiance_rating IS NULL OR ambiance_rating BETWEEN 1 AND 5`
- **Indexes**:
  - `idx_ratings_source_id` ON `ratings(source_rating_id)` UNIQUE
  - `idx_ratings_dish_time` ON `ratings(menu_item_id, rating_timestamp)` WHERE `menu_item_id IS NOT NULL`
  - `idx_ratings_restaurant_time` ON `ratings(restaurant_id, rating_timestamp)`
  - `idx_ratings_order` ON `ratings(order_id)` WHERE `order_id IS NOT NULL`
- **Scale expectation**: Full historical dataset has 100,000 to 200,000 ratings in Parquet and raw snapshots. PostgreSQL stores a demo slice or active operational reviews.

#### 10. `inventory`
- **Purpose**: Tracks ingredient and raw material stock levels, reorder thresholds, and unit costs at each restaurant branch to monitor inventory turnover and stockout risk.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY`)
- **Stable source key**: `source_inventory_id` (`VARCHAR(64)`, unique, required, indexed; e.g. `'INV-REST01-0084'`)
- **Foreign keys**:
  - `restaurant_id` references `restaurants(id)` on delete cascade, required.
- **Columns**:
  - `id`: Surrogate operational primary key, required.
  - `source_inventory_id`: Stable source identifier, `VARCHAR(64)`, required, unique.
  - `restaurant_id`: Restaurant branch holding the stock (`restaurants.id`), required.
  - `ingredient_name`: Common culinary name of ingredient, `VARCHAR(100)`, required.
  - `ingredient_category`: Storage category, `VARCHAR(40)`, required. Allowed values: `'Produce'`, `'Meat & Poultry'`, `'Dairy'`, `'Dry Goods'`, `'Beverage Supplies'`, `'Packaging'`.
  - `current_stock_quantity`: Available stock on hand, `DECIMAL(10,2)`, required.
  - `unit_of_measure`: Physical measurement unit, `VARCHAR(20)`, required. Allowed values: `'kg'`, `'g'`, `'L'`, `'ml'`, `'units'`, `'boxes'`.
  - `reorder_threshold`: Minimum safe stock level triggering replenishment, `DECIMAL(10,2)`, required.
  - `reorder_quantity`: Standard replenishment order batch size, `DECIMAL(10,2)`, required.
  - `unit_purchase_cost`: Current procurement acquisition cost per unit in USD, `DECIMAL(10,2)`, required.
  - `last_restock_date`: Date of most recent delivery intake, `DATE`, nullable.
  - `created_at`: Record creation timestamp, `TIMESTAMPTZ`, required, default `CURRENT_TIMESTAMP`.
  - `updated_at`: Inventory balance modification timestamp, `TIMESTAMPTZ`, required, default `CURRENT_TIMESTAMP`.
- **Constraints**:
  - `CHK_inventory_stock`: `current_stock_quantity >= 0.00`
  - `CHK_inventory_threshold`: `reorder_threshold >= 0.00`
  - `CHK_inventory_cost`: `unit_purchase_cost >= 0.00`
  - `UQ_inventory_rest_item`: `UNIQUE(restaurant_id, ingredient_name)`
- **Indexes**:
  - `idx_inventory_source_id` ON `inventory(source_inventory_id)` UNIQUE
  - `idx_inventory_reorder` ON `inventory(restaurant_id, current_stock_quantity, reorder_threshold)`
  - `idx_inventory_category` ON `inventory(ingredient_category)`
- **Scale expectation**: 2,000 to 5,000 records across active branches.

#### 11. `wastage`
- **Purpose**: Records food spoilage, preparation trim loss, customer returns, and expired goods per dish or ingredient, supporting wastage prediction and cost recovery models.
- **Primary key**: `id` (`BIGINT GENERATED ALWAYS AS IDENTITY`)
- **Stable source key**: `source_wastage_id` (`VARCHAR(64)`, unique, required, indexed; e.g. `'WASTE-00049281'`)
- **Foreign keys**:
  - `restaurant_id` references `restaurants(id)` on delete cascade, required.
  - `menu_item_id` references `menu_items(id)` on delete set null, nullable (set when finished dish was wasted).
- **Columns**:
  - `id`: Surrogate operational primary key, required.
  - `source_wastage_id`: Stable source identifier, `VARCHAR(64)`, required, unique.
  - `restaurant_id`: Restaurant branch reporting loss (`restaurants.id`), required.
  - `menu_item_id`: Finished dish wasted (`menu_items.id`), nullable.
  - `ingredient_name`: Raw ingredient wasted if not a finished dish, `VARCHAR(100)`, nullable.
  - `wastage_timestamp`: Date and time loss occurred or was logged, `TIMESTAMPTZ`, required.
  - `quantity_lost`: Number of units or portions discarded, `DECIMAL(10,2)`, required.
  - `unit_of_measure`: Discard measurement unit, `VARCHAR(20)`, required. Allowed values: `'portions'`, `'kg'`, `'g'`, `'L'`, `'units'`.
  - `cost_loss_amount`: Financial impact calculated from item or ingredient standard cost (`quantity_lost * unit_cost`), `DECIMAL(10,2)`, required.
  - `wastage_reason`: Standard classification of loss event, `VARCHAR(40)`, required. Allowed values: `'Expired'`, `'Over-preparation'`, `'Cooking Error'`, `'Equipment Failure'`, `'Customer Returned'`, `'Spillage'`.
  - `reported_by`: Staff member or station reporting the discard, `VARCHAR(80)`, nullable.
  - `created_at`: Record creation timestamp, `TIMESTAMPTZ`, required, default `CURRENT_TIMESTAMP`.
- **Constraints**:
  - `CHK_wastage_quantity`: `quantity_lost > 0.00`
  - `CHK_wastage_cost`: `cost_loss_amount >= 0.00`
  - `CHK_wastage_reason`: `wastage_reason IN ('Expired', 'Over-preparation', 'Cooking Error', 'Equipment Failure', 'Customer Returned', 'Spillage')`
  - `CHK_wastage_target`: `menu_item_id IS NOT NULL OR ingredient_name IS NOT NULL`
- **Indexes**:
  - `idx_wastage_source_id` ON `wastage(source_wastage_id)` UNIQUE
  - `idx_wastage_dish_time` ON `wastage(menu_item_id, wastage_timestamp)` WHERE `menu_item_id IS NOT NULL`
  - `idx_wastage_restaurant_time` ON `wastage(restaurant_id, wastage_timestamp)`
  - `idx_wastage_reason` ON `wastage(wastage_reason)`
- **Scale expectation**: Full historical dataset has 50,000 to 100,000 wastage events.

---

### Dual Key Architecture and Cross Layer Traceability

To bridge the operational transactional database with the big data and data science pipelines, the architecture establishes a clean separation between surrogate identity keys and stable business source keys:

```
+--------------------------------------------------------------------------------------------------+
| 1. Generator / Raw Snapshot Layer (`data/snapshots/v<TIMESTAMP>/`)                               |
| - Originates stable business identifiers (`source_*_id`) e.g. `'ORD-00042851'`, `'DISH-0142'`   |
| - Foreign key links between raw CSV / Parquet files use stable source identifiers                |
| - Immutable file checksums recorded in `snapshot_manifest.json`                                   |
+--------------------------------------------------------------------------------------------------+
                                                 |
               +---------------------------------+---------------------------------+
               | (Batch Ingestion)                                                 | (Operational Sync)
               v                                                                   v
+----------------------------------------------+  +------------------------------------------------+
| 2. Analytical Feature Marts (Parquet)        |  | 3. Operational Relational Store (PostgreSQL)  |
| - `data/marts/spark/` and `data/marts/python/`|  | - Table primary keys: `id BIGINT IDENTITY`     |
| - Retains `source_*_id` for join auditability|  | - Stores `source_*_id` with UNIQUE constraints |
| - Aggregates indexed by business identifiers |  | - Foreign keys in PostgreSQL reference `id`    |
| - Direct columnar scans via PyArrow          |  | - References raw snapshot ID in `job_runs`     |
+----------------------------------------------+  +------------------------------------------------+
                                                 \                                 /
                                                  \                               /
                                                   v                             v
+--------------------------------------------------------------------------------------------------+
| 4. End to End Traceability and Lineage                                                           |
| - A prediction or mart record carrying `source_menu_item_id = 'DISH-0142'` can be traced:        |
|   1. Directly to the raw snapshot row in `data/snapshots/` by matching `source_menu_item_id`    |
|   2. Directly to the active operational record in PostgreSQL via `menu_items.source_menu_item_id`|
|   3. Directly to the training job run in PostgreSQL `job_runs` via `source_snapshot_id`          |
+--------------------------------------------------------------------------------------------------+
```

---

### PostgreSQL versus Analytical Storage Responsibilities

The system clearly demarcates what belongs inside PostgreSQL versus what remains in Parquet files:

1. **PostgreSQL Responsibilities**:
   - Master Catalog Data: Menu categories, menu items, restaurant locations, active promotion parameters.
   - Security and Access: User accounts, hashed credentials, role definitions, permission mappings.
   - Operational Metadata: Background job execution records (`job_runs`), trained model registry (`model_registry`), data quality run summaries.
   - Decision Records: System generated actionable recommendations, what if simulation templates, and audit logs.
   - Demonstration Slice: A limited operational transaction subset (e.g. 5,000 to 10,000 recent orders) for point of sale entry and user interface testing.

2. **Why Full One Million Row Transactions Are Not Mirrored in PostgreSQL**:
   - **Connection and Memory Saturation**: Running multi table analytical joins and grouping aggregations across 1,000,000+ transaction lines inside PostgreSQL would consume large buffer pool memory, causing query contention and increasing latency for concurrent web users.
   - **Storage Bloat**: Storing 1,000,000+ rows with comprehensive secondary indexes in a row oriented relational engine requires 400MB to 600MB of storage, compared to only 40MB to 80MB in columnar compressed Parquet format.
   - **Dual Pipeline Independence**: Ingesting from PostgreSQL tables introduces network and driver coupling (such as JDBC dependencies and database locks), whereas ingesting from immutable file snapshots in `data/snapshots/` allows Spark and Python to run fully decoupled.
   - **Architectural Boundary Rule**: The approved project architecture strictly prohibits heavy table scans in HTTP request handlers. Direct columnar scanning of precomputed Parquet marts via PyArrow ensures sub 50 millisecond dashboard queries.

---

### Transaction Line Metric Semantics

The model establishes explicit mathematical definitions for revenue and profitability at the line item level:

1. **Gross Revenue**:
   $$\text{gross\_revenue} = \text{quantity} \times \text{unit\_price\_at\_sale}$$
   Where `unit_price_at_sale` is the historical retail price stored on `order_items` at the moment of order placement.

2. **Net Revenue**:
   $$\text{net\_revenue} = (\text{quantity} \times \text{unit\_price\_at\_sale}) - \text{line\_discount}$$
   Where `line_discount` represents the monetary reduction attributed to promotion codes or manager discounts.

3. **Cost of Goods Sold (Ingredient and Preparation Cost)**:
   $$\text{cogs} = \text{quantity} \times \text{unit\_cost\_at\_sale}$$
   Where `unit_cost_at_sale` is the historical recipe standard cost captured at the moment of order placement.

4. **Contribution Margin**:
   $$\text{contribution\_margin} = \text{net\_revenue} - \text{cogs}$$
   This metric captures the direct financial contribution of each sold dish toward covering fixed operating expenses.

5. **Distinction from Net Profit**:
   Contribution margin must never be labeled or treated as net profit. Net profit requires subtracting operating overheads (property leases, electricity, general corporate salaries, and depreciation) which are not part of the POS transaction line grain.

---

### Analytical Value Sourcing Table

The following table traces every required analytical value and metric to its authoritative data source:

| Metric / Action | Value Produced or Displayed | Data Source | Calculation / Derivation |
|---|---|---|---|
| Menu Profitability | Item Net Revenue | `order_items.line_net_revenue` | Sum over specified time window |
| Menu Profitability | Item Contribution Margin | `order_items.line_contribution_margin` | Sum of line margins over time window |
| Menu Classification | Profit Driver / Volume Driver / Hidden Opportunity / Low Performer | `order_items`, `menu_items` | Boston Consulting Group matrix quadrant: split on median order volume and median contribution margin |
| Customer Segmentation | Recency, Frequency, Monetary (RFM) Scores | `orders.order_timestamp`, `orders.source_customer_id`, `orders.total_amount` | Days since last order, distinct count of orders, sum of completed total amount |
| Market Basket Analysis | Item Support, Confidence, Lift | `order_items.source_menu_item_id`, `order_items.source_order_id` | Co occurrence frequency of item pairs within distinct completed `source_order_id`s |
| Hourly Demand Forecast | Units Sold per Hour by Category | `order_items.quantity`, `orders.order_timestamp`, `menu_items.category_id` | Aggregate sum of quantity grouped by date, hour, category, filtered to completed orders |
| Wastage Prediction | Wastage Cost Ratio | `wastage.cost_loss_amount`, `order_items.line_net_revenue` | Sum of wastage cost divided by sum of net revenue per dish/location |
| Price Elasticity | Price Sensitivity Coefficient ($\epsilon$) | `order_items.unit_price_at_sale`, `order_items.quantity`, `pricing_history` | Percentage change in quantity sold divided by percentage change in unit price across price transitions |
| Promotion Trap | Trap Flagged Campaign | `order_items.promotion_id`, `order_items.line_net_revenue`, `order_items.line_contribution_margin` | High sales volume uplift combined with negative aggregate contribution margin |
| Rating Anomaly | Anomaly Outlier Flag | `ratings.rating_score`, `ratings.rating_timestamp`, `ratings.source_menu_item_id` | Moving average 30 day z score deviation exceeding two standard deviations |
| Slow Moving Dish | Churn / Stagnation Indicator | `order_items.created_at`, `menu_items.source_menu_item_id` | Items with zero or sub threshold sales in the rolling 30 day period |
| Location Comparison | Branch Profit Margin % | `orders.source_restaurant_id`, `order_items.line_contribution_margin`, `order_items.line_net_revenue` | Sum of contribution margin divided by sum of net revenue grouped by `source_restaurant_id` |

---

### Temporal and Chronological Rules (Preventing Future Data Leakage)

1. **UTC Standard**: All timestamps across the database and snapshot files must be recorded in UTC using ISO 8601 representation with timezone offset (`TIMESTAMPTZ` in PostgreSQL, timestamp[us, tz=UTC] in Parquet).
2. **Point in Time Lookup**: When analyzing transactions, dish prices and recipe costs must be read directly from the transaction line (`unit_price_at_sale`, `unit_cost_at_sale`) rather than retroactively querying `menu_items.current_base_price`.
3. **SCD Type 2 Boundaries**: For historical simulation where line items lack cost tags, `pricing_history` is queried using `order_timestamp >= effective_from AND (effective_to IS NULL OR order_timestamp < effective_to)`.
4. **Chronological Splitting**: Machine learning train, validation, and test sets must be split chronologically by `order_timestamp` or `wastage_timestamp` (for example, months 1 through 9 for training, months 10 and 11 for validation, month 12 for test). Random k fold splits on time series transaction data are prohibited to prevent future leakage.
5. **Feature Window Lag**: Feature engineering for week $t$ may only incorporate order, rating, and wastage records timestamped on or before the end of week $t - 1$.

---

### Dataset Versioning and Audit Traceability

1. **Snapshot Manifest**: Every generated dataset export creates a directory `data/snapshots/v<YYYYMMDD_HHMMSS>/` accompanied by a `manifest.json` holding:
   - `snapshot_id`: Unique snapshot string identifier
   - `generator_seed`: Random generator seed for exact reproducibility
   - `created_at`: Generation UTC timestamp
   - `tables`: Array of table descriptors with file path, format, record count, and SHA256 checksum
2. **Pipeline Job Runs**: Background Spark and Python jobs record execution metadata in the PostgreSQL `job_runs` table:
   - `job_id`: Unique run identifier
   - `pipeline_type`: `'SPARK'` or `'PYTHON'`
   - `source_snapshot_id`: Reference to snapshot processed
   - `start_time` and `end_time`: Execution duration
   - `records_processed` and `records_cleaned`: Cleaning throughput
   - `status`: `'SUCCESS'`, `'FAILED'`, or `'RUNNING'`
3. **Model Registry**: Models trained by either pipeline record metadata in the PostgreSQL `model_registry` table:
   - `model_id`: Unique model version identifier
   - `pipeline_type`: `'SPARK_MLLIB'` or `'PYTHON_SKLEARN'`
   - `algorithm_name`: E.g. `'RandomForestClassifier'`, `'GradientBoostingRegressor'`
   - `training_snapshot_id`: Reference to source snapshot
   - `hyperparameters`: JSON map of parameters
   - `metrics`: JSON map of evaluation scores (RMSE, R2, F1, Accuracy)
   - `artifact_path`: Relative filesystem path to serialized model artifact

---

### Key Invariants

1. Every order line item must reference a valid parent order and catalog dish.
2. In the transactional ledger, `line_net_revenue` must equal `(quantity * unit_price_at_sale) - line_discount`.
3. In the transactional ledger, `line_contribution_margin` must equal `line_net_revenue - (quantity * unit_cost_at_sale)`.
4. A rating record must contain a rating score between 1 and 5.
5. A restaurant location can only have one active inventory record per unique ingredient name.
6. Pricing history records for a single item and location must not have overlapping `[effective_from, effective_to)` intervals.
7. Orders with status `'Cancelled'` or `'Voided'` must not be included in net revenue calculations, but must be retained for cancellation rate analysis.
8. Unregistered guest checkouts must be supported with null `customer_id` without failing foreign key constraints.
9. Every record originating in raw snapshots must possess a non null `source_*_id` that is unique within its entity scope.

---

### Security and Authorization Model

- **Public and Unauthenticated**: Health check endpoints and API documentation.
- **Cashier / Floor Staff Role**: Can submit orders and register items; no access to recipe cost or margin data.
- **Store Manager Role**: Can view restaurant specific operational analytics, wastage logs, and local inventory; read only access to menu catalog.
- **Data Scientist Role**: Can trigger pipeline runs, view raw snapshot manifests, run model evaluation, and query Parquet analytical marts.
- **Executive / Admin Role**: Unrestricted access to chain wide financial margins, what if simulators, user administration, and system audit logs.

---

### Configuration Required

- `DATABASE_URL`: Connection string for PostgreSQL database.
- `DEFAULT_CURRENCY`: Default three letter ISO currency code (default `'USD'`).
- `DATA_SNAPSHOT_DIR`: Relative path to raw snapshot storage (default `'data/snapshots'`).
- `ANALYTICAL_MART_DIR`: Relative path to Parquet analytical marts (default `'data/marts'`).
- `MODEL_ARTIFACT_DIR`: Relative path to serialized model artifacts (default `'data/artifacts'`).

---

### Critical Test Scenarios

- **Scenario 1 (Financial Metric Math Integrity)**: Insert order item with quantity 3, unit price 12.00, discount 4.00, and unit cost 5.00. Verify net revenue equals 32.00 and contribution margin equals 17.00. Verifies **AC-2**.
- **Scenario 2 (Historical Price Immutability)**: Change `current_base_price` on a menu item in catalog. Query past order items for that menu item and confirm `unit_price_at_sale` and `line_net_revenue` remain identical to historical transaction values. Verifies **AC-2**, **AC-3**.
- **Scenario 3 (Guest Checkout Handling)**: Insert an order record with `customer_id = NULL`. Verify insertion succeeds cleanly and order contributes to daily store revenue without foreign key rejection. Verifies **AC-1**, **AC-5**.
- **Scenario 4 (Pricing History Chronological Lookup)**: Query the effective price for item 10 at timestamp $T$. Verify the query returns the single record where $T \ge \text{effective\_from}$ and $(T < \text{effective\_to} \text{ OR effective\_to IS NULL})$. Verifies **AC-3**, **AC-6**.
- **Scenario 5 (Rating Score Boundary Check)**: Attempt to insert rating with score 0 or 6. Verify check constraint rejects record with database constraint violation. Verifies **AC-8**.
- **Scenario 6 (Promotion Trap Identification)**: Aggregate order items tied to a promotional campaign with 50 percent discount. Confirm that when unit cost exceeds discounted unit price, contribution margin aggregates to a negative value. Verifies **AC-2**, **AC-10**.
- **Scenario 7 (Cross Layer Source Key Linkage)**: Ingest a raw order line with `source_order_id = 'ORD-000100'`. Verify that the cleaned Parquet record and operational order retain identical source identifiers and resolve to the same branch. Verifies **AC-1**, **AC-10**.

## Build plan

The build plan follows the project Tracer Bullet approach, establishing the core schema migrations first, then wiring synthetic seed verification:

1. Create initial Alembic database migration defining the eleven operational tables with `BIGINT GENERATED ALWAYS AS IDENTITY` primary keys and `source_*_id` business keys in `packages/db/migrations/`, satisfies **AC-1**, **AC-7**, **AC-8**, **AC-9**
2. Implement declarative SQLAlchemy 2.0 ORM models in `packages/db/models/` for all eleven tables with relations and constraints, satisfies **AC-1**, **AC-4**, **AC-7**
3. Create domain contract schemas and metric computation validators in `packages/core/schemas/` enforcing transaction line formulas, satisfies **AC-2**, **AC-4**
4. Create snapshot manifest validator and Parquet schema definitions in `packages/common/` for raw data file contracts with stable source identifiers, satisfies **AC-5**, **AC-6**, **AC-10**
5. Implement unit and integration tests in `tests/unit/test_schema.py` and `tests/integration/test_db_models.py` verifying constraints, guest orders, metric math, and source key integrity, satisfies **AC-1**, **AC-2**, **AC-3**, **AC-8**

## Consequences

**Positive**:
- Direct point in time price and cost capture on transaction lines eliminates complex, slow point in time joins during analytical queries and guarantees immutable accounting history.
- Relational integrity in PostgreSQL protects administrative master data, while columnar Parquet marts keep high volume analytical queries sub second without overloading the database engine.
- Dual key strategy (surrogate `id` in PostgreSQL and stable `source_*_id` across all layers) ensures seamless cross pipeline joins and complete audit traceability.
- Keeping 1,000,000+ transaction lines out of PostgreSQL prevents connection pool exhaustion, memory bloat, and table locks during heavy analytical processing.
- Explicit metric definitions prevent conflating contribution margin with net profit, satisfying competition evaluation rubrics.

**Negative and Tradeoffs**:
- Denormalizing price, cost, and stable source keys onto order items increases row width on the one million line table by approximately 24 bytes per row (around 24 megabytes total uncompressed), which is a negligible storage tradeoff for query speed and immutability.
- Maintaining both PostgreSQL models and Parquet schemas requires contract synchronization in `packages/core/` to ensure schema definitions do not drift.

**Neutral**:
- Requires the dataset generator (Feature 5) to generate both the relational seed data and the bulk transaction snapshot files with matching stable source identifiers.

## Follow-up

- [ ] Implement the database migration and SQLAlchemy models during Feature 3 build execution (`/develop data model and schema`).

## Rationale

Reasoning, alternatives considered, and architectural tradeoffs: see [rationale.md](rationale.md).
