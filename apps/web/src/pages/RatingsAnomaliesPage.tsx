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
        <span className="page-eyebrow">Anomaly Detection & Quality Control</span>
        <h1 className="page-title">Operational Anomalies & Ratings Intelligence</h1>
        <p className="page-description">
          Statistical anomaly detection tracking sudden revenue deviations (Z-score &gt; 2.5) and customer satisfaction drops.
        </p>
      </div>

      {error && <div className="alert-box error">{error}</div>}

      <div className="tab-group" style={{ marginBottom: '16px' }}>
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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
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
                  <th className="text-right">Daily Revenue</th>
                  <th className="text-right">Rolling Baseline</th>
                  <th className="text-right">Z-Score</th>
                  <th>Anomaly Pattern</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  Array.from({ length: 6 }).map((_, idx) => (
                    <tr key={`skel-anom-${idx}`}>
                      <td><div className="skeleton skeleton-text" style={{ width: '80px' }} /></td>
                      <td><div className="skeleton skeleton-text" style={{ width: '120px' }} /></td>
                      <td><div className="skeleton skeleton-text" style={{ width: '60px' }} /></td>
                      <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '65px', marginLeft: 'auto' }} /></td>
                      <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '65px', marginLeft: 'auto' }} /></td>
                      <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '40px', marginLeft: 'auto' }} /></td>
                      <td><div className="skeleton skeleton-text" style={{ width: '80px' }} /></td>
                    </tr>
                  ))
                ) : data?.sales_anomalies.map((anom, idx) => (
                  <tr key={`${anom.source_restaurant_id}-${anom.order_date}-${idx}`}>
                    <td><span className="code-id">{anom.order_date}</span></td>
                    <td><strong style={{ color: '#f8fafc' }}>{anom.location_name}</strong></td>
                    <td>{anom.city}</td>
                    <td className="text-right" style={{ fontWeight: 600 }}>${Number(anom.daily_revenue).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                    <td className="text-right" style={{ color: '#94a3b8' }}>
                      {anom.rolling_mean_revenue !== null
                        ? `$${Number(anom.rolling_mean_revenue).toLocaleString('en-US', { minimumFractionDigits: 2 })}`
                        : 'N/A'}
                    </td>
                    <td className="text-right">
                      <strong style={{ color: Number(anom.z_score_revenue) >= 3 ? '#ef4444' : '#f59e0b' }}>
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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
            <div>
              <h2 className="card-title" style={{ margin: 0 }}>Customer Review Quality Anomalies</h2>
              <p style={{ margin: '4px 0 0', fontSize: '0.78rem', color: '#94a3b8' }}>
                Menu items exhibiting statistically anomalous downward shifts in customer sentiment.
              </p>
            </div>
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
                  <th className="text-right">Mean Rating</th>
                  <th className="text-right">Review Volume</th>
                  <th className="text-right">Negative Rate</th>
                  <th>Diagnostic Reason</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  Array.from({ length: 6 }).map((_, idx) => (
                    <tr key={`skel-rtg-${idx}`}>
                      <td><div className="skeleton skeleton-text" style={{ width: '130px' }} /></td>
                      <td><div className="skeleton skeleton-text" style={{ width: '70px' }} /></td>
                      <td><div className="skeleton skeleton-text" style={{ width: '40px' }} /></td>
                      <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '45px', marginLeft: 'auto' }} /></td>
                      <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '55px', marginLeft: 'auto' }} /></td>
                      <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '45px', marginLeft: 'auto' }} /></td>
                      <td><div className="skeleton skeleton-text" style={{ width: '90px' }} /></td>
                    </tr>
                  ))
                ) : data?.rating_anomalies.map((r, idx) => (
                  <tr key={`${r.source_menu_item_id}-${r.calendar_week}-${idx}`}>
                    <td>
                      <strong style={{ color: '#f8fafc' }}>{r.item_name}</strong>
                      <div><span className="code-id">{r.source_menu_item_id}</span></div>
                    </td>
                    <td><span className="code-id">{r.source_restaurant_id}</span></td>
                    <td>W{r.calendar_week}</td>
                    <td className="text-right">
                      <strong style={{ color: Number(r.mean_rating) < 3.0 ? '#ef4444' : '#f59e0b' }}>
                        ★ {Number(r.mean_rating).toFixed(1)}
                      </strong>
                    </td>
                    <td className="text-right">{r.rating_count} reviews</td>
                    <td className="text-right" style={{ color: Number(r.negative_rating_rate) > 0.25 ? '#ef4444' : '#94a3b8' }}>
                      {(Number(r.negative_rating_rate) * 100).toFixed(1)}%
                    </td>
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
