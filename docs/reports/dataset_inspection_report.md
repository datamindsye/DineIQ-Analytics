# DineIQ Analytics — Dataset Inspection & Forensic Verification Report

**Document ID**: `REPORT-DATASET-INSPECTION-20260925`  
**Date**: `2026-09-25`  
**Dataset Profile**: `competition` (Benchmark v1)  
**Evaluation Stage**: Pre-Phase 3 Baseline Inspection (Read-Only)  
**Primary Target Path**: `data/snapshots/competition_benchmark_v1/`  
**Cleaned Target Path**: `data/cleaned/competition_benchmark_v1/`  
**Quarantine Path**: `data/quarantine/competition_benchmark_v1/`  

---

## Executive Summary

This report delivers a forensic audit and structural inspection of the complete synthetic dataset generated for the **DineIQ Analytics — Data Science Intelligence Arena** platform. All metrics, schemas, record distributions, referential relationships, financial calculations, and data quality anomalies reported herein were extracted directly from the underlying physical Apache Parquet files residing on local storage.

- **Authoritative Total Raw Records**: **1,311,264 records** across 11 tables.
- **Clean Records Output**: **1,302,220 records** (99.31% cleanliness rate).
- **Quarantined Records Isolated**: **9,044 records** (0.69% anomaly rate).
- **Mathematical Reconciliation**: $1,302,220 \text{ (clean)} + 9,044 \text{ (quarantine)} = 1,311,264 \text{ (raw)}$. Perfect $0$ variance.
- **Referential Integrity**: 100% exact foreign key alignment across all clean tables (0 orphaned child records).
- **Financial Consistency**: 100% formula adherence on Line Net Revenue, Line Contribution Margin, and Order Settlement Total ($0$ mismatch exceeding $\pm$ $0.01).
- **Temporal Split**: 4-way chronological boundary verified: TRAIN (66.66%), VALIDATION (16.61%), TEST (8.23%), and UNSEEN_COMPARISON (8.49%).

---

## Part 1: Detailed Table-by-Table Inspection

This section presents comprehensive structural profiles for each of the eleven domain tables in the raw snapshot.

### 1.1 Table: `customers`

- **Physical File**: `data/snapshots/competition_benchmark_v1/customers.parquet`
- **Row Count**: `50,000`
- **Column Count**: `11`

#### Complete Schema Definition

| # | Column Name | PyArrow Data Type | Nullable | Null Count | Null % | Unique Count |
|---|---|---|---|---|---|---|
| 1 | `source_customer_id` | `string` | No | 0 | 0.00% | 50,000 |
| 2 | `first_name` | `string` | Yes | 0 | 0.00% | 40 |
| 3 | `last_name` | `string` | Yes | 0 | 0.00% | 31 |
| 4 | `email` | `string` | Yes | 3,830 | 7.66% | 46,170 |
| 5 | `phone` | `string` | Yes | 3,694 | 7.39% | 46,174 |
| 6 | `registration_date` | `date32[day]` | No | 0 | 0.00% | 730 |
| 7 | `loyalty_tier` | `string` | No | 0 | 0.00% | 5 |
| 8 | `preferred_channel` | `string` | Yes | 0 | 0.00% | 4 |
| 9 | `home_city` | `string` | Yes | 0 | 0.00% | 20 |
| 10 | `is_active` | `bool` | No | 0 | 0.00% | 1 |
| 11 | `created_at` | `timestamp[us, tz=UTC]` | No | 0 | 0.00% | 730 |

#### Column Statistics & Value Ranges

| Column Name | Metric / Value Bounds | Sample / Top Frequency Distribution |
|---|---|---|
| `source_customer_id` | N/A | `CUST-00000001`: 1, `CUST-00000002`: 1, `CUST-00000003`: 1 |
| `first_name` | N/A | `Paul`: 1,326, `Daniel`: 1,304, `Ashley`: 1,295 |
| `last_name` | N/A | `Moore`: 1,680, `Lopez`: 1,667, `Jackson`: 1,657 |
| `email` | N/A | `sarah.jones1@example.com`: 1, `charles.hernandez2@example.com`: 1, `sarah.hernandez3@example.com`: 1 |
| `phone` | N/A | `+1-555-726-9843`: 2, `+1-555-502-3115`: 2, `+1-555-528-7834`: 2 |
| `registration_date` | N/A | `2025-10-09`: 93, `2025-08-10`: 92, `2025-09-17`: 92 |
| `loyalty_tier` | N/A | `Bronze`: 19,872, `Silver`: 12,561, `Gold`: 7,641 |
| `preferred_channel` | N/A | `Delivery Direct`: 12,579, `Takeaway`: 12,543, `Dine-in`: 12,532 |
| `home_city` | N/A | `Indianapolis`: 2,599, `Charlotte`: 2,584, `New York`: 2,570 |
| `is_active` | Min: 1.00 | Max: 1.00 | Mean: 1.00 | Span: [1.00 .. 1.00] |
| `created_at` | Earliest: `2024-01-02 00:00:00+00:00`<br>Latest: `2025-12-31 00:00:00+00:00` | Temporal span recorded |

#### First 3 Representative Records

```json
[
  {
    "source_customer_id": "CUST-00000001",
    "first_name": "Sarah",
    "last_name": "Jones",
    "email": "sarah.jones1@example.com",
    "phone": "+1-555-367-6818",
    "registration_date": "2025-01-31",
    "loyalty_tier": "Platinum",
    "preferred_channel": "Delivery Direct",
    "home_city": "Philadelphia",
    "is_active": true,
    "created_at": "2025-01-31 00:00:00+00:00"
  },
  {
    "source_customer_id": "CUST-00000002",
    "first_name": "Charles",
    "last_name": "Hernandez",
    "email": "charles.hernandez2@example.com",
    "phone": "+1-555-245-1983",
    "registration_date": "2025-10-13",
    "loyalty_tier": "Silver",
    "preferred_channel": "Delivery Direct",
    "home_city": "Nashville",
    "is_active": true,
    "created_at": "2025-10-13 00:00:00+00:00"
  },
  {
    "source_customer_id": "CUST-00000003",
    "first_name": "Sarah",
    "last_name": "Hernandez",
    "email": "sarah.hernandez3@example.com",
    "phone": "+1-555-930-6035",
    "registration_date": "2025-09-04",
    "loyalty_tier": "Silver",
    "preferred_channel": "Delivery Aggregator",
    "home_city": "San Jose",
    "is_active": true,
    "created_at": "2025-09-04 00:00:00+00:00"
  }
]
```

#### Last 3 Representative Records

```json
[
  {
    "source_customer_id": "CUST-00049998",
    "first_name": "Thomas",
    "last_name": "Smith",
    "email": "thomas.smith49998@example.com",
    "phone": "+1-555-470-6463",
    "registration_date": "2024-01-06",
    "loyalty_tier": "Silver",
    "preferred_channel": "Delivery Aggregator",
    "home_city": "San Francisco",
    "is_active": true,
    "created_at": "2024-01-06 00:00:00+00:00"
  },
  {
    "source_customer_id": "CUST-00049999",
    "first_name": "Elizabeth",
    "last_name": "Hernandez",
    "email": "elizabeth.hernandez49999@example.com",
    "phone": "+1-555-253-7761",
    "registration_date": "2025-04-26",
    "loyalty_tier": "Bronze",
    "preferred_channel": "Delivery Direct",
    "home_city": "Charlotte",
    "is_active": true,
    "created_at": "2025-04-26 00:00:00+00:00"
  },
  {
    "source_customer_id": "CUST-00050000",
    "first_name": "Patricia",
    "last_name": "Smith",
    "email": "patricia.smith50000@example.com",
    "phone": "+1-555-842-6951",
    "registration_date": "2024-03-30",
    "loyalty_tier": "None",
    "preferred_channel": "Delivery Aggregator",
    "home_city": "San Francisco",
    "is_active": true,
    "created_at": "2024-03-30 00:00:00+00:00"
  }
]
```

---

### 1.2 Table: `orders`

- **Physical File**: `data/snapshots/competition_benchmark_v1/orders.parquet`
- **Row Count**: `100,508`
- **Column Count**: `13`

#### Complete Schema Definition

| # | Column Name | PyArrow Data Type | Nullable | Null Count | Null % | Unique Count |
|---|---|---|---|---|---|---|
| 1 | `source_order_id` | `string` | No | 0 | 0.00% | 100,000 |
| 2 | `source_restaurant_id` | `string` | No | 0 | 0.00% | 20 |
| 3 | `source_customer_id` | `string` | Yes | 10,070 | 10.02% | 35,259 |
| 4 | `order_timestamp` | `timestamp[us, tz=UTC]` | No | 0 | 0.00% | 99,557 |
| 5 | `order_channel` | `string` | No | 0 | 0.00% | 4 |
| 6 | `order_status` | `string` | No | 0 | 0.00% | 3 |
| 7 | `subtotal_amount` | `double` | No | 0 | 0.00% | 31,521 |
| 8 | `discount_amount` | `double` | No | 0 | 0.00% | 6,226 |
| 9 | `tax_amount` | `double` | No | 0 | 0.00% | 5,992 |
| 10 | `tip_amount` | `double` | No | 0 | 0.00% | 8,989 |
| 11 | `total_amount` | `double` | No | 0 | 0.00% | 36,808 |
| 12 | `payment_method` | `string` | No | 0 | 0.00% | 5 |
| 13 | `created_at` | `timestamp[us, tz=UTC]` | No | 0 | 0.00% | 99,557 |

#### Column Statistics & Value Ranges

| Column Name | Metric / Value Bounds | Sample / Top Frequency Distribution |
|---|---|---|
| `source_order_id` | N/A | `ORD-00000284`: 2, `ORD-00000767`: 2, `ORD-00000903`: 2 |
| `source_restaurant_id` | N/A | `REST-0011`: 7,535, `REST-0003`: 7,528, `REST-0009`: 7,518 |
| `source_customer_id` | N/A | `CUST-00002380`: 20, `CUST-00002421`: 20, `CUST-00001126`: 19 |
| `order_timestamp` | Earliest: `2025-01-01 11:09:01+00:00`<br>Latest: `2027-05-13 17:46:31+00:00` | Temporal span recorded |
| `order_channel` | N/A | `Dine-in`: 45,153, `Takeaway`: 24,980, `Delivery Direct`: 20,275 |
| `order_status` | N/A | `Completed`: 96,478, `Cancelled`: 3,516, `Voided`: 514 |
| `subtotal_amount` | Min: 0.00 | Max: 1,569.04 | Mean: 265.34 | Span: [0.00 .. 1,569.04] |
| `discount_amount` | Min: 0.00 | Max: 471.90 | Mean: 10.52 | Span: [0.00 .. 471.90] |
| `tax_amount` | Min: 0.00 | Max: 129.45 | Mean: 20.18 | Span: [0.00 .. 129.45] |
| `tip_amount` | Min: 0.00 | Max: 187.73 | Mean: 23.38 | Span: [0.00 .. 187.73] |
| `total_amount` | Min: 0.00 | Max: 1,698.49 | Mean: 298.39 | Span: [0.00 .. 1,698.49] |
| `payment_method` | N/A | `Credit Card`: 55,373, `Debit Card`: 20,092, `Digital Wallet`: 12,029 |
| `created_at` | Earliest: `2025-01-01 11:09:01+00:00`<br>Latest: `2027-05-13 17:46:31+00:00` | Temporal span recorded |

