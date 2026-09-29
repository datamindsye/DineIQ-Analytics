import React, { useEffect, useState } from 'react';
import { PlotlyChart } from '../components/charts/PlotlyChart';
import { ProjectJourneyPipeline } from '../components/pipeline/ProjectJourneyPipeline';
import { useFilters } from '../context/useFilters';
import { apiService } from '../services/api';
import type { ExecutiveSummaryKPIs, MenuSummaryResponse } from '../types';

export const DashboardPage: React.FC = () => {
  const { selectedLocation } = useFilters();
  const [kpis, setKpis] = useState<ExecutiveSummaryKPIs | null>(null);
  const [menuSummary, setMenuSummary] = useState<MenuSummaryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    Promise.all([
      apiService.getExecutiveSummary(),
      apiService.getMenuIntelligence({ limit: 40 }),
    ])
      .then(([summaryData, menuData]) => {
        if (isMounted) {
          setKpis(summaryData);
          setMenuSummary(menuData);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to fetch executive metrics');
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedLocation]);

  // Construct Boston Matrix Plotly Scatter chart from real menu items
  const scatterItems = menuSummary?.items || [];
  const matrixData = [
    {
      x: scatterItems.map((item) => item.total_quantity),
      y: scatterItems.map((item) => item.profitability_pct),
      text: scatterItems.map((item) => `${item.item_name} (${item.classification})`),
      mode: 'markers' as const,
      marker: {
        size: scatterItems.map((item) => Math.min(26, Math.max(9, item.gross_revenue / 450))),
        color: scatterItems.map((item) => {
          if (item.classification === 'Profit Driver') return '#10b981';
          if (item.classification === 'Volume Driver') return '#38bdf8';
          if (item.classification === 'Hidden Opportunity') return '#f59e0b';
          return '#ef4444';
        }),
        opacity: 0.88,
        line: { color: '#0f172a', width: 1.5 },
      },
      type: 'scatter' as const,
      hovertemplate:
        '<b>%{text}</b><br>Volume Sold: <b>%{x:,} units</b><br>Profit Margin: <b>%{y:.1f}%</b><extra></extra>',
    },
  ];

  const matrixLayout = {
    title: {
      text: 'Menu Portfolio Matrix (Sales Volume vs Contribution Margin %)',
      font: { size: 15, color: '#f8fafc' },
    },
    xaxis: {
      title: { text: 'Total Quantity Sold (Units)', font: { color: '#94a3b8', size: 12 } },
      gridcolor: '#1e293b',
      zerolinecolor: '#334155',
    },
    yaxis: {
      title: { text: 'Profit Margin (%)', font: { color: '#94a3b8', size: 12 } },
      gridcolor: '#1e293b',
      zerolinecolor: '#334155',
    },
    shapes: [
      {
        type: 'line' as const,
        xref: 'paper' as const,
        x0: 0,
        x1: 1,
        y0: 45,
        y1: 45,
        line: { color: 'rgba(148, 163, 184, 0.25)', width: 1, dash: 'dot' as const },
      },
    ],
    annotations: [
      {
        xref: 'paper' as const,
        yref: 'paper' as const,
        x: 0.98,
        y: 0.96,
        text: '★ Profit Drivers (High Margin & High Vol)',
        showarrow: false,
        font: { size: 10, color: '#34d399' },
        align: 'right' as const,
      },
      {
        xref: 'paper' as const,
        yref: 'paper' as const,
        x: 0.98,
        y: 0.04,
        text: '⚡ Volume Drivers (High Vol, Lower Margin)',
        showarrow: false,
        font: { size: 10, color: '#38bdf8' },
        align: 'right' as const,
      },
      {
        xref: 'paper' as const,
        yref: 'paper' as const,
        x: 0.02,
        y: 0.96,
        text: '💎 Hidden Opportunities (High Margin, Lower Vol)',
        showarrow: false,
        font: { size: 10, color: '#fbbf24' },
        align: 'left' as const,
      },
      {
        xref: 'paper' as const,
        yref: 'paper' as const,
        x: 0.02,
        y: 0.04,
        text: '⚠️ Low Performers (Low Margin & Low Vol)',
        showarrow: false,
        font: { size: 10, color: '#f87171' },
        align: 'left' as const,
      },
    ],
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-eyebrow">
          <span className="badge-tag badge-profit">EXECUTIVE COCKPIT</span>
          <span className="page-timestamp">Precomputed Spark Parquet Marts</span>
        </div>
        <h1 className="page-title">Executive Intelligence Overview</h1>
        <p className="page-description">
          Cross-cutting executive performance indicators derived from precomputed Apache Spark analytical marts and dual-pipeline ML models.
        </p>
      </div>

      {error && <div className="alert-box error">{error}</div>}

      {/* Primary KPI Grid */}
      <div className="metrics-grid">
        <div className="metric-card primary-kpi">
          <div className="metric-card-top">
            <span className="metric-label">Total Gross Revenue</span>
            <span className="metric-icon">💰</span>
          </div>
          <div className="metric-value">
            {loading ? <span className="skeleton skeleton-kpi" /> : `$${kpis?.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
          </div>
          <div className="metric-sub">
            <span className="badge-pill-sub">Network total</span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-card-top">
            <span className="metric-label">Total Orders</span>
            <span className="metric-icon">🧾</span>
          </div>
          <div className="metric-value">
            {loading ? <span className="skeleton skeleton-kpi" /> : kpis?.total_orders.toLocaleString()}
          </div>
          <div className="metric-sub">
            <span className="badge-pill-sub">Completed transactions</span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-card-top">
            <span className="metric-label">Average Order Value</span>
            <span className="metric-icon">📈</span>
          </div>
          <div className="metric-value">
            {loading ? <span className="skeleton skeleton-kpi" /> : `$${kpis?.average_order_value.toFixed(2)}`}
          </div>
          <div className="metric-sub">
            <span className="badge-pill-sub">Revenue per order</span>
          </div>
        </div>

        <div className="metric-card profit-card">
          <div className="metric-card-top">
            <span className="metric-label">Contribution Margin</span>
            <span className="metric-icon">💎</span>
          </div>
          <div className="metric-value" style={{ color: '#10b981' }}>
            {loading ? <span className="skeleton skeleton-kpi" /> : `${kpis?.margin_percentage.toFixed(1)}%`}
          </div>
          <div className="metric-sub" style={{ color: '#34d399' }}>
            {loading ? '' : `$${kpis?.contribution_margin.toLocaleString('en-US', { minimumFractionDigits: 2 })} net profit`}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-card-top">
            <span className="metric-label">Active Customers</span>
            <span className="metric-icon">👥</span>
          </div>
          <div className="metric-value">
            {loading ? <span className="skeleton skeleton-kpi" /> : kpis?.active_customers.toLocaleString()}
          </div>
          <div className="metric-sub">
            <span className="badge-pill-sub">RFM profiles</span>
          </div>
        </div>

        <div className="metric-card warning-kpi">
          <div className="metric-card-top">
            <span className="metric-label">Wastage Cost Impact</span>
            <span className="metric-icon">🗑️</span>
          </div>
          <div className="metric-value" style={{ color: '#f59e0b' }}>
            {loading ? <span className="skeleton skeleton-kpi" /> : `$${kpis?.total_waste_cost.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
          </div>
          <div className="metric-sub" style={{ color: '#fbbf24' }}>
            {loading ? '' : `${kpis?.waste_to_revenue_ratio.toFixed(2)}% of sales`}
          </div>
        </div>

        <div className="metric-card alert-kpi">
          <div className="metric-card-top">
            <span className="metric-label">Operational Anomalies</span>
            <span className="metric-icon">⚠️</span>
          </div>
          <div className="metric-value" style={{ color: (kpis?.detected_anomalies_count || 0) > 0 ? '#ef4444' : '#10b981' }}>
            {loading ? <span className="skeleton skeleton-kpi" /> : kpis?.detected_anomalies_count}
          </div>
          <div className="metric-sub">
            <span className="badge-pill-sub">Spikes & drops detected</span>
          </div>
        </div>

        <div className="metric-card status-kpi">
          <div className="metric-card-top">
            <span className="metric-label">Analytical Pipeline</span>
            <span className="metric-icon">⚡</span>
          </div>
          <div className="metric-value" style={{ color: '#38bdf8' }}>
            {kpis?.pipeline_status || 'ONLINE'}
          </div>
          <div className="metric-sub" style={{ color: '#7dd3fc' }}>
            12 Spark Marts Ready
          </div>
        </div>
      </div>

      {/* DineIQ Analytics Pipeline Journey Section */}
      <ProjectJourneyPipeline />

      {/* Portfolio Matrix Section */}
      <div className="card chart-card">
        <div className="card-header-row">
          <div>
            <h2 className="card-title" style={{ margin: 0 }}>Menu Profitability & Volume Matrix (Boston BCG Quadrants)</h2>
            <p className="card-subtitle">
              Bubble size represents item gross revenue. Color indicates analytical classification derived from volume and margin thresholds.
            </p>
          </div>
          <div className="matrix-legend-row">
            <span className="legend-chip profit">● Profit Driver</span>
            <span className="legend-chip volume">● Volume Driver</span>
            <span className="legend-chip hidden">● Hidden Opportunity</span>
            <span className="legend-chip low">● Low Performer</span>
          </div>
        </div>

        {loading ? (
          <div className="chart-skeleton-box">
            <div className="skeleton skeleton-chart" />
          </div>
        ) : (
          <PlotlyChart data={matrixData} layout={matrixLayout} />
        )}
      </div>

      {/* Top Performing Menu Items */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <h2 className="card-title" style={{ margin: 0 }}>Top Performing Menu Items (Profit Drivers)</h2>
            <p className="card-subtitle">Top revenue contributors evaluated across analytical margin and order volumes.</p>
          </div>
          <a
            href={apiService.getExportUrl('spark/mart_menu_performance.parquet')}
            className="btn btn-secondary"
            download
          >
            Export Mart CSV
          </a>
        </div>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Item ID</th>
                <th>Item Name</th>
                <th>Category</th>
                <th className="text-right">Price</th>
                <th className="text-right">Units Sold</th>
                <th className="text-right">Revenue</th>
                <th className="text-right">Margin %</th>
                <th className="text-center">Classification</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 5 }).map((_, idx) => (
                  <tr key={idx}>
                    <td><div className="skeleton skeleton-text" style={{ width: '60px' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '140px' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '80px' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '50px', marginLeft: 'auto' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '60px', marginLeft: 'auto' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '70px', marginLeft: 'auto' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '40px', marginLeft: 'auto' }} /></td>
                    <td className="text-center"><div className="skeleton skeleton-badge" style={{ margin: '0 auto' }} /></td>
                  </tr>
                ))
              ) : scatterItems.slice(0, 10).map((item) => (
                <tr key={`${item.menu_item_id}-${item.restaurant_id}`}>
                  <td><code className="code-id">{item.menu_item_id}</code></td>
                  <td><strong>{item.item_name}</strong></td>
                  <td><span className="category-pill">{item.category_name}</span></td>
                  <td className="text-right">${item.current_base_price.toFixed(2)}</td>
                  <td className="text-right">{item.total_quantity.toLocaleString()}</td>
                  <td className="text-right">${item.gross_revenue.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                  <td className="text-right">
                    <span className={item.profitability_pct >= 40 ? 'val-positive' : 'val-neutral'}>
                      {item.profitability_pct.toFixed(1)}%
                    </span>
                  </td>
                  <td className="text-center">
                    <span
                      className={`badge-tag ${
                        item.classification === 'Profit Driver'
                          ? 'badge-profit'
                          : item.classification === 'Volume Driver'
                          ? 'badge-volume'
                          : item.classification === 'Hidden Opportunity'
                          ? 'badge-hidden'
                          : 'badge-low'
                      }`}
                    >
                      {item.classification}
                    </span>
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
