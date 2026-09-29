import React, { useEffect, useState } from 'react';
import { PlotlyChart } from '../components/charts/PlotlyChart';
import { useFilters } from '../context/useFilters';
import { apiService } from '../services/api';
import type { DemandPricingResponse } from '../types';

export const DemandPricingPage: React.FC = () => {
  const { selectedLocation } = useFilters();
  const [data, setData] = useState<DemandPricingResponse | null>(null);
  const [selectedItem, setSelectedItem] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    apiService
      .getDemandPricing({
        menu_item_id: selectedItem || undefined,
        restaurant_id: selectedLocation || undefined,
      })
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        if (isMounted) setError(err instanceof Error ? err.message : 'Failed loading demand & pricing');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedLocation, selectedItem]);

  const [pipelineView, setPipelineView] = useState<'both' | 'spark' | 'python'>('both');

  // Forecast vs Actuals curve (Dual Pipeline)
  const sparkCurve = data?.demand_forecast_curve || [];
  const pythonCurve = data?.python_demand_forecast_curve || [];

  const sparkAlgo = data?.spark_selected_algorithm || 'GBTRegressor';
  const pythonAlgo = data?.python_selected_algorithm || 'GradientBoostingRegressor';

  const forecastData: Array<{
    x: string[];
    y: number[];
    type: 'scatter';
    mode: 'lines+markers' | 'lines';
    name: string;
    line: { color: string; width: number; dash?: 'dash' | 'dot' };
  }> = [
    {
      x: sparkCurve.map((c) => c.week_start_date),
      y: sparkCurve.map((c) => c.actual_quantity),
      type: 'scatter',
      mode: 'lines+markers',
      name: 'Actual Sold Quantity',
      line: { color: '#38bdf8', width: 2.5 },
    },
  ];

  if (pipelineView === 'both' || pipelineView === 'spark') {
    forecastData.push({
      x: sparkCurve.map((c) => c.week_start_date),
      y: sparkCurve.map((c) => c.predicted_quantity),
      type: 'scatter',
      mode: 'lines',
      name: `⚡ Spark MLlib (${sparkAlgo})`,
      line: { color: '#10b981', dash: 'dash', width: 2 },
    });
  }

  if (pipelineView === 'both' || pipelineView === 'python') {
    forecastData.push({
      x: pythonCurve.map((c) => c.week_start_date),
      y: pythonCurve.map((c) => c.predicted_quantity),
      type: 'scatter',
      mode: 'lines',
      name: `🐍 Python Sklearn (${pythonAlgo})`,
      line: { color: '#f59e0b', dash: 'dot', width: 2 },
    });
  }

  const forecastLayout = {
    title: {
      text: 'Demand Forecasting: Actual Sales vs ML Champion Predictions Across Splits',
      font: { size: 15, color: '#f8fafc' },
    },
    xaxis: { title: { text: 'ISO Week Starting Date', font: { color: '#94a3b8' } }, gridcolor: '#334155' },
    yaxis: { title: { text: 'Units Demanded', font: { color: '#94a3b8' } }, gridcolor: '#334155' },
    legend: { font: { color: '#94a3b8' } },
  };

  // Elasticity Pie
  const elDist = data?.elasticity_distribution || {};
  const elChartData = [
    {
      values: Object.values(elDist),
      labels: Object.keys(elDist),
      type: 'pie' as const,
      hole: 0.5,
      marker: {
        colors: Object.keys(elDist).map((cls) => {
          if (cls === 'Elastic') return '#f59e0b';
          if (cls === 'Inelastic') return '#10b981';
          return '#38bdf8';
        }),
      },
    },
  ];

  const elChartLayout = {
    title: { text: 'Price Sensitivity Class Distribution', font: { size: 15, color: '#f8fafc' } },
    legend: { font: { color: '#94a3b8' } },
    margin: { l: 20, r: 20, t: 40, b: 20 },
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <span className="page-eyebrow">Predictive Modeling & Microeconomics</span>
        <h1 className="page-title">Demand Forecasting & Price Elasticity</h1>
        <p className="page-description">
          Dual-pipeline ML demand trajectories ({sparkAlgo} vs {pythonAlgo}) and empirical price elasticity estimates.
        </p>
      </div>

      {error && <div className="alert-box error">{error}</div>}

      {/* Dual Pipeline Champions Overview Cards */}
      <div className="metrics-grid" style={{ marginBottom: '24px' }}>
        <div className="metric-card" style={{ borderLeft: '4px solid #10b981' }}>
          <div className="metric-label">⚡ Spark MLlib Champion</div>
          <div className="metric-value" style={{ fontSize: '1.25rem' }}>{sparkAlgo}</div>
          <div className="metric-sub">Distributed regression tournament winner</div>
        </div>
        <div className="metric-card" style={{ borderLeft: '4px solid #f59e0b' }}>
          <div className="metric-label">🐍 Python Sklearn Champion</div>
          <div className="metric-value" style={{ fontSize: '1.25rem' }}>{pythonAlgo}</div>
          <div className="metric-sub">Scikit-learn tournament winner</div>
        </div>
        <div className="metric-card" style={{ borderLeft: '4px solid #38bdf8' }}>
          <div className="metric-label">Forecast Evaluation Points</div>
          <div className="metric-value">{sparkCurve.length} Weeks</div>
          <div className="metric-sub">Chronological holdout series</div>
        </div>
        <div className="metric-card" style={{ borderLeft: '4px solid #818cf8' }}>
          <div className="metric-label">Elasticity Observations</div>
          <div className="metric-value">{data?.pricing_items?.length || 0} Items</div>
          <div className="metric-sub">Empirical price adjustments recorded</div>
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-group">
          <input
            type="text"
            placeholder="Filter by Dish ID (e.g. DISH-0001)..."
            value={selectedItem}
            onChange={(e) => setSelectedItem(e.target.value)}
            className="search-input"
          />
          {selectedItem && (
            <button className="btn btn-secondary" onClick={() => setSelectedItem('')}>
              Clear Dish Filter
            </button>
          )}
        </div>

        {/* Dual-Pipeline View Selector */}
        <div className="filter-group">
          <div className="tab-group" style={{ margin: 0 }}>
            <button
              className={`tab-btn ${pipelineView === 'both' ? 'active' : ''}`}
              onClick={() => setPipelineView('both')}
            >
              Dual-Pipeline (Both)
            </button>
            <button
              className={`tab-btn ${pipelineView === 'spark' ? 'active' : ''}`}
              onClick={() => setPipelineView('spark')}
            >
              ⚡ Spark ({sparkAlgo})
            </button>
            <button
              className={`tab-btn ${pipelineView === 'python' ? 'active' : ''}`}
              onClick={() => setPipelineView('python')}
            >
              🐍 Python ({pythonAlgo})
            </button>
          </div>
        </div>

        <div className="filter-group">
          <a
            href={apiService.getExportUrl('spark/ml_demand_forecast.parquet')}
            className="btn btn-secondary"
            download
          >
            Export Spark CSV
          </a>
          <a
            href={apiService.getExportUrl('python/ml_demand_forecast.parquet')}
            className="btn btn-secondary"
            download
          >
            Export Python CSV
          </a>
          <a
            href={apiService.getExportUrl('spark/mart_pricing.parquet')}
            className="btn btn-secondary"
            download
          >
            Export Elasticity CSV
          </a>
        </div>
      </div>

      <div className="demand-pricing-grid">
        <div className="card chart-card">
          <PlotlyChart data={forecastData} layout={forecastLayout} />
        </div>
        <div className="card chart-card">
          <PlotlyChart data={elChartData} layout={elChartLayout} />
        </div>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <h2 className="card-title" style={{ margin: 0 }}>Price Elasticity Observations</h2>
            <p style={{ margin: '4px 0 0', fontSize: '0.78rem', color: '#94a3b8' }}>
              Note: Price elasticity estimates reflect historical demand responses during price adjustments and do not constitute causal proof.
            </p>
          </div>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Item ID</th>
                <th>Item Name</th>
                <th className="text-right">Current Price</th>
                <th className="text-right">Pre Price</th>
                <th className="text-right">Post Price</th>
                <th className="text-right">Pre Volume</th>
                <th className="text-right">Post Volume</th>
                <th className="text-right">Elasticity (ε)</th>
                <th>Sensitivity Class</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 8 }).map((_, idx) => (
                  <tr key={`skel-prc-${idx}`}>
                    <td><div className="skeleton skeleton-text" style={{ width: '80px' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '130px' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '45px', marginLeft: 'auto' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '45px', marginLeft: 'auto' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '45px', marginLeft: 'auto' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '50px', marginLeft: 'auto' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '50px', marginLeft: 'auto' }} /></td>
                    <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '45px', marginLeft: 'auto' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '80px' }} /></td>
                  </tr>
                ))
              ) : data?.pricing_items.map((prc, idx) => (
                <tr key={`${prc.source_menu_item_id}-${idx}`}>
                  <td><span className="code-id">{prc.source_menu_item_id}</span></td>
                  <td><strong style={{ color: '#f8fafc' }}>{prc.item_name}</strong></td>
                  <td className="text-right">${Number(prc.base_price).toFixed(2)}</td>
                  <td className="text-right" style={{ color: '#94a3b8' }}>${Number(prc.pre_price).toFixed(2)}</td>
                  <td className="text-right">${Number(prc.post_price).toFixed(2)}</td>
                  <td className="text-right" style={{ color: '#94a3b8' }}>{Number(prc.pre_quantity).toLocaleString()}</td>
                  <td className="text-right">{Number(prc.post_quantity).toLocaleString()}</td>
                  <td className="text-right">
                    <strong style={{ color: prc.elasticity !== null && Number(prc.elasticity) < -1 ? '#f59e0b' : '#38bdf8' }}>
                      {prc.elasticity !== null ? Number(prc.elasticity).toFixed(3) : 'N/A'}
                    </strong>
                  </td>
                  <td>
                    <span
                      className={`badge-tag ${
                        prc.sensitivity_class === 'Inelastic'
                          ? 'badge-profit'
                          : prc.sensitivity_class === 'Elastic'
                          ? 'badge-hidden'
                          : 'badge-volume'
                      }`}
                    >
                      {prc.sensitivity_class || 'Standard'}
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
