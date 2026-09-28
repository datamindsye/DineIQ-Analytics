import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { apiService } from '../services/api';
import type { UserResponse } from '../types';
import { AuthContext, type UserRole } from './AuthContextCore';

const TOKEN_KEY = 'dineiq_token';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [token, setToken] = useState<string | null>(() => {
    if (typeof localStorage !== 'undefined') {
      return localStorage.getItem(TOKEN_KEY);
    }
    return null;
  });
  const [isLoading, setIsLoading] = useState<boolean>(() => {
    if (typeof localStorage !== 'undefined') {
      return !!localStorage.getItem(TOKEN_KEY);
    }
    return false;
  });

  const logout = useCallback(() => {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem(TOKEN_KEY);
    }
    setToken(null);
    setUser(null);
  }, []);

  // Fetch current user whenever token is set
  useEffect(() => {
    let isMounted = true;
    if (!token) {
      return;
    }

    apiService
      .getMe()
      .then((userData) => {
        if (isMounted) {
          setUser(userData);
          setIsLoading(false);
        }
      })
      .catch((_err) => {
        if (isMounted) {
          logout();
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [token, logout]);

  // Listen for unauthorized 401 event across app
  useEffect(() => {
    const handleUnauthorized = () => {
      logout();
    };

    window.addEventListener('dineiq:unauthorized', handleUnauthorized);
    return () => {
      window.removeEventListener('dineiq:unauthorized', handleUnauthorized);
    };
  }, [logout]);

  const login = useCallback(async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await apiService.login({ username, password });
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(TOKEN_KEY, response.access_token);
      }
      setToken(response.access_token);
      setUser(response.user);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const roles = useMemo(() => {
    if (!user) return [];
    return user.roles.map((r) => r.name);
  }, [user]);

  const permissions = useMemo(() => {
    if (!user) return [];
    const set = new Set<string>();
    for (const r of user.roles) {
      for (const p of r.permissions) {
        set.add(p.name);
      }
    }
    return Array.from(set);
  }, [user]);

  const role: UserRole = useMemo(() => {
    if (!user) return 'User';
    if (user.is_superuser || roles.includes('Admin')) return 'Admin';
    if (roles.includes('StoreManager')) return 'StoreManager';
    if (roles.includes('DataScientist')) return 'DataScientist';
    if (roles.includes('Cashier')) return 'Cashier';
    return (roles[0] as UserRole) || 'User';
  }, [user, roles]);

  const hasRole = useCallback(
    (...allowedRoles: string[]) => {
      if (!user) return false;
      if (user.is_superuser) return true;
      return roles.some((r) => allowedRoles.includes(r));
    },
    [user, roles]
  );

  const contextValue = useMemo(
    () => ({
      user,
      token,
      role,
      roles,
      permissions,
      isAuthenticated: !!token && !!user,
      isLoading,
      login,
      logout,
      hasRole,
    }),
    [user, token, role, roles, permissions, isLoading, login, logout, hasRole]
  );

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
};
