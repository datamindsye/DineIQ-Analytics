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

  const [segmentView, setSegmentView] = useState<'rfm' | 'ml'>('rfm');

  // Pie chart of segments (RFM vs ML Clustering)
  const dist = (segmentView === 'rfm' ? data?.segment_distribution : data?.ml_segment_distribution) || {};
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

  const chartTitle = segmentView === 'rfm'
    ? 'Rule-Based RFM Segment Distribution'
    : `ML Clustering Distribution (${data?.spark_selected_algorithm || 'BisectingKMeans'})`;

  const segmentChartLayout = {
    title: { text: chartTitle, font: { size: 15, color: '#f8fafc' } },
    showlegend: true,
    legend: { font: { color: '#94a3b8' } },
    margin: { l: 20, r: 20, t: 40, b: 20 },
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <span className="page-eyebrow">Customer Analytics Mart & MLlib</span>
        <h1 className="page-title">Customer Intelligence & Churn Risk</h1>
        <p className="page-description">
          Dual-view segmentation (Rule-based RFM vs ML unsupervised clustering) and ML churn probabilities.
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
          <a
            href={apiService.getExportUrl('spark/ml_customer_segmentation.parquet')}
            className="btn btn-secondary"
            download
          >
            Export ML Clusters CSV
          </a>
        </div>
      </div>

      {/* Segment Cards */}
      <div className="metrics-grid">
        <div className="metric-card" style={{ borderLeft: '4px solid #10b981' }}>
          <div className="metric-label">★ Champions</div>
          <div className="metric-value">{dist['Champions']?.toLocaleString() || 0}</div>
          <div className="metric-sub">Highest frequency & spend</div>
        </div>
        <div className="metric-card" style={{ borderLeft: '4px solid #38bdf8' }}>
          <div className="metric-label">▲ Loyal Customers</div>
          <div className="metric-value">{dist['Loyal']?.toLocaleString() || 0}</div>
          <div className="metric-sub">Consistent repeat diners</div>
        </div>
        <div className="metric-card" style={{ borderLeft: '4px solid #f59e0b' }}>
          <div className="metric-label">⚠️ At Risk</div>
          <div className="metric-value">{dist['At Risk']?.toLocaleString() || 0}</div>
          <div className="metric-sub">High spenders fading</div>
        </div>
        <div className="metric-card" style={{ borderLeft: '4px solid #ef4444' }}>
          <div className="metric-label">✕ Lost / Inactive</div>
          <div className="metric-value">{dist['Lost']?.toLocaleString() || 0}</div>
          <div className="metric-sub">Long overdue for win-back</div>
        </div>
      </div>

      <div className="card chart-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
<<<<<<< HEAD
          <h2 className="card-title" style={{ margin: 0 }}>Customer Portfolio Share</h2>
=======
          <div>
            <h2 className="card-title" style={{ margin: 0 }}>Customer Portfolio Share</h2>
            <p style={{ margin: '4px 0 0', fontSize: '0.78rem', color: '#94a3b8' }}>
              Compare heuristic RFM scoring vs ML unsupervised spatial clustering.
            </p>
          </div>
>>>>>>> be10b32 (chore: prepare final competition repository)
          <div className="tab-group" style={{ margin: 0 }}>
            <button
              className={`tab-btn ${segmentView === 'rfm' ? 'active' : ''}`}
              onClick={() => setSegmentView('rfm')}
            >
              Rule-Based RFM
            </button>
            <button
              className={`tab-btn ${segmentView === 'ml' ? 'active' : ''}`}
              onClick={() => setSegmentView('ml')}
            >
              ML Clustering ({data?.spark_selected_algorithm || 'BisectingKMeans'})
            </button>
          </div>
        </div>
        <PlotlyChart data={segmentChartData} layout={segmentChartLayout} />
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <h2 className="card-title" style={{ margin: 0 }}>
              Customer Cohort Records ({data?.total_count.toLocaleString() || 0} profiles)
            </h2>
            <p style={{ margin: '4px 0 0', fontSize: '0.78rem', color: '#94a3b8' }}>
              Unified customer profile joining mart RFM metrics with ML churn inference.
            </p>
          </div>
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
<<<<<<< HEAD
                <th>Orders</th>
                <th>Total Spent</th>
                <th>Recency</th>
                <th>RFM Segment (Rule)</th>
                <th>ML Cluster Segment</th>
                <th>ML Churn Risk</th>
=======
                <th className="text-right">Orders</th>
                <th className="text-right">Total Spent</th>
                <th className="text-right">Recency</th>
                <th>RFM Segment</th>
                <th>ML Cluster</th>
                <th className="text-right">ML Churn Risk</th>
>>>>>>> be10b32 (chore: prepare final competition repository)
              </tr>
            </thead>
            <tbody>
              {loading ? (
<<<<<<< HEAD
                <tr>
                  <td colSpan={10} style={{ textAlign: 'center', padding: '30px' }}>Loading customers...</td>
                </tr>
=======
                Array.from({ length: 10 }).map((_, idx) => (
                  <tr key={`skel-cust-${idx}`}>
                    <td><div className="skeleton skeleton-text" style={{ width: '120px' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '60px' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '70px' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '60px' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '35px', marginLeft: 'auto' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '55px', marginLeft: 'auto' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '60px', marginLeft: 'auto' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '80px' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '80px' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '70px', marginLeft: 'auto' }} /></td>
                  </tr>
                ))
>>>>>>> be10b32 (chore: prepare final competition repository)
              ) : data?.customers.map((c) => (
                <tr key={c.customer_id}>
                  <td>
                    <div style={{ fontWeight: 600, color: '#f8fafc' }}>{c.customer_name}</div>
                    <span className="code-id">{c.customer_id}</span>
                  </td>
                  <td>{c.home_city}</td>
                  <td>
                    <span className="category-pill">{c.loyalty_tier}</span>
                  </td>
                  <td>{c.preferred_channel}</td>
                  <td className="text-right">{c.frequency}</td>
                  <td className="text-right" style={{ fontWeight: 600 }}>
                    ${Number(c.monetary_value).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="text-right" style={{ color: '#94a3b8' }}>{c.recency_days}d ago</td>
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
                    {c.segment_label ? (
                      <span
                        className="badge-tag badge-volume"
                        title={c.cluster_id !== undefined && c.cluster_id !== null ? `Cluster #${c.cluster_id}` : ''}
                      >
                        {c.segment_label} {c.cluster_id !== undefined && c.cluster_id !== null ? `(C${c.cluster_id})` : ''}
                      </span>
                    ) : (
                      <span style={{ color: '#64748b' }}>Unclustered</span>
                    )}
                  </td>
<<<<<<< HEAD
                  <td>
=======
                  <td className="text-right">
>>>>>>> be10b32 (chore: prepare final competition repository)
                    {c.churn_probability !== undefined && c.churn_probability !== null ? (
                      <span
                        className={`badge-tag ${
                          c.churn_probability > 0.65 ? 'badge-risk-high' : c.churn_probability < 0.35 ? 'badge-profit' : 'badge-hidden'
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
