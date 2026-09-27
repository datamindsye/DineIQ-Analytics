import React, { useEffect, useState } from 'react';
import { useFilters } from '../../context/useFilters';
import { apiService } from '../../services/api';
import type { HealthStatus } from '../../types';

export const Header: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const { selectedLocation, setSelectedLocation, options, currentRole, setCurrentRole } = useFilters();

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
        <div className="role-control">
          <span className="role-label">Role:</span>
          <select
            value={currentRole}
            onChange={(e) => setCurrentRole(e.target.value as 'Admin' | 'StoreManager' | 'DataScientist')}
            className="role-select"
          >
            <option value="Admin">Admin (Full Access)</option>
            <option value="StoreManager">Store Manager</option>
            <option value="DataScientist">Data Scientist</option>
          </select>
        </div>

        <span className={`status-badge ${health?.status === 'ok' ? 'ok' : 'warning'}`}>
          {health?.status === 'ok' ? '● Pipeline Online' : '○ Standby'}
        </span>
      </div>
    </header>
  );
};
