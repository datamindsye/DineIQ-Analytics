import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import type { RatingsAnomaliesResponse } from '../types';

export const RatingsAnomaliesPage: React.FC = () => {
  const [data, setData] = useState<RatingsAnomaliesResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'sales' | 'ratings'>('sales');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    apiService
      .getRatingsAnomalies()
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        if (isMounted) setError(err instanceof Error ? err.message : 'Failed loading anomalies');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Operational Anomalies & Ratings Intelligence</h1>
        <p className="page-description">
          Statistical anomaly detection tracking sudden revenue deviations (Z-score &gt; 2.5) and customer satisfaction drops.
        </p>
      </div>

      {error && <div className="alert-box error">{error}</div>}

      <div className="tab-group">
        <button
          className={`tab-btn ${activeTab === 'sales' ? 'active' : ''}`}
          onClick={() => setActiveTab('sales')}
        >
          🚨 Sales Revenue Anomalies ({data?.sales_anomalies.length || 0})
        </button>
        <button
          className={`tab-btn ${activeTab === 'ratings' ? 'active' : ''}`}
          onClick={() => setActiveTab('ratings')}
        >
          ⭐ Review & Rating Shifts ({data?.rating_anomalies.length || 0})
        </button>
      </div>

      {activeTab === 'sales' ? (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <div>
              <h2 className="card-title" style={{ margin: 0 }}>Sales Anomaly Events (Rolling Baseline Excludes Day t)</h2>
              <p style={{ margin: '4px 0 0', fontSize: '0.78rem', color: '#94a3b8' }}>
                Strict anti-leakage verified: baseline rolling window computed via <code>rowsBetween(-14, -1)</code>.
              </p>
            </div>
            <a
              href={apiService.getExportUrl('spark/mart_sales_anomalies.parquet')}
              className="btn btn-secondary"
              download
            >
              Export Anomalies CSV
            </a>
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Location</th>
                  <th>City</th>
                  <th>Daily Revenue</th>
                  <th>Rolling Baseline</th>
                  <th>Z-Score</th>
                  <th>Anomaly Pattern</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={7} style={{ textAlign: 'center', padding: '30px' }}>Loading sales anomalies...</td>
                  </tr>
                ) : data?.sales_anomalies.map((anom, idx) => (
                  <tr key={`${anom.source_restaurant_id}-${anom.order_date}-${idx}`}>
                    <td><code>{anom.order_date}</code></td>
                    <td><strong>{anom.location_name}</strong></td>
                    <td>{anom.city}</td>
                    <td>${Number(anom.daily_revenue).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                    <td>
                      {anom.rolling_mean_revenue !== null
                        ? `$${Number(anom.rolling_mean_revenue).toLocaleString('en-US', { minimumFractionDigits: 2 })}`
                        : 'N/A'}
                    </td>
                    <td>
                      <strong>
                        {anom.z_score_revenue !== null ? Number(anom.z_score_revenue).toFixed(2) : 'N/A'}
                      </strong>
                    </td>
                    <td>
                      <span
                        className={`badge-tag ${
                          anom.anomaly_type?.includes('SPIKE')
                            ? 'badge-profit'
                            : 'badge-low'
                        }`}
                      >
                        {anom.anomaly_type || 'OUTLIER'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h2 className="card-title" style={{ margin: 0 }}>Customer Review Quality Anomalies</h2>
            <a
              href={apiService.getExportUrl('spark/mart_ratings_anomalies.parquet')}
              className="btn btn-secondary"
              download
            >
              Export Ratings CSV
            </a>
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Menu Item</th>
                  <th>Location</th>
                  <th>Week</th>
                  <th>Mean Rating</th>
                  <th>Review Volume</th>
                  <th>Negative Review Rate</th>
                  <th>Diagnostic Reason</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={7} style={{ textAlign: 'center', padding: '30px' }}>Loading rating anomalies...</td>
                  </tr>
                ) : data?.rating_anomalies.map((r, idx) => (
                  <tr key={`${r.source_menu_item_id}-${r.calendar_week}-${idx}`}>
                    <td>
                      <strong>{r.item_name}</strong>
                      <div><code style={{ fontSize: '0.72rem', color: '#94a3b8' }}>{r.source_menu_item_id}</code></div>
                    </td>
                    <td><code>{r.source_restaurant_id}</code></td>
                    <td>W{r.calendar_week}</td>
                    <td>
                      <strong style={{ color: Number(r.mean_rating) < 3.0 ? '#ef4444' : '#f59e0b' }}>
                        ★ {Number(r.mean_rating).toFixed(1)}
                      </strong>
                    </td>
                    <td>{r.rating_count} reviews</td>
                    <td>{(Number(r.negative_rating_rate) * 100).toFixed(1)}%</td>
                    <td>
                      <span className="badge-tag badge-low">{r.anomaly_reason || 'Sentiment Decline'}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
