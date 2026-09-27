import React, { useEffect, useState } from 'react';
import { PlotlyChart } from '../components/charts/PlotlyChart';
import { useFilters } from '../context/useFilters';
import { apiService } from '../services/api';
import type { WastageInventoryResponse } from '../types';

export const WastageInventoryPage: React.FC = () => {
  const { selectedLocation } = useFilters();
  const [data, setData] = useState<WastageInventoryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    apiService
      .getWastageInventory({ restaurant_id: selectedLocation || undefined })
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        if (isMounted) setError(err instanceof Error ? err.message : 'Failed loading wastage inventory');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedLocation]);

  // Wastage causes bar chart
  const reasonData = [
    {
      x: data?.reasons.map((r) => r.primary_reason) || [],
      y: data?.reasons.map((r) => r.waste_cost) || [],
      type: 'bar' as const,
      marker: { color: '#ef4444' },
    },
  ];

  const reasonLayout = {
    title: { text: 'Wastage Financial Loss by Root Cause ($)', font: { size: 15, color: '#f8fafc' } },
    xaxis: { gridcolor: '#334155', font: { color: '#94a3b8' } },
    yaxis: { title: { text: 'Loss Amount ($)' }, gridcolor: '#334155', font: { color: '#94a3b8' } },
  };

  // Weekly trend
  const weeklyData = [
    {
      x: data?.weekly_trend.map((w) => `W${w.calendar_week} ${w.calendar_year}`) || [],
      y: data?.weekly_trend.map((w) => w.waste_cost) || [],
      type: 'scatter' as const,
      mode: 'lines+markers' as const,
      line: { color: '#f59e0b', width: 2 },
    },
  ];

  const weeklyLayout = {
    title: { text: 'Weekly Food Wastage Loss Trajectory', font: { size: 15, color: '#f8fafc' } },
    xaxis: { gridcolor: '#334155', font: { color: '#94a3b8' } },
    yaxis: { title: { text: 'Waste Cost ($)' }, gridcolor: '#334155', font: { color: '#94a3b8' } },
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Wastage & Spoilage Intelligence</h1>
        <p className="page-description">
          Forensic food loss accounting, root cause diagnostics, and high-risk preparation warnings.
        </p>
      </div>

      {error && <div className="alert-box error">{error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        <div className="card chart-card">
          <PlotlyChart data={reasonData} layout={reasonLayout} />
        </div>
        <div className="card chart-card">
          <PlotlyChart data={weeklyData} layout={weeklyLayout} />
        </div>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div>
            <h2 className="card-title" style={{ margin: 0 }}>High Wastage Risk Menu Items</h2>
            <p style={{ margin: '4px 0 0', fontSize: '0.78rem', color: '#94a3b8' }}>
              Identified by the approved forensic rule: Waste Cost Ratio &gt; 5% OR Waste Quantity Ratio &gt; 10%.
            </p>
          </div>
          <a
            href={apiService.getExportUrl('spark/mart_wastage.parquet')}
            className="btn btn-secondary"
            download
          >
            Export Wastage CSV
          </a>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Item ID</th>
                <th>Item Name</th>
                <th>Units Sold</th>
                <th>Units Wasted</th>
                <th>Wastage Cost Loss</th>
                <th>Risk Status</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '30px' }}>Loading wastage risks...</td>
                </tr>
              ) : data?.high_risk_items.map((item) => (
                <tr key={item.source_menu_item_id}>
                  <td><code>{item.source_menu_item_id}</code></td>
                  <td><strong>{item.item_name}</strong></td>
                  <td>{Number(item.sold_quantity).toLocaleString()}</td>
                  <td>{Number(item.waste_quantity).toLocaleString()}</td>
                  <td>
                    <strong style={{ color: '#ef4444' }}>
                      ${Number(item.waste_cost).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </strong>
                  </td>
                  <td>
                    <span className="badge-tag badge-risk-high">HIGH RISK</span>
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
