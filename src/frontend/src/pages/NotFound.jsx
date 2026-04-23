import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Home, SearchX } from 'lucide-react';

export default function NotFound() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      style={{ textAlign: 'center', padding: '5rem 1rem', maxWidth: 480, margin: '0 auto' }}
    >
      <div style={{ width: 80, height: 80, background: 'linear-gradient(135deg, #0f2440, #2563eb)', borderRadius: 'var(--radius-xl)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem', boxShadow: '0 8px 24px rgba(37,99,235,.3)' }}>
        <SearchX size={36} strokeWidth={2} color="#fff" />
      </div>
      <div style={{ fontSize: '4rem', fontWeight: 900, letterSpacing: '-0.04em', lineHeight: 1, background: 'linear-gradient(135deg, #0f2440, #2563eb)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text', marginBottom: '0.5rem' }}>404</div>
      <h1 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a', marginBottom: '0.5rem', letterSpacing: '-0.02em' }}>Page not found</h1>
      <p style={{ color: '#64748b', fontSize: '0.925rem', lineHeight: 1.65, marginBottom: '1.75rem' }}>The page you&apos;re looking for doesn&apos;t exist or has been removed.</p>
      <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', background: 'linear-gradient(135deg, #1e3a5f, #2563eb)', color: '#fff', padding: '0.65rem 1.4rem', borderRadius: 'var(--radius-lg)', fontWeight: 700, fontSize: '0.875rem', textDecoration: 'none', boxShadow: '0 4px 14px rgba(37,99,235,.3)', transition: 'opacity 0.15s' }}
        onMouseEnter={(e) => { e.currentTarget.style.opacity = '0.88'; }}
        onMouseLeave={(e) => { e.currentTarget.style.opacity = '1'; }}
      >
        <Home size={15} strokeWidth={2.5} />Go to Home
      </Link>
    </motion.div>
  );
}
