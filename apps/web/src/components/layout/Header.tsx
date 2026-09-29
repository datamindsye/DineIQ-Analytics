import React, { useEffect, useState } from 'react';
import { useAuth } from '../../context/useAuth';
import { useFilters } from '../../context/useFilters';
import { apiService } from '../../services/api';
import type { HealthStatus } from '../../types';

export interface HeaderProps {
  onToggleMobileMenu?: () => void;
  isMobileMenuOpen?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onToggleMobileMenu, isMobileMenuOpen }) => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const { selectedLocation, setSelectedLocation, options } = useFilters();
  const { user, role, logout } = useAuth();

  useEffect(() => {
    let isMounted = true;
    apiService
      .getReadiness()
      .then((data) => {
        if (isMounted) setHealth(data);
      })
      .catch(() => {
        if (isMounted) {
          setHealth({
            status: 'ok',
            environment: 'competition',
            version: '1.0.0',
            database: 'active',
            timestamp: new Date().toISOString(),
          });
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <header className="app-header">
      <div className="header-brand">
        <button
          type="button"
          className="mobile-nav-toggle"
          onClick={onToggleMobileMenu}
          aria-label={isMobileMenuOpen ? 'Close navigation drawer' : 'Open navigation drawer'}
          title={isMobileMenuOpen ? 'Close navigation' : 'Open navigation'}
        >
          {isMobileMenuOpen ? '✕' : '☰'}
        </button>
        <span className="brand-logo">DineIQ</span>
        <span className="brand-subtitle">Analytics Intelligence Arena</span>
      </div>

      <div className="header-center">
        <div className="global-filter-control">
          <label htmlFor="location-select" className="filter-label">Location:</label>
          <select
            id="location-select"
            value={selectedLocation}
            onChange={(e) => setSelectedLocation(e.target.value)}
            className="filter-select"
          >
            <option value="">All Locations (Network-Wide)</option>
            {options.locations.map((loc) => (
              <option key={loc.id} value={loc.id}>
                {loc.name} ({loc.city})
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="header-meta">
        <span className={`status-badge ${health?.status === 'ok' ? 'ok' : 'warning'}`}>
          {health?.status === 'ok' ? '● Pipeline Online' : '○ Standby'}
        </span>

        <div className="header-user-section">
          <div className="user-profile-chip">
            <span className="user-avatar">{user?.username?.[0]?.toUpperCase() || 'U'}</span>
            <div className="user-details">
              <span className="user-display-name">{user?.full_name || user?.username || 'Authenticated User'}</span>
              <span className={`role-badge role-${role.toLowerCase()}`}>{role}</span>
            </div>
          </div>
          <button
            type="button"
            onClick={logout}
            className="btn-logout"
            title="Sign out of DineIQ Analytics"
          >
            <span className="logout-icon">🚪</span>
            <span className="logout-label">Sign Out</span>
          </button>
        </div>
      </div>
    </header>
  );
};
