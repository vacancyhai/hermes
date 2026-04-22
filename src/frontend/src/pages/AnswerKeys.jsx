import { Link } from 'react-router-dom';
import { FileText, Star } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTrackedItems } from '../hooks/useTrackedItems';

export default function AnswerKeys() {
  const { token } = useAuth();
  const { items: keys, pagination, loading, offset, limit, trackedJobIds, trackedAdmIds, track, setSearchParams } = useTrackedItems('/answer-keys', token);

  return (
    <div>
      <div style={{ background: 'linear-gradient(135deg, #78350f 0%, #92400e 45%, #d97706 100%)', color: '#fff', padding: '1.75rem 2rem', borderRadius: '1rem', marginBottom: '1.5rem', position: 'relative', overflow: 'hidden', boxShadow: '0 8px 28px rgba(146,64,14,.35)' }}>
        <div style={{ position: 'absolute', top: -50, right: -30, width: 200, height: 200, background: 'rgba(255,255,255,.06)', borderRadius: '50%', pointerEvents: 'none' }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 800, marginBottom: '0.25rem', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><FileText size={20} strokeWidth={2.5} />Answer Keys</h1>
          <p style={{ fontSize: '0.875rem', opacity: 0.78 }}>Official answer keys for government and entrance examinations</p>
        </div>
      </div>

      {loading && Array.from({ length: 5 }).map((_, i) => (
        <div key={i} style={{ background: '#fff', border: '1px solid #e2e8f0', borderLeft: '3px solid #e2e8f0', borderRadius: '0.65rem', padding: '1rem 1.1rem', marginBottom: '0.6rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem' }}>
            <div style={{ flex: 1 }}>
              <div className="skeleton" style={{ height: 16, width: '70%', borderRadius: '0.4rem', marginBottom: '0.45rem' }} />
              <div style={{ display: 'flex', gap: '0.3rem' }}>
                <div className="skeleton" style={{ height: 22, width: 110, borderRadius: '9999px' }} />
                <div className="skeleton" style={{ height: 22, width: 130, borderRadius: '9999px' }} />
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.4rem' }}>
              <div className="skeleton" style={{ height: 28, width: 56, borderRadius: '0.4rem' }} />
              <div className="skeleton" style={{ height: 28, width: 32, borderRadius: '0.4rem' }} />
            </div>
          </div>
        </div>
      ))}
      {!loading && keys.length === 0 && <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>No answer keys available.</div>}
      {!loading && keys.map((key) => {
        const type = key.job_id ? 'job' : 'admission';
        const tid = key.job_id || key.admission_id;
        const isTracking = type === 'job' ? trackedJobIds.has(String(tid)) : trackedAdmIds.has(String(tid));
        return (
          <div key={key.id} style={{ background: '#fff', border: '1px solid #e2e8f0', borderLeft: '3px solid #d97706', borderRadius: '0.65rem', padding: '1rem 1.1rem', marginBottom: '0.6rem', boxShadow: '0 1px 3px rgba(0,0,0,.04)', transition: 'box-shadow .15s' }}
            onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 14px rgba(0,0,0,.08)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,.04)'; }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem' }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3 style={{ fontSize: '0.975rem', fontWeight: 700, lineHeight: 1.4, marginBottom: '0.3rem' }}>
                  <Link to={`/answer-keys/${key.slug}`} style={{ color: '#0f172a', textDecoration: 'none' }}>{key.title}</Link>
                </h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                  {key.published_at && <span style={{ fontSize: '0.75rem', color: '#a16207', background: '#fef3c7', border: '1px solid #fde68a', padding: '0.12rem 0.45rem', borderRadius: '9999px' }}>Published: {key.published_at.slice(0, 10)}</span>}
                  {(key.start_date || key.end_date) && <span style={{ fontSize: '0.75rem', color: '#92400e', background: '#fef3c7', border: '1px solid #fde68a', padding: '0.12rem 0.45rem', borderRadius: '9999px' }}>Challenge: {key.start_date || '?'} – {key.end_date || '?'}</span>}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexShrink: 0 }}>
                <Link to={`/answer-keys/${key.slug}`} className="btn btn-sm" style={{ background: '#d97706', color: '#fff', border: 'none' }}>View →</Link>
                {tid && (token ? (
                  <button onClick={() => track(type, tid)} className={isTracking ? 'btn-tracking btn btn-sm' : 'btn btn-outline btn-sm'} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                    <Star size={12} strokeWidth={2} fill={isTracking ? 'currentColor' : 'none'} />
                  </button>
                ) : (
                  <Link to={`/login?next=/answer-keys/${key.slug}`} className="btn btn-outline btn-sm" style={{ display: 'inline-flex', alignItems: 'center' }}><Star size={12} strokeWidth={2} /></Link>
                ))}
              </div>
            </div>
          </div>
        );
      })}
      {pagination.has_more && (
        <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
          <button onClick={() => setSearchParams({ offset: offset + limit })} className="btn btn-outline">Load More</button>
        </div>
      )}
    </div>
  );
}
