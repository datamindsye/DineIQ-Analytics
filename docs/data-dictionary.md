# DineIQ Analytics Data Dictionary

This document serves as the authoritative data dictionary for the eleven business domain tables comprising the analytical foundation of DineIQ Analytics.

---

## 1. Architectural Principles

1. **Dual Identifiers**: Every domain entity provides a sixty four bit identity surrogate key (`id BIGINT`) in PostgreSQL for relational joins, and an immutable business source identifier (`source_*_id VARCHAR(64)`) preserved across all raw snapshots, Apache Spark DataFrames, Pandas DataFrames, and Parquet analytical marts.
2. **Point in Time Financial Integrity**: Transaction sales prices and recipe costs are captured directly on each order item line at the instant of checkout.
3. **Slowly Changing Dimensions**: Price modifications and ingredient cost fluctuations are tracked via Slowly Changing Dimension Type 2 in `pricing_history`.
4. **Timezone Representation**: All timestamps are stored and evaluated in UTC with timezone offset (`TIMESTAMPTZ` in PostgreSQL, `timestamp[us, tz=UTC]` in PyArrow).

---

## 2. Authoritative Financial Definitions

The platform enforces the following exact mathematical definitions:

$$\text{Line Net Revenue} = (\text{quantity} \times \text{unit\_price\_at\_sale}) - \text{line\_discount}$$

$$\text{Line Contribution Margin} = \text{Line Net Revenue} - (\text{quantity} \times \text{unit\_cost\_at\_sale})$$

$$\text{Order Total Amount} = \text{subtotal\_amount} - \text{discount\_amount} + \text{tax\_amount} + \text{tip\_amount}$$

---

## 3. Domain Entity Specifications

### Table 1: `menu_categories`
Culinary classification groupings for dishes and beverage offerings.

| Column Name | PostgreSQL Type | PyArrow Type | Nullable | Description |
|---|---|---|---|---|
| `id` | `BIGINT IDENTITY` | N/A | No | Surrogate relational primary key |
| `source_category_id` | `VARCHAR(64)` | `string` | No | Stable business key matching pattern `CAT-\d{3}` |
| `category_name` | `VARCHAR(60)` | `string` | No | Canonical category name (10 canonical values) |
| `description` | `TEXT` | `string` | Yes | Descriptive explanation of category items |
| `display_order` | `INTEGER` | `int32` | No | Sort order position for menu display |
| `is_active` | `BOOLEAN` | `bool` | No | Active catalog status flag |
| `created_at` | `TIMESTAMPTZ` | `timestamp[us, tz=UTC]` | No | Record creation timestamp |

---

### Table 2: `restaurants`
Physical branch units, seating capacities, and regional operating attributes.

| Column Name | PostgreSQL Type | PyArrow Type | Nullable | Description |
|---|---|---|---|---|
| `id` | `BIGINT IDENTITY` | N/A | No | Surrogate relational primary key |
| `source_restaurant_id` | `VARCHAR(64)` | `string` | No | Stable business key matching pattern `REST-\d{4}` |
| `location_name` | `VARCHAR(100)` | `string` | No | Branch location designation |
| `city` | `VARCHAR(100)` | `string` | No | City where branch operates |
| `state_region` | `VARCHAR(100)` | `string` | No | State or administrative territory |
| `postal_code` | `VARCHAR(20)` | `string` | No | Postal code |
| `seating_capacity` | `INTEGER` | `int32` | No | Number of guest dining seats |
| `dining_type` | `VARCHAR(40)` | `string` | No | Service style: Fast Casual, Casual Dining, Fine Dining, Express Kiosk |
| `manager_name` | `VARCHAR(100)` | `string` | Yes | Branch manager in charge |
| `opening_date` | `DATE` | `date32` | No | Official location inauguration date |
| `latitude` | `NUMERIC(9,6)` | `float64` | Yes | Geographic latitude |
| `longitude` | `NUMERIC(9,6)` | `float64` | Yes | Geographic longitude |
| `is_active` | `BOOLEAN` | `bool` | No | Operational branch activity status |
| `created_at` | `TIMESTAMPTZ` | `timestamp[us, tz=UTC]` | No | Record creation timestamp |

---

