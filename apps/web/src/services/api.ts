/**
 * API client service foundation for DineIQ backend communication.
 */

import type { AnalyticsStatus, DataEnvelope, HealthStatus } from '../types';

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
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      let errorCode = 'REQUEST_FAILED';
      try {
        const errorData = await response.json();
        if (errorData?.error?.message) {
          errorMessage = errorData.error.message;
          errorCode = errorData.error.code || errorCode;
        }
      } catch {
        // Response body was not JSON
      }
      throw new ApiError(errorMessage, errorCode, response.status);
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(
      error instanceof Error ? error.message : 'Network request failed',
      'NETWORK_ERROR',
      0
    );
  }
}

export const apiService = {
  getLiveness: (): Promise<HealthStatus> => request<HealthStatus>('/health'),
  getReadiness: (): Promise<HealthStatus> => request<HealthStatus>('/health/ready'),
  getAnalyticsStatus: async (): Promise<AnalyticsStatus> => {
    const envelope = await request<DataEnvelope<AnalyticsStatus>>('/analytics/status');
    return envelope.data;
  },
};
