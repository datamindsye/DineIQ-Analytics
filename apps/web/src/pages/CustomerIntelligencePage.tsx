import React, { useEffect, useState } from 'react';
import { PlotlyChart } from '../components/charts/PlotlyChart';
import { apiService } from '../services/api';
import type { CustomerSummaryResponse } from '../types';

export const CustomerIntelligencePage: React.FC = () => {
  const [data, setData] = useState<CustomerSummaryResponse | null>(null);
  const [selectedSegment, setSelectedSegment] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [page, setPage] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const PAGE_SIZE = 25;

  const loadCustomerData = React.useCallback(() => {
    let isMounted = true;
    apiService
      .getCustomerIntelligence({
        segment: selectedSegment || undefined,
        search: searchQuery || undefined,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      })
      .then((res) => {
        if (isMounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to load customer intelligence');
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [selectedSegment, searchQuery, page]);

  useEffect(() => {
    return loadCustomerData();
  }, [loadCustomerData]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    setLoading(true);
    loadCustomerData();
  };

  // Pie chart of RFM segments
  const dist = data?.segment_distribution || {};
  const segmentChartData = [
    {
      values: Object.values(dist),
      labels: Object.keys(dist),
      type: 'pie' as const,
      hole: 0.55,
      marker: {
        colors: Object.keys(dist).map((seg) => {
          if (seg === 'Champions') return '#10b981';
          if (seg === 'Loyal') return '#38bdf8';
          if (seg === 'At Risk') return '#f59e0b';
          return '#ef4444';
        }),
      },
      textinfo: 'label+percent' as const,
      hoverinfo: 'label+value+percent' as const,
    },
  ];

  const segmentChartLayout = {
    title: { text: 'RFM Customer Segment Distribution', font: { size: 15, color: '#f8fafc' } },
    showlegend: true,
    legend: { font: { color: '#94a3b8' } },
    margin: { l: 20, r: 20, t: 40, b: 20 },
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Customer Intelligence & Churn Risk</h1>
        <p className="page-description">
          RFM lifecycle segmentation, retention analytics, and machine learning churn probabilities.
        </p>
      </div>

      {error && <div className="alert-box error">{error}</div>}

      <div className="filter-bar">
        <form onSubmit={handleSearchSubmit} className="filter-group">
          <input
            type="text"
            placeholder="Search customer name or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          <button type="submit" className="btn btn-primary">Search</button>
        </form>

        <div className="filter-group">
          <select
            value={selectedSegment}
            onChange={(e) => { setSelectedSegment(e.target.value); setPage(0); }}
            className="filter-select"
          >
            <option value="">All RFM Segments</option>
            <option value="Champions">Champions</option>
            <option value="Loyal">Loyal Customers</option>
            <option value="At Risk">At Risk (Retention Target)</option>
            <option value="Lost">Lost / Inactive</option>
          </select>

          <a
            href={apiService.getExportUrl('spark/mart_customer_rfm.parquet')}
            className="btn btn-secondary"
            download
          >
            Export RFM CSV
          </a>
        </div>
      </div>

      {/* Segment Cards */}
      <div className="metrics-grid">
        <div className="metric-card" style={{ borderLeft: '4px solid #10b981' }}>
          <div className="metric-label">Champions</div>
          <div className="metric-value">{dist['Champions']?.toLocaleString() || 0}</div>
          <div className="metric-sub">Highest frequency & spend</div>
        </div>
        <div className="metric-card" style={{ borderLeft: '4px solid #38bdf8' }}>
          <div className="metric-label">Loyal Customers</div>
          <div className="metric-value">{dist['Loyal']?.toLocaleString() || 0}</div>
          <div className="metric-sub">Consistent repeat diners</div>
        </div>
        <div className="metric-card" style={{ borderLeft: '4px solid #f59e0b' }}>
          <div className="metric-label">At Risk</div>
          <div className="metric-value">{dist['At Risk']?.toLocaleString() || 0}</div>
          <div className="metric-sub">High spenders fading</div>
        </div>
        <div className="metric-card" style={{ borderLeft: '4px solid #ef4444' }}>
          <div className="metric-label">Lost / Inactive</div>
          <div className="metric-value">{dist['Lost']?.toLocaleString() || 0}</div>
          <div className="metric-sub">Long overdue for win-back</div>
        </div>
      </div>

      <div className="card chart-card">
        <h2 className="card-title">Customer Portfolio Share</h2>
        <PlotlyChart data={segmentChartData} layout={segmentChartLayout} />
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h2 className="card-title" style={{ margin: 0 }}>
            Customer Profiles ({data?.total_count.toLocaleString() || 0} profiles)
          </h2>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              className="btn btn-secondary"
              disabled={page === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
            >
              Previous
            </button>
            <button
              className="btn btn-secondary"
              disabled={((page + 1) * PAGE_SIZE) >= (data?.total_count || 0)}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Customer</th>
                <th>City</th>
                <th>Loyalty Tier</th>
                <th>Preferred Channel</th>
                <th>Orders</th>
                <th>Total Spent</th>
                <th>Recency</th>
                <th>Segment</th>
                <th>ML Churn Risk</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '30px' }}>Loading customers...</td>
                </tr>
              ) : data?.customers.map((c) => (
                <tr key={c.customer_id}>
                  <td>
                    <strong>{c.customer_name}</strong>
                    <div><code style={{ fontSize: '0.72rem', color: '#94a3b8' }}>{c.customer_id}</code></div>
                  </td>
                  <td>{c.home_city}</td>
                  <td>{c.loyalty_tier}</td>
                  <td>{c.preferred_channel}</td>
                  <td>{c.frequency}</td>
                  <td>${Number(c.monetary_value).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                  <td>{c.recency_days} days ago</td>
                  <td>
                    <span
                      className={`badge-tag ${
                        c.rfm_segment === 'Champions'
                          ? 'badge-profit'
                          : c.rfm_segment === 'Loyal'
                          ? 'badge-volume'
                          : c.rfm_segment === 'At Risk'
                          ? 'badge-hidden'
                          : 'badge-low'
                      }`}
                    >
                      {c.rfm_segment}
                    </span>
                  </td>
                  <td>
                    {c.churn_probability !== undefined && c.churn_probability !== null ? (
                      <span
                        className={`badge-tag ${
                          c.churn_probability > 0.65 ? 'badge-risk-high' : 'badge-risk-low'
                        }`}
                      >
                        {(c.churn_probability * 100).toFixed(1)}% Churn
                      </span>
                    ) : (
                      <span style={{ color: '#64748b' }}>N/A</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
