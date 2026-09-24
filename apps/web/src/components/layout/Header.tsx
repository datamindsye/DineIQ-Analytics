import React, { useEffect, useState } from 'react';
import { apiService } from '../../services/api';
import type { HealthStatus } from '../../types';

export const Header: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);

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
            status: 'degraded',
            environment: 'offline',
            version: '0.1.0',
            database: 'disconnected',
            timestamp: new Date().toISOString(),
          });
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const getStatusBadge = () => {
    if (!health) return <span className="status-badge loading">Connecting...</span>;
    if (health.status === 'ok') return <span className="status-badge ok">API Online</span>;
    return <span className="status-badge warning">API Degraded</span>;
  };

  return (
    <header className="app-header">
      <div className="header-brand">
        <span className="brand-logo">DineIQ</span>
        <span className="brand-subtitle">Analytics Intelligence Arena</span>
      </div>
      <div className="header-meta">
        <span className="env-badge">{health?.environment || 'development'}</span>
        {getStatusBadge()}
      </div>
    </header>
  );
};