#### First 3 Representative Records

```json
[
  {
    "source_order_id": "ORD-00000001",
    "source_restaurant_id": "REST-0017",
    "source_customer_id": "CUST-00006146",
    "order_timestamp": "2025-01-08 19:12:05+00:00",
    "order_channel": "Delivery Aggregator",
    "order_status": "Cancelled",
    "subtotal_amount": 267.3,
    "discount_amount": 0.0,
    "tax_amount": 0.0,
    "tip_amount": 0.0,
    "total_amount": 267.3,
    "payment_method": "Digital Wallet",
    "created_at": "2025-01-08 19:12:05+00:00"
  },
  {
    "source_order_id": "ORD-00000002",
    "source_restaurant_id": "REST-0018",
    "source_customer_id": "CUST-00002949",
    "order_timestamp": "2025-10-09 14:54:54+00:00",
    "order_channel": "Takeaway",
    "order_status": "Completed",
    "subtotal_amount": 230.4,
    "discount_amount": 0.0,
    "tax_amount": 19.01,
    "tip_amount": 0.0,
    "total_amount": 249.41,
    "payment_method": "Credit Card",
    "created_at": "2025-10-09 14:54:54+00:00"
  },
  {
    "source_order_id": "ORD-00000003",
    "source_restaurant_id": "REST-0005",
    "source_customer_id": "CUST-00001224",
    "order_timestamp": "2025-08-06 11:18:23+00:00",
    "order_channel": "Dine-in",
    "order_status": "Completed",
    "subtotal_amount": 249.1,
    "discount_amount": 0.0,
    "tax_amount": 20.55,
    "tip_amount": 37.36,
    "total_amount": 307.01,
    "payment_method": "Credit Card",
    "created_at": "2025-08-06 11:18:23+00:00"
  }
]
```

#### Last 3 Representative Records

```json
[
  {
    "source_order_id": "ORD-00099998",
    "source_restaurant_id": "REST-0009",
    "source_customer_id": "CUST-00000546",
    "order_timestamp": "2025-03-09 19:54:37+00:00",
    "order_channel": "Delivery Direct",
    "order_status": "Completed",
    "subtotal_amount": 278.12,
    "discount_amount": 139.06,
    "tax_amount": 11.47,
    "tip_amount": 20.86,
    "total_amount": 171.39,
    "payment_method": "Credit Card",
    "created_at": "2025-03-09 19:54:37+00:00"
  },
  {
    "source_order_id": "ORD-00099999",
    "source_restaurant_id": "REST-0011",
    "source_customer_id": NaN,
    "order_timestamp": "2025-09-02 18:11:18+00:00",
    "order_channel": "Dine-in",
    "order_status": "Completed",
    "subtotal_amount": 363.55,
    "discount_amount": 0.0,
    "tax_amount": 29.99,
    "tip_amount": 54.53,
    "total_amount": 448.07,
    "payment_method": "Credit Card",
    "created_at": "2025-09-02 18:11:18+00:00"
  },
  {
    "source_order_id": "ORD-00100000",
    "source_restaurant_id": "REST-0016",
    "source_customer_id": "CUST-00040876",
    "order_timestamp": "2025-11-25 17:28:16+00:00",
    "order_channel": "Dine-in",
    "order_status": "Completed",
    "subtotal_amount": 239.35,
    "discount_amount": 2.24,
    "tax_amount": 19.56,
    "tip_amount": 35.57,
    "total_amount": 292.24,
    "payment_method": "Digital Wallet",
    "created_at": "2025-11-25 17:28:16+00:00"
  }
]
```

---

### 1.3 Table: `order_items`

- **Physical File**: `data/snapshots/competition_benchmark_v1/order_items.parquet`
- **Row Count**: `1,006,051`
- **Column Count**: `12`

#### Complete Schema Definition

| # | Column Name | PyArrow Data Type | Nullable | Null Count | Null % | Unique Count |
|---|---|---|---|---|---|---|
| 1 | `source_order_item_id` | `string` | No | 0 | 0.00% | 1,001,009 |
| 2 | `source_order_id` | `string` | No | 0 | 0.00% | 100,000 |
| 3 | `source_menu_item_id` | `string` | No | 0 | 0.00% | 150 |
| 4 | `quantity` | `int32` | No | 0 | 0.00% | 4 |
| 5 | `unit_price_at_sale` | `double` | No | 0 | 0.00% | 390 |
| 6 | `unit_cost_at_sale` | `double` | No | 0 | 0.00% | 207 |
| 7 | `line_discount` | `double` | No | 0 | 0.00% | 1,014 |
| 8 | `source_promotion_id` | `string` | Yes | 840,867 | 83.58% | 16 |
| 9 | `line_net_revenue` | `double` | No | 0 | 0.00% | 2,243 |
| 10 | `line_contribution_margin` | `double` | No | 0 | 0.00% | 3,185 |
| 11 | `special_instructions` | `string` | Yes | 955,724 | 95.00% | 1 |
| 12 | `created_at` | `timestamp[us, tz=UTC]` | No | 0 | 0.00% | 99,557 |

#### Column Statistics & Value Ranges

| Column Name | Metric / Value Bounds | Sample / Top Frequency Distribution |
|---|---|---|
| `source_order_item_id` | N/A | `ITEM-00000407`: 2, `ITEM-00000677`: 2, `ITEM-00000682`: 2 |
| `source_order_id` | N/A | `ORD-00081724`: 27, `ORD-00094954`: 26, `ORD-00023900`: 25 |
| `source_menu_item_id` | N/A | `DISH-0001`: 125,258, `DISH-0002`: 69,380, `DISH-0003`: 49,149 |
| `quantity` | Min: 0.00 | Max: 3.00 | Mean: 1.25 | Span: [0.00 .. 3.00] |
| `unit_price_at_sale` | Min: -209.00 | Max: 229.90 | Mean: 21.23 | Span: [-209.00 .. 229.90] |
| `unit_cost_at_sale` | Min: 0.48 | Max: 72.24 | Mean: 6.67 | Span: [0.48 .. 72.24] |
| `line_discount` | Min: -187.00 | Max: 282.15 | Mean: 1.05 | Span: [-187.00 .. 282.15] |
| `source_promotion_id` | N/A | `PROMO-0003`: 32,917, `PROMO-0018`: 25,819, `PROMO-0024`: 23,905 |
| `line_net_revenue` | Min: -495.00 | Max: 627.00 | Mean: 25.45 | Span: [-495.00 .. 627.00] |
| `line_contribution_margin` | Min: -663.00 | Max: 420.60 | Mean: 17.12 | Span: [-663.00 .. 420.60] |
| `special_instructions` | N/A | `Special chef request`: 50,327 |
| `created_at` | Earliest: `2025-01-01 11:09:01+00:00`<br>Latest: `2027-05-13 17:46:31+00:00` | Temporal span recorded |

#### First 3 Representative Records

```json
[
  {
    "source_order_item_id": "ITEM-00000001",
    "source_order_id": "ORD-00000001",
    "source_menu_item_id": "DISH-0002",
    "quantity": 2,
    "unit_price_at_sale": 26.0,
    "unit_cost_at_sale": 9.0,
    "line_discount": 0.0,
    "source_promotion_id": NaN,
    "line_net_revenue": 52.0,
    "line_contribution_margin": 34.0,
    "special_instructions": NaN,
    "created_at": "2025-01-08 19:12:05+00:00"
  },
  {
    "source_order_item_id": "ITEM-00000002",
    "source_order_id": "ORD-00000001",
    "source_menu_item_id": "DISH-0001",
    "quantity": 1,
    "unit_price_at_sale": 8.5,
    "unit_cost_at_sale": 2.2,
    "line_discount": 0.0,
    "source_promotion_id": NaN,
    "line_net_revenue": 8.5,
    "line_contribution_margin": 6.3,
    "special_instructions": NaN,
    "created_at": "2025-01-08 19:12:05+00:00"
  },
  {
    "source_order_item_id": "ITEM-00000003",
    "source_order_id": "ORD-00000001",
    "source_menu_item_id": "DISH-0102",
    "quantity": 1,
    "unit_price_at_sale": 47.52,
    "unit_cost_at_sale": 16.28,
    "line_discount": 0.0,
    "source_promotion_id": NaN,
    "line_net_revenue": 47.52,
    "line_contribution_margin": 31.24,
    "special_instructions": NaN,
    "created_at": "2025-01-08 19:12:05+00:00"
  }
]
```

#### Last 3 Representative Records

```json
[
  {
    "source_order_item_id": "ITEM-01001007",
    "source_order_id": "ORD-00100000",
    "source_menu_item_id": "DISH-0066",
    "quantity": 1,
    "unit_price_at_sale": 9.1,
    "unit_cost_at_sale": 1.98,
    "line_discount": 0.0,
    "source_promotion_id": NaN,
    "line_net_revenue": 9.1,
    "line_contribution_margin": 7.12,
    "special_instructions": NaN,
    "created_at": "2025-11-25 17:28:16+00:00"
  },
  {
    "source_order_item_id": "ITEM-01001008",
    "source_order_id": "ORD-00100000",
    "source_menu_item_id": "DISH-0053",
    "quantity": 1,
    "unit_price_at_sale": 36.4,
    "unit_cost_at_sale": 13.64,
    "line_discount": 0.0,
    "source_promotion_id": NaN,
    "line_net_revenue": 36.4,
    "line_contribution_margin": 22.76,
    "special_instructions": NaN,
    "created_at": "2025-11-25 17:28:16+00:00"
  },
  {
    "source_order_item_id": "ITEM-01001009",
    "source_order_id": "ORD-00100000",
    "source_menu_item_id": "DISH-0048",
    "quantity": 1,
    "unit_price_at_sale": 5.2,
    "unit_cost_at_sale": 0.62,
    "line_discount": 0.0,
    "source_promotion_id": NaN,
    "line_net_revenue": 5.2,
    "line_contribution_margin": 4.58,
    "special_instructions": NaN,
    "created_at": "2025-11-25 17:28:16+00:00"
  }
]
```

---

### 1.4 Table: `menu_items`

- **Physical File**: `data/snapshots/competition_benchmark_v1/menu_items.parquet`
- **Row Count**: `150`
- **Column Count**: `12`

#### Complete Schema Definition

