import React, { useState } from 'react';

interface PipelineStage {
  id: string;
  stepNumber: string;
  name: string;
  shortDesc: string;
  technology: string;
  inputOutput: string;
  category: 'ingestion' | 'quality' | 'bigdata' | 'features' | 'marts' | 'ml' | 'verification' | 'bi' | 'decisions';
  icon: string;
  isParallel?: boolean;
}

const LINEAR_STAGES_PRE: PipelineStage[] = [
  {
    id: 'raw-data',
    stepNumber: '01',
    name: 'Raw Restaurant Data',
    shortDesc: '11 relational domain tables capturing POS transactions, customers, menu items, inventory, ratings, pricing, and promotions.',
    technology: '1.31M Rows • 17 Business Complexities',
    inputOutput: 'Relational DB → Raw CSV/Parquet',
    category: 'ingestion',
    icon: '📦',
  },
  {
    id: 'data-quality',
    stepNumber: '02',
    name: 'Data Quality & Cleaning',
    shortDesc: 'Automated defect quarantine engine isolating schema anomalies, negative amounts, orphaned checkouts, and corrupt records.',
    technology: 'Defect Quarantine Engine',
    inputOutput: 'Raw Snapshots → Clean Data Directory',
    category: 'quality',
    icon: '🛡️',
  },
  {
    id: 'apache-spark',
    stepNumber: '03',
    name: 'Apache Spark Processing',
    shortDesc: 'Distributed joins, multi-table aggregations, and schema transformations across 11 clean domain tables with zero hallucination.',
    technology: 'Apache Spark 4.2.0 / PySpark',
    inputOutput: 'Clean Snapshots → Distributed DataFrames',
    category: 'bigdata',
    icon: '⚡',
  },
  {
    id: 'feature-engineering',
    stepNumber: '04',
    name: 'Feature Engineering',
    shortDesc: 'Leakage-safe historical windows (strictly rowsBetween(-14, -1)), RFM recency counters, and cross-channel elasticity metrics.',
    technology: 'Temporal Anti-Leakage Windows',
    inputOutput: 'Raw Metrics → Model Feature Matrices',
    category: 'features',
    icon: '⚙️',
  },
  {
    id: 'analytical-marts',
    stepNumber: '05',
    name: 'Analytical Marts',
    shortDesc: '12 precomputed Snappy Parquet analytical marts (741,310 total records) materialized on disk for sub-second query performance.',
    technology: '12 Precomputed Parquet Marts',
    inputOutput: 'Spark Transformations → data/marts/spark/',
    category: 'marts',
    icon: '🏛️',
  },
];

const PARALLEL_SPARK: PipelineStage = {
  id: 'spark-ml',
  stepNumber: '06A',
  name: 'Spark MLlib Pipeline',
  shortDesc: 'Independent distributed model competition across LinearRegression, RF, GBT, LogisticRegression & BisectingKMeans with validation selection.',
  technology: 'Apache Spark MLlib • Isolated Pipeline',
  inputOutput: 'Clean Marts → ml_*.parquet (Spark)',
  category: 'ml',
  icon: '🔥',
  isParallel: true,
};

const PARALLEL_PYTHON: PipelineStage = {
  id: 'python-ml',
  stepNumber: '06B',
  name: 'Python Sklearn Pipeline',
  shortDesc: 'Independent single-node model competition across Ridge, RF, HistGBR, LogisticRegression & KMeans with validation selection.',
  technology: 'Python 3.13 / scikit-learn • Isolated',
  inputOutput: 'Clean Marts → ml_*.parquet (Python)',
  category: 'ml',
  icon: '🐍',
  isParallel: true,
};

