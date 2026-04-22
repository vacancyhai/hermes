import { useState, useEffect } from 'react';
import { Outlet, NavLink, Link, useNavigate, useLocation } from 'react-router-dom';
import { Home, Briefcase, CreditCard, FileText, Trophy, GraduationCap, Bell, User, LogOut, Menu, X, Landmark } from 'lucide-react';
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
  { to: '/', icon: Home, label: 'Home', exact: true },
  { to: '/jobs', icon: Briefcase, label: 'Jobs' },
  { to: '/admit-cards', icon: CreditCard, label: 'Admit Cards' },
  { to: '/answer-keys', icon: FileText, label: 'Answer Keys' },
  { to: '/results', icon: Trophy, label: 'Results' },
  { to: '/admissions', icon: GraduationCap, label: 'Admissions' },
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

  const navLinkStyle = (isActive) => ({
    padding: '0.45rem 0.8rem',
    textDecoration: 'none',
    fontSize: '0.82rem',
    fontWeight: isActive ? 700 : 500,
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.3rem',
    borderRadius: '0.375rem',
    background: isActive ? 'rgba(255,255,255,.12)' : 'transparent',
    color: isActive ? '#fff' : 'rgba(255,255,255,.72)',
    transition: 'background 0.15s, color 0.15s',
    whiteSpace: 'nowrap',
  });

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', overflowX: 'hidden', maxWidth: '100vw' }}>
      {/* Header */}
      <header style={{
        background: 'linear-gradient(90deg, #0f2440 0%, #1e3a5f 100%)',
        color: '#fff',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        boxShadow: '0 2px 12px rgba(0,0,0,.3)',
        borderBottom: '1px solid rgba(255,255,255,.06)',
      }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 1.5rem', height: 56, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
          {/* Brand */}
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 800, fontSize: '1.1rem', color: '#fff', flexShrink: 0, textDecoration: 'none', letterSpacing: '-0.02em' }}>
            <span style={{ width: 32, height: 32, background: 'linear-gradient(135deg, #3b82f6, #2563eb)', borderRadius: '0.45rem', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 2px 8px rgba(37,99,235,.5)' }}>
              <Landmark size={16} strokeWidth={2.5} />
            </span>
            Vacancy Hai
          </Link>

          {/* Center nav — desktop only */}
          <nav className="md:flex hidden" style={{ alignItems: 'center', gap: '0.05rem', flex: 1, justifyContent: 'center' }}>
            {navLinks.map(({ to, icon: Icon, label, exact }) => (
              <NavLink key={to} to={to} end={exact}
                style={({ isActive }) => navLinkStyle(isActive)}
              >
                <Icon size={13} strokeWidth={2} />{label}
              </NavLink>
            ))}
          </nav>

          {/* Right nav — desktop only */}
          <nav className="md:flex hidden" style={{ alignItems: 'center', gap: '0.2rem', flexShrink: 0 }}>
            {token ? (
              <>
                <Link to="/profile" style={{ color: 'rgba(255,255,255,.8)', fontSize: '0.82rem', fontWeight: 500, padding: '0.4rem 0.7rem', borderRadius: '0.4rem', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem', transition: 'background 0.15s' }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,.1)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                ><User size={14} strokeWidth={2} />Profile</Link>
                <Link to="/notifications" style={{ position: 'relative', color: 'rgba(255,255,255,.8)', fontSize: '0.82rem', padding: '0.4rem 0.7rem', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem', borderRadius: '0.4rem', transition: 'background 0.15s' }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,.1)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <Bell size={14} strokeWidth={2} /><NotifBadge />
                </Link>
                <button onClick={handleLogout} style={{ color: 'rgba(255,255,255,.8)', fontSize: '0.82rem', fontWeight: 500, padding: '0.4rem 0.7rem', borderRadius: '0.4rem', background: 'none', border: 'none', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.3rem', transition: 'background 0.15s' }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,.1)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                ><LogOut size={14} strokeWidth={2} />Logout</button>
              </>
            ) : (
              <Link to="/login" style={{ background: 'rgba(255,255,255,.12)', color: '#fff', border: '1px solid rgba(255,255,255,.18)', fontSize: '0.82rem', fontWeight: 600, padding: '0.4rem 0.9rem', borderRadius: '0.4rem', textDecoration: 'none', transition: 'background 0.15s' }}
                onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,.2)'}
                onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,.12)'}
              >Sign In</Link>
            )}
          </nav>

          {/* Hamburger — mobile only */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden"
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: '0.4rem', border: '1px solid rgba(255,255,255,.15)', background: 'rgba(255,255,255,.08)', borderRadius: '0.4rem', color: '#fff', transition: 'background 0.15s' }}
            aria-label="Toggle menu"
          >
            {menuOpen ? <X size={20} strokeWidth={2} /> : <Menu size={20} strokeWidth={2} />}
          </button>
        </div>

        {/* Mobile dropdown menu */}
        {menuOpen && (
          <div className="md:hidden" style={{ background: '#0f2440', borderTop: '1px solid rgba(255,255,255,.06)', padding: '0.5rem 0' }}>
            {navLinks.map(({ to, icon: Icon, label }) => (
              <Link key={to} to={to} style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', color: 'rgba(255,255,255,.82)', fontSize: '0.875rem', padding: '0.6rem 1.25rem', textDecoration: 'none', transition: 'background 0.15s' }}
                onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,.06)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                <Icon size={15} strokeWidth={2} />{label}
              </Link>
            ))}
            <div style={{ height: '1px', background: 'rgba(255,255,255,.06)', margin: '0.4rem 0' }} />
            {token ? (
              <>
                <Link to="/profile" style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', color: 'rgba(255,255,255,.82)', fontSize: '0.875rem', padding: '0.6rem 1.25rem', textDecoration: 'none' }}><User size={15} strokeWidth={2} />Profile</Link>
                <Link to="/notifications" style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', color: 'rgba(255,255,255,.82)', fontSize: '0.875rem', padding: '0.6rem 1.25rem', textDecoration: 'none' }}><Bell size={15} strokeWidth={2} />Notifications</Link>
                <button onClick={handleLogout} style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', width: '100%', textAlign: 'left', color: 'rgba(255,255,255,.82)', fontSize: '0.875rem', padding: '0.6rem 1.25rem', background: 'none', border: 'none', cursor: 'pointer' }}><LogOut size={15} strokeWidth={2} />Logout</button>
              </>
            ) : (
              <Link to="/login" style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', color: '#60a5fa', fontSize: '0.875rem', fontWeight: 600, padding: '0.6rem 1.25rem', textDecoration: 'none' }}>Sign In</Link>
            )}
          </div>
        )}
      </header>

      {/* Main content */}
      <main style={{ flex: 1, padding: '1.5rem', background: '#f0f4f8', overflowX: 'hidden', minWidth: 0 }}>
        <div style={{ maxWidth: 1280, margin: '0 auto' }}>
          <Outlet />
        </div>
      </main>

      {/* Footer */}
      <footer style={{ background: '#fff', borderTop: '1px solid #e2e8f0', padding: '1.25rem 1.5rem' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
          <p style={{ color: '#64748b', fontSize: '0.8rem' }}>© 2025 Vacancy Hai — Government Jobs &amp; Exam Tracker</p>
          <div style={{ display: 'flex', gap: '1.25rem' }}>
            {[['Jobs', '/jobs'], ['Admissions', '/admissions'], ['Results', '/results'], ['Notifications', '/notifications']].map(([label, href]) => (
              <Link key={href} to={href} style={{ color: '#94a3b8', fontSize: '0.8rem', textDecoration: 'none', transition: 'color 0.15s' }}
                onMouseEnter={e => e.currentTarget.style.color = '#2563eb'}
                onMouseLeave={e => e.currentTarget.style.color = '#94a3b8'}
              >{label}</Link>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
