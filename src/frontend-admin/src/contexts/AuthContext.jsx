import { createContext, useContext, useState, useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('admin_token'));
  const [adminName, setAdminName] = useState(() => localStorage.getItem('admin_name') || '');
  const [adminRole, setAdminRole] = useState(() => localStorage.getItem('admin_role') || '');

  const login = useCallback((data) => {
    localStorage.setItem('admin_token', data.access_token);
    if (data.refresh_token) localStorage.setItem('admin_refresh_token', data.refresh_token);
    if (data.name) localStorage.setItem('admin_name', data.name);
    if (data.role) localStorage.setItem('admin_role', data.role);
    setToken(data.access_token);
    setAdminName(data.name || '');
    setAdminRole(data.role || '');
  }, []);

  const logout = useCallback(() => {
    ['admin_token', 'admin_refresh_token', 'admin_name', 'admin_role'].forEach(
      (k) => localStorage.removeItem(k)
    );
    setToken(null);
    setAdminName('');
    setAdminRole('');
  }, []);

  const value = useMemo(
    () => ({ token, adminName, adminRole, login, logout }),
    [token, adminName, adminRole, login, logout]
  );

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