const LINEAR_STAGES_POST: PipelineStage[] = [
  {
    id: 'comparison-arena',
    stepNumber: '07',
    name: 'Comparison Arena',
    shortDesc: 'Strict head-to-head evaluation on unseen comparison dataset (2025-12). Measures dual-pipeline consensus without feature sharing.',
    technology: '63.48% Cross-Pipeline Consensus',
    inputOutput: 'Spark vs Python → Comparison Marts',
    category: 'verification',
    icon: '⚔️',
  },
  {
    id: 'bi-dashboards',
    stepNumber: '08',
    name: 'Business Intelligence',
    shortDesc: 'Domain-specific analytical intelligence across Menu BCG Matrix, Customer RFM, Hourly Peak Rush, Demand, and Wastage.',
    technology: 'FastAPI + PyArrow + Plotly.react()',
    inputOutput: 'Parquet Marts → Analytical Envelopes',
    category: 'bi',
    icon: '📊',
  },
  {
    id: 'recommendations',
    stepNumber: '09',
    name: 'Prescriptive Decisions',
    shortDesc: 'Evidence-based operational interventions dynamically synthesized from empirical mart signals and ML classifications.',
    technology: 'Prescriptive Intelligence Engine',
    inputOutput: 'Mart Signals → Prioritized Action Cards',
    category: 'decisions',
    icon: '💡',
  },
  {
    id: 'what-if',
    stepNumber: '10',
    name: 'What-If Simulation',
    shortDesc: 'Interactive sensitivity simulator modeling forward-looking contribution margin impact from price changes & waste reductions.',
    technology: 'Elasticity Model: ΔQ/Q = ε · ΔP/P',
    inputOutput: 'User Scenario Parameters → Estimated Impact',
    category: 'decisions',
    icon: '🎛️',
  },
  {
    id: 'cockpit',
    stepNumber: '11',
    name: 'DineIQ Analytics Cockpit',
    shortDesc: 'Unified executive intelligence dashboard delivering real-time operational visibility, model transparency, and auditability.',
    technology: 'React 19 • TypeScript • Responsive Vanilla CSS',
    inputOutput: 'All Layers → Competition-Ready Dashboard',
    category: 'bi',
    icon: '🚀',
  },
];

