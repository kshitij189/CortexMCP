/**
 * Auth context — provides user state, login, register, logout to the entire app.
 */
import { createContext, useState, useEffect, useCallback } from 'react';
import { authAPI } from '../services/api';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // ─── Restore session on mount ───
  useEffect(() => {
    const token = localStorage.getItem('cortex_token');
    const savedUser = localStorage.getItem('cortex_user');

    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch {
        localStorage.removeItem('cortex_token');
        localStorage.removeItem('cortex_user');
      }
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (email, password) => {
    const res = await authAPI.login({ email, password });
    const { access_token, user: userData } = res.data;
    localStorage.setItem('cortex_token', access_token);
    localStorage.setItem('cortex_user', JSON.stringify(userData));
    setUser(userData);
    return userData;
  }, []);

  const register = useCallback(async (email, username, password) => {
    const res = await authAPI.register({ email, username, password });
    const { access_token, user: userData } = res.data;
    localStorage.setItem('cortex_token', access_token);
    localStorage.setItem('cortex_user', JSON.stringify(userData));
    setUser(userData);
    return userData;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('cortex_token');
    localStorage.removeItem('cortex_user');
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
