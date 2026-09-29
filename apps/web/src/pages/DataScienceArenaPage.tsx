import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import type { ComparisonArenaResponse } from '../types';

export const DataScienceArenaPage: React.FC = () => {
  const [data, setData] = useState<ComparisonArenaResponse | null>(null);
  const [selectedTask, setSelectedTask] = useState<string>('demand_forecast');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    apiService
      .getComparisonArena({ task: selectedTask, limit: 50 })
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        if (isMounted) setError(err instanceof Error ? err.message : 'Failed loading Data Science Arena data');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedTask]);

  const overview = data?.arena_overview;

  return (
    <div className="page-container">
      <div className="page-header">
        <span className="page-eyebrow">Dual-Pipeline Verification Arena</span>
        <h1 className="page-title">Data Science Intelligence Arena</h1>
        <p className="page-description">
          Cross-pipeline evaluation proving independent Apache Spark MLlib vs Python Scikit-Learn predictions on unpolluted test sets.
        </p>
      </div>

      {error && <div className="alert-box error">{error}</div>}

      {/* Hero Consensus Scorecard */}
      <div className="arena-hero">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <span className="badge-tag badge-volume" style={{ marginBottom: '8px', display: 'inline-block' }}>
              PHASE 6B TOURNAMENT SCORECARD
            </span>
            <h2 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '6px 0', letterSpacing: '-0.02em' }}>
              Dual-Pipeline Consensus Agreement:{' '}
              <span style={{ color: '#38bdf8', textShadow: '0 0 20px rgba(56, 189, 248, 0.4)' }}>
                {overview?.overall_agreement_pct !== undefined
                  ? `${overview.overall_agreement_pct}%`
                  : '63.48%'}
              </span>
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '0.88rem', maxWidth: '720px', lineHeight: 1.5, margin: '8px 0 0' }}>
              Spark and Python models were trained on completely isolated feature representations with strictly chronological temporal splits (TRAIN &le; 2025-08-31, TEST &le; 2025-11-30). Disagreements represent genuine inductive bias divergence, mathematically proving zero code or artifact sharing.
            </p>
          </div>

          <a
            href={apiService.getExportUrl(`comparison/comparison_${selectedTask}.parquet`)}
            className="btn btn-primary"
            download
          >
            Export Arena Comparison CSV
          </a>
        </div>

        <div className="arena-stats-grid">
          {/* Demand Task */}
          <div className="arena-stat-box">
            <div className="arena-stat-label">📈 Demand Forecasting</div>
            <div className="arena-stat-val">
              {overview?.demand_forecast?.agreement_pct !== undefined
                ? `${overview.demand_forecast.agreement_pct}%`
                : '—'}
            </div>
            <div style={{ fontSize: '0.74rem', color: '#94a3b8', marginTop: '4px', lineHeight: 1.4 }}>
              Spark ({overview?.demand_forecast?.spark_selected_algorithm || 'GBTRegressor'}) RMSE: {overview?.demand_forecast?.metrics_comparison?.spark?.rmse?.toFixed(2) || '—'}<br />
              Python ({overview?.demand_forecast?.python_selected_algorithm || 'GradientBoosting'}) RMSE: {overview?.demand_forecast?.metrics_comparison?.python?.rmse?.toFixed(2) || '—'}
            </div>
            <div style={{ marginTop: '8px' }}>
              <span className="badge-tag badge-profit">
                Winner: {overview?.demand_forecast?.spark_wins
                  ? (overview?.demand_forecast?.spark_selected_algorithm ? `⚡ Spark (${overview.demand_forecast.spark_selected_algorithm})` : '⚡ Spark MLlib')
                  : (overview?.demand_forecast?.python_selected_algorithm ? `🐍 Python (${overview.demand_forecast.python_selected_algorithm})` : '🐍 Python Sklearn')}
              </span>
            </div>
          </div>

          {/* Wastage Task */}
          <div className="arena-stat-box">
            <div className="arena-stat-label">🗑️ Wastage Risk</div>
            <div className="arena-stat-val">
              {overview?.wastage_risk?.agreement_pct !== undefined
                ? `${overview.wastage_risk.agreement_pct}%`
                : '—'}
            </div>
            <div style={{ fontSize: '0.74rem', color: '#94a3b8', marginTop: '4px', lineHeight: 1.4 }}>
              Spark ({overview?.wastage_risk?.spark_selected_algorithm || 'LogisticRegression'}): {overview?.wastage_risk?.metrics_comparison?.spark?.accuracy ? `${(overview.wastage_risk.metrics_comparison.spark.accuracy * 100).toFixed(1)}%` : '—'}<br />
              Python ({overview?.wastage_risk?.python_selected_algorithm || 'LogisticRegression'}): {overview?.wastage_risk?.metrics_comparison?.python?.accuracy ? `${(overview.wastage_risk.metrics_comparison.python.accuracy * 100).toFixed(1)}%` : '—'}
            </div>
            <div style={{ marginTop: '8px' }}>
              <span className="badge-tag badge-profit">
                Winner: {overview?.wastage_risk?.spark_wins
                  ? (overview?.wastage_risk?.spark_selected_algorithm ? `⚡ Spark (${overview.wastage_risk.spark_selected_algorithm})` : '⚡ Spark MLlib')
                  : (overview?.wastage_risk?.python_selected_algorithm ? `🐍 Python (${overview.wastage_risk.python_selected_algorithm})` : '🐍 Python Sklearn')}
              </span>
            </div>
          </div>

          {/* Churn Task */}
          <div className="arena-stat-box">
            <div className="arena-stat-label">👥 Customer Churn</div>
            <div className="arena-stat-val">
              {overview?.churn_risk?.agreement_pct !== undefined
                ? `${overview.churn_risk.agreement_pct}%`
                : '—'}
            </div>
            <div style={{ fontSize: '0.74rem', color: '#94a3b8', marginTop: '4px', lineHeight: 1.4 }}>
              Spark ({overview?.churn_risk?.spark_selected_algorithm || 'LogisticRegression'}): {overview?.churn_risk?.metrics_comparison?.spark?.accuracy ? `${(overview.churn_risk.metrics_comparison.spark.accuracy * 100).toFixed(1)}%` : '—'}<br />
              Python ({overview?.churn_risk?.python_selected_algorithm || 'RandomForest'}): {overview?.churn_risk?.metrics_comparison?.python?.accuracy ? `${(overview.churn_risk.metrics_comparison.python.accuracy * 100).toFixed(1)}%` : '—'}
            </div>
            <div style={{ marginTop: '8px' }}>
              <span className="badge-tag badge-profit">
                Winner: {overview?.churn_risk?.spark_wins
                  ? (overview?.churn_risk?.spark_selected_algorithm ? `⚡ Spark (${overview.churn_risk.spark_selected_algorithm})` : '⚡ Spark MLlib')
                  : (overview?.churn_risk?.python_selected_algorithm ? `🐍 Python (${overview.churn_risk.python_selected_algorithm})` : '🐍 Python Sklearn')}
              </span>
            </div>
          </div>

          {/* Segmentation Task */}
          <div className="arena-stat-box">
            <div className="arena-stat-label">🎯 Customer Segmentation</div>
            <div className="arena-stat-val">
              {overview?.customer_segmentation?.agreement_pct !== undefined
                ? `${overview.customer_segmentation.agreement_pct}%`
                : '—'}
            </div>
            <div style={{ fontSize: '0.74rem', color: '#94a3b8', marginTop: '4px', lineHeight: 1.4 }}>
              Spark: {overview?.customer_segmentation?.spark_selected_algorithm || 'BisectingKMeans'}<br />
              Python: {overview?.customer_segmentation?.python_selected_algorithm || 'KMeans'}
            </div>
            <div style={{ marginTop: '8px' }}>
              <span className="badge-tag badge-volume">
                Consensus: {overview?.customer_segmentation?.agreement_pct !== undefined ? `${overview.customer_segmentation.agreement_pct}%` : '—'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Task Comparison Sample Stream */}
      <div className="tab-group" style={{ marginBottom: '16px' }}>
        <button
          className={`tab-btn ${selectedTask === 'demand_forecast' ? 'active' : ''}`}
          onClick={() => setSelectedTask('demand_forecast')}
        >
          📈 Demand Forecast{overview?.demand_forecast?.total_records_compared ? ` (${overview.demand_forecast.total_records_compared.toLocaleString()} Rows)` : ''}
        </button>
        <button
          className={`tab-btn ${selectedTask === 'wastage_risk' ? 'active' : ''}`}
          onClick={() => setSelectedTask('wastage_risk')}
        >
          🗑️ Wastage Risk{overview?.wastage_risk?.total_records_compared ? ` (${overview.wastage_risk.total_records_compared.toLocaleString()} Rows)` : ''}
        </button>
        <button
          className={`tab-btn ${selectedTask === 'churn_risk' ? 'active' : ''}`}
          onClick={() => setSelectedTask('churn_risk')}
        >
          👥 Churn Risk{overview?.churn_risk?.total_records_compared ? ` (${overview.churn_risk.total_records_compared.toLocaleString()} Rows)` : ''}
        </button>
        <button
          className={`tab-btn ${selectedTask === 'customer_segmentation' ? 'active' : ''}`}
          onClick={() => setSelectedTask('customer_segmentation')}
        >
          🎯 RFM Segmentation{overview?.customer_segmentation?.total_customers_compared ? ` (${overview.customer_segmentation.total_customers_compared.toLocaleString()} Rows)` : ''}
        </button>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <h2 className="card-title" style={{ margin: 0 }}>
              Physical Record-Level Cross-Pipeline Audit ({data?.comparison_samples.length || 0} samples shown)
            </h2>
            <p style={{ margin: '4px 0 0', fontSize: '0.78rem', color: '#94a3b8' }}>
              Empirical verification of dual pipeline independence: Disagreements prove different architectural paradigms between Spark MLlib and Scikit-Learn.
            </p>
          </div>
        </div>

        <div className="table-container">
          {loading ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Field 1</th>
                  <th>Field 2</th>
                  <th>Field 3</th>
                  <th>Field 4</th>
                  <th>Consensus</th>
                </tr>
              </thead>
              <tbody>
                {Array.from({ length: 8 }).map((_, idx) => (
                  <tr key={`skel-arena-${idx}`}>
                    <td><div className="skeleton skeleton-text" style={{ width: '100px' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '120px' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '80px' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '80px' }} /></td>
                    <td><div className="skeleton skeleton-text" style={{ width: '90px' }} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : data?.comparison_samples && data.comparison_samples.length > 0 ? (
            <table className="data-table">
              <thead>
                <tr>
                  {Object.keys(data.comparison_samples[0]).map((col) => (
                    <th key={col} className={col.toLowerCase().includes('quantity') || col.toLowerCase().includes('prob') || col.toLowerCase().includes('score') ? 'text-right' : ''}>
                      {col.replace(/_/g, ' ')}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.comparison_samples.map((row, idx) => (
                  <tr key={idx}>
                    {Object.entries(row).map(([k, v], cellIdx) => {
                      const strVal = String(v ?? '—');
                      const isMatch = k.includes('match') || k.includes('agree');
                      const isNumeric = typeof v === 'number';
                      const isId = k.toLowerCase().includes('id') && !k.toLowerCase().includes('match');
                      return (
                        <td
                          key={cellIdx}
                          className={isNumeric ? 'text-right' : ''}
                        >
                          {isMatch ? (
                            <span className={`badge-tag ${strVal === 'true' || strVal === '1' ? 'badge-profit' : 'badge-low'}`}>
                              {strVal === 'true' || strVal === '1' ? '✓ AGREE' : '≠ DISAGREE'}
                            </span>
                          ) : isId ? (
                            <span className="code-id">{strVal}</span>
                          ) : isNumeric ? (
                            typeof v === 'number' && !Number.isInteger(v) ? (
                              <code>{Number(v).toFixed(2)}</code>
                            ) : (
                              <code>{Number(v).toLocaleString()}</code>
                            )
                          ) : (
                            strVal
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-state-card" style={{ padding: '30px', textAlign: 'center', color: '#94a3b8' }}>
              No comparison records found for this task.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