| # | Column Name | PyArrow Data Type | Nullable | Null Count | Null % | Unique Count |
|---|---|---|---|---|---|---|
| 1 | `source_menu_item_id` | `string` | No | 0 | 0.00% | 150 |
| 2 | `source_category_id` | `string` | No | 0 | 0.00% | 10 |
| 3 | `item_name` | `string` | No | 0 | 0.00% | 150 |
| 4 | `description` | `string` | Yes | 0 | 0.00% | 150 |
| 5 | `current_base_price` | `double` | No | 0 | 0.00% | 129 |
| 6 | `current_base_cost` | `double` | No | 0 | 0.00% | 133 |
| 7 | `prep_time_minutes` | `int32` | No | 0 | 0.00% | 17 |
| 8 | `is_seasonal` | `bool` | No | 0 | 0.00% | 2 |
| 9 | `is_active` | `bool` | No | 0 | 0.00% | 1 |
| 10 | `spiciness_level` | `int32` | No | 0 | 0.00% | 1 |
| 11 | `allergens` | `string` | Yes | 90 | 60.00% | 2 |
| 12 | `created_at` | `timestamp[us, tz=UTC]` | No | 0 | 0.00% | 1 |

#### Column Statistics & Value Ranges

| Column Name | Metric / Value Bounds | Sample / Top Frequency Distribution |
|---|---|---|
| `source_menu_item_id` | N/A | `DISH-0001`: 1, `DISH-0002`: 1, `DISH-0003`: 1 |
| `source_category_id` | N/A | `CAT-001`: 15, `CAT-002`: 15, `CAT-003`: 15 |
| `item_name` | N/A | `Truffle Fries`: 1, `Pan Seared Salmon`: 1, `Crispy Beer Battered Cod`: 1 |
| `description` | N/A | `Freshly crafted truffle fries prepared to order.`: 1, `Freshly crafted pan seared salmon prepared to order.`: 1, `Freshly crafted crispy beer battered cod prepared to order.`: 1 |
| `current_base_price` | Min: 4.40 | Max: 209.00 | Mean: 28.89 | Span: [4.40 .. 209.00] |
| `current_base_cost` | Min: 0.54 | Max: 68.80 | Mean: 9.00 | Span: [0.54 .. 68.80] |
| `prep_time_minutes` | Min: 8.00 | Max: 24.00 | Mean: 15.91 | Span: [8.00 .. 24.00] |
| `is_seasonal` | Min: 0.00 | Max: 1.00 | Mean: 0.12 | Span: [0.00 .. 1.00] |
| `is_active` | Min: 1.00 | Max: 1.00 | Mean: 1.00 | Span: [1.00 .. 1.00] |
| `spiciness_level` | Min: 0.00 | Max: 0.00 | Mean: 0.00 | Span: [0.00 .. 0.00] |
| `allergens` | N/A | `Gluten, Dairy`: 50, `Seafood`: 10 |
| `created_at` | Earliest: `2024-01-01 00:00:00+00:00`<br>Latest: `2024-01-01 00:00:00+00:00` | Temporal span recorded |

#### First 3 Representative Records

```json
[
  {
    "source_menu_item_id": "DISH-0001",
    "source_category_id": "CAT-001",
    "item_name": "Truffle Fries",
    "description": "Freshly crafted truffle fries prepared to order.",
    "current_base_price": 8.5,
    "current_base_cost": 2.2,
    "prep_time_minutes": 24,
    "is_seasonal": false,
    "is_active": true,
    "spiciness_level": 0,
    "allergens": NaN,
    "created_at": "2024-01-01 00:00:00+00:00"
  },
  {
    "source_menu_item_id": "DISH-0002",
    "source_category_id": "CAT-002",
    "item_name": "Pan Seared Salmon",
    "description": "Freshly crafted pan seared salmon prepared to order.",
    "current_base_price": 26.0,
    "current_base_cost": 9.0,
    "prep_time_minutes": 22,
    "is_seasonal": false,
    "is_active": true,
    "spiciness_level": 0,
    "allergens": NaN,
    "created_at": "2024-01-01 00:00:00+00:00"
  },
  {
    "source_menu_item_id": "DISH-0003",
    "source_category_id": "CAT-003",
    "item_name": "Crispy Beer Battered Cod",
    "description": "Freshly crafted crispy beer battered cod prepared to order.",
    "current_base_price": 18.0,
    "current_base_cost": 5.5,
    "prep_time_minutes": 18,
    "is_seasonal": false,
    "is_active": true,
    "spiciness_level": 0,
    "allergens": "Gluten, Dairy",
    "created_at": "2024-01-01 00:00:00+00:00"
  }
]
```

#### Last 3 Representative Records

```json
[
  {
    "source_menu_item_id": "DISH-0148",
    "source_category_id": "CAT-008",
    "item_name": "Berry Hibiscus Cooler Style 10",
    "description": "Freshly crafted berry hibiscus cooler style 10 prepared to order.",
    "current_base_price": 9.5,
    "current_base_cost": 1.38,
    "prep_time_minutes": 16,
    "is_seasonal": false,
    "is_active": true,
    "spiciness_level": 0,
    "allergens": NaN,
    "created_at": "2024-01-01 00:00:00+00:00"
  },
  {
    "source_menu_item_id": "DISH-0149",
    "source_category_id": "CAT-009",
    "item_name": "Prosecco Brut Sparkling Glass Style 10",
    "description": "Freshly crafted prosecco brut sparkling glass style 10 prepared to order.",
    "current_base_price": 20.9,
    "current_base_cost": 4.13,
    "prep_time_minutes": 12,
    "is_seasonal": false,
    "is_active": true,
    "spiciness_level": 0,
    "allergens": NaN,
    "created_at": "2024-01-01 00:00:00+00:00"
  },
  {
    "source_menu_item_id": "DISH-0150",
    "source_category_id": "CAT-010",
    "item_name": "Chef Seven Course Tasting Preview Style 10",
    "description": "Freshly crafted chef seven course tasting preview style 10 prepared to order.",
    "current_base_price": 209.0,
    "current_base_cost": 68.8,
    "prep_time_minutes": 9,
    "is_seasonal": false,
    "is_active": true,
    "spiciness_level": 0,
    "allergens": "Gluten, Dairy",
    "created_at": "2024-01-01 00:00:00+00:00"
  }
]
```

---

### 1.5 Table: `menu_categories`

- **Physical File**: `data/snapshots/competition_benchmark_v1/menu_categories.parquet`
- **Row Count**: `10`
- **Column Count**: `6`

#### Complete Schema Definition

| # | Column Name | PyArrow Data Type | Nullable | Null Count | Null % | Unique Count |
|---|---|---|---|---|---|---|
| 1 | `source_category_id` | `string` | No | 0 | 0.00% | 10 |
| 2 | `category_name` | `string` | No | 0 | 0.00% | 10 |
| 3 | `description` | `string` | Yes | 0 | 0.00% | 10 |
| 4 | `display_order` | `int32` | No | 0 | 0.00% | 10 |
| 5 | `is_active` | `bool` | No | 0 | 0.00% | 1 |
| 6 | `created_at` | `timestamp[us, tz=UTC]` | No | 0 | 0.00% | 1 |

#### Column Statistics & Value Ranges

| Column Name | Metric / Value Bounds | Sample / Top Frequency Distribution |
|---|---|---|
| `source_category_id` | N/A | `CAT-001`: 1, `CAT-002`: 1, `CAT-003`: 1 |
| `category_name` | N/A | `Appetizers`: 1, `Entrees`: 1, `Seafood Specialties`: 1 |
| `description` | N/A | `Standard culinary category for appetizers`: 1, `Standard culinary category for entrees`: 1, `Standard culinary category for seafood specialties`: 1 |
| `display_order` | Min: 1.00 | Max: 10.00 | Mean: 5.50 | Span: [1.00 .. 10.00] |
| `is_active` | Min: 1.00 | Max: 1.00 | Mean: 1.00 | Span: [1.00 .. 1.00] |
| `created_at` | Earliest: `2024-01-01 00:00:00+00:00`<br>Latest: `2024-01-01 00:00:00+00:00` | Temporal span recorded |

#### First 3 Representative Records

```json
[
  {
    "source_category_id": "CAT-001",
    "category_name": "Appetizers",
    "description": "Standard culinary category for appetizers",
    "display_order": 1,
    "is_active": true,
    "created_at": "2024-01-01 00:00:00+00:00"
  },
  {
    "source_category_id": "CAT-002",
    "category_name": "Entrees",
    "description": "Standard culinary category for entrees",
    "display_order": 2,
    "is_active": true,
    "created_at": "2024-01-01 00:00:00+00:00"
  },
  {
    "source_category_id": "CAT-003",
    "category_name": "Seafood Specialties",
    "description": "Standard culinary category for seafood specialties",
    "display_order": 3,
    "is_active": true,
    "created_at": "2024-01-01 00:00:00+00:00"
  }
]
```

#### Last 3 Representative Records

```json
[
  {
    "source_category_id": "CAT-008",
    "category_name": "Non-Alcoholic Beverages",
    "description": "Standard culinary category for non-alcoholic beverages",
    "display_order": 8,
    "is_active": true,
    "created_at": "2024-01-01 00:00:00+00:00"
  },
  {
    "source_category_id": "CAT-009",
    "category_name": "Bar & Cocktails",
    "description": "Standard culinary category for bar & cocktails",
    "display_order": 9,
    "is_active": true,
    "created_at": "2024-01-01 00:00:00+00:00"
  },
  {
    "source_category_id": "CAT-010",
    "category_name": "Chef Specials",
    "description": "Standard culinary category for chef specials",
    "display_order": 10,
    "is_active": true,
    "created_at": "2024-01-01 00:00:00+00:00"
  }
]
```

---

### 1.6 Table: `restaurants`

- **Physical File**: `data/snapshots/competition_benchmark_v1/restaurants.parquet`
- **Row Count**: `20`
- **Column Count**: `13`

#### Complete Schema Definition

| # | Column Name | PyArrow Data Type | Nullable | Null Count | Null % | Unique Count |
|---|---|---|---|---|---|---|
| 1 | `source_restaurant_id` | `string` | No | 0 | 0.00% | 20 |
| 2 | `location_name` | `string` | No | 0 | 0.00% | 20 |
| 3 | `city` | `string` | No | 0 | 0.00% | 20 |
| 4 | `state_region` | `string` | No | 0 | 0.00% | 13 |
| 5 | `postal_code` | `string` | No | 0 | 0.00% | 20 |
| 6 | `seating_capacity` | `int32` | No | 0 | 0.00% | 18 |
| 7 | `dining_type` | `string` | No | 0 | 0.00% | 4 |
| 8 | `manager_name` | `string` | Yes | 0 | 0.00% | 20 |
| 9 | `opening_date` | `date32[day]` | No | 0 | 0.00% | 19 |
| 10 | `latitude` | `double` | Yes | 0 | 0.00% | 20 |
| 11 | `longitude` | `double` | Yes | 0 | 0.00% | 20 |
| 12 | `is_active` | `bool` | No | 0 | 0.00% | 1 |
| 13 | `created_at` | `timestamp[us, tz=UTC]` | No | 0 | 0.00% | 1 |

#### Column Statistics & Value Ranges

