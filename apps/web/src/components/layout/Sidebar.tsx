import React from 'react';
import { NavLink } from 'react-router-dom';

export const Sidebar: React.FC = () => {
  return (
    <aside className="app-sidebar">
      <nav className="sidebar-nav">
        <div className="nav-group-label">OVERVIEW</div>
        <NavLink
          to="/"
          end
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <span className="nav-icon">📊</span>
          <span className="nav-label">Executive Overview</span>
        </NavLink>

        <div className="nav-group-label">BUSINESS INTELLIGENCE</div>
        <NavLink
          to="/menu"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <span className="nav-icon">🍽️</span>
          <span className="nav-label">Menu Intelligence</span>
        </NavLink>

        <NavLink
          to="/customers"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <span className="nav-icon">👥</span>
          <span className="nav-label">Customer & RFM</span>
        </NavLink>

        <NavLink
          to="/sales"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <span className="nav-icon">🏪</span>
          <span className="nav-label">Sales & Operations</span>
        </NavLink>

        <NavLink
          to="/demand-pricing"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <span className="nav-icon">📈</span>
          <span className="nav-label">Demand & Pricing</span>
        </NavLink>

        <NavLink
          to="/wastage"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <span className="nav-icon">🗑️</span>
          <span className="nav-label">Wastage & Inventory</span>
        </NavLink>

        <NavLink
          to="/promotions"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <span className="nav-icon">🏷️</span>
          <span className="nav-label">Promotions & Basket</span>
        </NavLink>

        <NavLink
          to="/anomalies"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <span className="nav-icon">⚠️</span>
          <span className="nav-label">Ratings & Anomalies</span>
        </NavLink>

        <div className="nav-group-label">INTELLIGENCE & SCENARIOS</div>
        <NavLink
          to="/arena"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <span className="nav-icon">⚔️</span>
          <span className="nav-label">Data Science Arena</span>
        </NavLink>

        <NavLink
          to="/recommendations"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <span className="nav-icon">💡</span>
          <span className="nav-label">Recommendations</span>
        </NavLink>

        <NavLink
          to="/what-if"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <span className="nav-icon">🎛️</span>
          <span className="nav-label">What-If Analysis</span>
        </NavLink>

        <div className="nav-group-label">INFRASTRUCTURE</div>
        <NavLink
          to="/health"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <span className="nav-icon">🩺</span>
          <span className="nav-label">Pipelines & Health</span>
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <div className="system-pill">Spark 4.2 + Scikit-Learn</div>
        <div className="version-pill">DineIQ v1.0 Production</div>
      </div>
    </aside>
  );
};
