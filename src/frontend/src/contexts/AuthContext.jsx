import PropTypes from 'prop-types';
import { createContext, useContext, useState, useCallback, useEffect, useMemo } from 'react';
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
      } catch (err) { void err; }
    }
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_name');
    setToken(null);
    setUserName('');
  }, []);

  useEffect(() => {
    globalThis.addEventListener('auth:logout', logout);
    return () => globalThis.removeEventListener('auth:logout', logout);
  }, [logout]);

  const value = useMemo(() => ({ token, userName, login, logout }), [token, userName, login, logout]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

AuthProvider.propTypes = { children: PropTypes.node.isRequired };

export function useAuth() {
  return useContext(AuthContext);
}
