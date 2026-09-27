import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import type { RecommendationItem } from '../types';

export const RecommendationsPage: React.FC = () => {
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [selectedDomain, setSelectedDomain] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    apiService
      .getRecommendations()
      .then((recs) => {
        if (isMounted) setRecommendations(recs);
      })
      .catch((err) => {
        if (isMounted) setError(err instanceof Error ? err.message : 'Failed loading recommendations');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const filtered = selectedDomain
    ? recommendations.filter((r) => r.domain === selectedDomain)
    : recommendations;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Evidence-Based Business Recommendations</h1>
        <p className="page-description">
          Actionable intelligence derived deterministically from analytical marts using the forensic flow: Observation &rarr; Evidence &rarr; Interpretation &rarr; Recommendation.
        </p>
      </div>

      {error && <div className="alert-box error">{error}</div>}

      <div className="filter-bar">
        <div className="filter-group">
          <button
            className={`tab-btn ${selectedDomain === '' ? 'active' : ''}`}
            onClick={() => setSelectedDomain('')}
          >
            All Domains ({recommendations.length})
          </button>
          <button
            className={`tab-btn ${selectedDomain === 'Menu Optimization' ? 'active' : ''}`}
            onClick={() => setSelectedDomain('Menu Optimization')}
          >
            🍽️ Menu Optimization
          </button>
          <button
            className={`tab-btn ${selectedDomain === 'Operational Wastage' ? 'active' : ''}`}
            onClick={() => setSelectedDomain('Operational Wastage')}
          >
            🗑️ Operational Wastage
          </button>
          <button
            className={`tab-btn ${selectedDomain === 'Customer Retention' ? 'active' : ''}`}
            onClick={() => setSelectedDomain('Customer Retention')}
          >
            👥 Customer Retention
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: '#94a3b8' }}>
          Synthesizing recommendations from analytical marts...
        </div>
      ) : filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px', color: '#94a3b8' }}>
          No recommendations found for this domain.
        </div>
      ) : (
        <div className="rec-grid">
          {filtered.map((rec) => (
            <div key={rec.id} className="rec-card">
              <div>
                <div className="rec-header">
                  <span className="rec-domain">{rec.domain}</span>
                  <span
                    className={`badge-tag ${
                      rec.priority === 'Critical'
                        ? 'badge-risk-high'
                        : rec.priority === 'High'
                        ? 'badge-hidden'
                        : 'badge-volume'
                    }`}
                  >
                    {rec.priority} Priority
                  </span>
                </div>

                <div className="rec-target">{rec.target}</div>

                <div className="rec-body">
                  <strong>Observation:</strong> {rec.observation}
                </div>

                <div className="rec-evidence">
                  <strong>Evidence:</strong> {rec.evidence}
                </div>

                <div className="rec-body" style={{ color: '#cbd5e1' }}>
                  <strong>Interpretation:</strong> {rec.interpretation}
                </div>

                <div className="rec-action" style={{ color: '#38bdf8' }}>
                  <strong>Action:</strong> {rec.recommendation}
                </div>
              </div>

              <div className="rec-footer">
                <span style={{ color: '#10b981', fontWeight: 600 }}>{rec.expected_impact}</span>
                <span style={{ color: '#64748b' }}>ID: {rec.id}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
