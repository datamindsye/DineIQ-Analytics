import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import type { PromotionsBasketResponse } from '../types';

export const PromotionsBasketPage: React.FC = () => {
  const [data, setData] = useState<PromotionsBasketResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'promotions' | 'basket'>('promotions');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    apiService
      .getPromotionsBasket()
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        if (isMounted) setError(err instanceof Error ? err.message : 'Failed loading promotions & basket');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="page-container">
      <div className="page-header">
        <span className="page-eyebrow">Marketing Analytics & Association Rules</span>
        <h1 className="page-title">Promotions & Market Basket Analysis</h1>
        <p className="page-description">
          Campaign margin impact diagnostics, promotion trap isolation, and association rule mining for pairing bundles.
        </p>
      </div>

      {error && <div className="alert-box error">{error}</div>}

      <div className="tab-group" style={{ marginBottom: '16px' }}>
        <button
          className={`tab-btn ${activeTab === 'promotions' ? 'active' : ''}`}
          onClick={() => setActiveTab('promotions')}
        >
          🏷️ Promotional Campaigns ({data?.promotions.length || 0})
        </button>
        <button
          className={`tab-btn ${activeTab === 'basket' ? 'active' : ''}`}
          onClick={() => setActiveTab('basket')}
        >
          🛒 Market Basket Pairings ({data?.market_basket_pairs.length || 0})
        </button>
      </div>

      {activeTab === 'promotions' ? (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
            <div>
              <h2 className="card-title" style={{ margin: 0 }}>Promotional Campaign Performance</h2>
              <p style={{ margin: '4px 0 0', fontSize: '0.78rem', color: '#94a3b8' }}>
                Contribution margin after discounting. Promotion traps indicate campaigns driving unit volume at negative incremental margin.
              </p>
            </div>
            <a
              href={apiService.getExportUrl('spark/mart_promotions.parquet')}
              className="btn btn-secondary"
              download
            >
              Export Promotions CSV
            </a>
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Campaign ID</th>
                  <th>Campaign Name</th>
                  <th>Type</th>
                  <th className="text-right">Units Sold</th>
                  <th className="text-right">Gross Discount</th>
                  <th className="text-right">Net Revenue</th>
                  <th className="text-right">Contribution Margin</th>
                  <th>Promotion Trap?</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  Array.from({ length: 6 }).map((_, idx) => (
                    <tr key={`skel-promo-${idx}`}>
                      <td><div className="skeleton skeleton-text" style={{ width: '80px' }} /></td>
                      <td><div className="skeleton skeleton-text" style={{ width: '130px' }} /></td>
                      <td><div className="skeleton skeleton-text" style={{ width: '70px' }} /></td>
                      <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '50px', marginLeft: 'auto' }} /></td>
                      <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '60px', marginLeft: 'auto' }} /></td>
                      <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '65px', marginLeft: 'auto' }} /></td>
                      <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '65px', marginLeft: 'auto' }} /></td>
                      <td><div className="skeleton skeleton-text" style={{ width: '90px' }} /></td>
                    </tr>
                  ))
                ) : data?.promotions.map((p) => (
                  <tr key={p.source_promotion_id}>
                    <td><span className="code-id">{p.source_promotion_id}</span></td>
                    <td><strong style={{ color: '#f8fafc' }}>{p.campaign_name}</strong></td>
                    <td>
                      <span className="category-pill">{p.discount_type}</span>
                    </td>
                    <td className="text-right">{Number(p.units_sold).toLocaleString()}</td>
                    <td className="text-right" style={{ color: '#ef4444' }}>-${Number(p.total_discount).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                    <td className="text-right">${Number(p.net_revenue).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                    <td className="text-right" style={{ color: Number(p.contribution_margin) >= 0 ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                      ${Number(p.contribution_margin).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </td>
                    <td>
                      {p.is_promotion_trap ? (
                        <span className="badge-tag badge-low">🚨 PROMOTION TRAP</span>
                      ) : (
                        <span className="badge-tag badge-profit">✓ Profitable</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
            <div>
              <h2 className="card-title" style={{ margin: 0 }}>High-Lift Item Association Rules</h2>
              <p style={{ margin: '4px 0 0', fontSize: '0.78rem', color: '#94a3b8' }}>
                Pairs sorted by Lift (P(A ∩ B) / [P(A) × P(B)]). Lift &gt; 1.0 indicates strong affinity for bundle combos.
              </p>
            </div>
            <a
              href={apiService.getExportUrl('spark/mart_basket_analysis.parquet')}
              className="btn btn-secondary"
              download
            >
              Export Basket CSV
            </a>
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Primary Item (A)</th>
                  <th>Associated Item (B)</th>
                  <th className="text-right">Co-Occurrences</th>
                  <th className="text-right">Pair Support</th>
                  <th className="text-right">Confidence (A → B)</th>
                  <th className="text-right">Lift Score</th>
                  <th>Strategic Opportunity</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  Array.from({ length: 6 }).map((_, idx) => (
                    <tr key={`skel-bsk-${idx}`}>
                      <td><div className="skeleton skeleton-text" style={{ width: '120px' }} /></td>
                      <td><div className="skeleton skeleton-text" style={{ width: '120px' }} /></td>
                      <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '50px', marginLeft: 'auto' }} /></td>
                      <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '45px', marginLeft: 'auto' }} /></td>
                      <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '45px', marginLeft: 'auto' }} /></td>
                      <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '40px', marginLeft: 'auto' }} /></td>
                      <td><div className="skeleton skeleton-text" style={{ width: '80px' }} /></td>
                    </tr>
                  ))
                ) : data?.market_basket_pairs.map((b, idx) => (
                  <tr key={`${b.item_a_id}-${b.item_b_id}-${idx}`}>
                    <td>
                      <strong style={{ color: '#f8fafc' }}>{b.item_a_name}</strong>
                      <div><span className="code-id">{b.item_a_id}</span></div>
                    </td>
                    <td>
                      <strong style={{ color: '#f8fafc' }}>{b.item_b_name}</strong>
                      <div><span className="code-id">{b.item_b_id}</span></div>
                    </td>
                    <td className="text-right">{Number(b.co_occurrence_count).toLocaleString()} orders</td>
                    <td className="text-right" style={{ color: '#94a3b8' }}>{(Number(b.support_ab) * 100).toFixed(2)}%</td>
                    <td className="text-right" style={{ color: '#94a3b8' }}>{(Number(b.confidence_a_to_b) * 100).toFixed(1)}%</td>
                    <td className="text-right">
                      <strong style={{ color: Number(b.lift) > 1.2 ? '#10b981' : '#f59e0b' }}>
                        {Number(b.lift).toFixed(2)}x
                      </strong>
                    </td>
                    <td>
                      <span className="badge-tag badge-volume">Combo Bundle</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
