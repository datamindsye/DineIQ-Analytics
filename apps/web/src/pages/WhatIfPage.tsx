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

  useEffect(() => {
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

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-eyebrow">
          <span className="badge-tag badge-profit">DECISION SIMULATION</span>
          <span className="page-timestamp">Empirical Elasticity Model</span>
        </div>
        <h1 className="page-title">What-If Scenario Simulation Engine</h1>
        <p className="page-description">
          Interactive sensitivity simulation using empirical price elasticity estimates and baseline margins to forecast forward-looking contribution margin impact.
        </p>
      </div>

      {error && <div className="alert-box error">{error}</div>}

      <div className="whatif-grid-split">
        {/* Controls Card: Scenario Inputs */}
        <div className="card">
          <div className="section-label-bar">
            <span className="phase-indicator">STEP 1</span>
            <span className="phase-title">Scenario Parameter Adjustments</span>
          </div>

          <div className="slider-container">
            <div style={{ marginBottom: '18px' }}>
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
              <div className="slider-label-group">
                <span className="slider-label">Price Adjustment</span>
                <span className="slider-hint">Simulates menu price change</span>
              </div>
              <input
                type="range"
                min="-30"
                max="30"
                step="1"
                value={priceChange}
                onChange={(e) => setPriceChange(Number(e.target.value))}
                className="slider-input"
              />
              <span className={`slider-val ${priceChange > 0 ? 'pos' : priceChange < 0 ? 'neg' : ''}`}>
                {priceChange > 0 ? `+${priceChange}` : priceChange}%
              </span>
            </div>

            <div className="slider-row">
              <div className="slider-label-group">
                <span className="slider-label">Discount Shift</span>
                <span className="slider-hint">Promotional coupon adjustment</span>
              </div>
              <input
                type="range"
                min="-50"
                max="50"
                step="5"
                value={discountChange}
                onChange={(e) => setDiscountChange(Number(e.target.value))}
                className="slider-input"
              />
              <span className={`slider-val ${discountChange > 0 ? 'pos' : discountChange < 0 ? 'neg' : ''}`}>
                {discountChange > 0 ? `+${discountChange}` : discountChange}%
              </span>
            </div>

            <div className="slider-row">
              <div className="slider-label-group">
                <span className="slider-label">Wastage Reduction</span>
                <span className="slider-hint">Kitchen inventory efficiency</span>
              </div>
              <input
                type="range"
                min="0"
                max="50"
                step="5"
                value={wasteReduction}
                onChange={(e) => setWasteReduction(Number(e.target.value))}
                className="slider-input"
              />
              <span className="slider-val pos">+{wasteReduction}%</span>
            </div>
          </div>

          <div className="elasticity-rationale-box">
            <div className="elasticity-row">
              <span className="el-label">Applied Price Elasticity (&epsilon;):</span>
              <strong className="el-val">{result?.parameters.elasticity_applied ?? '—'}</strong>
            </div>
            <div className="elasticity-formula">
              Formula: <code>&Delta;Q / Q = &epsilon; &times; (&Delta;P / P)</code> combined with unit food cost & waste mitigation savings.
            </div>
          </div>
        </div>

        {/* Outcome Card: Estimated Impact */}
        <div className="card">
          <div className="section-label-bar">
            <span className="phase-indicator parallel">STEP 2</span>
            <span className="phase-title">Estimated Business Outcome</span>
            <span className="badge-tag badge-hidden" style={{ marginLeft: 'auto' }}>ESTIMATED</span>
          </div>

          {loading ? (
            <div className="chart-skeleton-box" style={{ padding: '60px 20px' }}>
              <div className="skeleton skeleton-chart" style={{ height: '180px' }} />
            </div>
          ) : result ? (
            <div>
              <div className="whatif-dish-header">
                <div>
                  <h3 className="dish-name">{result.item_name}</h3>
                  <code className="code-id">{result.item_id}</code>
                </div>
                <div className="baseline-chip">
                  <span>Baseline Base Price:</span>
                  <strong>${result.baseline.base_price.toFixed(2)}</strong>
                </div>
              </div>

              <div className="scenario-result-grid">
                <div className="scenario-box">
                  <div className="metric-label">Estimated Price</div>
                  <div className="metric-value">${result.estimated_outcome.estimated_price.toFixed(2)}</div>
                  <div className="metric-sub">
                    <span className="badge-pill-sub">Base: ${result.baseline.base_price.toFixed(2)}</span>
                  </div>
                </div>

                <div className="scenario-box">
                  <div className="metric-label">Estimated Demand</div>
                  <div className="metric-value">{result.estimated_outcome.estimated_volume.toLocaleString()}</div>
                  <div className="metric-sub">
                    <span className={result.estimated_outcome.volume_delta_pct >= 0 ? 'scenario-delta positive' : 'scenario-delta negative'}>
                      {result.estimated_outcome.volume_delta_pct >= 0 ? `+${result.estimated_outcome.volume_delta_pct}` : result.estimated_outcome.volume_delta_pct}% units
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

                <div className="scenario-box highlight-box">
                  <div className="metric-label">Estimated Contribution Margin</div>
                  <div className="metric-value" style={{ color: '#10b981' }}>
                    ${result.estimated_outcome.estimated_contribution_margin.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </div>
                  <div className="metric-sub">
                    <span className={result.estimated_outcome.margin_delta >= 0 ? 'scenario-delta positive' : 'scenario-delta negative'}>
                      {result.estimated_outcome.margin_delta >= 0 ? `+$${result.estimated_outcome.margin_delta.toFixed(2)}` : `-$${Math.abs(result.estimated_outcome.margin_delta).toFixed(2)}`}
                    </span>
                  </div>
                </div>
              </div>

              {/* Step 3: Business Interpretation & Disclaimer */}
              <div className="whatif-interpretation-box">
                <div className="interp-header">
                  <span className="interp-icon">📊</span>
                  <span className="interp-title">Business Interpretation</span>
                </div>
                <p className="interp-text">
                  A price change of {priceChange >= 0 ? `+${priceChange}` : priceChange}% alongside a {wasteReduction}% reduction in kitchen wastage is projected to produce a net margin shift of{' '}
                  <strong style={{ color: result.estimated_outcome.margin_delta >= 0 ? '#10b981' : '#ef4444' }}>
                    {result.estimated_outcome.margin_delta >= 0 ? `+$${result.estimated_outcome.margin_delta.toFixed(2)}` : `-$${Math.abs(result.estimated_outcome.margin_delta).toFixed(2)}`}
                  </strong>.
                </p>
                <div className="whatif-disclaimer">
                  <span>ℹ️ {result.disclaimer}</span>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};
