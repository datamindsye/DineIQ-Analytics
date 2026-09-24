import React from 'react';
import { NavLink } from 'react-router-dom';

export const Sidebar: React.FC = () => {
  return (
    <aside className="app-sidebar">
      <nav className="sidebar-nav">
        <NavLink
          to="/"
          end
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <span className="nav-icon">📊</span>
          <span className="nav-label">Executive Dashboard</span>
        </NavLink>
        <NavLink
          to="/pipelines"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <span className="nav-icon">⚡</span>
          <span className="nav-label">Dual Pipelines</span>
        </NavLink>
        <NavLink
          to="/health"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <span className="nav-icon">🩺</span>
          <span className="nav-label">System Health</span>
        </NavLink>
      </nav>
      <div className="sidebar-footer">
        <div className="system-pill">Modular Monolith</div>
        <div className="version-pill">v0.1.0-alpha</div>
      </div>
    </aside>
  );
};
