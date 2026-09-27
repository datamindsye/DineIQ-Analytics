import React, { useEffect, useState } from 'react';
import { PlotlyChart } from '../components/charts/PlotlyChart';
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
        size: scatterItems.map((item) => Math.min(30, Math.max(10, item.gross_revenue / 400))),
        color: scatterItems.map((item) => {
          if (item.classification === 'Profit Driver') return '#10b981';
          if (item.classification === 'Volume Driver') return '#38bdf8';
          if (item.classification === 'Hidden Opportunity') return '#f59e0b';
          return '#ef4444';
        }),
        opacity: 0.85,
      },
      type: 'scatter' as const,
      hovertemplate: '<b>%{text}</b><br>Volume Sold: %{x} units<br>Profit Margin: %{y:.1f}%<extra></extra>',
    },
  ];

  const matrixLayout = {
    title: { text: 'Menu Portfolio Matrix (Real Sales Volume vs Profit Margin)', font: { size: 15, color: '#f8fafc' } },
    xaxis: { title: { text: 'Total Quantity Sold (Units)', font: { color: '#94a3b8' } }, gridcolor: '#334155' },
    yaxis: { title: { text: 'Profit Margin (%)', font: { color: '#94a3b8' } }, gridcolor: '#334155' },
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Executive Intelligence Overview</h1>
        <p className="page-description">
          Cross-cutting executive performance indicators derived from precomputed Apache Spark analytical marts.
        </p>
      </div>

      {error && <div className="alert-box error">{error}</div>}

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Total Gross Revenue</div>
          <div className="metric-value">
            {loading ? '...' : `$${kpis?.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
          </div>
          <div className="metric-sub">Network total</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Total Orders</div>
          <div className="metric-value">{loading ? '...' : kpis?.total_orders.toLocaleString()}</div>
          <div className="metric-sub">Completed transactions</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Average Order Value</div>
          <div className="metric-value">{loading ? '...' : `$${kpis?.average_order_value.toFixed(2)}`}</div>
          <div className="metric-sub">Revenue per order</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Contribution Margin</div>
          <div className="metric-value">{loading ? '...' : `${kpis?.margin_percentage.toFixed(1)}%`}</div>
          <div className="metric-sub">
            {loading ? '' : `$${kpis?.contribution_margin.toLocaleString('en-US', { minimumFractionDigits: 2 })} profit`}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Active Customers</div>
          <div className="metric-value">{loading ? '...' : kpis?.active_customers.toLocaleString()}</div>
          <div className="metric-sub">RFM tracked profiles</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Wastage Cost Impact</div>
          <div className="metric-value">
            {loading ? '...' : `$${kpis?.total_waste_cost.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
          </div>
          <div className="metric-sub">{loading ? '' : `${kpis?.waste_to_revenue_ratio.toFixed(2)}% of gross sales`}</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Operational Anomalies</div>
          <div className="metric-value">{loading ? '...' : kpis?.detected_anomalies_count}</div>
          <div className="metric-sub">Revenue spikes & drops</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Analytical Pipeline</div>
          <div className="metric-value" style={{ color: '#10b981' }}>
            {kpis?.pipeline_status || 'ONLINE'}
          </div>
          <div className="metric-sub">12 Spark Marts Materialized</div>
        </div>
      </div>

      <div className="card chart-card">
        <h2 className="card-title">Menu Profitability & Volume Matrix</h2>
        {loading ? (
          <div style={{ padding: '60px', textAlign: 'center', color: '#94a3b8' }}>Loading analytical mart...</div>
        ) : (
          <PlotlyChart data={matrixData} layout={matrixLayout} />
        )}
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 className="card-title" style={{ margin: 0 }}>Top Performing Menu Items (Profit Drivers)</h2>
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
                <th>Price</th>
                <th>Units Sold</th>
                <th>Revenue</th>
                <th>Margin %</th>
                <th>Classification</th>
              </tr>
            </thead>
            <tbody>
              {scatterItems.slice(0, 10).map((item) => (
                <tr key={`${item.menu_item_id}-${item.restaurant_id}`}>
                  <td><code>{item.menu_item_id}</code></td>
                  <td><strong>{item.item_name}</strong></td>
                  <td>{item.category_name}</td>
                  <td>${item.current_base_price.toFixed(2)}</td>
                  <td>{item.total_quantity.toLocaleString()}</td>
                  <td>${item.gross_revenue.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                  <td>{item.profitability_pct.toFixed(1)}%</td>
                  <td>
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