| Column Name | Metric / Value Bounds | Sample / Top Frequency Distribution |
|---|---|---|
| `source_restaurant_id` | N/A | `REST-0001`: 1, `REST-0002`: 1, `REST-0003`: 1 |
| `location_name` | N/A | `Chicago Fast Casual #1`: 1, `New York Casual Dining #2`: 1, `Los Angeles Fine Dining #3`: 1 |
| `city` | N/A | `Chicago`: 1, `New York`: 1, `Los Angeles`: 1 |
| `state_region` | N/A | `TX`: 5, `CA`: 4, `IL`: 1 |
| `postal_code` | N/A | `60601`: 1, `10001`: 1, `90001`: 1 |
| `seating_capacity` | Min: 68.00 | Max: 200.00 | Mean: 122.15 | Span: [68.00 .. 200.00] |
| `dining_type` | N/A | `Fast Casual`: 5, `Casual Dining`: 5, `Fine Dining`: 5 |
| `manager_name` | N/A | `Patricia Davis`: 1, `Michael Anderson`: 1, `Elizabeth Perez`: 1 |
| `opening_date` | N/A | `2024-05-29`: 2, `2024-04-20`: 1, `2024-05-15`: 1 |
| `latitude` | Min: 29.42 | Max: 47.61 | Mean: 36.08 | Span: [29.42 .. 47.61] |
| `longitude` | Min: -122.42 | Max: -74.01 | Mean: -98.00 | Span: [-122.42 .. -74.01] |
| `is_active` | Min: 1.00 | Max: 1.00 | Mean: 1.00 | Span: [1.00 .. 1.00] |
| `created_at` | Earliest: `2024-01-01 00:00:00+00:00`<br>Latest: `2024-01-01 00:00:00+00:00` | Temporal span recorded |

#### First 3 Representative Records

```json
[
  {
    "source_restaurant_id": "REST-0001",
    "location_name": "Chicago Fast Casual #1",
    "city": "Chicago",
    "state_region": "IL",
    "postal_code": "60601",
    "seating_capacity": 164,
    "dining_type": "Fast Casual",
    "manager_name": "Patricia Davis",
    "opening_date": "2024-04-20",
    "latitude": 41.881832,
    "longitude": -87.623177,
    "is_active": true,
    "created_at": "2024-01-01 00:00:00+00:00"
  },
  {
    "source_restaurant_id": "REST-0002",
    "location_name": "New York Casual Dining #2",
    "city": "New York",
    "state_region": "NY",
    "postal_code": "10001",
    "seating_capacity": 176,
    "dining_type": "Casual Dining",
    "manager_name": "Michael Anderson",
    "opening_date": "2024-05-15",
    "latitude": 40.712776,
    "longitude": -74.005974,
    "is_active": true,
    "created_at": "2024-01-01 00:00:00+00:00"
  },
  {
    "source_restaurant_id": "REST-0003",
    "location_name": "Los Angeles Fine Dining #3",
    "city": "Los Angeles",
    "state_region": "CA",
    "postal_code": "90001",
    "seating_capacity": 200,
    "dining_type": "Fine Dining",
    "manager_name": "Elizabeth Perez",
    "opening_date": "2024-05-21",
    "latitude": 34.052235,
    "longitude": -118.243683,
    "is_active": true,
    "created_at": "2024-01-01 00:00:00+00:00"
  }
]
```

#### Last 3 Representative Records

```json
[
  {
    "source_restaurant_id": "REST-0018",
    "location_name": "Seattle Casual Dining #18",
    "city": "Seattle",
    "state_region": "WA",
    "postal_code": "98101",
    "seating_capacity": 171,
    "dining_type": "Casual Dining",
    "manager_name": "Joseph Williams",
    "opening_date": "2024-03-19",
    "latitude": 47.606209,
    "longitude": -122.332069,
    "is_active": true,
    "created_at": "2024-01-01 00:00:00+00:00"
  },
  {
    "source_restaurant_id": "REST-0019",
    "location_name": "Denver Fine Dining #19",
    "city": "Denver",
    "state_region": "CO",
    "postal_code": "80201",
    "seating_capacity": 92,
    "dining_type": "Fine Dining",
    "manager_name": "Sarah Martinez",
    "opening_date": "2024-05-30",
    "latitude": 39.739236,
    "longitude": -104.99025,
    "is_active": true,
    "created_at": "2024-01-01 00:00:00+00:00"
  },
  {
    "source_restaurant_id": "REST-0020",
    "location_name": "Nashville Express Kiosk #20",
    "city": "Nashville",
    "state_region": "TN",
    "postal_code": "37201",
    "seating_capacity": 104,
    "dining_type": "Express Kiosk",
    "manager_name": "Christopher Taylor",
    "opening_date": "2024-04-25",
    "latitude": 36.162663,
    "longitude": -86.781601,
    "is_active": true,
    "created_at": "2024-01-01 00:00:00+00:00"
  }
]
```

---

### 1.7 Table: `pricing_history`

- **Physical File**: `data/snapshots/competition_benchmark_v1/pricing_history.parquet`
- **Row Count**: `1,500`
- **Column Count**: `9`

#### Complete Schema Definition

| # | Column Name | PyArrow Data Type | Nullable | Null Count | Null % | Unique Count |
|---|---|---|---|---|---|---|
| 1 | `source_pricing_history_id` | `string` | No | 0 | 0.00% | 1,500 |
| 2 | `source_menu_item_id` | `string` | No | 0 | 0.00% | 150 |
| 3 | `source_restaurant_id` | `string` | Yes | 200 | 13.33% | 20 |
| 4 | `base_price` | `double` | No | 0 | 0.00% | 601 |
| 5 | `base_cost` | `double` | No | 0 | 0.00% | 502 |
| 6 | `effective_from` | `timestamp[us, tz=UTC]` | No | 0 | 0.00% | 275 |
| 7 | `effective_to` | `timestamp[us, tz=UTC]` | Yes | 150 | 10.00% | 296 |
| 8 | `change_reason` | `string` | No | 0 | 0.00% | 8 |
| 9 | `created_at` | `timestamp[us, tz=UTC]` | No | 0 | 0.00% | 275 |

#### Column Statistics & Value Ranges

| Column Name | Metric / Value Bounds | Sample / Top Frequency Distribution |
|---|---|---|
| `source_pricing_history_id` | N/A | `PRC-000001`: 1, `PRC-000002`: 1, `PRC-000003`: 1 |
| `source_menu_item_id` | N/A | `DISH-0051`: 11, `DISH-0054`: 11, `DISH-0057`: 11 |
| `source_restaurant_id` | N/A | `REST-0002`: 65, `REST-0003`: 65, `REST-0004`: 65 |
| `base_price` | Min: 3.96 | Max: 229.90 | Mean: 30.50 | Span: [3.96 .. 229.90] |
| `base_cost` | Min: 0.48 | Max: 72.24 | Mean: 9.25 | Span: [0.48 .. 72.24] |
| `effective_from` | Earliest: `2024-07-05 00:00:00+00:00`<br>Latest: `2025-11-01 00:00:00+00:00` | Temporal span recorded |
| `effective_to` | Earliest: `2025-02-18 00:00:00+00:00`<br>Latest: `2025-12-26 00:00:00+00:00` | Temporal span recorded |
| `change_reason` | N/A | `Seasonal summer menu repricing`: 260, `Local branch operational overhead adjustment`: 260, `Holiday promotional dining window`: 260 |
| `created_at` | Earliest: `2024-07-05 00:00:00+00:00`<br>Latest: `2025-11-01 00:00:00+00:00` | Temporal span recorded |

#### First 3 Representative Records

```json
[
  {
    "source_pricing_history_id": "PRC-000001",
    "source_menu_item_id": "DISH-0001",
    "source_restaurant_id": NaN,
    "base_price": 8.5,
    "base_cost": 2.2,
    "effective_from": "2024-07-05 00:00:00+00:00",
    "effective_to": "NaT",
    "change_reason": "Catalog standard baseline price",
    "created_at": "2024-07-05 00:00:00+00:00"
  },
  {
    "source_pricing_history_id": "PRC-000002",
    "source_menu_item_id": "DISH-0002",
    "source_restaurant_id": NaN,
    "base_price": 26.0,
    "base_cost": 9.0,
    "effective_from": "2024-07-05 00:00:00+00:00",
    "effective_to": "NaT",
    "change_reason": "Catalog standard baseline price",
    "created_at": "2024-07-05 00:00:00+00:00"
  },
  {
    "source_pricing_history_id": "PRC-000003",
    "source_menu_item_id": "DISH-0003",
    "source_restaurant_id": NaN,
    "base_price": 16.2,
    "base_cost": 4.84,
    "effective_from": "2024-10-03 00:00:00+00:00",
    "effective_to": "2025-05-27 00:00:00+00:00",
    "change_reason": "Introductory catalog launch pricing",
    "created_at": "2024-10-03 00:00:00+00:00"
  }
]
```

#### Last 3 Representative Records

```json
[
  {
    "source_pricing_history_id": "PRC-001498",
    "source_menu_item_id": "DISH-0148",
    "source_restaurant_id": "REST-0019",
    "base_price": 10.45,
    "base_cost": 1.35,
    "effective_from": "2025-05-31 00:00:00+00:00",
    "effective_to": "2025-07-17 00:00:00+00:00",
    "change_reason": "Holiday promotional dining window",
    "created_at": "2025-05-31 00:00:00+00:00"
  },
  {
    "source_pricing_history_id": "PRC-001499",
    "source_menu_item_id": "DISH-0149",
    "source_restaurant_id": "REST-0020",
    "base_price": 22.57,
    "base_cost": 4.34,
    "effective_from": "2025-10-03 00:00:00+00:00",
    "effective_to": "2025-10-21 00:00:00+00:00",
    "change_reason": "Chef specialty kitchen test rate",
    "created_at": "2025-10-03 00:00:00+00:00"
  },
  {
    "source_pricing_history_id": "PRC-001500",
    "source_menu_item_id": "DISH-0150",
    "source_restaurant_id": "REST-0001",
    "base_price": 229.9,
    "base_cost": 72.24,
    "effective_from": "2025-05-31 00:00:00+00:00",
    "effective_to": "2025-06-14 00:00:00+00:00",
    "change_reason": "Urban flagship location premium tier",
    "created_at": "2025-05-31 00:00:00+00:00"
  }
]
```

---

### 1.8 Table: `promotions`

- **Physical File**: `data/snapshots/competition_benchmark_v1/promotions.parquet`
- **Row Count**: `25`
- **Column Count**: `14`

#### Complete Schema Definition

| # | Column Name | PyArrow Data Type | Nullable | Null Count | Null % | Unique Count |
|---|---|---|---|---|---|---|
| 1 | `source_promotion_id` | `string` | No | 0 | 0.00% | 25 |
| 2 | `campaign_name` | `string` | No | 0 | 0.00% | 11 |
| 3 | `promo_code` | `string` | Yes | 0 | 0.00% | 11 |
| 4 | `discount_type` | `string` | No | 0 | 0.00% | 3 |
| 5 | `discount_value` | `double` | No | 0 | 0.00% | 8 |
| 6 | `start_date` | `date32[day]` | No | 0 | 0.00% | 25 |
| 7 | `end_date` | `date32[day]` | No | 0 | 0.00% | 25 |
| 8 | `minimum_order_amount` | `double` | No | 0 | 0.00% | 2 |
| 9 | `source_category_id` | `string` | Yes | 12 | 48.00% | 5 |
| 10 | `source_menu_item_id` | `string` | Yes | 13 | 52.00% | 12 |
| 11 | `applicable_channel` | `string` | Yes | 17 | 68.00% | 1 |
| 12 | `is_active` | `bool` | No | 0 | 0.00% | 1 |
| 13 | `is_misleading` | `bool` | No | 0 | 0.00% | 2 |
| 14 | `created_at` | `timestamp[us, tz=UTC]` | No | 0 | 0.00% | 25 |

