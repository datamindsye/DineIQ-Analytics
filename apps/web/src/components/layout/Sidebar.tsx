import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/useAuth';
<<<<<<< HEAD

export const Sidebar: React.FC = () => {
  const { hasRole, role } = useAuth();

  const canViewExecutive = hasRole('Admin', 'StoreManager', 'DataScientist');
  const canViewOperationalBI = hasRole('Admin', 'StoreManager', 'DataScientist');
  const canViewArena = hasRole('Admin', 'DataScientist');
  const canViewScenarios = hasRole('Admin', 'StoreManager', 'DataScientist');

  return (
    <aside className="app-sidebar">
=======

export interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen = false, onClose }) => {
  const { hasRole, role } = useAuth();

  const canViewExecutive = hasRole('Admin', 'StoreManager', 'DataScientist');
  const canViewOperationalBI = hasRole('Admin', 'StoreManager', 'DataScientist');
  const canViewArena = hasRole('Admin', 'DataScientist');
  const canViewScenarios = hasRole('Admin', 'StoreManager', 'DataScientist');

  return (
    <aside className={`app-sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-mobile-header">
        <span className="brand-logo">DineIQ</span>
        <button
          type="button"
          className="sidebar-close-btn"
          onClick={onClose}
          aria-label="Close sidebar"
        >
          ✕
        </button>
      </div>

>>>>>>> be10b32 (chore: prepare final competition repository)
      <nav className="sidebar-nav">
        {canViewExecutive && (
          <>
            <div className="nav-group-label">OVERVIEW</div>
            <NavLink
              to="/"
              end
<<<<<<< HEAD
=======
              onClick={onClose}
>>>>>>> be10b32 (chore: prepare final competition repository)
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">📊</span>
              <span className="nav-label">Executive Overview</span>
            </NavLink>
          </>
        )}

        <div className="nav-group-label">BUSINESS INTELLIGENCE</div>
        <NavLink
          to="/menu"
          onClick={onClose}
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <span className="nav-icon">🍽️</span>
          <span className="nav-label">Menu Intelligence</span>
        </NavLink>

        {canViewOperationalBI && (
          <>
            <NavLink
              to="/customers"
<<<<<<< HEAD
=======
              onClick={onClose}
>>>>>>> be10b32 (chore: prepare final competition repository)
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">👥</span>
              <span className="nav-label">Customer & RFM</span>
            </NavLink>

            <NavLink
              to="/sales"
<<<<<<< HEAD
=======
              onClick={onClose}
>>>>>>> be10b32 (chore: prepare final competition repository)
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">🏪</span>
              <span className="nav-label">Sales & Operations</span>
            </NavLink>

            <NavLink
              to="/demand-pricing"
<<<<<<< HEAD
=======
              onClick={onClose}
>>>>>>> be10b32 (chore: prepare final competition repository)
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">📈</span>
              <span className="nav-label">Demand & Pricing</span>
            </NavLink>

            <NavLink
              to="/wastage"
<<<<<<< HEAD
=======
              onClick={onClose}
>>>>>>> be10b32 (chore: prepare final competition repository)
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">🗑️</span>
              <span className="nav-label">Wastage & Inventory</span>
            </NavLink>

            <NavLink
              to="/promotions"
<<<<<<< HEAD
=======
              onClick={onClose}
>>>>>>> be10b32 (chore: prepare final competition repository)
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">🏷️</span>
              <span className="nav-label">Promotions & Basket</span>
            </NavLink>

            <NavLink
              to="/anomalies"
<<<<<<< HEAD
=======
              onClick={onClose}
>>>>>>> be10b32 (chore: prepare final competition repository)
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">⚠️</span>
              <span className="nav-label">Ratings & Anomalies</span>
            </NavLink>
          </>
        )}

        {(canViewArena || canViewScenarios) && (
          <>
            <div className="nav-group-label">INTELLIGENCE & SCENARIOS</div>
            {canViewArena && (
              <NavLink
                to="/arena"
<<<<<<< HEAD
=======
                onClick={onClose}
>>>>>>> be10b32 (chore: prepare final competition repository)
                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              >
                <span className="nav-icon">⚔️</span>
                <span className="nav-label">Data Science Arena</span>
              </NavLink>
            )}

            {canViewScenarios && (
              <>
                <NavLink
                  to="/recommendations"
<<<<<<< HEAD
=======
                  onClick={onClose}
>>>>>>> be10b32 (chore: prepare final competition repository)
                  className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                >
                  <span className="nav-icon">💡</span>
                  <span className="nav-label">Recommendations</span>
                </NavLink>

                <NavLink
                  to="/what-if"
<<<<<<< HEAD
=======
                  onClick={onClose}
>>>>>>> be10b32 (chore: prepare final competition repository)
                  className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                >
                  <span className="nav-icon">🎛️</span>
                  <span className="nav-label">What-If Analysis</span>
                </NavLink>
              </>
            )}
          </>
        )}

        <div className="nav-group-label">INFRASTRUCTURE</div>
        <NavLink
          to="/health"
          onClick={onClose}
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <span className="nav-icon">🩺</span>
          <span className="nav-label">Pipelines & Health</span>
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <div className="system-pill">Role: {role}</div>
        <div className="version-pill">DineIQ v1.0 Production</div>
      </div>
    </aside>
  );
};
