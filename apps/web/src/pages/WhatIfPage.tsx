import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import type { WhatIfResponse } from '../types';

export const WhatIfPage: React.FC = () => {
  const [itemId, setItemId] = useState<string>('DISH-0001');
  const [priceChange, setPriceChange] = useState<number>(5);
  const [discountChange, setDiscountChange] = useState<number>(0);
  const [wasteReduction, setWasteReduction] = useState<number>(10);
  const [result, setResult] = useState<WhatIfResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const calculateScenario = React.useCallback(() => {
    let isMounted = true;
    apiService
      .runWhatIf({
        item_id: itemId,
        price_change_pct: priceChange,
        discount_change_pct: discountChange,
        waste_reduction_pct: wasteReduction,
      })
      .then((res) => {
        if (isMounted) {
          setResult(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed running what-if calculation');
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [itemId, priceChange, discountChange, wasteReduction]);

  useEffect(() => {
    return calculateScenario();
  }, [calculateScenario]);

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">What-If Scenario Simulation Engine</h1>
        <p className="page-description">
          Interactive sensitivity simulation using empirical price elasticity estimates and baseline margins.
        </p>
      </div>

      {error && <div className="alert-box error">{error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Controls Card */}
        <div className="card">
          <h2 className="card-title">Scenario Parameter Adjustments</h2>

          <div className="slider-container">
            <div>
              <label className="slider-label" htmlFor="whatif-dish-id" style={{ display: 'block', marginBottom: '8px' }}>
                Target Menu Item ID:
              </label>
              <input
                id="whatif-dish-id"
                type="text"
                value={itemId}
                onChange={(e) => setItemId(e.target.value.toUpperCase())}
                className="search-input"
                style={{ width: '100%' }}
                placeholder="Enter Dish ID (e.g. DISH-0001, DISH-0002)..."
              />
            </div>

            <div className="slider-row">
              <span className="slider-label">Price Adjustment:</span>
              <input
                type="range"
                min="-30"
                max="30"
                step="1"
                value={priceChange}
                onChange={(e) => setPriceChange(Number(e.target.value))}
                className="slider-input"
              />
              <span className="slider-val">{priceChange > 0 ? `+${priceChange}` : priceChange}%</span>
            </div>

            <div className="slider-row">
              <span className="slider-label">Discount Rate Shift:</span>
              <input
                type="range"
                min="-50"
                max="50"
                step="5"
                value={discountChange}
                onChange={(e) => setDiscountChange(Number(e.target.value))}
                className="slider-input"
              />
              <span className="slider-val">{discountChange > 0 ? `+${discountChange}` : discountChange}%</span>
            </div>

            <div className="slider-row">
              <span className="slider-label">Wastage Reduction Goal:</span>
              <input
                type="range"
                min="0"
                max="50"
                step="5"
                value={wasteReduction}
                onChange={(e) => setWasteReduction(Number(e.target.value))}
                className="slider-input"
              />
              <span className="slider-val">+{wasteReduction}%</span>
            </div>
          </div>

          <div style={{ background: 'rgba(51, 65, 85, 0.3)', padding: '14px', borderRadius: '8px', fontSize: '0.8rem', color: '#94a3b8' }}>
            <div><strong>Applied Price Elasticity (ε):</strong> {result?.parameters.elasticity_applied ?? '—'}</div>
            <div style={{ marginTop: '4px' }}>
              Formula: <code>&Delta;Q/Q = &epsilon; &times; (&Delta;P/P)</code> combined with food cost and waste mitigation savings.
            </div>
          </div>
        </div>

        {/* Outcome Card */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h2 className="card-title" style={{ margin: 0 }}>
              Simulated Financial Outcome
            </h2>
            <span className="badge-tag badge-hidden">{result?.status || 'ESTIMATE'}</span>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>Simulating scenario impact...</div>
          ) : result ? (
            <div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', marginBottom: '14px' }}>
                {result.item_name} (<code>{result.item_id}</code>)
              </div>

              <div className="scenario-result-grid">
                <div className="scenario-box">
                  <div className="metric-label">Estimated Price</div>
                  <div className="metric-value">${result.estimated_outcome.estimated_price.toFixed(2)}</div>
                  <div className="metric-sub">Base: ${result.baseline.base_price.toFixed(2)}</div>
                </div>

                <div className="scenario-box">
                  <div className="metric-label">Demand Volume</div>
                  <div className="metric-value">{result.estimated_outcome.estimated_volume.toLocaleString()}</div>
                  <div className="metric-sub">
                    <span className={result.estimated_outcome.volume_delta_pct >= 0 ? 'scenario-delta positive' : 'scenario-delta negative'}>
                      {result.estimated_outcome.volume_delta_pct >= 0 ? `+${result.estimated_outcome.volume_delta_pct}` : result.estimated_outcome.volume_delta_pct}%
                    </span>
                  </div>
                </div>

                <div className="scenario-box">
                  <div className="metric-label">Estimated Revenue</div>
                  <div className="metric-value">${result.estimated_outcome.estimated_revenue.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
                  <div className="metric-sub">
                    <span className={result.estimated_outcome.revenue_delta >= 0 ? 'scenario-delta positive' : 'scenario-delta negative'}>
                      {result.estimated_outcome.revenue_delta >= 0 ? `+$${result.estimated_outcome.revenue_delta.toFixed(2)}` : `-$${Math.abs(result.estimated_outcome.revenue_delta).toFixed(2)}`}
                    </span>
                  </div>
                </div>

                <div className="scenario-box">
                  <div className="metric-label">Contribution Margin</div>
                  <div className="metric-value">${result.estimated_outcome.estimated_contribution_margin.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
                  <div className="metric-sub">
                    <span className={result.estimated_outcome.margin_delta >= 0 ? 'scenario-delta positive' : 'scenario-delta negative'}>
                      {result.estimated_outcome.margin_delta >= 0 ? `+$${result.estimated_outcome.margin_delta.toFixed(2)}` : `-$${Math.abs(result.estimated_outcome.margin_delta).toFixed(2)}`}
                    </span>
                  </div>
                </div>
              </div>

              <div style={{ marginTop: '20px', borderTop: '1px solid rgba(51, 65, 85, 0.5)', paddingTop: '12px', fontSize: '0.75rem', color: '#64748b', fontStyle: 'italic' }}>
                {result.disclaimer}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};
