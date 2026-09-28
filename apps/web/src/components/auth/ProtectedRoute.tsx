import React from 'react';
import { Link, Navigate, useLocation } from 'react-router-dom';
import { useAuth, type UserRole } from '../../context/useAuth';

interface ProtectedRouteProps {
  children: React.ReactElement;
  allowedRoles?: UserRole[];
  pageTitle?: string;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  allowedRoles,
  pageTitle = 'this analytical resource',
}) => {
  const { isAuthenticated, isLoading, hasRole, role } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="auth-loading-screen">
        <div className="auth-spinner" />
        <div className="auth-loading-text">Verifying security credentials & session...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If role is Cashier and root path '/' is requested, seamlessly redirect to permitted menu
  if (role === 'Cashier' && location.pathname === '/') {
    return <Navigate to="/menu" replace />;
  }

  if (allowedRoles && allowedRoles.length > 0 && !hasRole(...allowedRoles)) {
    const fallbackPath = role === 'Cashier' ? '/menu' : '/';
    const fallbackLabel = role === 'Cashier' ? 'Menu Intelligence' : 'Executive Overview';

    return (
      <div className="page-container">
        <div className="forbidden-card">
          <div className="forbidden-icon">🛡️</div>
          <div className="forbidden-badge">HTTP 403 • ACCESS RESTRICTED</div>
          <h2 className="forbidden-title">Role-Based Authorization Required</h2>
          <p className="forbidden-desc">
            Your authenticated account role (<span className={`role-pill role-${role.toLowerCase()}`}>{role}</span>)
            does not have permission to view <strong>{pageTitle}</strong>.
          </p>
          <div className="forbidden-info-box">
            <div className="info-label">Required Roles:</div>
            <div className="info-roles">
              {allowedRoles.map((r) => (
                <span key={r} className={`role-pill role-${r.toLowerCase()}`}>
                  {r}
                </span>
              ))}
            </div>
          </div>
          <div className="forbidden-actions">
            <Link to={fallbackPath} className="btn-primary">
              Return to {fallbackLabel}
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return children;
};
