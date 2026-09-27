import React, { useEffect, useState } from 'react';
import { PlotlyChart } from '../components/charts/PlotlyChart';
import { useFilters } from '../context/useFilters';
import { apiService } from '../services/api';
import type { SalesOperationsResponse } from '../types';

export const SalesOperationsPage: React.FC = () => {
  const { selectedLocation } = useFilters();
  const [data, setData] = useState<SalesOperationsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    apiService
      .getSalesOperations({ restaurant_id: selectedLocation || undefined })
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        if (isMounted) setError(err instanceof Error ? err.message : 'Failed loading sales operations');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedLocation]);

  // Channel bar chart
  const channelData = [
    {
      x: data?.channel_breakdown.map((c) => c.channel) || [],
      y: data?.channel_breakdown.map((c) => c.net_revenue) || [],
      type: 'bar' as const,
      name: 'Net Revenue ($)',
      marker: { color: '#38bdf8' },
    },
    {
      x: data?.channel_breakdown.map((c) => c.channel) || [],
      y: data?.channel_breakdown.map((c) => c.contribution_margin) || [],
      type: 'bar' as const,
      name: 'Contribution Margin ($)',
      marker: { color: '#10b981' },
    },
  ];

  const channelLayout = {
    title: { text: 'Ordering Channel Revenue vs Contribution Margin', font: { size: 15, color: '#f8fafc' } },
    barmode: 'group' as const,
    xaxis: { gridcolor: '#334155', font: { color: '#94a3b8' } },
    yaxis: { title: { text: 'Amount ($)', font: { color: '#94a3b8' } }, gridcolor: '#334155' },
    legend: { font: { color: '#94a3b8' } },
  };

  // Peak hourly pattern
  const peakData = [
    {
      x: data?.peak_hourly_heatmap.map((p) => `${p.day_of_week.slice(0, 3)} ${p.hour_of_day}:00`) || [],
      y: data?.peak_hourly_heatmap.map((p) => p.total_orders) || [],
      type: 'scatter' as const,
      mode: 'lines+markers' as const,
      line: { color: '#f59e0b', width: 2 },
      marker: { size: 6 },
    },
  ];

  const peakLayout = {
    title: { text: 'Peak Period Order Velocity (Day of Week & Hour)', font: { size: 15, color: '#f8fafc' } },
    xaxis: { title: { text: 'Time Slot', font: { color: '#94a3b8' } }, gridcolor: '#334155', tickangle: -45 },
    yaxis: { title: { text: 'Total Orders', font: { color: '#94a3b8' } }, gridcolor: '#334155' },
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Sales & Operational Performance</h1>
        <p className="page-description">
          Cross-store operational efficiency, peak period rush analysis, and ordering channel unit economics.
        </p>
      </div>

      {error && <div className="alert-box error">{error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        <div className="card chart-card">
          <PlotlyChart data={channelData} layout={channelLayout} />
        </div>
        <div className="card chart-card">
          <PlotlyChart data={peakData} layout={peakLayout} />
        </div>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h2 className="card-title" style={{ margin: 0 }}>
            Restaurant Location Performance Rankings
          </h2>
          <a
            href={apiService.getExportUrl('spark/mart_location_performance.parquet')}
            className="btn btn-secondary"
            download
          >
            Export Location CSV
          </a>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Location</th>
                <th>City</th>
                <th>Concept</th>
                <th>Total Orders</th>
                <th>Gross Revenue</th>
                <th>Contribution Margin</th>
                <th>Margin %</th>
                <th>Total Waste Cost</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '30px' }}>Loading locations...</td>
                </tr>
              ) : data?.locations.map((loc) => (
                <tr key={loc.source_restaurant_id}>
                  <td>
                    <strong>{loc.location_name}</strong>
                    <div><code style={{ fontSize: '0.72rem', color: '#94a3b8' }}>{loc.source_restaurant_id}</code></div>
                  </td>
                  <td>{loc.city}</td>
                  <td>{loc.dining_type}</td>
                  <td>{Number(loc.total_orders).toLocaleString()}</td>
                  <td>${Number(loc.gross_revenue).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                  <td>${Number(loc.contribution_margin).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                  <td>
                    <span className="badge-tag badge-profit">{loc.margin_pct}%</span>
                  </td>
                  <td>${Number(loc.total_waste_cost).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
