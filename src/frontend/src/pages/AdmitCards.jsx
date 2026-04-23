import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CreditCard, Star } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTrackedItems } from '../hooks/useTrackedItems';

const cardVariants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.28, ease: [0.16, 1, 0.3, 1] } },
};
const listVariants = { hidden: {}, show: { transition: { staggerChildren: 0.06, delayChildren: 0.04 } } };

export default function AdmitCards() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const { items: cards, pagination, loading, offset, limit, trackedJobIds, trackedAdmIds, track, setSearchParams } = useTrackedItems('/admit-cards', token);

  return (
    <div>
      <motion.div
        initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
        style={{ background: 'linear-gradient(135deg, #1e3a8a 0%, #1e40af 50%, #3b82f6 100%)', color: '#fff', padding: '1.75rem 2rem', borderRadius: 'var(--radius-2xl)', marginBottom: '1.5rem', position: 'relative', overflow: 'hidden', boxShadow: '0 16px 48px rgba(30,64,175,.4), 0 4px 12px rgba(30,64,175,.2)' }}
      >
        <div style={{ position: 'absolute', top: -60, right: -40, width: 240, height: 240, background: 'rgba(255,255,255,.06)', borderRadius: '50%', pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', bottom: -50, left: 20, width: 160, height: 160, background: 'rgba(255,255,255,.04)', borderRadius: '50%', pointerEvents: 'none' }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', background: 'rgba(255,255,255,.14)', backdropFilter: 'blur(8px)', borderRadius: '0.5rem', padding: '0.28rem 0.75rem', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '0.75rem', border: '1px solid rgba(255,255,255,.1)' }}>
            <CreditCard size={11} strokeWidth={2.5} />Admit Cards
          </div>
          <h1 style={{ fontSize: '1.55rem', fontWeight: 800, marginBottom: '0.3rem', letterSpacing: '-0.025em', lineHeight: 1.18 }}>Admit Cards</h1>
          <p style={{ fontSize: '0.875rem', opacity: 0.78, lineHeight: 1.6 }}>Download hall tickets and admit cards for upcoming examinations</p>
        </div>
      </motion.div>

      {loading && Array.from({ length: 5 }).map((_, i) => (
        <div key={i} style={{ background: '#fff', border: '1px solid #e2e8f0', borderLeft: '3px solid #e2e8f0', borderRadius: '0.65rem', padding: '1rem 1.1rem', marginBottom: '0.6rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem' }}>
            <div style={{ flex: 1 }}>
              <div className="skeleton" style={{ height: 16, width: '70%', borderRadius: '0.4rem', marginBottom: '0.45rem' }} />
              <div className="skeleton" style={{ height: 22, width: 140, borderRadius: '9999px' }} />
            </div>
            <div style={{ display: 'flex', gap: '0.4rem' }}>
              <div className="skeleton" style={{ height: 28, width: 56, borderRadius: '0.4rem' }} />
              <div className="skeleton" style={{ height: 28, width: 32, borderRadius: '0.4rem' }} />
            </div>
          </div>
        </div>
      ))}
      {!loading && cards.length === 0 && <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>No admit cards available.</div>}
      {!loading && (
        <motion.div variants={listVariants} initial="hidden" animate="show">
        {cards.map((card) => {
        const type = card.job_id ? 'job' : 'admission';
        const tid = card.job_id || card.admission_id;
        const isTracking = type === 'job' ? trackedJobIds.has(String(tid)) : trackedAdmIds.has(String(tid));
        return (
          <motion.div key={card.id}
            variants={cardVariants}
            onClick={() => navigate(`/admit-cards/${card.slug}`)}
            whileHover={{ y: -3, boxShadow: '0 8px 24px rgba(15,23,42,.1), 0 2px 8px rgba(15,23,42,.06)', borderColor: '#93c5fd' }}
            whileTap={{ scale: 0.99 }}
            style={{ background: '#fff', border: '1px solid #e2e8f0', borderLeft: '3px solid #2563eb', borderRadius: 'var(--radius-lg)', padding: '1rem 1.1rem', marginBottom: '0.65rem', boxShadow: 'var(--shadow-sm)', transition: 'border-color 0.15s', cursor: 'pointer' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem' }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3 style={{ fontSize: '0.975rem', fontWeight: 700, lineHeight: 1.4, marginBottom: '0.3rem', color: '#0f172a' }}>
                  {card.title}
                </h3>
                {(card.exam_start || card.exam_end) && <div style={{ fontSize: '0.78rem', color: '#64748b', display: 'inline-flex', alignItems: 'center', gap: '0.25rem', background: '#eff6ff', border: '1px solid #bfdbfe', padding: '0.15rem 0.5rem', borderRadius: '9999px', marginBottom: '0.25rem' }}>Exam: {card.exam_start || '?'} – {card.exam_end || 'ongoing'}</div>}
                {card.published_at && <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Published: {card.published_at.slice(0, 10)}</div>}
              </div>
              <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexShrink: 0 }}>
                {tid && (token ? (
                  <button onClick={(e) => { e.stopPropagation(); track(type, tid); }} className={isTracking ? 'btn-tracking btn btn-sm' : 'btn btn-outline btn-sm'} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                    <Star size={12} strokeWidth={2} fill={isTracking ? 'currentColor' : 'none'} />{isTracking ? 'Tracking' : 'Keep Track'}
                  </button>
                ) : (
                  <Link to={`/login?next=/admit-cards/${card.slug}`} onClick={(e) => e.stopPropagation()} className="btn btn-outline btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><Star size={12} strokeWidth={2} />Keep Track</Link>
                ))}
              </div>
            </div>
          </motion.div>
        );
      })}
        </motion.div>
      )}

      {pagination.has_more && (
        <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
          <button onClick={() => setSearchParams({ offset: offset + limit })} className="btn btn-outline">Load More</button>
        </div>
      )}
    </div>
  );
}
