import React from 'react';

export const PipelinesPage: React.FC = () => {
  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Dual Pipeline Architecture</h1>
        <p className="page-description">
          Rigorous independent evaluation between Apache Spark and Python Data Science.
        </p>
      </div>

      <div className="pipeline-cards-grid">
        <div className="card pipeline-card">
          <div className="pipeline-header">
            <span className="pipeline-badge spark">Pipeline 1</span>
            <h2>Apache Spark & PySpark</h2>
          </div>
          <p className="pipeline-desc">
            Distributed big data processing, data quality validation, large scale joins,
            feature marts, and Spark MLlib classifiers.
          </p>
          <ul className="spec-list">
            <li><strong>Engine:</strong> PySpark + Spark SQL</li>
            <li><strong>ML:</strong> Spark MLlib</li>
            <li><strong>Output:</strong> data/marts/{'{run_id}'}/spark/</li>
          </ul>
        </div>

        <div className="card pipeline-card">
          <div className="pipeline-header">
            <span className="pipeline-badge python">Pipeline 2</span>
            <h2>Python Data Science</h2>
          </div>
          <p className="pipeline-desc">
            Independent data processing, statistical preprocessing, NumPy/Pandas feature
            engineering, and scikit-learn predictive modeling.
          </p>
          <ul className="spec-list">
            <li><strong>Engine:</strong> Pandas + NumPy</li>
            <li><strong>ML:</strong> scikit-learn</li>
            <li><strong>Output:</strong> data/marts/{'{run_id}'}/python/</li>
          </ul>
        </div>
      </div>

      <div className="card comparison-box">
        <h3>Evaluation Contract & Shared Boundary</h3>
        <p>
          Pipelines share only raw/clean dataset snapshots, entity identifiers, chronological split
          manifests, and evaluation contracts. They never share intermediate features, model weights, or
          predictions.
        </p>
      </div>
    </div>
  );
};
