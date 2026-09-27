/**
 * Core TypeScript definitions for DineIQ Analytics frontend.
 */

export interface HealthStatus {
  status: 'ok' | 'degraded' | 'error';
  environment: string;
  version: string;
  database: string;
  timestamp: string;
}

export interface ErrorDetail {
  loc?: string[];
  msg: string;
  type?: string;
}

export interface ErrorPayload {
  code: string;
  message: string;
  details: ErrorDetail[];
}

export interface ErrorEnvelope {
  error: ErrorPayload;
}

export interface DataEnvelope<T> {
  data: T;
  meta?: Record<string, unknown>;
}

export interface AnalyticsStatus {
  marts_available: boolean;
  spark_pipeline_marts: boolean;
  python_pipeline_marts: boolean;
  comparison_marts: boolean;
  marts_directory: string;
}

export interface GlobalFilterOptions {
  locations: { id: string; name: string; city: string; type: string }[];
  categories: { id: string; name: string }[];
  channels: string[];
  segments: string[];
  classifications: string[];
}

export interface ExecutiveSummaryKPIs {
  total_revenue: number;
  total_orders: number;
  average_order_value: number;
  contribution_margin: number;
  margin_percentage: number;
  total_waste_cost: number;
  waste_to_revenue_ratio: number;
  active_customers: number;
  detected_anomalies_count: number;
  pipeline_status: string;
  marts_loaded: number;
}

export interface MenuItemData {
  menu_item_id: string;
  restaurant_id: string;
  item_name: string;
  category_name: string;
  current_base_price: number;
  current_base_cost: number;
  total_quantity: number;
  gross_revenue: number;
  contribution_margin: number;
  profitability_pct: number;
  classification: 'Profit Driver' | 'Volume Driver' | 'Hidden Opportunity' | 'Low Performer';
  composite_score: number;
  demand_score: number;
  profitability_score: number;
  customer_signal_score: number;
  wastage_health_score: number;
  sales_trend_score: number;
  promotion_independence_score: number;
  flags: {
    high_selling_loss_making: boolean;
    profitable_rarely_purchased: boolean;
    popular_high_wastage: boolean;
    high_rating_low_profitability: boolean;
    low_rating_high_sales: boolean;
    promotion_dependent: boolean;
    weekend_only_pattern: boolean;
    seasonal_item: boolean;
    location_divergence: boolean;
  };
}

export interface MenuSummaryResponse {
  items: MenuItemData[];
  total_count: number;
  classification_counts: Record<string, number>;
}

export interface CustomerData {
  customer_id: string;
  customer_name: string;
  loyalty_tier: string;
  preferred_channel: string;
  home_city: string;
  frequency: number;
  monetary_value: number;
  recency_days: number;
  rfm_segment: 'Champions' | 'Loyal' | 'At Risk' | 'Lost';
  churn_probability?: number | null;
}

export interface CustomerSummaryResponse {
  customers: CustomerData[];
  total_count: number;
  segment_distribution: Record<string, number>;
}

export interface SalesOperationsResponse {
  peak_hourly_heatmap: { day_of_week: string; hour_of_day: number; total_orders: number }[];
  channel_breakdown: { channel: string; total_orders: number; net_revenue: number; contribution_margin: number }[];
  locations: {
    source_restaurant_id: string;
    location_name: string;
    city: string;
    dining_type: string;
    gross_revenue: number;
    total_orders: number;
    contribution_margin: number;
    total_waste_cost: number;
    margin_pct: number;
  }[];
}

export interface DemandPricingResponse {
  demand_forecast_curve: {
    week_start_date: string;
    split: string;
    actual_quantity: number;
    predicted_quantity: number;
    absolute_error: number;
  }[];
  pricing_items: {
    source_menu_item_id: string;
    item_name: string;
    base_price: number;
    pre_price: number;
    post_price: number;
    pre_quantity: number;
    post_quantity: number;
    elasticity: number | null;
    sensitivity_class: string;
  }[];
  elasticity_distribution: Record<string, number>;
}

