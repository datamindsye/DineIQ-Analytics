/**
 * API client service connecting DineIQ React frontend to FastAPI backend.
 */

import type {
  AnalyticsStatus,
  ComparisonArenaResponse,
  CustomerSummaryResponse,
  DataEnvelope,
  DemandPricingResponse,
  ExecutiveSummaryKPIs,
  GlobalFilterOptions,
  HealthStatus,
  MenuSummaryResponse,
  PromotionsBasketResponse,
  RatingsAnomaliesResponse,
  RecommendationItem,
  SalesOperationsResponse,
  WastageInventoryResponse,
  WhatIfRequestPayload,
  WhatIfResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(message: string, code: string = 'API_ERROR', status: number = 500) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
  }
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem('dineiq_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      let errorCode = 'REQUEST_FAILED';
      try {
        const errorData = await response.json();
        if (errorData?.error?.message) {
          errorMessage = errorData.error.message;
          errorCode = errorData.error.code || errorCode;
        } else if (errorData?.detail) {
          errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
        }
      } catch {
        // Body not JSON
      }
      throw new ApiError(errorMessage, errorCode, response.status);
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(
      error instanceof Error ? error.message : 'Network connection failure',
      'NETWORK_ERROR',
      0
    );
  }
}

export const apiService = {
  getLiveness: (): Promise<HealthStatus> => request<HealthStatus>('/health'),
  getReadiness: (): Promise<HealthStatus> => request<HealthStatus>('/health/ready'),

  getAnalyticsStatus: async (): Promise<AnalyticsStatus> => {
    const res = await request<DataEnvelope<AnalyticsStatus>>('/analytics/status');
    return res.data;
  },

  getFilters: async (): Promise<GlobalFilterOptions> => {
    const res = await request<DataEnvelope<GlobalFilterOptions>>('/analytics/filters');
    return res.data;
  },

  getExecutiveSummary: async (): Promise<ExecutiveSummaryKPIs> => {
    const res = await request<DataEnvelope<ExecutiveSummaryKPIs>>('/analytics/executive-summary');
    return res.data;
  },

  getMenuIntelligence: async (params?: {
    category_id?: string;
    restaurant_id?: string;
    classification?: string;
    flag?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<MenuSummaryResponse> => {
    const q = new URLSearchParams();
    if (params?.category_id) q.set('category_id', params.category_id);
    if (params?.restaurant_id) q.set('restaurant_id', params.restaurant_id);
    if (params?.classification) q.set('classification', params.classification);
    if (params?.flag) q.set('flag', params.flag);
    if (params?.search) q.set('search', params.search);
    if (params?.limit) q.set('limit', String(params.limit));
    if (params?.offset) q.set('offset', String(params.offset));

    const res = await request<DataEnvelope<MenuSummaryResponse>>(`/analytics/menu?${q.toString()}`);
    return res.data;
  },

  getCustomerIntelligence: async (params?: {
    segment?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<CustomerSummaryResponse> => {
    const q = new URLSearchParams();
    if (params?.segment) q.set('segment', params.segment);
    if (params?.search) q.set('search', params.search);
    if (params?.limit) q.set('limit', String(params.limit));
    if (params?.offset) q.set('offset', String(params.offset));

    const res = await request<DataEnvelope<CustomerSummaryResponse>>(`/analytics/customers?${q.toString()}`);
    return res.data;
  },

  getSalesOperations: async (params?: { restaurant_id?: string }): Promise<SalesOperationsResponse> => {
    const q = new URLSearchParams();
    if (params?.restaurant_id) q.set('restaurant_id', params.restaurant_id);

    const res = await request<DataEnvelope<SalesOperationsResponse>>(`/analytics/sales?${q.toString()}`);
    return res.data;
  },

  getDemandPricing: async (params?: {
    menu_item_id?: string;
    restaurant_id?: string;
  }): Promise<DemandPricingResponse> => {
    const q = new URLSearchParams();
    if (params?.menu_item_id) q.set('menu_item_id', params.menu_item_id);
    if (params?.restaurant_id) q.set('restaurant_id', params.restaurant_id);

    const res = await request<DataEnvelope<DemandPricingResponse>>(`/analytics/demand?${q.toString()}`);
    return res.data;
  },

  getWastageInventory: async (params?: { restaurant_id?: string }): Promise<WastageInventoryResponse> => {
    const q = new URLSearchParams();
    if (params?.restaurant_id) q.set('restaurant_id', params.restaurant_id);

    const res = await request<DataEnvelope<WastageInventoryResponse>>(`/analytics/wastage?${q.toString()}`);
    return res.data;
  },

  getPromotionsBasket: async (): Promise<PromotionsBasketResponse> => {
    const res = await request<DataEnvelope<PromotionsBasketResponse>>('/analytics/promotions');
    return res.data;
  },

  getRatingsAnomalies: async (): Promise<RatingsAnomaliesResponse> => {
    const res = await request<DataEnvelope<RatingsAnomaliesResponse>>('/analytics/anomalies');
    return res.data;
  },

  getComparisonArena: async (params?: { task?: string; limit?: number }): Promise<ComparisonArenaResponse> => {
    const q = new URLSearchParams();
    if (params?.task) q.set('task', params.task);
    if (params?.limit) q.set('limit', String(params.limit));

    const res = await request<DataEnvelope<ComparisonArenaResponse>>(`/analytics/comparison?${q.toString()}`);
    return res.data;
  },

  getRecommendations: async (): Promise<RecommendationItem[]> => {
    const res = await request<DataEnvelope<RecommendationItem[]>>('/analytics/recommendations');
    return res.data;
  },

  runWhatIf: async (payload: WhatIfRequestPayload): Promise<WhatIfResponse> => {
    const res = await request<DataEnvelope<WhatIfResponse>>('/analytics/what-if', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  getExportUrl: (martPath: string, limit: number = 5000): string => {
    return `${API_BASE_URL}/analytics/export?mart_path=${encodeURIComponent(martPath)}&limit=${limit}`;
  },
};
