import { Link } from 'react-router-dom';
import { Trophy, Star } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTrackedItems } from '../hooks/useTrackedItems';

export default function Results() {
  const { token } = useAuth();
  const { items: results, pagination, loading, offset, limit, trackedJobIds, trackedAdmIds, track, setSearchParams } = useTrackedItems('/results', token);

  return (
    <div>
      <div style={{ background: 'linear-gradient(135deg, #052e16 0%, #14532d 45%, #16a34a 100%)', color: '#fff', padding: '1.75rem 2rem', borderRadius: '1rem', marginBottom: '1.5rem', position: 'relative', overflow: 'hidden', boxShadow: '0 8px 28px rgba(20,83,45,.35)' }}>
        <div style={{ position: 'absolute', top: -50, right: -30, width: 200, height: 200, background: 'rgba(255,255,255,.06)', borderRadius: '50%', pointerEvents: 'none' }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 800, marginBottom: '0.25rem', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Trophy size={20} strokeWidth={2.5} />Results</h1>
          <p style={{ fontSize: '0.875rem', opacity: 0.78 }}>Official results for government and entrance examinations</p>
        </div>
      </div>

      {loading && Array.from({ length: 5 }).map((_, i) => (
        <div key={i} style={{ background: '#fff', border: '1px solid #e2e8f0', borderLeft: '3px solid #e2e8f0', borderRadius: '0.65rem', padding: '1rem 1.1rem', marginBottom: '0.6rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem' }}>
            <div style={{ flex: 1 }}>
              <div className="skeleton" style={{ height: 16, width: '65%', borderRadius: '0.4rem', marginBottom: '0.45rem' }} />
              <div className="skeleton" style={{ height: 22, width: 120, borderRadius: '9999px', marginBottom: '0.35rem' }} />
              <div className="skeleton" style={{ height: 13, width: '80%', borderRadius: '0.4rem' }} />
            </div>
            <div style={{ display: 'flex', gap: '0.4rem' }}>
              <div className="skeleton" style={{ height: 28, width: 56, borderRadius: '0.4rem' }} />
              <div className="skeleton" style={{ height: 28, width: 32, borderRadius: '0.4rem' }} />
            </div>
          </div>
        </div>
      ))}
      {!loading && results.length === 0 && <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>No results available.</div>}
      {!loading && results.map((res) => {
        const type = res.job_id ? 'job' : 'admission';
        const tid = res.job_id || res.admission_id;
        const isTracking = type === 'job' ? trackedJobIds.has(String(tid)) : trackedAdmIds.has(String(tid));
        return (
          <div key={res.id} style={{ background: '#fff', border: '1px solid #e2e8f0', borderLeft: '3px solid #16a34a', borderRadius: '0.65rem', padding: '1rem 1.1rem', marginBottom: '0.6rem', boxShadow: '0 1px 3px rgba(0,0,0,.04)', transition: 'box-shadow .15s' }}
            onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 14px rgba(0,0,0,.08)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,.04)'; }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem' }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3 style={{ fontSize: '0.975rem', fontWeight: 700, lineHeight: 1.4, marginBottom: '0.3rem' }}>
                  <Link to={`/results/${res.slug}`} style={{ color: '#0f172a', textDecoration: 'none' }}>{res.title}</Link>
                </h3>
                {res.published_at && <span style={{ fontSize: '0.75rem', color: '#15803d', background: '#dcfce7', border: '1px solid #bbf7d0', padding: '0.12rem 0.45rem', borderRadius: '9999px', display: 'inline-block', marginBottom: '0.3rem' }}>Published: {res.published_at.slice(0, 10)}</span>}
                {res.notes && <div style={{ fontSize: '0.845rem', color: '#475569', lineHeight: 1.55, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>{res.notes}</div>}
              </div>
              <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexShrink: 0 }}>
                <Link to={`/results/${res.slug}`} className="btn btn-sm" style={{ background: '#16a34a', color: '#fff', border: 'none' }}>View →</Link>
                {tid && (token ? (
                  <button onClick={() => track(type, tid)} className={isTracking ? 'btn-tracking btn btn-sm' : 'btn btn-outline btn-sm'} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                    <Star size={12} strokeWidth={2} fill={isTracking ? 'currentColor' : 'none'} />
                  </button>
                ) : (
                  <Link to={`/login?next=/results/${res.slug}`} className="btn btn-outline btn-sm" style={{ display: 'inline-flex', alignItems: 'center' }}><Star size={12} strokeWidth={2} /></Link>
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
