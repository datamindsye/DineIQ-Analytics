import React from 'react';
import { PlotlyChart } from '../components/charts/PlotlyChart';

export const DashboardPage: React.FC = () => {
  // Sample demonstration data for Plotly foundation check (Boston Matrix Menu Quadrant)
  const chartData = [
    {
      x: [45, 80, 20, 95, 60, 30, 85, 15],
      y: [70, 65, 30, 25, 80, 85, 40, 50],
      text: [
        'Truffle Burger (Star)',
        'Classic Cheeseburger (Plowhorse)',
        'House Salad (Dog)',
        'French Fries (Plowhorse)',
        'Ribeye Steak (Star)',
        'Vintage Wine (Puzzle)',
        'Draft Beer (Plowhorse)',
        'Soup of Day (Dog)',
      ],
      mode: 'markers+text' as const,
      textposition: 'top center' as const,
      marker: {
        size: [24, 38, 14, 45, 28, 18, 40, 16],
        color: ['#10b981', '#3b82f6', '#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#3b82f6', '#ef4444'],
        opacity: 0.85,
      },
      type: 'scatter' as const,
    },
  ];

  const chartLayout = {
    title: { text: 'Menu Profitability Matrix (Plotly Foundation Demo)', font: { size: 16 } },
    xaxis: { title: { text: 'Sales Volume (Units)' }, gridcolor: '#334155' },
    yaxis: { title: { text: 'Contribution Margin (%)' }, gridcolor: '#334155' },
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Executive Overview</h1>
        <p className="page-description">
          DineIQ Analytics platform foundation scaffold. Analytical marts will populate here.
        </p>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Target Architecture</div>
          <div className="metric-value">Modular Monolith</div>
          <div className="metric-sub">FastAPI + React + Spark</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Dual Pipelines</div>
          <div className="metric-value">Isolated</div>
          <div className="metric-sub">Spark & Python DS</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Analytical Storage</div>
          <div className="metric-value">Parquet</div>
          <div className="metric-sub">data/marts/</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Metadata Store</div>
          <div className="metric-value">PostgreSQL</div>
          <div className="metric-sub">SQLAlchemy + Alembic</div>
        </div>
      </div>

      <div className="card chart-card">
        <h2 className="card-title">Interactive Chart Foundation</h2>
        <PlotlyChart data={chartData} layout={chartLayout} />
      </div>
    </div>
  );
};