#### Column Statistics & Value Ranges

| Column Name | Metric / Value Bounds | Sample / Top Frequency Distribution |
|---|---|---|
| `source_promotion_id` | N/A | `PROMO-0001`: 1, `PROMO-0002`: 1, `PROMO-0003`: 1 |
| `campaign_name` | N/A | `Appetizer Bonanza BOGO`: 3, `Chef Tasting Experience`: 3, `Holiday Family Bundle`: 3 |
| `promo_code` | N/A | `BOGOAPPS`: 3, `CHEFVIP`: 3, `HOLIDAY20`: 3 |
| `discount_type` | N/A | `Percentage`: 11, `Fixed Amount`: 11, `Buy One Get One`: 3 |
| `discount_value` | Min: 3.50 | Max: 100.00 | Mean: 26.16 | Span: [3.50 .. 100.00] |
| `start_date` | N/A | `2025-01-01`: 1, `2025-01-15`: 1, `2025-01-29`: 1 |
| `end_date` | N/A | `2025-01-31`: 1, `2025-03-01`: 1, `2025-03-30`: 1 |
| `minimum_order_amount` | Min: 15.00 | Max: 25.00 | Mean: 16.20 | Span: [15.00 .. 25.00] |
| `source_category_id` | N/A | `CAT-003`: 3, `CAT-007`: 3, `CAT-001`: 3 |
| `source_menu_item_id` | N/A | `DISH-0007`: 1, `DISH-0013`: 1, `DISH-0019`: 1 |
| `applicable_channel` | N/A | `Delivery Direct`: 8 |
| `is_active` | Min: 1.00 | Max: 1.00 | Mean: 1.00 | Span: [1.00 .. 1.00] |
| `is_misleading` | Min: 0.00 | Max: 1.00 | Mean: 0.12 | Span: [0.00 .. 1.00] |
| `created_at` | Earliest: `2024-12-25 00:00:00+00:00`<br>Latest: `2025-11-26 00:00:00+00:00` | Temporal span recorded |

#### First 3 Representative Records

```json
[
  {
    "source_promotion_id": "PROMO-0001",
    "campaign_name": "Extreme Deep Discount Promo Trap #1",
    "promo_code": "TRAP50",
    "discount_type": "Percentage",
    "discount_value": 50.0,
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "minimum_order_amount": 25.0,
    "source_category_id": "CAT-003",
    "source_menu_item_id": NaN,
    "applicable_channel": NaN,
    "is_active": true,
    "is_misleading": true,
    "created_at": "2024-12-25 00:00:00+00:00"
  },
  {
    "source_promotion_id": "PROMO-0002",
    "campaign_name": "Extreme Deep Discount Promo Trap #2",
    "promo_code": "TRAP100",
    "discount_type": "Percentage",
    "discount_value": 50.0,
    "start_date": "2025-01-15",
    "end_date": "2025-03-01",
    "minimum_order_amount": 25.0,
    "source_category_id": NaN,
    "source_menu_item_id": "DISH-0007",
    "applicable_channel": NaN,
    "is_active": true,
    "is_misleading": true,
    "created_at": "2025-01-08 00:00:00+00:00"
  },
  {
    "source_promotion_id": "PROMO-0003",
    "campaign_name": "Extreme Deep Discount Promo Trap #3",
    "promo_code": "TRAP150",
    "discount_type": "Percentage",
    "discount_value": 50.0,
    "start_date": "2025-01-29",
    "end_date": "2025-03-30",
    "minimum_order_amount": 25.0,
    "source_category_id": "CAT-007",
    "source_menu_item_id": NaN,
    "applicable_channel": "Delivery Direct",
    "is_active": true,
    "is_misleading": true,
    "created_at": "2025-01-22 00:00:00+00:00"
  }
]
```

#### Last 3 Representative Records

```json
[
  {
    "source_promotion_id": "PROMO-0023",
    "campaign_name": "Autumn Harvest Discount",
    "promo_code": "FALLHARVEST",
    "discount_type": "Fixed Amount",
    "discount_value": 5.0,
    "start_date": "2025-11-05",
    "end_date": "2025-12-05",
    "minimum_order_amount": 15.0,
    "source_category_id": "CAT-007",
    "source_menu_item_id": NaN,
    "applicable_channel": NaN,
    "is_active": true,
    "is_misleading": false,
    "created_at": "2025-10-29 00:00:00+00:00"
  },
  {
    "source_promotion_id": "PROMO-0024",
    "campaign_name": "Direct Delivery Incentive",
    "promo_code": "DELIVERFREE",
    "discount_type": "Fixed Amount",
    "discount_value": 4.0,
    "start_date": "2025-11-19",
    "end_date": "2026-01-18",
    "minimum_order_amount": 15.0,
    "source_category_id": NaN,
    "source_menu_item_id": "DISH-0073",
    "applicable_channel": "Delivery Direct",
    "is_active": true,
    "is_misleading": false,
    "created_at": "2025-11-12 00:00:00+00:00"
  },
  {
    "source_promotion_id": "PROMO-0025",
    "campaign_name": "Summer Kickoff Special",
    "promo_code": "SUMMER25",
    "discount_type": "Percentage",
    "discount_value": 15.0,
    "start_date": "2025-12-03",
    "end_date": "2026-01-02",
    "minimum_order_amount": 15.0,
    "source_category_id": "CAT-001",
    "source_menu_item_id": NaN,
    "applicable_channel": NaN,
    "is_active": true,
    "is_misleading": false,
    "created_at": "2025-11-26 00:00:00+00:00"
  }
]
```

---

### 1.9 Table: `ratings`

- **Physical File**: `data/snapshots/competition_benchmark_v1/ratings.parquet`
- **Row Count**: `100,000`
- **Column Count**: `13`

#### Complete Schema Definition

| # | Column Name | PyArrow Data Type | Nullable | Null Count | Null % | Unique Count |
|---|---|---|---|---|---|---|
| 1 | `source_rating_id` | `string` | No | 0 | 0.00% | 100,000 |
| 2 | `source_restaurant_id` | `string` | No | 0 | 0.00% | 20 |
| 3 | `source_order_id` | `string` | Yes | 25,056 | 25.06% | 1,992 |
| 4 | `source_customer_id` | `string` | Yes | 4,949 | 4.95% | 17,818 |
| 5 | `source_menu_item_id` | `string` | Yes | 15,136 | 15.14% | 150 |
| 6 | `rating_score` | `int32` | No | 0 | 0.00% | 5 |
| 7 | `food_rating` | `int32` | Yes | 0 | 0.00% | 5 |
| 8 | `service_rating` | `int32` | Yes | 0 | 0.00% | 5 |
| 9 | `ambiance_rating` | `int32` | Yes | 12,946 | 12.95% | 4 |
| 10 | `review_text` | `string` | Yes | 39,945 | 39.95% | 10 |
| 11 | `rating_timestamp` | `timestamp[us, tz=UTC]` | No | 0 | 0.00% | 75,475 |
| 12 | `is_verified_purchase` | `bool` | No | 0 | 0.00% | 2 |
| 13 | `created_at` | `timestamp[us, tz=UTC]` | No | 0 | 0.00% | 75,475 |

#### Column Statistics & Value Ranges

| Column Name | Metric / Value Bounds | Sample / Top Frequency Distribution |
|---|---|---|
| `source_rating_id` | N/A | `RAT-00000001`: 1, `RAT-00000002`: 1, `RAT-00000003`: 1 |
| `source_restaurant_id` | N/A | `REST-0003`: 6,964, `REST-0006`: 6,861, `REST-0018`: 6,824 |
| `source_order_id` | N/A | `ORD-00000903`: 80, `ORD-00000767`: 76, `ORD-00001265`: 75 |
| `source_customer_id` | N/A | `CUST-00010071`: 117, `CUST-00002305`: 115, `CUST-00001065`: 110 |
| `source_menu_item_id` | N/A | `DISH-0085`: 650, `DISH-0016`: 624, `DISH-0072`: 619 |
| `rating_score` | Min: 1.00 | Max: 5.00 | Mean: 4.07 | Span: [1.00 .. 5.00] |
| `food_rating` | Min: 1.00 | Max: 5.00 | Mean: 3.92 | Span: [1.00 .. 5.00] |
| `service_rating` | Min: 1.00 | Max: 5.00 | Mean: 3.92 | Span: [1.00 .. 5.00] |
| `ambiance_rating` | Min: 2.00 | Max: 5.00 | Mean: 4.24 | Span: [2.00 .. 5.00] |
| `review_text` | N/A | `A regular favorite at this branch.`: 9,084, `Outstanding meal and attentive staff.`: 9,011, `Crispy, hot, and seasoned to perfection.`: 8,999 |
| `rating_timestamp` | Earliest: `2025-01-01 12:04:00+00:00`<br>Latest: `2026-11-20 17:33:45+00:00` | Temporal span recorded |
| `is_verified_purchase` | Min: 0.00 | Max: 1.00 | Mean: 0.75 | Span: [0.00 .. 1.00] |
| `created_at` | Earliest: `2025-01-01 12:04:00+00:00`<br>Latest: `2026-11-20 17:33:45+00:00` | Temporal span recorded |

#### First 3 Representative Records

```json
[
  {
    "source_rating_id": "RAT-00000001",
    "source_restaurant_id": "REST-0005",
    "source_order_id": "ORD-00000003",
    "source_customer_id": "CUST-00001224",
    "source_menu_item_id": "DISH-0121",
    "rating_score": 2,
    "food_rating": 1,
    "service_rating": 3,
    "ambiance_rating": NaN,
    "review_text": "Order took over 45 minutes during peak hours.",
    "rating_timestamp": "2025-08-06 19:18:23+00:00",
    "is_verified_purchase": true,
    "created_at": "2025-08-06 19:18:23+00:00"
  },
  {
    "source_rating_id": "RAT-00000002",
    "source_restaurant_id": "REST-0011",
    "source_order_id": NaN,
    "source_customer_id": "CUST-00009108",
    "source_menu_item_id": "DISH-0025",
    "rating_score": 1,
    "food_rating": 1,
    "service_rating": 2,
    "ambiance_rating": NaN,
    "review_text": NaN,
    "rating_timestamp": "2025-04-17 18:59:00+00:00",
    "is_verified_purchase": false,
    "created_at": "2025-04-17 18:59:00+00:00"
  },
  {
    "source_rating_id": "RAT-00000003",
    "source_restaurant_id": "REST-0012",
    "source_order_id": NaN,
    "source_customer_id": "CUST-00032206",
    "source_menu_item_id": "DISH-0139",
    "rating_score": 5,
    "food_rating": 5,
    "service_rating": 5,
    "ambiance_rating": 5.0,
    "review_text": "Delicious presentation, flavorful and tender.",
    "rating_timestamp": "2025-12-14 19:00:00+00:00",
    "is_verified_purchase": false,
    "created_at": "2025-12-14 19:00:00+00:00"
  }
]
```

