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
  message: string;
  pipeline_modes: string[];
}

export interface MetricCardData {
  title: string;
  value: string | number;
  change?: string;
  status?: 'positive' | 'negative' | 'neutral';
}
