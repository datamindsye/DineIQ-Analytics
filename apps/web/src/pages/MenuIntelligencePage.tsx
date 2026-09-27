import React, { useEffect, useState } from 'react';
import { useFilters } from '../context/useFilters';
import { apiService } from '../services/api';
import type { MenuItemData, MenuSummaryResponse } from '../types';

export const MenuIntelligencePage: React.FC = () => {
  const { selectedLocation, options } = useFilters();
  const [data, setData] = useState<MenuSummaryResponse | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedClass, setSelectedClass] = useState<string>('');
  const [selectedFlag, setSelectedFlag] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [page, setPage] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<MenuItemData | null>(null);

  const PAGE_SIZE = 25;

  const loadMenuData = React.useCallback(() => {
    let isMounted = true;
    apiService
      .getMenuIntelligence({
        category_id: selectedCategory || undefined,
        restaurant_id: selectedLocation || undefined,
        classification: selectedClass || undefined,
        flag: selectedFlag || undefined,
        search: searchQuery || undefined,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      })
      .then((res) => {
        if (isMounted) {
          setData(res);
          setLoading(false);
          if (res.items.length > 0 && !selectedItem) {
            setSelectedItem(res.items[0]);
          }
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to load menu intelligence');
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [selectedCategory, selectedLocation, selectedClass, selectedFlag, searchQuery, page, selectedItem]);

  useEffect(() => {
    return loadMenuData();
  }, [loadMenuData]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    loadMenuData();
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Menu Intelligence & Engineering</h1>
        <p className="page-description">
          Multi-factor menu profitability classification, composite scoring model, and forensic business flags.
        </p>
      </div>

      {error && <div className="alert-box error">{error}</div>}

      <div className="filter-bar">
        <form onSubmit={handleSearchSubmit} className="filter-group">
          <input
            type="text"
            placeholder="Search dish name or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          <button type="submit" className="btn btn-primary">Search</button>
        </form>

        <div className="filter-group">
          <select
            value={selectedCategory}
            onChange={(e) => { setSelectedCategory(e.target.value); setPage(0); }}
            className="filter-select"
          >
            <option value="">All Categories</option>
            {options.categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>

          <select
            value={selectedClass}
            onChange={(e) => { setSelectedClass(e.target.value); setPage(0); }}
            className="filter-select"
          >
            <option value="">All Classifications</option>
            {options.classifications.map((cl) => (
              <option key={cl} value={cl}>{cl}</option>
            ))}
          </select>

          <select
            value={selectedFlag}
            onChange={(e) => { setSelectedFlag(e.target.value); setPage(0); }}
            className="filter-select"
          >
            <option value="">All Forensic Flags</option>
            <option value="flag_high_selling_loss_making">High Selling & Loss Making</option>
            <option value="flag_profitable_rarely_purchased">Profitable Rarely Purchased</option>
            <option value="flag_popular_high_wastage">Popular High Wastage</option>
            <option value="flag_high_rating_low_profitability">High Rating Low Profit</option>
            <option value="flag_low_rating_high_sales">Low Rating High Sales</option>
            <option value="flag_promotion_dependent">Promotion Dependent</option>
            <option value="flag_weekend_only_pattern">Weekend Only Pattern</option>
            <option value="flag_seasonal_item">Seasonal Item</option>
            <option value="flag_location_divergence">Location Divergence</option>
          </select>

          <a
            href={apiService.getExportUrl('spark/mart_menu_performance.parquet')}
            className="btn btn-secondary"
            download
          >
            Export CSV
          </a>
        </div>
      </div>

      {/* Class distribution overview cards */}
      <div className="metrics-grid">
        <div className="metric-card" style={{ borderLeft: '4px solid #10b981' }}>
          <div className="metric-label">Profit Drivers</div>
          <div className="metric-value">{data?.classification_counts['Profit Driver'] || 0}</div>
          <div className="metric-sub">High margin & high demand</div>
        </div>
        <div className="metric-card" style={{ borderLeft: '4px solid #38bdf8' }}>
          <div className="metric-label">Volume Drivers</div>
          <div className="metric-value">{data?.classification_counts['Volume Driver'] || 0}</div>
          <div className="metric-sub">High volume, moderate margin</div>
        </div>
        <div className="metric-card" style={{ borderLeft: '4px solid #f59e0b' }}>
          <div className="metric-label">Hidden Opportunities</div>
          <div className="metric-value">{data?.classification_counts['Hidden Opportunity'] || 0}</div>
          <div className="metric-sub">High margin, lower demand</div>
        </div>
        <div className="metric-card" style={{ borderLeft: '4px solid #ef4444' }}>
          <div className="metric-label">Low Performers</div>
          <div className="metric-value">{data?.classification_counts['Low Performer'] || 0}</div>
          <div className="metric-sub">Low demand & weak margins</div>
        </div>
      </div>

      {/* Main split: Table on Left, 6-Factor Drill Down on Right */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedItem ? '2fr 1fr' : '1fr', gap: '20px' }}>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h2 className="card-title" style={{ margin: 0 }}>
              Menu Items ({data?.total_count || 0} items)
            </h2>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                className="btn btn-secondary"
                disabled={page === 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
              >
                Previous
              </button>
              <button
                className="btn btn-secondary"
                disabled={((page + 1) * PAGE_SIZE) >= (data?.total_count || 0)}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Dish</th>
                  <th>Category</th>
                  <th>Price</th>
                  <th>Cost</th>
                  <th>Volume</th>
                  <th>Margin %</th>
                  <th>Score</th>
                  <th>Classification</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={8} style={{ textAlign: 'center', padding: '30px' }}>Loading menu items...</td>
                  </tr>
                ) : data?.items.map((item) => (
                  <tr
                    key={`${item.menu_item_id}-${item.restaurant_id}`}
                    onClick={() => setSelectedItem(item)}
                    style={{
                      cursor: 'pointer',
                      backgroundColor: selectedItem?.menu_item_id === item.menu_item_id ? 'rgba(56, 189, 248, 0.1)' : undefined,
                    }}
                  >
                    <td>
                      <div><strong>{item.item_name}</strong></div>
                      <code style={{ fontSize: '0.72rem', color: '#94a3b8' }}>{item.menu_item_id}</code>
                    </td>
                    <td>{item.category_name}</td>
                    <td>${item.current_base_price?.toFixed(2)}</td>
                    <td>${item.current_base_cost?.toFixed(2)}</td>
                    <td>{item.total_quantity?.toLocaleString()}</td>
                    <td>{item.profitability_pct?.toFixed(1)}%</td>
                    <td><strong>{item.composite_score?.toFixed(1)}</strong></td>
                    <td>
                      <span
                        className={`badge-tag ${
                          item.classification === 'Profit Driver'
                            ? 'badge-profit'
                            : item.classification === 'Volume Driver'
                            ? 'badge-volume'
                            : item.classification === 'Hidden Opportunity'
                            ? 'badge-hidden'
                            : 'badge-low'
                        }`}
                      >
                        {item.classification}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {selectedItem && (
          <div className="card">
            <h2 className="card-title">Dish Forensic Detail</h2>
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#38bdf8' }}>{selectedItem.item_name}</div>
              <div style={{ color: '#94a3b8', fontSize: '0.85rem' }}>{selectedItem.menu_item_id} • {selectedItem.category_name}</div>
            </div>

            <h3 style={{ fontSize: '0.85rem', textTransform: 'uppercase', color: '#64748b', marginBottom: '12px' }}>
              Approved 6-Factor Weights
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                  <span>Demand Score (25%)</span>
                  <strong>{selectedItem.demand_score?.toFixed(1)} / 100</strong>
                </div>
                <div style={{ height: '6px', background: '#334155', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${selectedItem.demand_score || 0}%`, height: '100%', background: '#38bdf8' }} />
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                  <span>Profitability Score (25%)</span>
                  <strong>{selectedItem.profitability_score?.toFixed(1)} / 100</strong>
                </div>
                <div style={{ height: '6px', background: '#334155', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${selectedItem.profitability_score || 0}%`, height: '100%', background: '#10b981' }} />
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                  <span>Customer Signal (15%)</span>
                  <strong>{selectedItem.customer_signal_score?.toFixed(1)} / 100</strong>
                </div>
                <div style={{ height: '6px', background: '#334155', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${selectedItem.customer_signal_score || 0}%`, height: '100%', background: '#818cf8' }} />
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                  <span>Wastage Health (15%)</span>
                  <strong>{selectedItem.wastage_health_score?.toFixed(1)} / 100</strong>
                </div>
                <div style={{ height: '6px', background: '#334155', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${selectedItem.wastage_health_score || 0}%`, height: '100%', background: '#f59e0b' }} />
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                  <span>Sales Trend (10%)</span>
                  <strong>{selectedItem.sales_trend_score?.toFixed(1)} / 100</strong>
                </div>
                <div style={{ height: '6px', background: '#334155', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${selectedItem.sales_trend_score || 0}%`, height: '100%', background: '#a855f7' }} />
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                  <span>Promo Independence (10%)</span>
                  <strong>{selectedItem.promotion_independence_score?.toFixed(1)} / 100</strong>
                </div>
                <div style={{ height: '6px', background: '#334155', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${selectedItem.promotion_independence_score || 0}%`, height: '100%', background: '#ec4899' }} />
                </div>
              </div>
            </div>

            <h3 style={{ fontSize: '0.85rem', textTransform: 'uppercase', color: '#64748b', marginBottom: '10px' }}>
              Active Business Flags
            </h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {selectedItem.flags.high_selling_loss_making && <span className="badge-tag badge-low">High Selling Loss-Making</span>}
              {selectedItem.flags.popular_high_wastage && <span className="badge-tag badge-low">Popular High Wastage</span>}
              {selectedItem.flags.profitable_rarely_purchased && <span className="badge-tag badge-hidden">Profitable Rarely Purchased</span>}
              {selectedItem.flags.promotion_dependent && <span className="badge-tag badge-volume">Promo Dependent</span>}
              {selectedItem.flags.weekend_only_pattern && <span className="badge-tag badge-volume">Weekend Pattern</span>}
              {selectedItem.flags.seasonal_item && <span className="badge-tag badge-hidden">Seasonal</span>}
              {selectedItem.flags.location_divergence && <span className="badge-tag badge-hidden">Location Divergence</span>}
              {!Object.values(selectedItem.flags).some(Boolean) && (
                <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>No adverse flags detected.</span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