### Table 3: `menu_items`
Catalog dish offering, benchmark retail price, and standard recipe cost.

| Column Name | PostgreSQL Type | PyArrow Type | Nullable | Description |
|---|---|---|---|---|
| `id` | `BIGINT IDENTITY` | N/A | No | Surrogate relational primary key |
| `source_menu_item_id` | `VARCHAR(64)` | `string` | No | Stable business key matching pattern `DISH-\d{4}` |
| `source_category_id` | `VARCHAR(64)` | `string` | No | Category business reference matching `CAT-\d{3}` |
| `category_id` | `BIGINT` | N/A | No | Relational foreign key referencing `menu_categories(id)` |
| `item_name` | `VARCHAR(120)` | `string` | No | Dish title |
| `description` | `TEXT` | `string` | Yes | Recipe culinary description |
| `current_base_price` | `NUMERIC(10,2)` | `float64` | No | Active benchmark retail price in USD |
| `current_base_cost` | `NUMERIC(10,2)` | `float64` | No | Standard ingredient preparation cost in USD |
| `prep_time_minutes` | `INTEGER` | `int32` | No | Kitchen ticket preparation duration |
| `is_seasonal` | `BOOLEAN` | `bool` | No | Seasonal menu rotation flag |
| `is_active` | `BOOLEAN` | `bool` | No | Item ordering availability flag |
| `spiciness_level` | `INTEGER` | `int32` | No | Heat index from zero (mild) to four (extra hot) |
| `allergens` | `VARCHAR(255)` | `string` | Yes | Common food allergens present |
| `created_at` | `TIMESTAMPTZ` | `timestamp[us, tz=UTC]` | No | Record creation timestamp |

---

### Table 4: `pricing_history`
Slowly Changing Dimension Type 2 tracking price and recipe cost adjustments over time.

| Column Name | PostgreSQL Type | PyArrow Type | Nullable | Description |
|---|---|---|---|---|
| `id` | `BIGINT IDENTITY` | N/A | No | Surrogate relational primary key |
| `source_pricing_history_id` | `VARCHAR(64)` | `string` | No | Stable business key matching pattern `PRC-\d{6}` |
| `source_menu_item_id` | `VARCHAR(64)` | `string` | No | Target dish identifier matching `DISH-\d{4}` |
| `source_restaurant_id` | `VARCHAR(64)` | `string` | Yes | Optional location identifier matching `REST-\d{4}` |
| `menu_item_id` | `BIGINT` | N/A | No | Relational foreign key referencing `menu_items(id)` |
| `restaurant_id` | `BIGINT` | N/A | Yes | Relational foreign key referencing `restaurants(id)` |
| `base_price` | `NUMERIC(10,2)` | `float64` | No | Historical retail price during window |
| `base_cost` | `NUMERIC(10,2)` | `float64` | No | Historical preparation cost during window |
| `effective_from` | `TIMESTAMPTZ` | `timestamp[us, tz=UTC]` | No | Date and time when price adjustment started |
| `effective_to` | `TIMESTAMPTZ` | `timestamp[us, tz=UTC]` | Yes | Date and time when price expired (null indicates active) |
| `change_reason` | `VARCHAR(120)` | `string` | No | Operational rationale for price change |
| `created_at` | `TIMESTAMPTZ` | `timestamp[us, tz=UTC]` | No | Record creation timestamp |

---

### Table 5: `promotions`
Marketing discount programs, promotional codes, and campaign durations.

