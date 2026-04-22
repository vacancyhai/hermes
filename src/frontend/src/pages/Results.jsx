import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTrackedItems } from '../hooks/useTrackedItems';

export default function Results() {
  const { token } = useAuth();
  const { items: results, pagination, loading, offset, limit, trackedJobIds, trackedAdmIds, track, setSearchParams } = useTrackedItems('/results', token);

  return (
    <div>
      <div style={{ background: 'linear-gradient(135deg,#14532d 0%,#16a34a 100%)', color: '#fff', padding: '1.75rem 1.5rem 1.5rem', borderRadius: '0.75rem', marginBottom: '1.25rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '0.3rem' }}>🏆 Results</h1>
        <p style={{ fontSize: '0.875rem', opacity: 0.85 }}>Official results for government and entrance examinations</p>
      </div>

      {loading && <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>Loading...</div>}
      {!loading && results.length === 0 && <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>No results available.</div>}
      {!loading && results.map((res) => {
        const type = res.job_id ? 'job' : 'admission';
        const tid = res.job_id || res.admission_id;
        const isTracking = type === 'job' ? trackedJobIds.has(String(tid)) : trackedAdmIds.has(String(tid));
        return (
          <div key={res.id} style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderLeft: '4px solid #16a34a', borderRadius: '0.5rem', padding: '1rem 1.1rem', marginBottom: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem', flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, lineHeight: 1.4, marginBottom: '0.25rem' }}>
                  <Link to={`/results/${res.slug}`} style={{ color: '#14532d' }}>{res.title}</Link>
                </h3>
                {res.published_at && <div style={{ fontSize: '0.78rem', color: '#16a34a' }}>Published: {res.published_at.slice(0, 10)}</div>}
                {res.notes && <div style={{ fontSize: '0.855rem', color: '#475569', margin: '0.25rem 0', overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>{res.notes}</div>}
              </div>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', alignItems: 'center' }}>
                <Link to={`/results/${res.slug}`} className="btn btn-sm" style={{ background: '#16a34a', color: '#fff', border: 'none' }}>View →</Link>
                {tid && (token ? (
                  <button onClick={() => track(type, tid)} className={isTracking ? 'btn-tracking btn btn-sm' : 'btn btn-outline btn-sm'}>
                    {isTracking ? '★' : '☆'}
                  </button>
                ) : (
                  <Link to={`/login?next=/results/${res.slug}`} className="btn btn-outline btn-sm">☆</Link>
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
