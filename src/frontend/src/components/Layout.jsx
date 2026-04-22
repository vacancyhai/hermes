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
            <span style={{ width: 30, height: 30, background: 'rgba(255,255,255,.15)', borderRadius: '0.4rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Landmark size={16} strokeWidth={2.5} />
            </span>
            {' '}Vacancy Hai
          </Link>

          {/* Center nav — desktop only */}
          <nav className="md:flex hidden" style={{ alignItems: 'center', gap: '0.1rem', flex: 1, justifyContent: 'center', overflowX: 'auto', scrollbarWidth: 'none' }}>
            {navLinks.map(({ to, icon: Icon, label, exact }) => (
              <NavLink key={to} to={to} end={exact} className={navLinkClass}
                style={{ borderBottom: '2px solid transparent', padding: '0.65rem 0.75rem', textDecoration: 'none', color: 'rgba(255,255,255,0.75)', fontSize: '0.82rem', fontWeight: 500, display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}
              >
                <Icon size={14} strokeWidth={2} />{label}
              </NavLink>
            ))}
          </nav>

          {/* Right nav — desktop only */}
          <nav className="md:flex hidden" style={{ alignItems: 'center', gap: '0.25rem' }}>
            {token ? (
              <>
                <Link to="/profile" style={{ color: 'rgba(255,255,255,.82)', fontSize: '0.875rem', fontWeight: 500, padding: '0.35rem 0.65rem', borderRadius: '0.35rem', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}><User size={15} strokeWidth={2} />Profile</Link>
                <Link to="/notifications" style={{ position: 'relative', color: 'rgba(255,255,255,.82)', fontSize: '0.875rem', padding: '0.35rem 0.65rem', textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}>
                  <Bell size={15} strokeWidth={2} /><NotifBadge />
                </Link>
                <button onClick={handleLogout} style={{ color: 'rgba(255,255,255,.82)', fontSize: '0.875rem', fontWeight: 500, padding: '0.35rem 0.65rem', borderRadius: '0.35rem', background: 'none', border: 'none', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}><LogOut size={15} strokeWidth={2} />Logout</button>
              </>
            ) : (
              <Link to="/login" style={{ background: 'rgba(255,255,255,.15)', color: '#fff', border: '1px solid rgba(255,255,255,.2)', fontSize: '0.875rem', fontWeight: 500, padding: '0.35rem 0.65rem', borderRadius: '0.35rem', textDecoration: 'none' }}>Login</Link>
            )}
          </nav>

          {/* Hamburger — mobile only */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden"
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: '0.4rem', border: 'none', background: 'transparent', borderRadius: '0.3rem', color: '#fff' }}
            aria-label="Toggle menu"
          >
            {menuOpen ? <X size={22} strokeWidth={2} /> : <Menu size={22} strokeWidth={2} />}
          </button>
        </div>

        {/* Mobile dropdown menu */}
        {menuOpen && (
          <div className="md:hidden" style={{ background: '#162d4a', borderTop: '1px solid rgba(255,255,255,.08)' }}>
            {navLinks.map(({ to, icon: Icon, label }) => (
              <Link key={to} to={to} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'rgba(255,255,255,.85)', fontSize: '0.9rem', padding: '0.65rem 1rem', borderBottom: '1px solid rgba(255,255,255,.06)', textDecoration: 'none' }}>
                <Icon size={16} strokeWidth={2} />{label}
              </Link>
            ))}
            {token ? (
              <>
                <Link to="/profile" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'rgba(255,255,255,.85)', fontSize: '0.9rem', padding: '0.65rem 1rem', borderBottom: '1px solid rgba(255,255,255,.06)', textDecoration: 'none' }}><User size={16} strokeWidth={2} />Profile</Link>
                <Link to="/notifications" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'rgba(255,255,255,.85)', fontSize: '0.9rem', padding: '0.65rem 1rem', borderBottom: '1px solid rgba(255,255,255,.06)', textDecoration: 'none' }}><Bell size={16} strokeWidth={2} />Notifications</Link>
                <button onClick={handleLogout} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', width: '100%', textAlign: 'left', color: 'rgba(255,255,255,.85)', fontSize: '0.9rem', padding: '0.65rem 1rem', background: 'none', border: 'none', cursor: 'pointer' }}><LogOut size={16} strokeWidth={2} />Logout</button>
              </>
            ) : (
              <Link to="/login" style={{ display: 'block', color: 'rgba(255,255,255,.85)', fontSize: '0.9rem', padding: '0.65rem 1rem', textDecoration: 'none' }}>Login</Link>
            )}
          </div>
        )}
      </header>

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
