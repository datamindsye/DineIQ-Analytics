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
        <div className="page-eyebrow">
          <span className="badge-tag badge-profit">DECISION INTELLIGENCE</span>
          <span className="page-timestamp">Prescriptive Heuristics</span>
        </div>
        <h1 className="page-title">Evidence-Based Business Recommendations</h1>
        <p className="page-description">
          Actionable operational interventions synthesized from empirical Spark analytical marts using the forensic hierarchy: Evidence &rarr; Insight &rarr; Recommended Action.
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
        <div className="rec-grid">
          {Array.from({ length: 4 }).map((_, idx) => (
            <div key={idx} className="rec-card skeleton-card">
              <div className="skeleton skeleton-text" style={{ width: '40%', height: '20px', marginBottom: '12px' }} />
              <div className="skeleton skeleton-text" style={{ width: '80%', height: '24px', marginBottom: '16px' }} />
              <div className="skeleton skeleton-box" style={{ height: '80px', marginBottom: '12px' }} />
              <div className="skeleton skeleton-box" style={{ height: '60px', marginBottom: '16px' }} />
              <div className="skeleton skeleton-text" style={{ width: '50%', height: '16px' }} />
            </div>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty-state-card">
          <div className="empty-icon">💡</div>
          <h3 className="empty-title">No Recommendations in this Category</h3>
          <p className="empty-desc">All operations within {selectedDomain || 'this domain'} are performing within acceptable bounds.</p>
        </div>
      ) : (
        <div className="rec-grid">
          {filtered.map((rec) => (
            <div key={rec.id} className="rec-card">
              <div className="rec-card-inner">
                {/* Header: Domain + Priority */}
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

                {/* Target Entity */}
                <h3 className="rec-target">{rec.target}</h3>

                {/* Section 1: Observation & Evidence */}
                <div className="rec-block evidence-block">
                  <div className="rec-block-label">
                    <span className="rec-block-icon">🔍</span>
                    <span>EMPIRICAL EVIDENCE</span>
                  </div>
                  <div className="rec-observation">{rec.observation}</div>
                  <div className="rec-evidence-code">
                    <code>{rec.evidence}</code>
                  </div>
                </div>

                {/* Section 2: Insight / Interpretation */}
                <div className="rec-block insight-block">
                  <div className="rec-block-label">
                    <span className="rec-block-icon">💡</span>
                    <span>BUSINESS INTERPRETATION</span>
                  </div>
                  <div className="rec-interpretation">{rec.interpretation}</div>
                </div>

                {/* Section 3: Recommended Action (Visual Focus) */}
                <div className="rec-block action-block">
                  <div className="rec-block-label action-label">
                    <span className="rec-block-icon">⚡</span>
                    <span>PRESCRIPTIVE ACTION</span>
                  </div>
                  <div className="rec-action-text">{rec.recommendation}</div>
                </div>
              </div>

              {/* Card Footer: Expected Impact & ID */}
              <div className="rec-footer">
                <div className="rec-impact">
                  <span className="impact-indicator">Impact:</span>
                  <span className="impact-val">{rec.expected_impact}</span>
                </div>
                <span className="rec-id">ID: {rec.id}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
