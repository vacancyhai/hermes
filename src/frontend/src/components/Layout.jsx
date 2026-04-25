import { useState, useEffect } from 'react';
import { Outlet, NavLink, Link, useNavigate, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { Home, Briefcase, CreditCard, FileText, Trophy, GraduationCap, Bell, User, LogOut, Menu, X, Landmark } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/client';

const pageVariants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.22, ease: [0.16, 1, 0.3, 1] } },
  exit: { opacity: 0, y: -6, transition: { duration: 0.14, ease: 'easeIn' } },
};

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
    padding: '0.45rem 0.85rem',
    textDecoration: 'none',
    fontSize: '0.82rem',
    fontWeight: isActive ? 700 : 500,
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.32rem',
    borderRadius: '0.5rem',
    background: isActive ? 'rgba(255,255,255,.14)' : 'transparent',
    color: isActive ? '#fff' : 'rgba(255,255,255,.68)',
    boxShadow: isActive ? 'inset 0 1px 0 rgba(255,255,255,.1), 0 1px 3px rgba(0,0,0,.15)' : 'none',
    transition: 'background 0.18s, color 0.18s, box-shadow 0.18s',
    whiteSpace: 'nowrap',
    letterSpacing: '0.005em',
  });

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header style={{
        background: 'linear-gradient(90deg, rgba(15,36,64,.97) 0%, rgba(30,58,95,.97) 100%)',
        backdropFilter: 'blur(20px) saturate(180%)',
        WebkitBackdropFilter: 'blur(20px) saturate(180%)',
        color: '#fff',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        boxShadow: '0 1px 0 rgba(255,255,255,.06), 0 4px 24px rgba(0,0,0,.25)',
        borderBottom: '1px solid rgba(255,255,255,.08)',
      }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 1.5rem', height: 60, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
          {/* Brand */}
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.55rem', fontWeight: 800, fontSize: '1.1rem', color: '#fff', flexShrink: 0, textDecoration: 'none', letterSpacing: '-0.025em' }}>
            <span style={{ width: 34, height: 34, background: 'linear-gradient(135deg, #60a5fa, #2563eb, #1d4ed8)', borderRadius: '0.55rem', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 2px 12px rgba(37,99,235,.55), inset 0 1px 0 rgba(255,255,255,.2)' }}>
              <Landmark size={17} strokeWidth={2.5} />
            </span>
            <span style={{ background: 'linear-gradient(135deg, #ffffff, rgba(255,255,255,.85))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>Vacancy Hai</span>
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
            style={{ alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: '0.4rem', border: '1px solid rgba(255,255,255,.15)', background: 'rgba(255,255,255,.08)', borderRadius: '0.4rem', color: '#fff', transition: 'background 0.15s' }}
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
      <main style={{ flex: 1, padding: 'var(--sp-6) 1.5rem', background: 'var(--surface)' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto' }}>
          <AnimatePresence mode="wait" initial={false}>
            <motion.div key={location.pathname} variants={pageVariants} initial="initial" animate="animate" exit="exit">
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </div>
      </main>

      {/* Footer */}
      <footer style={{ background: 'linear-gradient(180deg, #fff 0%, #f8fafc 100%)', borderTop: '1px solid var(--slate-200)', padding: '1.25rem 1.5rem' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
          <p style={{ color: '#94a3b8', fontSize: '0.8rem', fontWeight: 500 }}>© 2025 Vacancy Hai — Government Jobs &amp; Exam Tracker</p>
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
