import { useContext } from 'react';
import { AuthContext, type AuthContextType, type UserRole } from './AuthContextCore';

export type { UserRole };

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
