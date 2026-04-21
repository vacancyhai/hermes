import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import api from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [userName, setUserName] = useState(() => localStorage.getItem('user_name') || '');

  const login = useCallback((accessToken, refreshToken, name = '') => {
    localStorage.setItem('token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    if (name) localStorage.setItem('user_name', name);
    setToken(accessToken);
    setUserName(name);
  }, []);

  const logout = useCallback(async () => {
    const t = localStorage.getItem('token');
    if (t) {
      try {
        await api.post('/auth/logout');
      } catch (_) {}
    }
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_name');
    setToken(null);
    setUserName('');
  }, []);

  useEffect(() => {
    const handler = () => {
      setToken(null);
      setUserName('');
    };
    window.addEventListener('auth:logout', handler);
    return () => window.removeEventListener('auth:logout', handler);
  }, []);

  return (
    <AuthContext.Provider value={{ token, userName, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