export const ProjectJourneyPipeline: React.FC = () => {
  const [selectedStage, setSelectedStage] = useState<string | null>(null);

  const getCategoryBadgeClass = (category: PipelineStage['category']) => {
    switch (category) {
      case 'ingestion':
        return 'pipeline-tag-ingest';
      case 'quality':
        return 'pipeline-tag-quality';
      case 'bigdata':
        return 'pipeline-tag-spark';
      case 'features':
        return 'pipeline-tag-feature';
      case 'marts':
        return 'pipeline-tag-marts';
      case 'ml':
        return 'pipeline-tag-ml';
      case 'verification':
        return 'pipeline-tag-arena';
      case 'bi':
        return 'pipeline-tag-bi';
      case 'decisions':
        return 'pipeline-tag-decision';
      default:
        return 'badge-tag';
    }
  };

  const renderStageCard = (stage: PipelineStage) => {
    const isSelected = selectedStage === stage.id;
    return (
      <div
        key={stage.id}
        className={`journey-step-card ${stage.category} ${isSelected ? 'selected' : ''}`}
        onClick={() => setSelectedStage(isSelected ? null : stage.id)}
        role="button"
        tabIndex={0}
        aria-expanded={isSelected}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setSelectedStage(isSelected ? null : stage.id);
          }
        }}
      >
        <div className="journey-step-header">
          <span className="journey-step-num">{stage.stepNumber}</span>
          <span className={`journey-step-badge ${getCategoryBadgeClass(stage.category)}`}>
            {stage.category.toUpperCase()}
          </span>
        </div>

        <div className="journey-step-title-row">
          <span className="journey-step-icon">{stage.icon}</span>
          <h4 className="journey-step-title">{stage.name}</h4>
        </div>

        <p className="journey-step-desc">{stage.shortDesc}</p>

        <div className="journey-step-footer">
          <div className="journey-step-tech">
            <span className="tech-dot" />
            <span>{stage.technology}</span>
          </div>
          <div className="journey-step-flow">
            <span className="flow-label">I/O:</span>
            <code className="flow-val">{stage.inputOutput}</code>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="card journey-card">
      <div className="journey-header">
        <div>
          <div className="journey-eyebrow">
            <span className="badge-tag badge-volume">SYSTEM ARCHITECTURE</span>
            <span className="journey-consensus-badge">Authoritative Consensus: 63.48%</span>
          </div>
          <h2 className="journey-main-title">DineIQ Analytics End-to-End Pipeline Journey</h2>
          <p className="journey-main-desc">
            Forensic walk-through of the complete enterprise data intelligence architecture: from 1.31M raw transactions through dual-pipeline ML tournament to real-time executive decision intelligence.
          </p>
        </div>
        <div className="journey-summary-stats">
          <div className="summary-pill">
            <strong>1.31M</strong>
            <span>Raw Records</span>
          </div>
          <div className="summary-pill">
            <strong>12</strong>
            <span>Spark Marts</span>
          </div>
          <div className="summary-pill highlight">
            <strong>Dual ML</strong>
            <span>Independent</span>
          </div>
          <div className="summary-pill">
            <strong>11</strong>
            <span>Domains</span>
          </div>
        </div>
      </div>

      {/* Interactive Horizontal / Stepper Visual Journey */}
      <div className="journey-flow-container">
        {/* Phase 1: Data & Preparation */}
        <div className="journey-phase-group">
          <div className="phase-label-bar">
            <span className="phase-indicator">PHASE 1</span>
            <span className="phase-title">Data Ingestion, Quality & Spark Marts</span>
          </div>
          <div className="journey-steps-row">
            {LINEAR_STAGES_PRE.map((stage, idx) => (
              <React.Fragment key={stage.id}>
                {renderStageCard(stage)}
                {idx < LINEAR_STAGES_PRE.length - 1 && (
                  <div className="journey-connector" aria-hidden="true">
                    <span className="connector-arrow">→</span>
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Transition Connector to Dual ML */}
        <div className="journey-split-connector" aria-hidden="true">
          <div className="connector-split-branch top">
            <span className="branch-label">To Spark MLlib</span>
            <span className="branch-arrow">↳</span>
          </div>
          <div className="connector-split-branch bottom">
            <span className="branch-label">To Python Sklearn</span>
            <span className="branch-arrow">↳</span>
          </div>
        </div>

        {/* Phase 2: Dual Independent Parallel ML Pipelines */}
        <div className="journey-phase-group parallel-group">
          <div className="phase-label-bar parallel-bar">
            <span className="phase-indicator parallel">PHASE 2</span>
            <span className="phase-title">Dual Independent Machine Learning Tournament (Strictly Zero Shared State)</span>
          </div>
          <div className="journey-parallel-tracks">
            <div className="parallel-track spark-track">
              <div className="track-header">
                <span className="track-badge spark">Apache Spark MLlib Path</span>
                <span className="track-note">Distributed MLlib candidate models</span>
              </div>
              {renderStageCard(PARALLEL_SPARK)}
            </div>

            <div className="parallel-track python-track">
              <div className="track-header">
                <span className="track-badge python">Python Sklearn Path</span>
                <span className="track-note">scikit-learn candidate models</span>
              </div>
              {renderStageCard(PARALLEL_PYTHON)}
            </div>
          </div>
        </div>

        {/* Transition Connector from Dual ML to Verification & Intelligence */}
        <div className="journey-merge-connector" aria-hidden="true">
          <span className="merge-label">Unseen Data Evaluation</span>
          <span className="merge-arrow">↓</span>
        </div>

        {/* Phase 3: Model Comparison, Intelligence & Decisions */}
        <div className="journey-phase-group">
          <div className="phase-label-bar">
            <span className="phase-indicator">PHASE 3</span>
            <span className="phase-title">Verification Arena, Prescriptive Intelligence & Executive Cockpit</span>
          </div>
          <div className="journey-steps-row">
            {LINEAR_STAGES_POST.map((stage, idx) => (
              <React.Fragment key={stage.id}>
                {renderStageCard(stage)}
                {idx < LINEAR_STAGES_POST.length - 1 && (
                  <div className="journey-connector" aria-hidden="true">
                    <span className="connector-arrow">→</span>
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>

      <div className="journey-footnote">
        <span className="footnote-icon">ℹ️</span>
        <span>
          <strong>Architecture Guarantee:</strong> Spark MLlib and Python Sklearn pipelines share only clean dataset snapshots and split manifests. No feature matrices, weights, or hyperparameters were shared between pipelines.
        </span>
      </div>
    </div>
  );
};
