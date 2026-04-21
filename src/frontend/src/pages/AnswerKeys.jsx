import { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';

export default function AnswerKeys() {
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [keys, setKeys] = useState([]);
  const [pagination, setPagination] = useState({});
  const [trackedJobIds, setTrackedJobIds] = useState(new Set());
  const [trackedAdmIds, setTrackedAdmIds] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const offset = Number.parseInt(searchParams.get('offset') || '0', 10);
  const limit = 20;

  const fetchKeys = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/answer-keys', { params: { limit, offset } });
      setKeys(res.data.data || []);
      setPagination(res.data.pagination || {});
    } catch { } finally { setLoading(false); }
  }, [offset]);

  useEffect(() => { fetchKeys(); }, [fetchKeys]);

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
      if (isTracking) await api.delete(`/${type}s/${id}/track`);
      else await api.post(`/${type}s/${id}/track`);
      setFn((prev) => { const next = new Set(prev); if (isTracking) next.delete(String(id)); else next.add(String(id)); return next; });
    } catch { }
  };

  return (
    <div>
      <div style={{ background: 'linear-gradient(135deg,#92400e 0%,#d97706 100%)', color: '#fff', padding: '1.75rem 1.5rem 1.5rem', borderRadius: '0.75rem', marginBottom: '1.25rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '0.3rem' }}>📝 Answer Keys</h1>
        <p style={{ fontSize: '0.875rem', opacity: 0.85 }}>Official answer keys for government and entrance examinations</p>
      </div>

      {loading && <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>Loading...</div>}
      {!loading && keys.length === 0 && <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>No answer keys available.</div>}
      {!loading && keys.map((key) => {
        const type = key.job_id ? 'job' : 'admission';
        const tid = key.job_id || key.admission_id;
        const isTracking = type === 'job' ? trackedJobIds.has(String(tid)) : trackedAdmIds.has(String(tid));
        return (
          <div key={key.id} style={{ background: '#fefce8', border: '1px solid #fde68a', borderLeft: '4px solid #d97706', borderRadius: '0.5rem', padding: '1rem 1.1rem', marginBottom: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem', flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, lineHeight: 1.4, marginBottom: '0.25rem' }}>
                  <Link to={`/answer-keys/${key.slug}`} style={{ color: '#92400e' }}>{key.title}</Link>
                </h3>
                {key.published_at && <div style={{ fontSize: '0.78rem', color: '#a16207' }}>Published: {key.published_at.slice(0, 10)}</div>}
                {(key.start_date || key.end_date) && <div style={{ fontSize: '0.78rem', color: '#a16207' }}>Challenge: {key.start_date || '?'} – {key.end_date || '?'}</div>}
              </div>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', alignItems: 'center' }}>
                <Link to={`/answer-keys/${key.slug}`} className="btn btn-sm" style={{ background: '#d97706', color: '#fff', border: 'none' }}>View →</Link>
                {tid && (token ? (
                  <button onClick={() => track(type, tid)} className={isTracking ? 'btn-tracking btn btn-sm' : 'btn btn-outline btn-sm'}>
                    {isTracking ? '★' : '☆'}
                  </button>
                ) : (
                  <Link to={`/login?next=/answer-keys/${key.slug}`} className="btn btn-outline btn-sm">☆</Link>
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
