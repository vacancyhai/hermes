import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { LayoutDashboard, SearchX } from 'lucide-react';

export default function NotFound() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      style={{ textAlign: 'center', padding: '5rem 1rem', maxWidth: 440, margin: '0 auto' }}
    >
      <div style={{ width: 72, height: 72, background: 'linear-gradient(135deg,#0f2440,#2563eb)', borderRadius: 'var(--radius-xl)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.25rem', boxShadow: '0 8px 24px rgba(37,99,235,.3)' }}>
        <SearchX size={32} strokeWidth={2} color="#fff" />
      </div>
      <div style={{ fontSize: '3.5rem', fontWeight: 900, letterSpacing: '-0.04em', lineHeight: 1, background: 'linear-gradient(135deg,#0f2440,#2563eb)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text', marginBottom: '.4rem' }}>404</div>
      <h1 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', marginBottom: '.4rem', letterSpacing: '-0.015em' }}>Page not found</h1>
      <p style={{ color: '#64748b', fontSize: '.875rem', marginBottom: '1.5rem' }}>This page doesn’t exist or you don’t have access.</p>
      <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: '.4rem', background: 'linear-gradient(135deg,#1e3a5f,#2563eb)', color: '#fff', padding: '.6rem 1.25rem', borderRadius: 'var(--radius-lg)', fontWeight: 700, fontSize: '.82rem', textDecoration: 'none', boxShadow: '0 4px 14px rgba(37,99,235,.3)' }}>
        <LayoutDashboard size={14} strokeWidth={2.5} />Back to Dashboard
      </Link>
    </motion.div>
  );
}
