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
        <h1 className="page-title">Promotions & Market Basket Analysis</h1>
        <p className="page-description">
          Campaign margin impact diagnostics, promotion trap isolation, and association rule mining for pairing bundles.
        </p>
      </div>

      {error && <div className="alert-box error">{error}</div>}

      <div className="tab-group">
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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h2 className="card-title" style={{ margin: 0 }}>Promotional Campaign Performance</h2>
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
                  <th>Units Sold</th>
                  <th>Gross Discount</th>
                  <th>Net Revenue</th>
                  <th>Contribution Margin</th>
                  <th>Promotion Trap?</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={8} style={{ textAlign: 'center', padding: '30px' }}>Loading campaigns...</td>
                  </tr>
                ) : data?.promotions.map((p) => (
                  <tr key={p.source_promotion_id}>
                    <td><code>{p.source_promotion_id}</code></td>
                    <td><strong>{p.campaign_name}</strong></td>
                    <td>{p.discount_type}</td>
                    <td>{Number(p.units_sold).toLocaleString()}</td>
                    <td>${Number(p.total_discount).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                    <td>${Number(p.net_revenue).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                    <td>${Number(p.contribution_margin).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                    <td>
                      {p.is_promotion_trap ? (
                        <span className="badge-tag badge-low">PROMOTION TRAP</span>
                      ) : (
                        <span className="badge-tag badge-profit">Profitable</span>
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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <div>
              <h2 className="card-title" style={{ margin: 0 }}>High-Lift Item Association Rules</h2>
              <p style={{ margin: '4px 0 0', fontSize: '0.78rem', color: '#94a3b8' }}>
                Pairs sorted by Lift ($P(A \cap B) / [P(A) \times P(B)]$). Lift &gt; 1.0 indicates strong affinity for bundle combos.
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
                  <th>Co-Occurrences</th>
                  <th>Pair Support</th>
                  <th>Confidence (A → B)</th>
                  <th>Lift Score</th>
                  <th>Strategic Opportunity</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={7} style={{ textAlign: 'center', padding: '30px' }}>Loading basket analysis...</td>
                  </tr>
                ) : data?.market_basket_pairs.map((b, idx) => (
                  <tr key={`${b.item_a_id}-${b.item_b_id}-${idx}`}>
                    <td>
                      <strong>{b.item_a_name}</strong>
                      <div><code style={{ fontSize: '0.72rem', color: '#94a3b8' }}>{b.item_a_id}</code></div>
                    </td>
                    <td>
                      <strong>{b.item_b_name}</strong>
                      <div><code style={{ fontSize: '0.72rem', color: '#94a3b8' }}>{b.item_b_id}</code></div>
                    </td>
                    <td>{Number(b.co_occurrence_count).toLocaleString()} orders</td>
                    <td>{(Number(b.support_ab) * 100).toFixed(2)}%</td>
                    <td>{(Number(b.confidence_a_to_b) * 100).toFixed(1)}%</td>
                    <td>
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
