import { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';

export default function AdmitCards() {
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [cards, setCards] = useState([]);
  const [pagination, setPagination] = useState({});
  const [trackedJobIds, setTrackedJobIds] = useState(new Set());
  const [trackedAdmIds, setTrackedAdmIds] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const offset = parseInt(searchParams.get('offset') || '0', 10);
  const limit = 20;

  const fetchCards = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/admit-cards', { params: { limit, offset } });
      setCards(res.data.data || []);
      setPagination(res.data.pagination || {});
    } catch (_) {} finally { setLoading(false); }
  }, [offset]);

  useEffect(() => { fetchCards(); }, [fetchCards]);

  useEffect(() => {
    if (!token) return;
    api.get('/users/me/tracked').then((r) => {
      setTrackedJobIds(new Set((r.data.jobs || []).map((j) => String(j.id))));
      setTrackedAdmIds(new Set((r.data.admissions || []).map((a) => String(a.id))));
    }).catch(() => {});
  }, [token]);

  const track = async (type, id) => {
    const set = type === 'job' ? trackedJobIds : trackedAdmIds;
    const setFn = type === 'job' ? setTrackedJobIds : setTrackedAdmIds;
    const isTracking = set.has(String(id));
    try {
      if (isTracking) await api.delete(`/${type}s/${id}/track`);
      else await api.post(`/${type}s/${id}/track`);
      setFn((prev) => { const next = new Set(prev); if (isTracking) next.delete(String(id)); else next.add(String(id)); return next; });
    } catch (_) {}
  };

  return (
    <div>
      <div style={{ background: 'linear-gradient(135deg,#1e40af 0%,#3b82f6 100%)', color: '#fff', padding: '1.75rem 1.5rem 1.5rem', borderRadius: '0.75rem', marginBottom: '1.25rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '0.3rem' }}>🪪 Admit Cards</h1>
        <p style={{ fontSize: '0.875rem', opacity: 0.85 }}>Download hall tickets and admit cards for upcoming examinations</p>
      </div>

      {loading && <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>Loading...</div>}
      {!loading && cards.length === 0 && <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>No admit cards available.</div>}
      {!loading && cards.map((card) => {
        const type = card.job_id ? 'job' : 'admission';
        const tid = card.job_id || card.admission_id;
        const isTracking = type === 'job' ? trackedJobIds.has(String(tid)) : trackedAdmIds.has(String(tid));
        return (
          <div key={card.id} style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderLeft: '4px solid #2563eb', borderRadius: '0.5rem', padding: '1rem 1.1rem', marginBottom: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem', flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, lineHeight: 1.4, marginBottom: '0.25rem' }}>
                  <Link to={`/admit-cards/${card.slug}`} style={{ color: '#1e40af' }}>{card.title}</Link>
                </h3>
                {(card.exam_start || card.exam_end) && <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Exam: {card.exam_start || '?'} – {card.exam_end || 'ongoing'}</div>}
                {card.published_at && <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>Published: {card.published_at.slice(0, 10)}</div>}
              </div>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', alignItems: 'center' }}>
                <Link to={`/admit-cards/${card.slug}`} className="btn btn-outline btn-sm" style={{ borderColor: '#bfdbfe' }}>View →</Link>
                {tid && (token ? (
                  <button onClick={() => track(type, tid)} className={isTracking ? 'btn-tracking btn btn-sm' : 'btn btn-outline btn-sm'}>
                    {isTracking ? '★' : '☆'}
                  </button>
                ) : (
                  <Link to={`/login?next=/admit-cards/${card.slug}`} className="btn btn-outline btn-sm">☆</Link>
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
