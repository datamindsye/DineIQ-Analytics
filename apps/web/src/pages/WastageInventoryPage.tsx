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

  const sparkAlgo = data?.ml_risk_summary?.spark_selected_algorithm || 'LogisticRegression';

  return (
    <div className="page-container">
      <div className="page-header">
        <span className="page-eyebrow">Forensic Accounting & MLlib Classifier</span>
        <h1 className="page-title">Wastage & Spoilage Intelligence</h1>
        <p className="page-description">
          Forensic food loss accounting, root cause diagnostics, and high-risk preparation warnings.
        </p>
      </div>

      {error && <div className="alert-box error">{error}</div>}

      {/* ML Wastage Risk KPI Overview */}
      {data?.ml_risk_summary && (
        <div className="metrics-grid" style={{ marginBottom: '24px' }}>
          <div className="metric-card" style={{ borderLeft: '4px solid #38bdf8' }}>
            <div className="metric-label">Evaluated ML Records</div>
            <div className="metric-value">{data.ml_risk_summary.total_evaluated?.toLocaleString() || 0}</div>
            <div className="metric-sub">Temporal split observations</div>
          </div>
          <div className="metric-card" style={{ borderLeft: '4px solid #ef4444' }}>
            <div className="metric-label">ML High-Risk Alerts</div>
            <div className="metric-value">{data.ml_risk_summary.predicted_high_risk_count?.toLocaleString() || 0}</div>
            <div className="metric-sub">Forward-looking alert instances</div>
          </div>
          <div className="metric-card" style={{ borderLeft: '4px solid #f59e0b' }}>
            <div className="metric-label">High-Risk Rate</div>
            <div className="metric-value">{data.ml_risk_summary.high_risk_rate_pct?.toFixed(2) || 0}%</div>
            <div className="metric-sub">Avg Risk Prob: {((data.ml_risk_summary.avg_risk_probability || 0) * 100).toFixed(1)}%</div>
          </div>
          <div className="metric-card" style={{ borderLeft: '4px solid #10b981' }}>
            <div className="metric-label">⚡ ML Champion Model</div>
            <div className="metric-value" style={{ fontSize: '1.25rem' }}>{sparkAlgo}</div>
            <div className="metric-sub">Spark MLlib Validation-Selected</div>
          </div>
        </div>
      )}

      <div className="charts-grid-two">
        <div className="card chart-card">
          <PlotlyChart data={reasonData} layout={reasonLayout} />
        </div>
        <div className="card chart-card">
          <PlotlyChart data={weeklyData} layout={weeklyLayout} />
        </div>
      </div>

      {/* Historical Wastage Section */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="badge-tag badge-hidden">HISTORICAL EVIDENCE</span>
              <h2 className="card-title" style={{ margin: 0 }}>High-Wastage Menu Items (Accounting Realization)</h2>
            </div>
            <p style={{ margin: '4px 0 0', fontSize: '0.78rem', color: '#94a3b8' }}>
              Identified by empirical accounting rule: Waste Cost Ratio &gt; 5% OR Waste Quantity Ratio &gt; 10%.
            </p>
          </div>
          <a
            href={apiService.getExportUrl('spark/mart_wastage.parquet')}
            className="btn btn-secondary"
            download
          >
            Export Historical Wastage CSV
          </a>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Item ID</th>
                <th>Item Name</th>
                <th className="text-right">Units Sold</th>
                <th className="text-right">Units Wasted</th>
                <th className="text-right">Wastage Cost Loss</th>
                <th>Historical Risk Status</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 6 }).map((_, idx) => (
                  <tr key={`skel-wst-${idx}`}>
                    <td><div className="skeleton skeleton-text" style={{ width: '80px' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '130px' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '50px', marginLeft: 'auto' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '50px', marginLeft: 'auto' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '65px', marginLeft: 'auto' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '80px' }} /></td>
                  </tr>
                ))
              ) : data?.high_risk_items && data.high_risk_items.length > 0 ? (
                data.high_risk_items.map((item) => (
                  <tr key={item.source_menu_item_id}>
                    <td><span className="code-id">{item.source_menu_item_id}</span></td>
                    <td><strong style={{ color: '#f8fafc' }}>{item.item_name}</strong></td>
                    <td className="text-right">{Number(item.sold_quantity).toLocaleString()}</td>
                    <td className="text-right" style={{ color: '#f59e0b' }}>{Number(item.waste_quantity).toLocaleString()}</td>
                    <td className="text-right">
                      <strong style={{ color: '#ef4444' }}>
                        ${Number(item.waste_cost).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </strong>
                    </td>
                    <td>
                      <span className="badge-tag badge-risk-high">HIGH RISK</span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '24px', color: '#94a3b8' }}>
                    No items currently exceeding historical forensic accounting thresholds.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ML Forward-Looking Predictive Wastage Risk Section */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="badge-tag badge-profit">ML PREDICTIVE INFERENCE</span>
              <h2 className="card-title" style={{ margin: 0 }}>
                Machine Learning Wastage Risk (Spark MLlib {sparkAlgo})
              </h2>
            </div>
            <p style={{ margin: '4px 0 0', fontSize: '0.78rem', color: '#94a3b8' }}>
              Supervised classification prediction models estimating forward-looking risk probabilities, independent of past realization.
            </p>
          </div>
          <a
            href={apiService.getExportUrl('spark/ml_wastage_risk.parquet')}
            className="btn btn-secondary"
            download
          >
            Export ML Wastage Risk CSV
          </a>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Menu Item ID</th>
                <th>Item Name</th>
                <th>Risk Probability</th>
                <th className="text-right">High Risk Alert Occurrences</th>
                <th>ML Predicted Status</th>
                <th>Model Pipeline</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 6 }).map((_, idx) => (
                  <tr key={`skel-mlwst-${idx}`}>
                    <td><div className="skeleton skeleton-text" style={{ width: '80px' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '130px' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '120px' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '70px', marginLeft: 'auto' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '80px' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '100px' }} /></td>
                  </tr>
                ))
              ) : data?.ml_predicted_risks && data.ml_predicted_risks.length > 0 ? (
                data.ml_predicted_risks.map((pred) => (
                  <tr key={pred.menu_item_id}>
                    <td><span className="code-id">{pred.menu_item_id}</span></td>
                    <td><strong style={{ color: '#f8fafc' }}>{pred.item_name}</strong></td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ width: '90px', height: '8px', background: '#1e293b', borderRadius: '4px', overflow: 'hidden' }}>
                          <div
                            style={{
                              width: `${Math.min(100, Math.max(0, pred.risk_probability * 100))}%`,
                              height: '100%',
                              background: pred.risk_probability > 0.5 ? 'linear-gradient(90deg, #dc2626, #ef4444)' : pred.risk_probability > 0.2 ? 'linear-gradient(90deg, #d97706, #f59e0b)' : 'linear-gradient(90deg, #059669, #10b981)',
                            }}
                          />
                        </div>
                        <span style={{ fontWeight: 600, fontSize: '0.82rem' }}>
                          {(pred.risk_probability * 100).toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td className="text-right">{pred.high_risk_alerts_count} alert periods</td>
                    <td>
                      <span className={`badge-tag ${pred.predicted_label === 1 ? 'badge-risk-high' : 'badge-volume'}`}>
                        {pred.predicted_risk_status}
                      </span>
                    </td>
                    <td>
                      <span className="category-pill">
                        ⚡ Spark {sparkAlgo}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '24px', color: '#94a3b8' }}>
                    No forward-looking ML risk predictions found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
