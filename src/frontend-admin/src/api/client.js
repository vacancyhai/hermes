import axios from 'axios';

const BASE_URL = import.meta.env.VITE_BACKEND_API_URL || '/api/v1';

const client = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

client.interceptors.request.use((cfg) => {
  const token = localStorage.getItem('admin_token');
  if (token) cfg.headers['Authorization'] = `Bearer ${token}`;
  return cfg;
});

let refreshing = null;

client.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config;
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true;
      if (!refreshing) {
        refreshing = axios
          .post(`${BASE_URL}/auth/admin/refresh`, {
            refresh_token: localStorage.getItem('admin_refresh_token'),
          })
          .then((r) => {
            localStorage.setItem('admin_token', r.data.access_token);
            if (r.data.refresh_token) localStorage.setItem('admin_refresh_token', r.data.refresh_token);
            return r.data.access_token;
          })
          .catch(() => {
            localStorage.removeItem('admin_token');
            localStorage.removeItem('admin_refresh_token');
            localStorage.removeItem('admin_name');
            localStorage.removeItem('admin_role');
            window.location.href = '/login';
            return null;
          })
          .finally(() => { refreshing = null; });
      }
      const newToken = await refreshing;
      if (newToken) {
        original.headers['Authorization'] = `Bearer ${newToken}`;
        return client(original);
      }
    }
    return Promise.reject(err);
  }
);

export default client;