#### Last 3 Representative Records

```json
[
  {
    "source_rating_id": "RAT-00099998",
    "source_restaurant_id": "REST-0007",
    "source_order_id": "ORD-00002289",
    "source_customer_id": "CUST-00020779",
    "source_menu_item_id": "DISH-0045",
    "rating_score": 5,
    "food_rating": 5,
    "service_rating": 5,
    "ambiance_rating": 5.0,
    "review_text": "A regular favorite at this branch.",
    "rating_timestamp": "2025-08-19 11:06:43+00:00",
    "is_verified_purchase": true,
    "created_at": "2025-08-19 11:06:43+00:00"
  },
  {
    "source_rating_id": "RAT-00099999",
    "source_restaurant_id": "REST-0010",
    "source_order_id": "ORD-00002290",
    "source_customer_id": "CUST-00043447",
    "source_menu_item_id": "DISH-0150",
    "rating_score": 5,
    "food_rating": 5,
    "service_rating": 4,
    "ambiance_rating": 5.0,
    "review_text": "Outstanding meal and attentive staff.",
    "rating_timestamp": "2025-02-03 18:53:47+00:00",
    "is_verified_purchase": true,
    "created_at": "2025-02-03 18:53:47+00:00"
  },
  {
    "source_rating_id": "RAT-00100000",
    "source_restaurant_id": "REST-0018",
    "source_order_id": "ORD-00000002",
    "source_customer_id": "CUST-00002949",
    "source_menu_item_id": "DISH-0121",
    "rating_score": 5,
    "food_rating": 4,
    "service_rating": 4,
    "ambiance_rating": 5.0,
    "review_text": "A regular favorite at this branch.",
    "rating_timestamp": "2025-10-10 01:54:54+00:00",
    "is_verified_purchase": true,
    "created_at": "2025-10-10 01:54:54+00:00"
  }
]
```

---

### 1.10 Table: `inventory`

- **Physical File**: `data/snapshots/competition_benchmark_v1/inventory.parquet`
- **Row Count**: `3,000`
- **Column Count**: `12`

#### Complete Schema Definition

| # | Column Name | PyArrow Data Type | Nullable | Null Count | Null % | Unique Count |
|---|---|---|---|---|---|---|
| 1 | `source_inventory_id` | `string` | No | 0 | 0.00% | 3,000 |
| 2 | `source_restaurant_id` | `string` | No | 0 | 0.00% | 20 |
| 3 | `ingredient_name` | `string` | No | 0 | 0.00% | 150 |
| 4 | `ingredient_category` | `string` | No | 0 | 0.00% | 6 |
| 5 | `current_stock_quantity` | `double` | No | 0 | 0.00% | 2,687 |
| 6 | `unit_of_measure` | `string` | No | 0 | 0.00% | 4 |
| 7 | `reorder_threshold` | `double` | No | 0 | 0.00% | 2,110 |
| 8 | `reorder_quantity` | `double` | No | 0 | 0.00% | 2,477 |
| 9 | `unit_purchase_cost` | `double` | No | 0 | 0.00% | 19 |
| 10 | `last_restock_date` | `date32[day]` | Yes | 0 | 0.00% | 30 |
| 11 | `created_at` | `timestamp[us, tz=UTC]` | No | 0 | 0.00% | 1 |
| 12 | `updated_at` | `timestamp[us, tz=UTC]` | No | 0 | 0.00% | 1 |

#### Column Statistics & Value Ranges

| Column Name | Metric / Value Bounds | Sample / Top Frequency Distribution |
|---|---|---|
| `source_inventory_id` | N/A | `INV-REST01-0001`: 1, `INV-REST01-0002`: 1, `INV-REST01-0003`: 1 |
| `source_restaurant_id` | N/A | `REST-0001`: 150, `REST-0002`: 150, `REST-0003`: 150 |
| `ingredient_name` | N/A | `Ground Wagyu Beef`: 20, `Prime Ribeye Loins`: 20, `Chicken Breast Free Range`: 20 |
| `ingredient_category` | N/A | `Meat & Poultry`: 1,120, `Produce`: 480, `Dairy`: 420 |
| `current_stock_quantity` | Min: 20.06 | Max: 149.99 | Mean: 85.48 | Span: [20.06 .. 149.99] |
| `unit_of_measure` | N/A | `kg`: 2,300, `L`: 280, `units`: 280 |
| `reorder_threshold` | Min: 6.02 | Max: 45.00 | Mean: 25.65 | Span: [6.02 .. 45.00] |
| `reorder_quantity` | Min: 12.04 | Max: 89.99 | Mean: 51.29 | Span: [12.04 .. 89.99] |
| `unit_purchase_cost` | Min: 0.15 | Max: 38.00 | Mean: 10.83 | Span: [0.15 .. 38.00] |
| `last_restock_date` | N/A | `2025-01-07`: 119, `2025-01-30`: 117, `2025-01-24`: 111 |
| `created_at` | Earliest: `2024-01-01 00:00:00+00:00`<br>Latest: `2024-01-01 00:00:00+00:00` | Temporal span recorded |
| `updated_at` | Earliest: `2024-01-01 00:00:00+00:00`<br>Latest: `2024-01-01 00:00:00+00:00` | Temporal span recorded |

#### First 3 Representative Records

```json
[
  {
    "source_inventory_id": "INV-REST01-0001",
    "source_restaurant_id": "REST-0001",
    "ingredient_name": "Ground Wagyu Beef",
    "ingredient_category": "Meat & Poultry",
    "current_stock_quantity": 35.14,
    "unit_of_measure": "kg",
    "reorder_threshold": 10.54,
    "reorder_quantity": 21.08,
    "unit_purchase_cost": 12.5,
    "last_restock_date": "2025-01-24",
    "created_at": "2024-01-01 00:00:00+00:00",
    "updated_at": "2024-01-01 00:00:00+00:00"
  },
  {
    "source_inventory_id": "INV-REST01-0002",
    "source_restaurant_id": "REST-0001",
    "ingredient_name": "Prime Ribeye Loins",
    "ingredient_category": "Meat & Poultry",
    "current_stock_quantity": 123.83,
    "unit_of_measure": "kg",
    "reorder_threshold": 37.15,
    "reorder_quantity": 74.3,
    "unit_purchase_cost": 24.0,
    "last_restock_date": "2025-01-26",
    "created_at": "2024-01-01 00:00:00+00:00",
    "updated_at": "2024-01-01 00:00:00+00:00"
  },
  {
    "source_inventory_id": "INV-REST01-0003",
    "source_restaurant_id": "REST-0001",
    "ingredient_name": "Chicken Breast Free Range",
    "ingredient_category": "Meat & Poultry",
    "current_stock_quantity": 22.26,
    "unit_of_measure": "kg",
    "reorder_threshold": 6.68,
    "reorder_quantity": 13.36,
    "unit_purchase_cost": 7.2,
    "last_restock_date": "2025-01-15",
    "created_at": "2024-01-01 00:00:00+00:00",
    "updated_at": "2024-01-01 00:00:00+00:00"
  }
]
```

#### Last 3 Representative Records

```json
[
  {
    "source_inventory_id": "INV-REST20-2998",
    "source_restaurant_id": "REST-0020",
    "ingredient_name": "Russet Potatoes Select #8",
    "ingredient_category": "Produce",
    "current_stock_quantity": 139.69,
    "unit_of_measure": "kg",
    "reorder_threshold": 41.91,
    "reorder_quantity": 83.81,
    "unit_purchase_cost": 1.2,
    "last_restock_date": "2025-01-30",
    "created_at": "2024-01-01 00:00:00+00:00",
    "updated_at": "2024-01-01 00:00:00+00:00"
  },
  {
    "source_inventory_id": "INV-REST20-2999",
    "source_restaurant_id": "REST-0020",
    "ingredient_name": "Fresh Asparagus Select #8",
    "ingredient_category": "Produce",
    "current_stock_quantity": 131.64,
    "unit_of_measure": "kg",
    "reorder_threshold": 39.49,
    "reorder_quantity": 78.98,
    "unit_purchase_cost": 4.5,
    "last_restock_date": "2025-01-20",
    "created_at": "2024-01-01 00:00:00+00:00",
    "updated_at": "2024-01-01 00:00:00+00:00"
  },
  {
    "source_inventory_id": "INV-REST20-3000",
    "source_restaurant_id": "REST-0020",
    "ingredient_name": "Roma Tomatoes Select #8",
    "ingredient_category": "Produce",
    "current_stock_quantity": 60.52,
    "unit_of_measure": "kg",
    "reorder_threshold": 18.16,
    "reorder_quantity": 36.31,
    "unit_purchase_cost": 2.2,
    "last_restock_date": "2025-01-24",
    "created_at": "2024-01-01 00:00:00+00:00",
    "updated_at": "2024-01-01 00:00:00+00:00"
  }
]
```

---

### 1.11 Table: `wastage`

- **Physical File**: `data/snapshots/competition_benchmark_v1/wastage.parquet`
- **Row Count**: `50,000`
- **Column Count**: `11`

#### Complete Schema Definition

| # | Column Name | PyArrow Data Type | Nullable | Null Count | Null % | Unique Count |
|---|---|---|---|---|---|---|
| 1 | `source_wastage_id` | `string` | No | 0 | 0.00% | 50,000 |
| 2 | `source_restaurant_id` | `string` | No | 0 | 0.00% | 20 |
| 3 | `source_menu_item_id` | `string` | Yes | 33,334 | 66.67% | 150 |
| 4 | `ingredient_name` | `string` | Yes | 0 | 0.00% | 8 |
| 5 | `wastage_timestamp` | `timestamp[us, tz=UTC]` | No | 0 | 0.00% | 29,906 |
| 6 | `quantity_lost` | `double` | No | 0 | 0.00% | 971 |
| 7 | `unit_of_measure` | `string` | No | 0 | 0.00% | 3 |
| 8 | `cost_loss_amount` | `double` | No | 0 | 0.00% | 3,409 |
| 9 | `wastage_reason` | `string` | No | 0 | 0.00% | 6 |
| 10 | `reported_by` | `string` | Yes | 0 | 0.00% | 5 |
| 11 | `created_at` | `timestamp[us, tz=UTC]` | No | 0 | 0.00% | 29,906 |

#### Column Statistics & Value Ranges