| Column Name | PostgreSQL Type | PyArrow Type | Nullable | Description |
|---|---|---|---|---|
| `id` | `BIGINT IDENTITY` | N/A | No | Surrogate relational primary key |
| `source_promotion_id` | `VARCHAR(64)` | `string` | No | Stable business key matching pattern `PROMO-\d{4}` |
| `campaign_name` | `VARCHAR(120)` | `string` | No | Marketing campaign title |
| `promo_code` | `VARCHAR(40)` | `string` | Yes | Redeemable coupon voucher code |
| `discount_type` | `VARCHAR(30)` | `string` | No | Type: Percentage, Fixed Amount, Buy One Get One, Combo Bundle |
| `discount_value` | `NUMERIC(10,2)` | `float64` | No | Numerical percentage or currency discount |
| `start_date` | `DATE` | `date32` | No | Promotional eligibility start date |
| `end_date` | `DATE` | `date32` | No | Promotional conclusion date |
| `minimum_order_amount` | `NUMERIC(10,2)` | `float64` | No | Minimum spend qualification in USD |
| `source_category_id` | `VARCHAR(64)` | `string` | Yes | Target category limitation |
| `source_menu_item_id` | `VARCHAR(64)` | `string` | Yes | Target dish limitation |
| `applicable_channel` | `VARCHAR(30)` | `string` | Yes | Channel restriction |
| `is_active` | `BOOLEAN` | `bool` | No | Marketing campaign status |
| `is_misleading` | `BOOLEAN` | `bool` | No | Designates promotion trap campaigns yielding negative contribution margin |
| `created_at` | `TIMESTAMPTZ` | `timestamp[us, tz=UTC]` | No | Record creation timestamp |

---

### Table 6: `customers`
Master diner registry for loyalty tracking and RFM segmentation.

| Column Name | PostgreSQL Type | PyArrow Type | Nullable | Description |
|---|---|---|---|---|
| `id` | `BIGINT IDENTITY` | N/A | No | Surrogate relational primary key |
| `source_customer_id` | `VARCHAR(64)` | `string` | No | Stable business key matching pattern `CUST-\d{8}` |
| `first_name` | `VARCHAR(60)` | `string` | Yes | Diner given name |
| `last_name` | `VARCHAR(60)` | `string` | Yes | Diner family name |
| `email` | `VARCHAR(255)` | `string` | Yes | Electronic mail contact |
| `phone` | `VARCHAR(30)` | `string` | Yes | Telephone contact |
| `registration_date` | `DATE` | `date32` | No | Loyalty enrollment date |
| `loyalty_tier` | `VARCHAR(20)` | `string` | No | Loyalty level: Bronze, Silver, Gold, Platinum, None |
| `preferred_channel` | `VARCHAR(30)` | `string` | Yes | Favorite dining channel |
| `home_city` | `VARCHAR(100)` | `string` | Yes | Primary residential metropolitan area |
| `is_active` | `BOOLEAN` | `bool` | No | Customer active account status |
| `created_at` | `TIMESTAMPTZ` | `timestamp[us, tz=UTC]` | No | Record creation timestamp |

---

### Table 7: `orders`
Point of sale transaction header capturing fulfillment branch, channel, and settlement amounts.

| Column Name | PostgreSQL Type | PyArrow Type | Nullable | Description |
|---|---|---|---|---|
| `id` | `BIGINT IDENTITY` | N/A | No | Surrogate relational primary key |
| `source_order_id` | `VARCHAR(64)` | `string` | No | Stable business key matching pattern `ORD-\d{8}` |
| `source_restaurant_id` | `VARCHAR(64)` | `string` | No | Fulfilling branch key matching `REST-\d{4}` |
| `source_customer_id` | `VARCHAR(64)` | `string` | Yes | Diner key matching `CUST-\d{8}` (null indicates guest checkout) |
| `restaurant_id` | `BIGINT` | N/A | No | Relational foreign key referencing `restaurants(id)` |
| `customer_id` | `BIGINT` | N/A | Yes | Relational foreign key referencing `customers(id)` |
| `order_timestamp` | `TIMESTAMPTZ` | `timestamp[us, tz=UTC]` | No | Exact point of sale timestamp in UTC |
| `order_channel` | `VARCHAR(30)` | `string` | No | Channel: Dine-in, Takeaway, Delivery Direct, Delivery Aggregator |
| `order_status` | `VARCHAR(20)` | `string` | No | Status: Completed, Cancelled, Refunded, Voided |
| `subtotal_amount` | `NUMERIC(10,2)` | `float64` | No | Gross transaction line sum before discounts in USD |
| `discount_amount` | `NUMERIC(10,2)` | `float64` | No | Total promotional concession deducted in USD |
| `tax_amount` | `NUMERIC(10,2)` | `float64` | No | Local sales tax assessed in USD |
| `tip_amount` | `NUMERIC(10,2)` | `float64` | No | Discretionary gratuity provided in USD |
| `total_amount` | `NUMERIC(10,2)` | `float64` | No | Final settlement amount in USD |
| `payment_method` | `VARCHAR(30)` | `string` | No | Method: Credit Card, Debit Card, Cash, Digital Wallet, Gift Card |
| `created_at` | `TIMESTAMPTZ` | `timestamp[us, tz=UTC]` | No | Record creation timestamp |

