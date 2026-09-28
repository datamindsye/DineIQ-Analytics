import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/useAuth';

interface EvaluatorPreset {
  role: string;
  badge: string;
  badgeClass: string;
  username: string;
  password: string;
  description: string;
}

const EVALUATOR_PRESETS: EvaluatorPreset[] = [
  {
    role: 'Admin',
    badge: '👑 Full System Access',
    badgeClass: 'role-admin',
    username: 'admin',
    password: 'AdminDineIQ2026!',
    description: 'System administrator with full RBAC, model governance, and all analytical domains.',
  },
  {
    role: 'StoreManager',
    badge: '🏪 Operations & Pricing',
    badgeClass: 'role-storemanager',
    username: 'manager',
    password: 'ManagerPass123!',
    description: 'Restaurant manager with operational KPIs, what-if simulations, wastage, and CSV export.',
  },
  {
    role: 'DataScientist',
    badge: '🔬 ML & Arena',
    badgeClass: 'role-datascientist',
    username: 'scientist',
    password: 'ScientistPass123!',
    description: 'Data scientist with raw marts, ML models, tournament metadata, and comparison arena.',
  },
  {
    role: 'Cashier',
    badge: '💳 Operational POS',
    badgeClass: 'role-cashier',
    username: 'cashier',
    password: 'CashierPass123!',
    description: 'Frontline staff with catalog menu lookup; restricted from executive, ML, and sensitive analytics.',
  },
];

export const LoginPage: React.FC = () => {
  const { login, isAuthenticated, role } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  // If already authenticated, navigate to intended path or role default
  useEffect(() => {
    if (isAuthenticated) {
      const from = (location.state as { from?: { pathname?: string } })?.from?.pathname;
      if (from && from !== '/login') {
        navigate(from, { replace: true });
      } else if (role === 'Cashier') {
        navigate('/menu', { replace: true });
      } else {
        navigate('/', { replace: true });
      }
    }
  }, [isAuthenticated, role, navigate, location.state]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Please provide both username and password.');
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      await login(username.trim(), password);
      // Navigation is handled by the useEffect above
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Invalid credentials or authentication error';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSelectPreset = (preset: EvaluatorPreset) => {
    setUsername(preset.username);
    setPassword(preset.password);
    setError(null);
  };

  return (
    <div className="login-page-wrapper">
      <div className="login-modal-card">
        <div className="login-header">
          <div className="login-logo-badge">DineIQ</div>
          <h1 className="login-title">Analytics Intelligence Arena</h1>
          <p className="login-subtitle">
            Secure Role-Based Access Control • Apache Spark & Python MLlib Pipeline
          </p>
        </div>

        {error && (
          <div className="login-error-alert" role="alert">
            <span className="error-icon">⚠️</span>
            <span className="error-text">{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="login-username" className="form-label">
              Username or Email
            </label>
            <input
              id="login-username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. admin or manager"
              required
              autoComplete="username"
              className="form-input"
              disabled={isSubmitting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="login-password" className="form-label">
              Password
            </label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              required
              autoComplete="current-password"
              className="form-input"
              disabled={isSubmitting}
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="btn-login-submit"
          >
            {isSubmitting ? (
              <span className="submit-loading-text">
                <span className="btn-spinner" /> Authenticating...
              </span>
            ) : (
              'Sign In to DineIQ Analytics'
            )}
          </button>
        </form>

        <div className="evaluator-quickfill-section">
          <div className="evaluator-section-header">
            <span className="section-title">Evaluation & Tournament Test Accounts</span>
            <span className="section-badge">Click to Quick-Fill</span>
          </div>

          <div className="evaluator-cards-grid">
            {EVALUATOR_PRESETS.map((preset) => (
              <button
                key={preset.role}
                type="button"
                onClick={() => handleSelectPreset(preset)}
                className={`evaluator-card ${username === preset.username ? 'selected' : ''}`}
              >
                <div className="card-top">
                  <span className={`preset-badge ${preset.badgeClass}`}>{preset.role}</span>
                  <span className="preset-name">{preset.badge}</span>
                </div>
                <div className="preset-creds">
                  <code>{preset.username}</code> / <code>••••••••</code>
                </div>
                <p className="preset-desc">{preset.description}</p>
              </button>
            ))}
          </div>
        </div>

        <div className="login-footer">
          <span>Enterprise JWT Bearer • SHA-256 / Bcrypt Hashing • Zero External Cloud LLM Runtime</span>
        </div>
      </div>
    </div>
  );
};
