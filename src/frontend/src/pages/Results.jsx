import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Trophy, Landmark, Briefcase, GraduationCap, CalendarDays } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTrackedItems } from '../hooks/useTrackedItems';
import OrgLogoCircle from '../components/OrgLogoCircle';
import TrackControl from '../components/TrackControl';

const cardVariants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.28, ease: [0.16, 1, 0.3, 1] } },
};
const listVariants = { hidden: {}, show: { transition: { staggerChildren: 0.06, delayChildren: 0.04 } } };

export default function Results() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const { items: results, pagination, loading, offset, limit, trackedJobIds, trackedAdmIds, track, setSearchParams } = useTrackedItems('/results', token);

  return (
    <div>
      <motion.div
        initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
        style={{ background: 'linear-gradient(135deg, #052e16 0%, #14532d 45%, #16a34a 100%)', color: '#fff', padding: '1.75rem 2rem', borderRadius: 'var(--radius-2xl)', marginBottom: '1.5rem', position: 'relative', overflow: 'hidden', boxShadow: '0 16px 48px rgba(20,83,45,.4), 0 4px 12px rgba(20,83,45,.2)' }}
      >
        <div style={{ position: 'absolute', top: -60, right: -40, width: 240, height: 240, background: 'rgba(255,255,255,.06)', borderRadius: '50%', pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', bottom: -50, left: 20, width: 160, height: 160, background: 'rgba(255,255,255,.04)', borderRadius: '50%', pointerEvents: 'none' }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', background: 'rgba(255,255,255,.14)', backdropFilter: 'blur(8px)', borderRadius: '0.5rem', padding: '0.28rem 0.75rem', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '0.75rem', border: '1px solid rgba(255,255,255,.1)' }}>
            <Trophy size={11} strokeWidth={2.5} />Results
          </div>
          <h1 style={{ fontSize: '1.55rem', fontWeight: 800, marginBottom: '0.3rem', letterSpacing: '-0.025em', lineHeight: 1.18 }}>Results</h1>
          <p style={{ fontSize: '0.875rem', opacity: 0.78, lineHeight: 1.6 }}>Official results for government and entrance examinations</p>
        </div>
      </motion.div>

      {loading && ['s1','s2','s3','s4','s5'].map((sk) => (
        <div key={sk} style={{ background: '#fff', border: '1px solid #e2e8f0', borderLeft: '3px solid #16a34a', borderRadius: '0.65rem', padding: '1rem 1.1rem', marginBottom: '0.65rem' }}>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
            <div className="skeleton" style={{ width: 40, height: 40, borderRadius: '50%', flexShrink: 0 }} />
            <div style={{ flex: 1 }}>
              <div className="skeleton" style={{ height: 15, width: '65%', borderRadius: '0.4rem', marginBottom: '0.4rem' }} />
              <div className="skeleton" style={{ height: 12, width: '50%', borderRadius: '0.4rem', marginBottom: '0.3rem' }} />
              <div className="skeleton" style={{ height: 11, width: '35%', borderRadius: '0.4rem' }} />
            </div>
          </div>
          <div style={{ borderTop: '1px solid #f1f5f9', marginTop: '0.55rem', paddingTop: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', gap: '0.35rem' }}>
              <div className="skeleton" style={{ height: 22, width: 110, borderRadius: '9999px' }} />
              <div className="skeleton" style={{ height: 22, width: 160, borderRadius: '9999px' }} />
            </div>
            <div className="skeleton" style={{ height: 28, width: 88, borderRadius: '0.4rem' }} />
          </div>
        </div>
      ))}
      {!loading && results.length === 0 && <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>No results available.</div>}
      {!loading && (
        <motion.div variants={listVariants} initial="hidden" animate="show">
        {results.map((res) => {
        const type = res.job_id ? 'job' : 'admission';
        const tid = res.job_id || res.admission_id;
        const isTracking = type === 'job' ? trackedJobIds.has(String(tid)) : trackedAdmIds.has(String(tid));
        return (
          <motion.div key={res.id}
            variants={cardVariants}
            onClick={() => navigate(`/results/${res.slug}`)}
            whileHover={{ y: -3, boxShadow: '0 8px 24px rgba(15,23,42,.1), 0 2px 8px rgba(15,23,42,.06)', borderColor: '#86efac' }}
            whileTap={{ scale: 0.99 }}
            style={{ background: '#fff', border: '1px solid #e2e8f0', borderLeft: '3px solid #16a34a', borderRadius: 'var(--radius-lg)', padding: '1rem 1.1rem', marginBottom: '0.65rem', boxShadow: 'var(--shadow-sm)', transition: 'border-color 0.15s', cursor: 'pointer' }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
              <OrgLogoCircle logoUrl={res.parent_logo_url} orgName={res.parent_organization} title={res.title} gradient="linear-gradient(135deg,#052e16,#16a34a)" />
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3 style={{ fontSize: '0.975rem', fontWeight: 700, lineHeight: 1.4, marginBottom: '0.15rem', color: '#0f172a' }}>
                  {res.title}
                </h3>
                {res.parent_title && <div style={{ fontSize: '0.82rem', color: '#64748b', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '0.3rem', marginBottom: '0.2rem' }}>{res.parent_type === 'job' ? <Briefcase size={11} strokeWidth={2} /> : <GraduationCap size={11} strokeWidth={2} />}{res.parent_title}</div>}
                {res.parent_organization && <div style={{ fontSize: '0.78rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.25rem' }}><Landmark size={10} strokeWidth={2} />{res.parent_organization}</div>}
              </div>
            </div>

            {/* Date + track row */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginTop: '0.55rem', paddingTop: '0.5rem', borderTop: '1px solid #f1f5f9', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', alignItems: 'center' }}>
                {res.published_at && (
                  <span style={{ fontSize: '0.72rem', color: '#15803d', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.25rem', background: '#dcfce7', border: '1px solid #bbf7d0', padding: '0.15rem 0.5rem', borderRadius: '9999px' }}>
                    <CalendarDays size={10} strokeWidth={2} />Published: {res.published_at.slice(0, 10)}
                  </span>
                )}
                {res.notes && (
                  <span style={{ fontSize: '0.72rem', color: '#475569', display: 'inline-flex', alignItems: 'center', gap: '0.25rem', background: '#f8fafc', border: '1px solid #e2e8f0', padding: '0.15rem 0.5rem', borderRadius: '9999px', maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {res.notes}
                  </span>
                )}
              </div>
              {tid && <TrackControl token={token} isTracking={isTracking} onTrack={() => track(type, tid)} loginPath={`/login?next=/results/${res.slug}`} />}
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