---

### Table 8: `order_items`
Granular line item capturing unit sales price, recipe cost, discount, and contribution margin.

| Column Name | PostgreSQL Type | PyArrow Type | Nullable | Description |
|---|---|---|---|---|
| `id` | `BIGINT IDENTITY` | N/A | No | Surrogate relational primary key |
| `source_order_item_id` | `VARCHAR(64)` | `string` | No | Stable business key matching pattern `ITEM-\d{8}` |
| `source_order_id` | `VARCHAR(64)` | `string` | No | Parent transaction key matching `ORD-\d{8}` |
| `source_menu_item_id` | `VARCHAR(64)` | `string` | No | Ordered dish key matching `DISH-\d{4}` |
| `source_promotion_id` | `VARCHAR(64)` | `string` | Yes | Applied campaign key matching `PROMO-\d{4}` |
| `order_id` | `BIGINT` | N/A | No | Relational foreign key referencing `orders(id)` |
| `menu_item_id` | `BIGINT` | N/A | No | Relational foreign key referencing `menu_items(id)` |
| `promotion_id` | `BIGINT` | N/A | Yes | Relational foreign key referencing `promotions(id)` |
| `quantity` | `INTEGER` | `int32` | No | Number of portions ordered |
| `unit_price_at_sale` | `NUMERIC(10,2)` | `float64` | No | Retail price charged per unit at transaction time |
| `unit_cost_at_sale` | `NUMERIC(10,2)` | `float64` | No | Standard recipe ingredient cost per unit at transaction time |
| `line_discount` | `NUMERIC(10,2)` | `float64` | No | Promotional discount deducted on this line |
| `line_net_revenue` | `NUMERIC(10,2)` | `float64` | No | Authoritative net revenue for the line |
| `line_contribution_margin` | `NUMERIC(10,2)` | `float64` | No | Authoritative contribution margin for the line |
| `special_instructions` | `VARCHAR(255)` | `string` | Yes | Custom preparation notes |
| `created_at` | `TIMESTAMPTZ` | `timestamp[us, tz=UTC]` | No | Record creation timestamp |

---

### Table 9: `ratings`
Customer satisfaction feedback, component ratings, and written commentary.

| Column Name | PostgreSQL Type | PyArrow Type | Nullable | Description |
|---|---|---|---|---|
| `id` | `BIGINT IDENTITY` | N/A | No | Surrogate relational primary key |
| `source_rating_id` | `VARCHAR(64)` | `string` | No | Stable business key matching pattern `RAT-\d{8}` |
| `source_restaurant_id` | `VARCHAR(64)` | `string` | No | Evaluated restaurant key matching `REST-\d{4}` |
| `source_order_id` | `VARCHAR(64)` | `string` | Yes | Optional transaction key matching `ORD-\d{8}` |
| `source_customer_id` | `VARCHAR(64)` | `string` | Yes | Optional diner key matching `CUST-\d{8}` |
| `source_menu_item_id` | `VARCHAR(64)` | `string` | Yes | Optional dish key matching `DISH-\d{4}` |
| `restaurant_id` | `BIGINT` | N/A | No | Relational foreign key referencing `restaurants(id)` |
| `order_id` | `BIGINT` | N/A | Yes | Relational foreign key referencing `orders(id)` |
| `customer_id` | `BIGINT` | N/A | Yes | Relational foreign key referencing `customers(id)` |
| `menu_item_id` | `BIGINT` | N/A | Yes | Relational foreign key referencing `menu_items(id)` |
| `rating_score` | `INTEGER` | `int32` | No | Overall satisfaction rating from one to five |
| `food_rating` | `INTEGER` | `int32` | Yes | Specific food quality score from one to five |
| `service_rating` | `INTEGER` | `int32` | Yes | Specific hospitality service score from one to five |
| `ambiance_rating` | `INTEGER` | `int32` | Yes | Specific dining atmosphere score from one to five |
| `review_text` | `TEXT` | `string` | Yes | Qualitative feedback commentary |
| `rating_timestamp` | `TIMESTAMPTZ` | `timestamp[us, tz=UTC]` | No | Feedback submission timestamp in UTC |
| `is_verified_purchase` | `BOOLEAN` | `bool` | No | Confirmed point of sale transaction flag |
| `created_at` | `TIMESTAMPTZ` | `timestamp[us, tz=UTC]` | No | Record creation timestamp |