export interface WastageInventoryResponse {
  reasons: { primary_reason: string; waste_cost: number; waste_quantity: number }[];
  high_risk_items: {
    source_menu_item_id: string;
    item_name: string;
    waste_cost: number;
    waste_quantity: number;
    sold_quantity: number;
  }[];
  weekly_trend: { calendar_year: number; calendar_week: number; waste_cost: number; waste_quantity: number }[];
}

export interface PromotionsBasketResponse {
  promotions: {
    source_promotion_id: string;
    campaign_name: string;
    discount_type: string;
    units_sold: number;
    net_revenue: number;
    total_discount: number;
    contribution_margin: number;
    is_promotion_trap: boolean;
  }[];
  market_basket_pairs: {
    item_a_id: string;
    item_a_name: string;
    item_b_id: string;
    item_b_name: string;
    co_occurrence_count: number;
    support_ab: number;
    confidence_a_to_b: number;
    lift: number;
  }[];
}

export interface RatingsAnomaliesResponse {
  sales_anomalies: {
    source_restaurant_id: string;
    order_date: string;
    daily_orders: number;
    daily_revenue: number;
    rolling_mean_revenue: number | null;
    z_score_revenue: number | null;
    anomaly_type: string;
    location_name: string;
    city: string;
  }[];
  rating_anomalies: {
    source_menu_item_id: string;
    item_name: string;
    source_restaurant_id: string;
    calendar_week: number;
    rating_count: number;
    mean_rating: number;
    negative_rating_rate: number;
    anomaly_reason: string;
  }[];
}

export interface ComparisonArenaResponse {
  arena_overview: {
    overall_agreement_pct: number;
    demand_forecast?: {
      agreement_pct: number;
      total_records_compared: number;
      spark_wins: boolean;
      metrics_comparison: {
        spark: { rmse: number; mae: number };
        python: { rmse: number; mae: number };
      };
    };
    wastage_risk?: {
      agreement_pct: number;
      total_records_compared: number;
      spark_wins: boolean;
      metrics_comparison: {
        spark: { accuracy: number };
        python: { accuracy: number };
      };
    };
    churn_risk?: {
      agreement_pct: number;
      total_records_compared: number;
      spark_wins: boolean;
      metrics_comparison: {
        spark: { accuracy: number };
        python: { accuracy: number };
      };
    };
    customer_segmentation?: {
      agreement_pct: number;
      total_customers_compared: number;
      spark_wins: boolean | null;
      segment_agreement_breakdown: { segment_label: string; python_segment_label: string; count: number }[];
    };
  };
  selected_task: string;
  comparison_samples: Record<string, unknown>[];
}

export interface RecommendationItem {
  id: string;
  domain: string;
  target: string;
  observation: string;
  evidence: string;
  interpretation: string;
  recommendation: string;
  priority: 'Critical' | 'High' | 'Medium' | 'Low';
  expected_impact: string;
}

export interface WhatIfRequestPayload {
  item_id: string;
  price_change_pct: number;
  discount_change_pct: number;
  waste_reduction_pct: number;
}

export interface WhatIfResponse {
  status: 'ESTIMATE';
  item_id: string;
  item_name: string;
  parameters: {
    price_change_pct: number;
    discount_change_pct: number;
    waste_reduction_pct: number;
    elasticity_applied: number;
  };
  baseline: {
    base_price: number;
    base_cost: number;
    base_volume: number;
    revenue: number;
    contribution_margin: number;
  };
  estimated_outcome: {
    estimated_price: number;
    estimated_volume: number;
    estimated_revenue: number;
    estimated_contribution_margin: number;
    revenue_delta: number;
    margin_delta: number;
    volume_delta_pct: number;
  };
  disclaimer: string;
}
