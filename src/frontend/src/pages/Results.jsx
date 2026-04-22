import { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';

export default function Results() {
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [results, setResults] = useState([]);
  const [pagination, setPagination] = useState({});
  const [trackedJobIds, setTrackedJobIds] = useState(new Set());
  const [trackedAdmIds, setTrackedAdmIds] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const offset = Number.parseInt(searchParams.get('offset') || '0', 10);
  const limit = 20;

  const fetchResults = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/results', { params: { limit, offset } });
      setResults(res.data.data || []);
      setPagination(res.data.pagination || {});
    } catch { } finally { setLoading(false); }
  }, [offset]);

  useEffect(() => { fetchResults(); }, [fetchResults]);

  useEffect(() => {
    if (!token) return;
    api.get('/users/me/tracked').then((r) => {
      setTrackedJobIds(new Set((r.data.jobs || []).map((j) => String(j.id))));
      setTrackedAdmIds(new Set((r.data.admissions || []).map((a) => String(a.id))));
    }).catch(() => { });
  }, [token]);

  const track = async (type, id) => {
    const set = type === 'job' ? trackedJobIds : trackedAdmIds;
    const setFn = type === 'job' ? setTrackedJobIds : setTrackedAdmIds;
    const isTracking = set.has(String(id));
    try {
      if (isTracking) { await api.delete(`/${type}s/${id}/track`); }
      else { await api.post(`/${type}s/${id}/track`); }
      setFn((prev) => { const next = new Set(prev); if (isTracking) next.delete(String(id)); else next.add(String(id)); return next; });
    } catch { }
  };

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
