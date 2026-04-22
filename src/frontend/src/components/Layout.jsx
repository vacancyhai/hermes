import { useState, useEffect } from 'react';
import { Outlet, NavLink, Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/client';

function NotifBadge() {
  const [count, setCount] = useState(0);
  const { token } = useAuth();

  useEffect(() => {
    if (!token) { setCount(0); return; }
    const fetch = async () => {
      try {
        const res = await api.get('/notifications/count');
        setCount(res.data.count || 0);
      } catch { }
    };
    fetch();
    const id = setInterval(fetch, 30000);
    return () => clearInterval(id);
  }, [token]);

  if (!count) return null;
  return (
    <span style={{
      position: 'absolute', top: -5, right: -8,
      background: '#ef4444', color: '#fff',
      borderRadius: '50%', fontSize: '0.6rem', minWidth: 15, height: 15,
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      fontWeight: 700, border: '1.5px solid #1e3a5f',
    }}>
      {count > 99 ? '99+' : count}
    </span>
  );
}

const navLinks = [
  { to: '/', label: '🏠 Home', exact: true },
  { to: '/jobs', label: '💼 Jobs' },
  { to: '/admit-cards', label: '🪪 Admit Cards' },
  { to: '/answer-keys', label: '📝 Answer Keys' },
  { to: '/results', label: '🏆 Results' },
  { to: '/admissions', label: '🎓 Admissions' },
];

export default function Layout() {
  const { token, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => { setMenuOpen(false); }, [location.pathname]);

  async function handleLogout() {
    try { await api.post('/auth/logout'); } catch { }
    logout();
    navigate('/login');
  };

  const navLinkClass = ({ isActive }) =>
    `text-sm font-medium px-3 py-2 rounded transition-colors whitespace-nowrap border-b-2 no-underline ` +
    (isActive
      ? 'text-white border-blue-400 font-bold'
      : 'text-white/75 border-transparent hover:text-white');

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header style={{
        background: '#1e3a5f', color: '#fff', position: 'sticky', top: 0, zIndex: 100,
        boxShadow: '0 1px 4px rgba(0,0,0,.25)',
      }}>
        <div style={{ width: '100%', padding: '1rem 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
          {/* Brand */}
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 800, fontSize: '1.15rem', color: '#fff', flexShrink: 0, textDecoration: 'none' }}>
            <span style={{ width: 30, height: 30, background: 'rgba(255,255,255,.15)', borderRadius: '0.4rem', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.95rem' }}>🏛</span>
            Vacancy Hai
          </Link>

          {/* Center nav (desktop) */}
          <nav style={{ display: 'flex', alignItems: 'center', gap: '0.1rem', flex: 1, justifyContent: 'center', overflowX: 'auto', scrollbarWidth: 'none' }}
            className="hidden md:flex">
            {navLinks.map(({ to, label, exact }) => (
              <NavLink key={to} to={to} end={exact} className={navLinkClass}
                style={{ borderBottom: '2px solid transparent', padding: '0.65rem 0.85rem', textDecoration: 'none', color: 'rgba(255,255,255,0.75)', fontSize: '0.85rem', fontWeight: 500 }}
              >
                {label}
              </NavLink>
            ))}
          </nav>

          {/* Right nav (desktop) */}
          <nav style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }} className="hidden sm:flex">
            {token ? (
              <>
                <Link to="/profile" style={{ color: 'rgba(255,255,255,.82)', fontSize: '0.875rem', fontWeight: 500, padding: '0.35rem 0.65rem', borderRadius: '0.35rem', textDecoration: 'none' }}>Profile</Link>
                <Link to="/notifications" style={{ position: 'relative', color: 'rgba(255,255,255,.82)', fontSize: '0.875rem', padding: '0.35rem 0.65rem', textDecoration: 'none', display: 'inline-flex' }}>
                  🔔<NotifBadge />
                </Link>
                <button onClick={handleLogout} style={{ color: 'rgba(255,255,255,.82)', fontSize: '0.875rem', fontWeight: 500, padding: '0.35rem 0.65rem', borderRadius: '0.35rem', background: 'none', border: 'none', cursor: 'pointer' }}>Logout</button>
              </>
            ) : (
              <Link to="/login" style={{ background: 'rgba(255,255,255,.15)', color: '#fff', border: '1px solid rgba(255,255,255,.2)', fontSize: '0.875rem', fontWeight: 500, padding: '0.35rem 0.65rem', borderRadius: '0.35rem', textDecoration: 'none' }}>Login</Link>
            )}
          </nav>

          {/* Hamburger */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            style={{ display: 'flex', flexDirection: 'column', gap: 4, cursor: 'pointer', padding: '0.4rem', border: 'none', background: 'transparent', borderRadius: '0.3rem' }}
            className="sm:hidden"
            aria-label="Toggle menu"
          >
            <span style={{ display: 'block', width: 20, height: 2, background: '#fff', borderRadius: 2 }} />
            <span style={{ display: 'block', width: 20, height: 2, background: '#fff', borderRadius: 2 }} />
            <span style={{ display: 'block', width: 20, height: 2, background: '#fff', borderRadius: 2 }} />
          </button>
        </div>

        {/* Mobile nav */}
        {menuOpen && (
          <div style={{ background: '#162d4a', borderTop: '1px solid rgba(255,255,255,.08)' }}>
            {navLinks.map(({ to, label }) => (
              <Link key={to} to={to} style={{ display: 'block', color: 'rgba(255,255,255,.85)', fontSize: '0.9rem', padding: '0.65rem 1rem', borderBottom: '1px solid rgba(255,255,255,.06)', textDecoration: 'none' }}>
                {label}
              </Link>
            ))}
            {token ? (
              <>
                <Link to="/profile" style={{ display: 'block', color: 'rgba(255,255,255,.85)', fontSize: '0.9rem', padding: '0.65rem 1rem', borderBottom: '1px solid rgba(255,255,255,.06)', textDecoration: 'none' }}>Profile</Link>
                <Link to="/notifications" style={{ display: 'block', color: 'rgba(255,255,255,.85)', fontSize: '0.9rem', padding: '0.65rem 1rem', borderBottom: '1px solid rgba(255,255,255,.06)', textDecoration: 'none' }}>Notifications 🔔</Link>
                <button onClick={handleLogout} style={{ display: 'block', width: '100%', textAlign: 'left', color: 'rgba(255,255,255,.85)', fontSize: '0.9rem', padding: '0.65rem 1rem', background: 'none', border: 'none', cursor: 'pointer', borderBottom: '1px solid rgba(255,255,255,.06)' }}>Logout</button>
              </>
            ) : (
              <Link to="/login" style={{ display: 'block', color: 'rgba(255,255,255,.85)', fontSize: '0.9rem', padding: '0.65rem 1rem', textDecoration: 'none' }}>Login</Link>
            )}
          </div>
        )}
      </header>

      {/* Mobile secondary nav (scrollable) */}
      <nav style={{ background: '#162d4a', borderBottom: '1px solid rgba(255,255,255,.08)', overflowX: 'auto', whiteSpace: 'nowrap', display: 'flex', scrollbarWidth: 'none' }} className="md:hidden">
        {navLinks.map(({ to, label, exact }) => (
          <NavLink key={to} to={to} end={exact} style={({ isActive }) => ({
            padding: '0.5rem 0.85rem', fontSize: '0.8rem', whiteSpace: 'nowrap',
            color: isActive ? '#fff' : 'rgba(147,175,197,.85)',
            borderBottom: isActive ? '2px solid #60a5fa' : '2px solid transparent',
            fontWeight: isActive ? 700 : 500, textDecoration: 'none', display: 'inline-block',
            flexShrink: 0,
          })}>
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Main content */}
      <main style={{ width: '100%', padding: '1.25rem 1.5rem 2rem', flex: 1 }}>
        <Outlet />
      </main>

      {/* Footer */}
      <footer style={{ textAlign: 'center', padding: '1.5rem', color: '#64748b', fontSize: '0.82rem', borderTop: '1px solid #e2e8f0' }}>
        <p>Vacancy Hai — Government Job Vacancy Portal © 2025 &nbsp;·&nbsp; <Link to="/jobs" style={{ color: '#64748b' }}>Jobs</Link> &nbsp;·&nbsp; <Link to="/admissions" style={{ color: '#64748b' }}>Admissions</Link></p>
      </footer>
    </div>
  );
}
