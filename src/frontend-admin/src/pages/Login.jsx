import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const BASE_URL = import.meta.env.VITE_BACKEND_API_URL || '/api/v1';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await axios.post(`${BASE_URL}/auth/admin/login`, { email, password });
      const tokenData = res.data;
      // Fetch verified name/role from backend
      try {
        const me = await axios.get(`${BASE_URL}/admin/me`, {
          headers: { Authorization: `Bearer ${tokenData.access_token}` },
        });
        tokenData.name = me.data.full_name || me.data.email || email;
        tokenData.role = me.data.role || '';
      } catch (_) {
        tokenData.name = email;
      }
      login(tokenData);
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
      <div style={{ width: '100%', maxWidth: 420 }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 60, height: 60, background: '#fff', borderRadius: '1rem', boxShadow: '0 4px 16px rgba(0,0,0,.25)', marginBottom: '.75rem' }}>
            <span style={{ fontWeight: 900, fontSize: '1.4rem', color: '#1e3a5f' }}>V</span>
          </div>
          <h1 style={{ color: '#fff', fontSize: '1.5rem', fontWeight: 800, margin: 0 }}>Admin Portal</h1>
          <p style={{ color: '#93c5fd', fontSize: '.85rem', marginTop: '.25rem' }}>Vacancy Hai • Restricted Access</p>
        </div>

        {/* Card */}
        <div style={{ background: '#fff', borderRadius: '1rem', boxShadow: '0 8px 32px rgba(0,0,0,.18)', padding: '2rem' }}>
          {error && <div className="flash-error">{error}</div>}
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label htmlFor="email">Email Address <span className="req">*</span></label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                placeholder="admin@example.com"
              />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label htmlFor="password">Password <span className="req">*</span></label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                placeholder="••••••••"
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ padding: '.65rem', fontSize: '.95rem', marginTop: '.5rem' }} disabled={loading}>
              {loading ? <><span className="spinner" style={{ borderTopColor: '#fff', borderColor: 'rgba(255,255,255,.3)' }} /> Signing in…</> : 'Sign In'}
            </button>
          </form>
        </div>
        <p style={{ textAlign: 'center', color: 'rgba(255,255,255,.5)', fontSize: '.75rem', marginTop: '1.25rem' }}>
          Unauthorised access is strictly prohibited.
        </p>
      </div>
    </div>
  );
}