| Column Name | Metric / Value Bounds | Sample / Top Frequency Distribution |
|---|---|---|
| `source_wastage_id` | N/A | `WASTE-00000001`: 1, `WASTE-00000002`: 1, `WASTE-00000003`: 1 |
| `source_restaurant_id` | N/A | `REST-0011`: 2,576, `REST-0015`: 2,564, `REST-0003`: 2,564 |
| `source_menu_item_id` | N/A | `DISH-0104`: 144, `DISH-0066`: 140, `DISH-0090`: 139 |
| `ingredient_name` | N/A | `Artisan Burger Buns`: 6,334, `Ground Wagyu Beef`: 6,323, `Fresh Atlantic Salmon`: 6,305 |
| `wastage_timestamp` | Earliest: `2025-01-01 21:00:00+00:00`<br>Latest: `2025-12-31 22:57:00+00:00` | Temporal span recorded |
| `quantity_lost` | Min: 0.30 | Max: 10.00 | Mean: 3.57 | Span: [0.30 .. 10.00] |
| `unit_of_measure` | N/A | `kg`: 25,025, `L`: 12,530, `units`: 12,445 |
| `cost_loss_amount` | Min: 0.20 | Max: 157.50 | Mean: 26.51 | Span: [0.20 .. 157.50] |
| `wastage_reason` | N/A | `Expired`: 19,894, `Over-preparation`: 12,394, `Cooking Error`: 7,582 |
| `reported_by` | N/A | `Sous Chef Maya`: 10,000, `Manager Elena`: 10,000, `Cook Sam`: 10,000 |
| `created_at` | Earliest: `2025-01-01 21:00:00+00:00`<br>Latest: `2025-12-31 22:57:00+00:00` | Temporal span recorded |

#### First 3 Representative Records

```json
[
  {
    "source_wastage_id": "WASTE-00000001",
    "source_restaurant_id": "REST-0001",
    "source_menu_item_id": NaN,
    "ingredient_name": "Heavy Cream 36%",
    "wastage_timestamp": "2025-01-09 22:06:00+00:00",
    "quantity_lost": 4.34,
    "unit_of_measure": "L",
    "cost_loss_amount": 18.23,
    "wastage_reason": "Cooking Error",
    "reported_by": "Sous Chef Maya",
    "created_at": "2025-01-09 22:06:00+00:00"
  },
  {
    "source_wastage_id": "WASTE-00000002",
    "source_restaurant_id": "REST-0013",
    "source_menu_item_id": NaN,
    "ingredient_name": "Ground Wagyu Beef",
    "wastage_timestamp": "2025-06-11 22:05:00+00:00",
    "quantity_lost": 2.3,
    "unit_of_measure": "kg",
    "cost_loss_amount": 28.75,
    "wastage_reason": "Expired",
    "reported_by": "Manager Elena",
    "created_at": "2025-06-11 22:05:00+00:00"
  },
  {
    "source_wastage_id": "WASTE-00000003",
    "source_restaurant_id": "REST-0007",
    "source_menu_item_id": "DISH-0122",
    "ingredient_name": "Fresh Atlantic Salmon",
    "wastage_timestamp": "2025-06-16 22:33:00+00:00",
    "quantity_lost": 2.63,
    "unit_of_measure": "kg",
    "cost_loss_amount": 47.34,
    "wastage_reason": "Over-preparation",
    "reported_by": "Cook Sam",
    "created_at": "2025-06-16 22:33:00+00:00"
  }
]
```

#### Last 3 Representative Records

```json
[
  {
    "source_wastage_id": "WASTE-00049998",
    "source_restaurant_id": "REST-0012",
    "source_menu_item_id": "DISH-0142",
    "ingredient_name": "Chef Clam Chowder Soup",
    "wastage_timestamp": "2025-07-15 22:52:00+00:00",
    "quantity_lost": 5.3,
    "unit_of_measure": "L",
    "cost_loss_amount": 26.5,
    "wastage_reason": "Expired",
    "reported_by": "Cook Sam",
    "created_at": "2025-07-15 22:52:00+00:00"
  },
  {
    "source_wastage_id": "WASTE-00049999",
    "source_restaurant_id": "REST-0004",
    "source_menu_item_id": NaN,
    "ingredient_name": "Fresh Mozzarella",
    "wastage_timestamp": "2025-08-23 21:43:00+00:00",
    "quantity_lost": 3.35,
    "unit_of_measure": "kg",
    "cost_loss_amount": 26.13,
    "wastage_reason": "Expired",
    "reported_by": "Line Cook Tyler",
    "created_at": "2025-08-23 21:43:00+00:00"
  },
  {
    "source_wastage_id": "WASTE-00050000",
    "source_restaurant_id": "REST-0001",
    "source_menu_item_id": NaN,
    "ingredient_name": "Ground Wagyu Beef",
    "wastage_timestamp": "2025-04-20 21:21:00+00:00",
    "quantity_lost": 5.26,
    "unit_of_measure": "kg",
    "cost_loss_amount": 65.75,
    "wastage_reason": "Expired",
    "reported_by": "Chef Carlos",
    "created_at": "2025-04-20 21:21:00+00:00"
  }
]
```

---

## Part 2: Global Dataset Inspection

### A. Dataset Size & Complete Reconciliation

The following table reconciles every record across raw storage, cleaned analytical storage, and quarantine isolation storage:

| Domain Table | Raw Snapshot Rows | Cleaned Rows | Quarantined Rows | Reconciliation Status | Cleanliness % |
|---|---|---|---|---|---|
| `customers` | 50,000 | 50,000 | 0 | `EXACT MATCH` | 100.00% |
| `orders` | 100,508 | 99,954 | 554 | `EXACT MATCH` | 99.45% |
| `order_items` | 1,006,051 | 997,561 | 8,490 | `EXACT MATCH` | 99.16% |
| `menu_items` | 150 | 150 | 0 | `EXACT MATCH` | 100.00% |
| `menu_categories` | 10 | 10 | 0 | `EXACT MATCH` | 100.00% |
| `restaurants` | 20 | 20 | 0 | `EXACT MATCH` | 100.00% |
| `pricing_history` | 1,500 | 1,500 | 0 | `EXACT MATCH` | 100.00% |
| `promotions` | 25 | 25 | 0 | `EXACT MATCH` | 100.00% |
| `ratings` | 100,000 | 100,000 | 0 | `EXACT MATCH` | 100.00% |
| `inventory` | 3,000 | 3,000 | 0 | `EXACT MATCH` | 100.00% |
| `wastage` | 50,000 | 50,000 | 0 | `EXACT MATCH` | 100.00% |
| **TOTAL** | **1,311,264** | **1,302,220** | **9,044** | `EXACT MATCH` | **99.31%** |

Mathematical verification equality holds across all tables:
$$\text{Total Raw Records (1,311,264)} = \text{Total Clean Records (1,302,220)} + \text{Total Quarantined Records (9,044)}$$

### B. Data Quality & Verified Injected Anomalies

The generator deliberately introduced controlled operational anomalies to evaluate data quality resilience. Every planned anomaly condition was confirmed present on disk:

1. **Guest Checkout Orders (Missing Customer IDs)**:
   - Identified **10,070 orders** (10.02% of orders) where `source_customer_id` is `null`.
   - Preserved in `cleaned/orders.parquet` as legitimate business activity (guest diners).
2. **Incomplete Customer Contact Profiles**:
   - Identified **7,524 customers** (15.05% of customers) missing email or phone number.
3. **Missing Customer Review Commentary**:
   - Identified **39,945 ratings** (39.95% of ratings) where `review_text` is `null` (star rating provided without text).
4. **Duplicate Orders Quarantined**:
   - Identified and isolated **508 duplicate order headers** into `orders_quarantine.parquet`.
5. **Duplicate Order Items Quarantined**:
   - Identified and isolated **5,027 duplicate line items** into `order_items_quarantine.parquet`.
6. **Future Timestamps Quarantined**:
   - Identified and isolated **46 orders** recorded with timestamps beyond the 2025 cutoff (dates between May 2026 and May 2027).
7. **Invalid Negative Prices Quarantined**:
   - Identified and isolated **1,964 order items** where `unit_price_at_sale < 0.00`.
8. **Invalid Zero Quantities Quarantined**:
   - Identified and isolated **1,024 order items** where `quantity == 0`.
9. **Orphaned Order Items (Cascading Quarantine)**:
   - Identified and isolated **475 order lines** whose parent order was quarantined, preventing orphaned transaction lines in clean tables.
10. **Legitimate Cancelled and Voided Orders Preserved**:
   - Raw Orders: `Completed`: 96,478, `Cancelled`: 3,516, `Voided`: 514.
   - Cleaned Orders: `Completed`: 95,948, `Cancelled`: 3,497, `Voided`: 509.
   - Verified that cancelled orders (3.50%) and voided orders (0.51%) remain in clean storage for cancellation prediction and operational loss modeling.
11. **Rating Collapse Anomalies**:
   - Identified localized rating collapse on targeted dishes following recipe cost modifications:
     - Lowest rated dish: `DISH-0008` (Average rating: `3.75` across 582 ratings).
     - Comparison against top dish: `DISH-0014` (Average rating: `4.23` across 545 ratings).
12. **Promotion Trap Campaigns**:
   - Verified 3 campaigns configured with `is_misleading = True` yielding high volume but negative contribution margins:
     - `PROMO-0001`: "Extreme Deep Discount Promo Trap #1" (Percentage discount of 50.0%)
     - `PROMO-0002`: "Extreme Deep Discount Promo Trap #2" (Percentage discount of 50.0%)
     - `PROMO-0003`: "Extreme Deep Discount Promo Trap #3" (Percentage discount of 50.0%)

### C. Temporal Distribution & Split Verification

- **Cleaned Orders Minimum Timestamp**: `2025-01-01 11:09:01+00:00`
- **Cleaned Orders Maximum Timestamp**: `2025-12-31 22:45:12+00:00`

#### Monthly Order Distribution (Cleaned Orders)

| Month | Order Count | Volume Share % | Seasonality Index |
|---|---|---|---|
| `2025-01` | 8,560 | 8.56% | 1.028 |
| `2025-02` | 7,614 | 7.62% | 0.914 |
| `2025-03` | 8,520 | 8.52% | 1.023 |
| `2025-04` | 8,130 | 8.13% | 0.976 |
| `2025-05` | 8,526 | 8.53% | 1.024 |
| `2025-06` | 8,252 | 8.26% | 0.991 |
| `2025-07` | 8,532 | 8.54% | 1.024 |
| `2025-08` | 8,497 | 8.50% | 1.020 |
| `2025-09` | 8,199 | 8.20% | 0.984 |
| `2025-10` | 8,406 | 8.41% | 1.009 |
| `2025-11` | 8,230 | 8.23% | 0.988 |
| `2025-12` | 8,488 | 8.49% | 1.019 |

#### Chronological 4-Way Machine Learning Split

| Split Window | Calendar Date Range | Order Count | Horizon Share % | Target Invariant |
|---|---|---|---|---|
| **TRAIN** | `2025-01-01` → `2025-08-31` | **66,631** | **66.66%** | Expected: 66,631 (66.66%) |
| **VALIDATION** | `2025-09-01` → `2025-10-31` | **16,605** | **16.61%** | Expected: 16,605 (16.61%) |
| **TEST** | `2025-11-01` → `2025-11-30` | **8,230** | **8.23%** | Expected: 8,230 (8.23%) |
| **UNSEEN_COMPARISON** | `2025-12-01` → `2025-12-31` | **8,488** | **8.49%** | Expected: 8,488 (8.49%) |
| **TOTAL CLEANED** | `2025-01-01` → `2025-12-31` | **99,954** | **100.00%** | Full 365 Days History |

### D. Relationships & Referential Integrity

