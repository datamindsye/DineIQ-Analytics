import { createContext } from 'react';
import type { UserResponse } from '../types';

export type UserRole = 'Admin' | 'StoreManager' | 'DataScientist' | 'Cashier' | 'User';

export interface AuthContextType {
  user: UserResponse | null;
  token: string | null;
  role: UserRole;
  roles: string[];
  permissions: string[];
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (...allowedRoles: string[]) => boolean;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);
