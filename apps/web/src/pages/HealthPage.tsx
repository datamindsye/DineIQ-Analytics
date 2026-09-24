import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import type { HealthStatus } from '../types';

export const HealthPage: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = () => {
    setLoading(true);
    setError(null);
    apiService
      .getReadiness()
      .then((data) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to reach API server');
        setLoading(false);
      });
  };

  useEffect(() => {
    let isMounted = true;
    apiService
      .getReadiness()
      .then((data) => {
        if (isMounted) {
          setHealth(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to reach API server');
          setLoading(false);
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">System Health & Verification</h1>
        <p className="page-description">
          Live verification status of backend API, PostgreSQL connection, and environments.
        </p>
      </div>

      <div className="health-card-container">
        <div className="card">
          <div className="card-top-action">
            <h2>Backend Status</h2>
            <button className="refresh-btn" onClick={fetchHealth} disabled={loading}>
              {loading ? 'Checking...' : 'Refresh Status'}
            </button>
          </div>

          {error && <div className="alert-box error">{error}</div>}

          {health && (
            <div className="health-details-grid">
              <div className="health-item">
                <span className="label">Overall Status:</span>
                <span className={`badge ${health.status}`}>{health.status.toUpperCase()}</span>
              </div>
              <div className="health-item">
                <span className="label">Environment:</span>
                <span className="value">{health.environment}</span>
              </div>
              <div className="health-item">
                <span className="label">API Version:</span>
                <span className="value">{health.version}</span>
              </div>
              <div className="health-item">
                <span className="label">PostgreSQL:</span>
                <span className={`badge ${health.database === 'connected' ? 'ok' : 'degraded'}`}>
                  {health.database.toUpperCase()}
                </span>
              </div>
              <div className="health-item">
                <span className="label">Last Checked:</span>
                <span className="value">{new Date(health.timestamp).toLocaleString()}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