Referential foreign key integrity checks were executed across all eleven clean tables:

| Relationship Tested | Cardinality Expectation | Unmatched Records | Verification Status |
|---|---|---|---|
| `customers` $\to$ `orders` | 1 to Many (non-guest) | 0 | `PERFECT (0 orphans)` |
| `orders` $\to$ `order_items` | 1 to Many | 0 | `PERFECT (0 orphans)` |
| `menu_categories` $\to$ `menu_items` | 1 to Many | 0 | `PERFECT (0 orphans)` |
| `menu_items` $\to$ `order_items` | 1 to Many | 0 | `PERFECT (0 orphans)` |
| `restaurants` $\to$ `orders` | 1 to Many | 0 | `PERFECT (0 orphans)` |
| `menu_items` $\to$ `pricing_history` | 1 to Many | 0 | `PERFECT (0 orphans)` |
| `restaurants` $\to$ `inventory` | 1 to Many | 0 | `PERFECT (0 orphans)` |
| `menu_items` $\to$ `wastage` | 1 to Many | 0 | `PERFECT (0 orphans)` |
| `restaurants` $\to$ `ratings` | 1 to Many | 0 | `PERFECT (0 orphans)` |
| `customers` $\to$ `ratings` | 1 to Many (registered) | 0 | `PERFECT (0 orphans)` |
| `promotions` $\to$ `order_items` | 1 to Many (promo sales) | 0 | `PERFECT (0 orphans)` |

- **Orders Without Line Items**: `0` (Every order has $\ge 1$ item line).
- **Dishes Without Pricing History**: `0` (Every menu item has $\ge 1$ SCD Type 2 price record).

### E. Financial Consistency Verification

Financial formulas mandated by the dataset contract were tested across all **997,561 clean order items** and **99,954 clean orders**:

1. **Line Net Revenue Formula**:
   $$\text{line\_net\_revenue} = (\text{quantity} \times \text{unit\_price\_at\_sale}) - \text{line\_discount}$$
   - Maximum Observed Absolute Error: `5.68e-14` (pure floating point epsilon)
   - Mismatches Exceeding $0.01: **0** (0% error)
   - Range: Min $0.00 to Max $627.00

2. **Line Contribution Margin Formula**:
   $$\text{line\_contribution\_margin} = \text{line\_net\_revenue} - (\text{quantity} \times \text{unit\_cost\_at\_sale})$$
   - Maximum Observed Absolute Error: `5.68e-14`
   - Mismatches Exceeding $0.01: **0** (0% error)
   - Range: Min $-5.00 to Max $420.60
   - Intentionally Negative Margin Lines (Promotion Traps): **9,471 lines** (0.95% of items)

3. **Order Total Settlement Formula**:
   $$\text{total\_amount} = \text{subtotal\_amount} - \text{discount\_amount} + \text{tax\_amount} + \text{tip\_amount}$$
   - Maximum Observed Absolute Error: `2.27e-13`
   - Mismatches Exceeding $0.01: **0** (0% error)

### F. Business Realism & Enterprise Complexity

The dataset demonstrates realistic restaurant operational dynamics:

- **Day of Week Volume**: Weekday volume: **57.52%** (Mon-Thu), Weekend volume: **42.48%** (Fri-Sun). Strong weekend surge pattern.
- **Intraday Peak Hours**: Lunch Rush (12:00-14:00): **28.20%**, Dinner Rush (18:00-21:00): **48.22%**. Total peak concentration = 76.42% of daily volume.
- **Dining Category Distribution**:
  - `Fast Casual`: 29.20% of orders
  - `Casual Dining`: 28.88% of orders
  - `Fine Dining`: 25.22% of orders
  - `Express Kiosk`: 16.71% of orders
- **Customer Spend Concentration (Pareto Principle)**:
  - Top 5% Champions generate **21.17%** of total customer revenue.
  - Top 20% Loyalists generate **51.02%** of total customer revenue.
- **Customer Churn Dynamics**:
  - **19,412 customers** (55.07%) have had zero transactions in the final 90 days of the year, providing a rich target for churn prediction models.
- **Boston Consulting Group (BCG) Menu Matrix Quadrants**:
  - `Stars` (High Volume, High Margin): **32 items**
  - `Plowhorses` (High Volume, Low Margin): **43 items**
  - `Puzzles` (Low Volume, High Margin): **43 items**
  - `Dogs` (Low Volume, Low Margin): **32 items**
- **Kitchen Wastage Log Breakdown**:
  - `Expired`: 19,894 logs (39.79%)
  - `Over-preparation`: 12,394 logs (24.79%)
  - `Cooking Error`: 7,582 logs (15.16%)
  - `Equipment Failure`: 4,969 logs (9.94%)
  - `Spillage`: 2,587 logs (5.17%)
  - `Customer Returned`: 2,574 logs (5.15%)

### G. SRS Requirement Traceability Matrix

| SRS Requirement Target | Required Benchmark | Evidence in Actual Dataset | Status | Operational Notes |
|---|---|---|---|---|
| **Order Lines Volume** | $\ge 1,000,000$ order items | `1,006,051` raw, `997,561` clean | **SATISFIED** | Average 10.0 line items per order |
| **Orders Header Volume** | $\ge 100,000$ unique orders | `100,508` raw, `99,954` clean | **SATISFIED** | Distributed across 20 locations and 365 days |
| **Customer Repository** | $\ge 50,000$ customers | `50,000` customer profiles | **SATISFIED** | Captures Pareto spend and churn behavior |
| **Menu Catalog Size** | $\ge 150$ menu items | `150` active items | **SATISFIED** | 15 items per category across 10 categories |
| **Culinary Categories** | $\ge 10$ menu categories | `10` canonical categories | **SATISFIED** | 10 canonical restaurant food groups |
| **Restaurant Locations** | $\ge 20$ restaurant units | `20` branch locations | **SATISFIED** | Flagship, Casual, and Kiosk units |
| **Historical Horizon** | $\ge 12$ months history | 365 days (`2025-01-01` to `2025-12-31`) | **SATISFIED** | Exact calendar year 2025 |
| **Customer Ratings** | $\ge 100,000$ ratings | `100,000` rating events | **SATISFIED** | Multi-dimensional star ratings (1-5) |
| **Inventory Balances** | $\ge 3,000$ ingredient rows | `3,000` stock records | **SATISFIED** | 150 tracked ingredients across 20 units |
| **Wastage Loss Logs** | $\ge 50,000$ wastage entries | `50,000` discard logs | **SATISFIED** | 6 operational loss reasons categorized |
| **Historical Pricing** | SCD Type 2 price tracking | `1,500` price records | **SATISFIED** | 10 price records per menu item |
| **Promotions & Traps** | Marketing campaign tracking | `25` promotions | **SATISFIED** | Includes 3 negative margin trap campaigns |
| **Data Quality Pipeline** | Automated anomaly isolation | 9,044 quarantined rows, 99.31% clean | **SATISFIED** | Detailed in `quality_report.json` |
| **Chronological Split** | 4-way time-aware ML split | TRAIN (67%), VAL (17%), TEST (8%), UNSEEN (8%) | **SATISFIED** | Enforced in `split_manifest.json` |
| **Dual-Pipeline Ready** | Independent Spark & Python | Clean Parquet tables stored in `data/cleaned/` | **SATISFIED** | Zero shared state; native columnar ingestion |

### H. Parquet Storage Structure & Optimization

| Table Parquet File | Disk Size (Bytes) | Disk Size (MB) | Compression | Partitioning | Ingestion Suitability |
|---|---|---|---|---|---|
| `customers.parquet` | 1,620,083 | 1.55 MB | Snappy | Flat file | Spark & Pandas compatible |
| `inventory.parquet` | 73,165 | 0.07 MB | Snappy | Flat file | Spark & Pandas compatible |
| `menu_categories.parquet` | 2,464 | 0.00 MB | Snappy | Flat file | Spark & Pandas compatible |
| `menu_items.parquet` | 10,248 | 0.01 MB | Snappy | Flat file | Spark & Pandas compatible |
| `order_items.parquet` | 15,354,196 | 14.64 MB | Snappy | Flat file | Spark & Pandas compatible |
| `orders.parquet` | 5,162,475 | 4.92 MB | Snappy | Flat file | Spark & Pandas compatible |
| `pricing_history.parquet` | 33,815 | 0.03 MB | Snappy | Flat file | Spark & Pandas compatible |
| `promotions.parquet` | 5,349 | 0.01 MB | Snappy | Flat file | Spark & Pandas compatible |
| `ratings.parquet` | 2,923,809 | 2.79 MB | Snappy | Flat file | Spark & Pandas compatible |
| `restaurants.parquet` | 5,651 | 0.01 MB | Snappy | Flat file | Spark & Pandas compatible |
| `wastage.parquet` | 1,196,111 | 1.14 MB | Snappy | Flat file | Spark & Pandas compatible |

- **Total Raw Parquet Footprint**: **~29.08 MB** (compressed columnar Snappy).
- **Suitability for Apache Spark**: Parquet files conform to Apache Arrow schemas, supporting vectorization, predicate pushdown, and partition pruning.
- **Suitability for Pandas / Scikit-Learn**: Columnar layout allows fast partial column projection and memory-efficient loading via PyArrow and DuckDB.
- **Raw Data Immutability**: Read-only filesystem permissions guarantee that source snapshots remain pristine throughout all downstream training cycles.

### I. Final Assessment

#### 1. Confirmed Working
- The dataset generator has successfully synthesized all 11 tables satisfying every SRS scale threshold.
- The data quality profiler and cleaner executed without error, isolating 9,044 defective rows into quarantine and producing 1,302,220 clean records.
- 100% referential integrity across all relationships with zero orphaned lines in the cleaned dataset.
- 100% financial consistency across revenue, margin, and order settlement calculations.
- The 4-way chronological split is strictly preserved across the 2025 calendar year.

#### 2. Key Observations
- Injected anomalies (duplicate keys, future dates, negative prices, zero quantities) successfully simulated real-world operational challenges without breaking data integrity.
- The dataset exhibits authentic business clustering: Pareto customer spending, bimodal dining hours, weekend surges, and BCG menu quadrants.
- Quarantining defective orders cleanly cascaded to child order items, ensuring that the clean transaction dataset is pristine and ready for machine learning.

#### 3. Matters Requiring Attention Before Phase 3
- Downstream feature engineering pipelines (Phase 3: Apache Spark, Phase 4: Python Data Science) must strictly read from `data/cleaned/competition_benchmark_v1/`, never directly from raw snapshots.
- Realized sales revenue aggregations must filter for `order_status == 'Completed'`, while cancellation risk models should ingest `order_status IN ('Cancelled', 'Voided')`.
- Feature engineering must adhere to the chronological cutoff timestamps defined in `split_manifest.json` to prevent future data leakage.

#### 4. Data Risks or Inconsistencies
- **Zero structural risks or inconsistencies detected.**
- The previous apparent count discrepancy (1,311,244 vs 1,311,264) was conclusively resolved as an omission of `restaurants` (20 rows) in earlier chat prose; all underlying Parquet files and specification documents are 100% consistent at **1,311,264 records**.