import React, { useEffect, useMemo, useState } from 'react';
import { PlotlyChart } from '../components/charts/PlotlyChart';
import { useFilters } from '../context/useFilters';
import { apiService } from '../services/api';
import type { SalesOperationsResponse } from '../types';

const DAYS_OF_WEEK = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
];

const HOURS_OF_DAY = Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`);

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

  // Peak hourly 7x24 heatmap transformation
  const peakMatrix = useMemo(() => {
    const map = new Map<string, number>();
    if (data?.peak_hourly_heatmap) {
      for (const item of data.peak_hourly_heatmap) {
        map.set(`${item.day_of_week}_${item.hour_of_day}`, item.total_orders);
      }
    }

    // 7 rows (Monday to Sunday) x 24 columns (00:00 to 23:00)
    return DAYS_OF_WEEK.map((day) =>
      Array.from({ length: 24 }, (_, hour) => map.get(`${day}_${hour}`) ?? 0)
    );
  }, [data]);

  const peakHeatmapData = [
    {
      z: peakMatrix,
      x: HOURS_OF_DAY,
      y: DAYS_OF_WEEK,
      type: 'heatmap' as const,
      hoverongaps: false,
      colorscale: [
        [0.0, '#0f172a'],
        [0.2, '#1e293b'],
        [0.4, '#0f4c81'],
        [0.6, '#0284c7'],
        [0.8, '#38bdf8'],
        [1.0, '#f59e0b'],
      ] as [number, string][],
      colorbar: {
        title: { text: 'Orders', font: { color: '#94a3b8', size: 12 } },
        tickfont: { color: '#94a3b8', size: 10 },
        outlinecolor: '#334155',
        len: 0.9,
      },
      hovertemplate: '<b>%{y}</b> at <b>%{x}</b><br>Order Velocity: <b>%{z:,}</b> orders<extra></extra>',
    },
  ];

  const peakHeatmapLayout = {
    title: {
      text: 'Peak Period Order Velocity (7×24 Hourly Heatmap)',
      font: { size: 15, color: '#f8fafc' },
    },
    xaxis: {
      title: { text: 'Hour of Day (00:00 – 23:00)', font: { color: '#94a3b8', size: 12 } },
      tickmode: 'array' as const,
      tickvals: HOURS_OF_DAY.filter((_, idx) => idx % 2 === 0),
      gridcolor: '#334155',
      tickfont: { color: '#94a3b8', size: 10 },
    },
    yaxis: {
      title: { text: 'Day of Week', font: { color: '#94a3b8', size: 12 } },
      autorange: 'reversed' as const,
      tickfont: { color: '#94a3b8', size: 11 },
    },
    margin: { l: 80, r: 20, t: 50, b: 60 },
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <span className="page-eyebrow">Operational Velocity & Channel Economics</span>
        <h1 className="page-title">Sales & Operational Performance</h1>
        <p className="page-description">
          Cross-store operational efficiency, peak period rush analysis, and ordering channel unit economics.
        </p>
      </div>

      {error && <div className="alert-box error">{error}</div>}

      <div className="charts-grid-two">
        <div className="card chart-card">
          <PlotlyChart data={channelData} layout={channelLayout} />
        </div>
        <div className="card chart-card">
          <PlotlyChart data={peakHeatmapData} layout={peakHeatmapLayout} />
        </div>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <h2 className="card-title" style={{ margin: 0 }}>
              Restaurant Location Performance Rankings
            </h2>
            <p style={{ margin: '4px 0 0', fontSize: '0.78rem', color: '#94a3b8' }}>
              Store-level P&L contribution, unit sales volume, and food loss tracking.
            </p>
          </div>
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
                <th className="text-right">Total Orders</th>
                <th className="text-right">Gross Revenue</th>
                <th className="text-right">Contribution Margin</th>
                <th className="text-right">Margin %</th>
                <th className="text-right">Total Waste Cost</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 6 }).map((_, idx) => (
                  <tr key={`skel-loc-${idx}`}>
                    <td><div className="skeleton skeleton-text" style={{ width: '130px' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '70px' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '80px' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '50px', marginLeft: 'auto' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '70px', marginLeft: 'auto' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '70px', marginLeft: 'auto' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '40px', marginLeft: 'auto' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '60px', marginLeft: 'auto' }} /></td>
                  </tr>
                ))
              ) : data?.locations.map((loc) => (
                <tr key={loc.source_restaurant_id}>
                  <td>
                    <strong style={{ color: '#f8fafc' }}>{loc.location_name}</strong>
                    <div><span className="code-id">{loc.source_restaurant_id}</span></div>
                  </td>
                  <td>{loc.city}</td>
                  <td>
                    <span className="category-pill">{loc.dining_type}</span>
                  </td>
                  <td className="text-right">{Number(loc.total_orders).toLocaleString()}</td>
                  <td className="text-right" style={{ fontWeight: 600 }}>
                    ${Number(loc.gross_revenue).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="text-right" style={{ color: '#10b981', fontWeight: 600 }}>
                    +${Number(loc.contribution_margin).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="text-right">
                    <span className="badge-tag badge-profit">{loc.margin_pct}%</span>
                  </td>
                  <td className="text-right" style={{ color: '#ef4444' }}>
                    ${Number(loc.total_waste_cost).toLocaleString('en-US', { minimumFractionDigits: 2 })}
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
