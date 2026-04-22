import { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Landmark, Clock, Star, SlidersHorizontal, X } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';

export default function Admissions() {
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [admissions, setAdmissions] = useState([]);
  const [pagination, setPagination] = useState({});
  const [trackedIds, setTrackedIds] = useState(new Set());
  const [loading, setLoading] = useState(false);

  const q = searchParams.get('q') || '';
  const stream = searchParams.get('stream') || '';
  const admission_type = searchParams.get('admission_type') || '';
  const offset = Number.parseInt(searchParams.get('offset') || '0', 10);
  const limit = 20;

  const fetchAdmissions = useCallback(async () => {
    setLoading(true);
    try {
      const params = { limit, offset };
      if (q) params.q = q;
      if (stream) params.stream = stream;
      if (admission_type) params.admission_type = admission_type;
      const res = await api.get('/admissions', { params });
      setAdmissions(res.data.data || []);
      setPagination(res.data.pagination || {});
    } catch { } finally { setLoading(false); }
  }, [q, stream, admission_type, offset]);

  useEffect(() => { fetchAdmissions(); }, [fetchAdmissions]);

  useEffect(() => {
    if (!token) { setTrackedIds(new Set()); return; }
    api.get('/users/me/tracked').then((r) => {
      setTrackedIds(new Set((r.data.admissions || []).map((a) => String(a.id))));
    }).catch(() => { });
  }, [token]);

  const toggleId = (id) => setTrackedIds((prev) => {
    const next = new Set(prev);
    if (next.has(String(id))) next.delete(String(id)); else next.add(String(id));
    return next;
  });

  const track = async (adm) => {
    const isTracking = trackedIds.has(String(adm.id));
    try {
      if (isTracking) await api.delete(`/admissions/${adm.id}/track`);
      else await api.post(`/admissions/${adm.id}/track`);
      toggleId(adm.id);
    } catch { }
  };

  const [search, setSearch] = useState(q);
  const handleSearch = (e) => { e.preventDefault(); setSearchParams({ q: search, offset: 0 }); };

  const statusMap = {
    active:   { bg: '#dcfce7', color: '#15803d', border: '#bbf7d0', label: 'Active' },
    upcoming: { bg: '#fef3c7', color: '#b45309', border: '#fde68a', label: 'Upcoming' },
    closed:   { bg: '#fee2e2', color: '#b91c1c', border: '#fecaca', label: 'Closed' },
  };

  return (
    <div>
      <div style={{ background: 'linear-gradient(135deg, #2e1065 0%, #4c1d95 45%, #7c3aed 100%)', color: '#fff', padding: '1.75rem 2rem', borderRadius: '1rem', marginBottom: '1.5rem', position: 'relative', overflow: 'hidden', boxShadow: '0 8px 28px rgba(76,29,149,.35)' }}>
        <div style={{ position: 'absolute', top: -50, right: -30, width: 200, height: 200, background: 'rgba(255,255,255,.06)', borderRadius: '50%', pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', bottom: -50, left: 30, width: 140, height: 140, background: 'rgba(255,255,255,.04)', borderRadius: '50%', pointerEvents: 'none' }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 800, marginBottom: '0.25rem', letterSpacing: '-0.02em' }}>College Admissions</h1>
          <p style={{ fontSize: '0.875rem', opacity: 0.78, marginBottom: '1rem' }}>NEET, JEE, GATE, CAT and all major entrance examinations</p>
          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search admissions..." style={{ flex: 1, minWidth: 180, padding: '0.5rem 0.8rem', borderRadius: '0.45rem', border: 'none', fontSize: '0.875rem', color: '#1e293b', outline: 'none' }} />
            <button type="submit" style={{ padding: '0.5rem 1.1rem', borderRadius: '0.45rem', background: 'rgba(255,255,255,.18)', color: '#fff', border: '1px solid rgba(255,255,255,.3)', cursor: 'pointer', fontWeight: 600, fontSize: '0.875rem' }}>Search</button>
            {q && <button type="button" onClick={() => { setSearch(''); setSearchParams({}); }} style={{ padding: '0.5rem 0.75rem', borderRadius: '0.45rem', background: 'rgba(255,255,255,.1)', color: '#fff', border: '1px solid rgba(255,255,255,.2)', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.875rem' }}><X size={13} strokeWidth={2.5} />Clear</button>}
          </form>
        </div>
      </div>

      <div className="list-page-grid">
        {/* Filter sidebar */}
        <aside className="filter-sidebar">
          <div className="filter-widget">
            <div className="filter-widget-header" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><SlidersHorizontal size={13} strokeWidth={2} />Filters</div>
            <div className="filter-widget-body">
              <div style={{ marginBottom: '0.85rem' }}>
                <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94a3b8', marginBottom: '0.4rem' }}>Type</div>
                {['UG', 'PG', 'PhD', 'Diploma', 'Integrated'].map((t) => (
                  <label key={t} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.3rem 0', cursor: 'pointer', fontSize: '0.82rem', color: '#334155' }}>
                    <input type="radio" name="atype" checked={admission_type === t} onChange={() => setSearchParams({ q, stream, admission_type: t, offset: 0 })} style={{ accentColor: '#7c3aed' }} />
                    {t}
                  </label>
                ))}
                {admission_type && <button onClick={() => setSearchParams({ q, stream, offset: 0 })} style={{ fontSize: '0.78rem', color: '#7c3aed', background: 'none', border: 'none', cursor: 'pointer', padding: '0.25rem 0', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}><X size={11} strokeWidth={2.5} />Clear filter</button>}
              </div>
              <div>
                <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94a3b8', marginBottom: '0.4rem' }}>Stream</div>
                {['Engineering', 'Medical', 'Management', 'Law', 'Arts & Science'].map((s) => (
                  <label key={s} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.3rem 0', cursor: 'pointer', fontSize: '0.82rem', color: '#334155' }}>
                    <input type="radio" name="stream" checked={stream === s} onChange={() => setSearchParams({ q, admission_type, stream: s, offset: 0 })} style={{ accentColor: '#7c3aed' }} />
                    {s}
                  </label>
                ))}
                {stream && <button onClick={() => setSearchParams({ q, admission_type, offset: 0 })} style={{ fontSize: '0.78rem', color: '#7c3aed', background: 'none', border: 'none', cursor: 'pointer', padding: '0.25rem 0', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}><X size={11} strokeWidth={2.5} />Clear filter</button>}
              </div>
            </div>
          </div>
        </aside>

        {/* List */}
        <div>
          {loading && Array.from({ length: 6 }).map((_, i) => (
            <div key={i} style={{ background: '#fff', border: '1px solid #e2e8f0', borderLeft: '3px solid #e2e8f0', borderRadius: '0.65rem', padding: '1rem 1.1rem', marginBottom: '0.6rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <div className="skeleton" style={{ height: 16, width: '65%', borderRadius: '0.4rem' }} />
                <div className="skeleton" style={{ height: 16, width: 52, borderRadius: '9999px' }} />
              </div>
              <div className="skeleton" style={{ height: 13, width: '45%', borderRadius: '0.4rem', marginBottom: '0.4rem' }} />
              <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.55rem' }}>
                <div className="skeleton" style={{ height: 22, width: 48, borderRadius: '9999px' }} />
                <div className="skeleton" style={{ height: 22, width: 80, borderRadius: '9999px' }} />
              </div>
              <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '0.55rem', display: 'flex', justifyContent: 'space-between' }}>
                <div className="skeleton" style={{ height: 22, width: 110, borderRadius: '9999px' }} />
                <div style={{ display: 'flex', gap: '0.4rem' }}>
                  <div className="skeleton" style={{ height: 28, width: 88, borderRadius: '0.4rem' }} />
                  <div className="skeleton" style={{ height: 28, width: 64, borderRadius: '0.4rem' }} />
                </div>
              </div>
            </div>
          ))}
          {!loading && admissions.length === 0 && <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>No admissions found.</div>}
          {!loading && admissions.map((adm) => {
            const isTracking = trackedIds.has(String(adm.id));
            return (
              <div key={adm.id} style={{ background: '#fff', border: '1px solid #e2e8f0', borderLeft: '3px solid #7c3aed', borderRadius: '0.65rem', padding: '1rem 1.1rem', marginBottom: '0.6rem', boxShadow: '0 1px 3px rgba(0,0,0,.04)', transition: 'box-shadow .15s' }}
                onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 14px rgba(0,0,0,.08)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,.04)'; }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '0.6rem', marginBottom: '0.3rem' }}>
                  <h3 style={{ fontSize: '0.975rem', fontWeight: 700, lineHeight: 1.4, flex: 1, minWidth: 0 }}>
                    <Link to={`/admissions/${adm.slug}`} style={{ color: '#0f172a', textDecoration: 'none' }}>{adm.admission_name}</Link>
                  </h3>
                  {(() => { const s = statusMap[adm.status]; return s ? <span style={{ background: s.bg, color: s.color, border: `1px solid ${s.border}`, fontSize: '0.65rem', fontWeight: 700, padding: '0.15rem 0.55rem', borderRadius: '9999px', whiteSpace: 'nowrap', flexShrink: 0, display: 'inline-flex', alignItems: 'center', lineHeight: 1.4 }}>{s.label}</span> : null; })()}
                </div>
                <div style={{ fontSize: '0.82rem', color: '#64748b', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '0.3rem', marginBottom: '0.35rem' }}><Landmark size={12} strokeWidth={2} />{adm.conducting_body}</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem', marginBottom: '0.6rem' }}>
                  {adm.admission_type && <span style={{ background: '#ede9fe', color: '#5b21b6', border: '1px solid #ddd6fe', padding: '0.15rem 0.5rem', borderRadius: '9999px', fontSize: '0.72rem', fontWeight: 700 }}>{adm.admission_type.toUpperCase()}</span>}
                  {adm.stream && <span style={{ background: '#dbeafe', color: '#1e40af', border: '1px solid #bfdbfe', padding: '0.15rem 0.5rem', borderRadius: '9999px', fontSize: '0.72rem', fontWeight: 600 }}>{adm.stream}</span>}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.55rem', borderTop: '1px solid #f1f5f9', flexWrap: 'wrap', gap: '0.4rem' }}>
                  {adm.application_end
                    ? <span style={{ fontSize: '0.75rem', color: '#b45309', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.25rem', background: '#fef3c7', border: '1px solid #fde68a', padding: '0.15rem 0.5rem', borderRadius: '9999px' }}><Clock size={11} strokeWidth={2} />Deadline: {adm.application_end}</span>
                    : <span />}
                  <div style={{ display: 'flex', gap: '0.4rem' }}>
                    <Link to={`/admissions/${adm.slug}`} className="btn btn-outline btn-sm">View Details →</Link>
                    {token ? (
                      <button onClick={() => track(adm)} className={isTracking ? 'btn-tracking btn btn-sm' : 'btn btn-outline btn-sm'} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                        {isTracking ? <><Star size={12} strokeWidth={2} fill="currentColor" />Tracking</> : <><Star size={12} strokeWidth={2} />Track</>}
                      </button>
                    ) : (
                      <Link to={`/login?next=/admissions/${adm.slug}`} className="btn btn-outline btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}><Star size={12} strokeWidth={2} />Track</Link>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
          {pagination.has_more && (
            <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
              <button onClick={() => setSearchParams({ q, stream, admission_type, offset: offset + limit })} className="btn btn-outline">Load More</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