---

### Table 10: `inventory`
Raw ingredient balances, threshold limits, and reorder levels by branch.

| Column Name | PostgreSQL Type | PyArrow Type | Nullable | Description |
|---|---|---|---|---|
| `id` | `BIGINT IDENTITY` | N/A | No | Surrogate relational primary key |
| `source_inventory_id` | `VARCHAR(64)` | `string` | No | Stable business key matching pattern `INV-REST\d{2}-\d{4}` |
| `source_restaurant_id` | `VARCHAR(64)` | `string` | No | Restaurant branch key matching `REST-\d{4}` |
| `restaurant_id` | `BIGINT` | N/A | No | Relational foreign key referencing `restaurants(id)` |
| `ingredient_name` | `VARCHAR(100)` | `string` | No | Specific ingredient title |
| `ingredient_category` | `VARCHAR(40)` | `string` | No | Category: Produce, Meat & Poultry, Dairy, Dry Goods, Beverage Supplies, Packaging |
| `current_stock_quantity` | `NUMERIC(10,2)` | `float64` | No | Current on hand stock balance |
| `unit_of_measure` | `VARCHAR(20)` | `string` | No | Measurement unit: kg, g, L, ml, units, boxes |
| `reorder_threshold` | `NUMERIC(10,2)` | `float64` | No | Inventory safety stock minimum triggering replenishment |
| `reorder_quantity` | `NUMERIC(10,2)` | `float64` | No | Standard batch procurement quantity |
| `unit_purchase_cost` | `NUMERIC(10,2)` | `float64` | No | Unit cost paid to suppliers in USD |
| `last_restock_date` | `DATE` | `date32` | Yes | Most recent procurement delivery date |
| `created_at` | `TIMESTAMPTZ` | `timestamp[us, tz=UTC]` | No | Record creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `timestamp[us, tz=UTC]` | No | Most recent stock modification timestamp |

---

### Table 11: `wastage`
Operational food waste, expired inventory, and cooking loss logs.

| Column Name | PostgreSQL Type | PyArrow Type | Nullable | Description |
|---|---|---|---|---|
| `id` | `BIGINT IDENTITY` | N/A | No | Surrogate relational primary key |
| `source_wastage_id` | `VARCHAR(64)` | `string` | No | Stable business key matching pattern `WASTE-\d{8}` |
| `source_restaurant_id` | `VARCHAR(64)` | `string` | No | Logging restaurant branch key matching `REST-\d{4}` |
| `source_menu_item_id` | `VARCHAR(64)` | `string` | Yes | Associated dish key matching `DISH-\d{4}` |
| `restaurant_id` | `BIGINT` | N/A | No | Relational foreign key referencing `restaurants(id)` |
| `menu_item_id` | `BIGINT` | N/A | Yes | Relational foreign key referencing `menu_items(id)` |
| `ingredient_name` | `VARCHAR(100)` | `string` | Yes | Raw ingredient discarded |
| `wastage_timestamp` | `TIMESTAMPTZ` | `timestamp[us, tz=UTC]` | No | Discard incident timestamp in UTC |
| `quantity_lost` | `NUMERIC(10,2)` | `float64` | No | Physical amount lost |
| `unit_of_measure` | `VARCHAR(20)` | `string` | No | Measurement unit: kg, g, L, ml, units, boxes |
| `cost_loss_amount` | `NUMERIC(10,2)` | `float64` | No | Financial loss value in USD |
| `wastage_reason` | `VARCHAR(40)` | `string` | No | Reason: Expired, Over-preparation, Cooking Error, Equipment Failure, Customer Returned, Spillage |
| `reported_by` | `VARCHAR(80)` | `string` | Yes | Staff member who registered the discard log |
| `created_at` | `TIMESTAMPTZ` | `timestamp[us, tz=UTC]` | No | Record creation timestamp |
