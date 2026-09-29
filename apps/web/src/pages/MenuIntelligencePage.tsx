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

  const getClassificationBadge = (classification: string) => {
    switch (classification) {
      case 'Profit Driver':
        return <span className="badge-tag badge-profit">★ {classification}</span>;
      case 'Volume Driver':
        return <span className="badge-tag badge-volume">▲ {classification}</span>;
      case 'Hidden Opportunity':
        return <span className="badge-tag badge-hidden">◆ {classification}</span>;
      case 'Low Performer':
      default:
        return <span className="badge-tag badge-low">▼ {classification}</span>;
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <span className="page-eyebrow">Enterprise Domain Mart</span>
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
          <div className="metric-label">★ Profit Drivers</div>
          <div className="metric-value">{data?.classification_counts['Profit Driver'] ?? 0}</div>
          <div className="metric-sub">High margin & high demand</div>
        </div>
        <div className="metric-card" style={{ borderLeft: '4px solid #38bdf8' }}>
          <div className="metric-label">▲ Volume Drivers</div>
          <div className="metric-value">{data?.classification_counts['Volume Driver'] ?? 0}</div>
          <div className="metric-sub">High volume, moderate margin</div>
        </div>
        <div className="metric-card" style={{ borderLeft: '4px solid #f59e0b' }}>
          <div className="metric-label">◆ Hidden Opportunities</div>
          <div className="metric-value">{data?.classification_counts['Hidden Opportunity'] ?? 0}</div>
          <div className="metric-sub">High margin, lower demand</div>
        </div>
        <div className="metric-card" style={{ borderLeft: '4px solid #ef4444' }}>
          <div className="metric-label">▼ Low Performers</div>
          <div className="metric-value">{data?.classification_counts['Low Performer'] ?? 0}</div>
          <div className="metric-sub">Low demand & weak margins</div>
        </div>
      </div>

      {/* Main split: Table on Left, 6-Factor Drill Down on Right */}
      <div className={`menu-grid-split ${selectedItem ? 'with-detail' : ''}`}>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
            <div>
              <h2 className="card-title" style={{ margin: 0 }}>
                Menu Catalog & Classifications
              </h2>
              <p style={{ margin: '4px 0 0', fontSize: '0.78rem', color: '#94a3b8' }}>
                Displaying {data?.items.length || 0} of {data?.total_count.toLocaleString() || 0} menu items across active filters. Click row to inspect forensic weights.
              </p>
            </div>
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
                  <th className="text-right">Price</th>
                  <th className="text-right">Cost</th>
                  <th className="text-right">Volume</th>
                  <th className="text-right">Margin %</th>
                  <th className="text-right">Score</th>
                  <th>Classification</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  Array.from({ length: 10 }).map((_, idx) => (
                    <tr key={`skel-${idx}`}>
                      <td><div className="skeleton skeleton-text" style={{ width: '130px' }} /></td>
                      <td><div className="skeleton skeleton-text" style={{ width: '70px' }} /></td>
                      <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '45px', marginLeft: 'auto' }} /></td>
                      <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '45px', marginLeft: 'auto' }} /></td>
                      <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '55px', marginLeft: 'auto' }} /></td>
                      <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '45px', marginLeft: 'auto' }} /></td>
                      <td className="text-right"><div className="skeleton skeleton-text" style={{ width: '40px', marginLeft: 'auto' }} /></td>
                      <td><div className="skeleton skeleton-text" style={{ width: '90px' }} /></td>
                    </tr>
                  ))
                ) : data?.items.map((item) => {
                  const isSelected = selectedItem?.menu_item_id === item.menu_item_id;
                  return (
                    <tr
                      key={`${item.menu_item_id}-${item.restaurant_id}`}
                      onClick={() => setSelectedItem(item)}
                      style={{
                        cursor: 'pointer',
                        backgroundColor: isSelected ? 'rgba(56, 189, 248, 0.08)' : undefined,
                        borderLeft: isSelected ? '3px solid #38bdf8' : undefined,
                      }}
                    >
                      <td>
                        <div style={{ fontWeight: 600, color: isSelected ? '#38bdf8' : '#f8fafc' }}>
                          {item.item_name}
                        </div>
                        <span className="code-id">{item.menu_item_id}</span>
                      </td>
                      <td>
                        <span className="category-pill">{item.category_name}</span>
                      </td>
                      <td className="text-right">${item.current_base_price?.toFixed(2)}</td>
                      <td className="text-right" style={{ color: '#94a3b8' }}>${item.current_base_cost?.toFixed(2)}</td>
                      <td className="text-right">{item.total_quantity?.toLocaleString()}</td>
                      <td className="text-right" style={{ fontWeight: 600, color: (item.profitability_pct || 0) >= 60 ? '#10b981' : (item.profitability_pct || 0) < 40 ? '#ef4444' : '#f59e0b' }}>
                        {item.profitability_pct?.toFixed(1)}%
                      </td>
                      <td className="text-right">
                        <strong style={{ color: '#f8fafc' }}>{item.composite_score?.toFixed(1)}</strong>
                      </td>
                      <td>
                        {getClassificationBadge(item.classification)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {selectedItem ? (
          <div className="card" style={{ height: 'fit-content' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <div>
                <span className="page-eyebrow" style={{ marginBottom: '4px' }}>Item Forensic Breakdown</span>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>{selectedItem.item_name}</div>
                <div style={{ color: '#94a3b8', fontSize: '0.82rem', marginTop: '2px' }}>
                  <code className="code-id">{selectedItem.menu_item_id}</code> • {selectedItem.category_name}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Composite</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#38bdf8' }}>
                  {selectedItem.composite_score?.toFixed(1)}
                  <span style={{ fontSize: '0.75rem', color: '#64748b' }}>/100</span>
                </div>
              </div>
            </div>

            {/* Quick Financial Summary */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '8px',
              padding: '12px',
              background: 'rgba(15, 23, 42, 0.6)',
              borderRadius: '8px',
              border: '1px solid #1e293b',
              marginBottom: '18px',
            }}>
              <div>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Unit Contribution</div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: '#10b981' }}>
                  +${((selectedItem.current_base_price || 0) - (selectedItem.current_base_cost || 0)).toFixed(2)}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Margin Ratio</div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: '#38bdf8' }}>
                  {selectedItem.profitability_pct?.toFixed(1)}%
                </div>
              </div>
            </div>

            <h3 style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: '#94a3b8', letterSpacing: '0.05em', marginBottom: '14px' }}>
              Approved 6-Factor Model Weights
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '22px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                  <span style={{ color: '#cbd5e1' }}>Demand Score (25%)</span>
                  <strong>{selectedItem.demand_score?.toFixed(1)} / 100</strong>
                </div>
                <div style={{ height: '6px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${selectedItem.demand_score || 0}%`, height: '100%', background: 'linear-gradient(90deg, #0284c7, #38bdf8)' }} />
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                  <span style={{ color: '#cbd5e1' }}>Profitability Score (25%)</span>
                  <strong>{selectedItem.profitability_score?.toFixed(1)} / 100</strong>
                </div>
                <div style={{ height: '6px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${selectedItem.profitability_score || 0}%`, height: '100%', background: 'linear-gradient(90deg, #059669, #10b981)' }} />
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                  <span style={{ color: '#cbd5e1' }}>Customer Signal (15%)</span>
                  <strong>{selectedItem.customer_signal_score?.toFixed(1)} / 100</strong>
                </div>
                <div style={{ height: '6px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${selectedItem.customer_signal_score || 0}%`, height: '100%', background: 'linear-gradient(90deg, #6366f1, #818cf8)' }} />
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                  <span style={{ color: '#cbd5e1' }}>Wastage Health (15%)</span>
                  <strong>{selectedItem.wastage_health_score?.toFixed(1)} / 100</strong>
                </div>
                <div style={{ height: '6px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${selectedItem.wastage_health_score || 0}%`, height: '100%', background: 'linear-gradient(90deg, #d97706, #f59e0b)' }} />
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                  <span style={{ color: '#cbd5e1' }}>Sales Trend (10%)</span>
                  <strong>{selectedItem.sales_trend_score?.toFixed(1)} / 100</strong>
                </div>
                <div style={{ height: '6px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${selectedItem.sales_trend_score || 0}%`, height: '100%', background: 'linear-gradient(90deg, #9333ea, #c084fc)' }} />
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                  <span style={{ color: '#cbd5e1' }}>Promo Independence (10%)</span>
                  <strong>{selectedItem.promotion_independence_score?.toFixed(1)} / 100</strong>
                </div>
                <div style={{ height: '6px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${selectedItem.promotion_independence_score || 0}%`, height: '100%', background: 'linear-gradient(90deg, #db2777, #f472b6)' }} />
                </div>
              </div>
            </div>

            <h3 style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: '#94a3b8', letterSpacing: '0.05em', marginBottom: '10px' }}>
              Active Forensic Business Flags
            </h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {selectedItem.flags.high_selling_loss_making && <span className="badge-tag badge-low">🚨 High Selling Loss-Making</span>}
              {selectedItem.flags.popular_high_wastage && <span className="badge-tag badge-low">⚠️ Popular High Wastage</span>}
              {selectedItem.flags.profitable_rarely_purchased && <span className="badge-tag badge-hidden">💎 Profitable Rarely Purchased</span>}
              {selectedItem.flags.promotion_dependent && <span className="badge-tag badge-volume">🏷️ Promo Dependent</span>}
              {selectedItem.flags.weekend_only_pattern && <span className="badge-tag badge-volume">📅 Weekend Pattern</span>}
              {selectedItem.flags.seasonal_item && <span className="badge-tag badge-hidden">🍂 Seasonal Item</span>}
              {selectedItem.flags.location_divergence && <span className="badge-tag badge-hidden">📍 Location Divergence</span>}
              {!Object.values(selectedItem.flags).some(Boolean) && (
                <div style={{
                  padding: '8px 12px',
                  background: 'rgba(16, 185, 129, 0.1)',
                  border: '1px solid rgba(16, 185, 129, 0.25)',
                  borderRadius: '6px',
                  color: '#10b981',
                  fontSize: '0.8rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}>
                  <span>✓</span> No adverse forensic flags detected (Optimal Performance)
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="card empty-state-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>🔍</div>
            <div style={{ fontWeight: 600, color: '#f8fafc', marginBottom: '4px' }}>Select a Dish</div>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem', margin: 0, textAlign: 'center' }}>
              Click any menu item row in the catalog to view its approved 6-factor forensic breakdown and active flags.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
