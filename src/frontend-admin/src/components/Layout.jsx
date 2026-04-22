import { useState } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import client from '../api/client';

const pageVariants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.22, ease: [0.16, 1, 0.3, 1] } },
  exit:    { opacity: 0, y: -6,  transition: { duration: 0.14, ease: 'easeIn' } },
};

const navItems = [
  { to: '/', label: 'Dashboard', exact: true },
  { to: '/jobs', label: 'Jobs' },
  { to: '/admissions', label: 'Admissions' },
  { to: '/users', label: 'Users' },
  { to: '/organizations', label: 'Organizations' },
  { to: '/logs', label: 'Audit Logs' },
];

export default function Layout() {
  const { adminName, adminRole, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  async function handleLogout() {
    try { await client.post('/auth/admin/logout'); } catch { }
    logout();
    navigate('/login');
  }

  const linkClass = ({ isActive }) =>
    `px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-150 ${isActive
      ? 'bg-white/[.15] text-white shadow-sm ring-1 ring-white/10'
      : 'text-blue-100/80 hover:bg-white/[.08] hover:text-white'}` ;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* ── Top navbar ── */}
      <header style={{
        background: 'linear-gradient(90deg, rgba(15,36,64,.97) 0%, rgba(30,58,95,.97) 60%, rgba(37,99,235,.95) 100%)',
        backdropFilter: 'blur(20px) saturate(180%)',
        WebkitBackdropFilter: 'blur(20px) saturate(180%)',
        boxShadow: '0 1px 0 rgba(255,255,255,.06), 0 4px 24px rgba(0,0,0,.28)',
        borderBottom: '1px solid rgba(255,255,255,.08)',
        zIndex: 10, position: 'sticky', top: 0,
      }}>
        <div style={{ maxWidth: 1400, margin: '0 auto', padding: '0 1.25rem', display: 'flex', alignItems: 'center', gap: '1rem', height: 58 }}>
          {/* Brand */}
          <NavLink to="/" style={{ fontWeight: 800, fontSize: '1rem', color: '#fff', textDecoration: 'none', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: '.5rem', letterSpacing: '-0.02em' }}>
            <span style={{ width: 30, height: 30, background: 'linear-gradient(135deg, #60a5fa, #2563eb, #1d4ed8)', borderRadius: '.45rem', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '.75rem', fontWeight: 900, color: '#fff', boxShadow: '0 2px 8px rgba(37,99,235,.5), inset 0 1px 0 rgba(255,255,255,.2)', flexShrink: 0 }}>V</span>
            <span style={{ background: 'linear-gradient(135deg,#fff,rgba(255,255,255,.8))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>Admin</span>
          </NavLink>

          {/* Desktop nav */}
          <nav style={{ display: 'flex', gap: '.25rem', flex: 1, overflowX: 'auto' }} className="hidden-xs">
            {navItems.map((n) => (
              <NavLink key={n.to} to={n.to} end={n.exact} className={linkClass}>
                {n.label}
              </NavLink>
            ))}
          </nav>

          {/* Right side */}
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '.75rem', flexShrink: 0 }}>
            {adminRole && (
              <span style={{ background: 'rgba(255,255,255,.15)', color: '#e0f2fe', fontSize: '.68rem', fontWeight: 700, padding: '.15rem .5rem', borderRadius: 9999, textTransform: 'uppercase', letterSpacing: '.05em' }}>
                {adminRole}
              </span>
            )}
            {adminName && (
              <span style={{ color: '#bfdbfe', fontSize: '.82rem' }}>{adminName}</span>
            )}
            <button onClick={handleLogout} className="btn btn-sm btn-outline" style={{ border: '1px solid rgba(255,255,255,.4)', color: '#fff', background: 'rgba(255,255,255,.08)' }}>
              Logout
            </button>

            {/* Mobile hamburger */}
            <button onClick={() => setMenuOpen(!menuOpen)} style={{ display: 'none', background: 'none', border: 'none', color: '#fff', cursor: 'pointer', padding: '.25rem' }} className="hamburger">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
            </button>
          </div>
        </div>

        {/* Mobile nav dropdown */}
        {menuOpen && (
          <div style={{ background: '#1e3a5f', padding: '.5rem 1rem 1rem', display: 'flex', flexDirection: 'column', gap: '.25rem' }}>
            {navItems.map((n) => (
              <NavLink key={n.to} to={n.to} end={n.exact} className={linkClass} onClick={() => setMenuOpen(false)}>
                {n.label}
              </NavLink>
            ))}
          </div>
        )}
      </header>

      {/* ── Main content ── */}
      <main style={{ flex: 1, maxWidth: 1400, margin: '0 auto', width: '100%', padding: '1.5rem 1.25rem' }}>
        <AnimatePresence mode="wait" initial={false}>
          <motion.div key={location.pathname} variants={pageVariants} initial="initial" animate="animate" exit="exit">
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>

      <footer style={{ textAlign: 'center', color: '#94a3b8', fontSize: '.75rem', padding: '.875rem', borderTop: '1px solid #e2e8f0', background: 'linear-gradient(180deg,#fff,#f8fafc)', fontWeight: 500 }}>
        Vacancy Hai Admin Panel &copy; {new Date().getFullYear()}
      </footer>
    </div>
  );
}
