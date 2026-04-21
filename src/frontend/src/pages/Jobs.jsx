import PropTypes from 'prop-types';
import { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';

function JobCard({ job, trackedIds, onToggle }) {
  const { token } = useAuth();
  const isTracking = trackedIds.has(String(job.id));

  const track = async (e) => {
    e.preventDefault();
    try {
      if (isTracking) await api.delete(`/jobs/${job.id}/track`);
      else await api.post(`/jobs/${job.id}/track`);
      onToggle(job.id);
    } catch { }
  };

  const statusColors = { active: '#22c55e', upcoming: '#f59e0b', closed: '#ef4444' };
  const statusLabels = { active: 'Active', upcoming: 'Upcoming', closed: 'Closed' };

  return (
    <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderLeft: '4px solid #1e3a5f', borderRadius: '0.5rem', padding: '1rem 1.1rem', marginBottom: '0.75rem', transition: 'box-shadow .15s' }}
      onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,.07)'; e.currentTarget.style.borderLeftColor = '#2563eb'; }}
      onMouseLeave={(e) => { e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.borderLeftColor = '#1e3a5f'; }}>
      <div style={{ marginBottom: '0.3rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, lineHeight: 1.4, display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
          <Link to={`/jobs/${job.slug}`} style={{ color: '#1e293b', flex: 1 }}>{job.job_title}</Link>
          {job.status && <span style={{ background: statusColors[job.status] || '#94a3b8', color: '#fff', fontSize: '0.7rem', fontWeight: 700, padding: '0.15rem 0.5rem', borderRadius: 9999, whiteSpace: 'nowrap' }}>{statusLabels[job.status] || job.status}</span>}
        </h3>
      </div>
      <div style={{ fontSize: '0.83rem', color: '#64748b', fontWeight: 500 }}>🏛 {job.organization}</div>
      {job.short_description && <div style={{ fontSize: '0.855rem', color: '#475569', margin: '0.35rem 0', lineHeight: 1.55, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>{job.short_description}</div>}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', margin: '0.4rem 0', fontSize: '0.8rem', color: '#64748b' }}>
        {job.total_vacancies && <span style={{ background: '#f1f5f9', padding: '0.15rem 0.5rem', borderRadius: '0.35rem' }}>👥 {job.total_vacancies.toLocaleString()} posts</span>}
        {job.qualification_level && <span style={{ background: '#dbeafe', color: '#1e40af', padding: '0.15rem 0.5rem', borderRadius: '0.35rem', fontWeight: 600 }}>{job.qualification_level}</span>}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.7rem', paddingTop: '0.6rem', borderTop: '1px solid #f1f5f9', flexWrap: 'wrap', gap: '0.4rem' }}>
        <div>
          {job.application_end && <span style={{ fontSize: '0.78rem', color: '#b45309', fontWeight: 600 }}>⏰ Deadline: {job.application_end}</span>}
        </div>
        <div style={{ display: 'flex', gap: '0.4rem' }}>
          <Link to={`/jobs/${job.slug}`} className="btn btn-outline btn-sm">View Details →</Link>
          {token ? (
            <button onClick={track} className={isTracking ? 'btn-tracking btn btn-sm' : 'btn btn-outline btn-sm'}>
              {isTracking ? '★ Tracking' : '☆ Track'}
            </button>
          ) : (
            <Link to={`/login?next=/jobs/${job.slug}`} className="btn btn-outline btn-sm">☆ Track</Link>
          )}
        </div>
      </div>
    </div>
  );
}

JobCard.propTypes = {
  job: PropTypes.object.isRequired,
  trackedIds: PropTypes.instanceOf(Set).isRequired,
  onToggle: PropTypes.func.isRequired,
};

export default function Jobs() {
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [jobs, setJobs] = useState([]);
  const [pagination, setPagination] = useState({});
  const [trackedIds, setTrackedIds] = useState(new Set());
  const [loading, setLoading] = useState(false);

  const q = searchParams.get('q') || '';
  const qualification = searchParams.get('qualification_level') || '';
  const org = searchParams.get('organization') || '';
  const offset = Number.parseInt(searchParams.get('offset') || '0', 10);
  const limit = 20;

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      const params = { limit, offset };
      if (q) params.q = q;
      if (qualification) params.qualification_level = qualification;
      if (org) params.organization = org;
      const res = await api.get('/jobs', { params });
      setJobs(res.data.data || []);
      setPagination(res.data.pagination || {});
    } catch { } finally { setLoading(false); }
  }, [q, qualification, org, offset]);

  useEffect(() => { fetchJobs(); }, [fetchJobs]);

  useEffect(() => {
    if (!token) { setTrackedIds(new Set()); return; }
    api.get('/users/me/tracked').then((r) => {
      setTrackedIds(new Set((r.data.jobs || []).map((j) => String(j.id))));
    }).catch(() => { });
  }, [token]);

  const toggleId = (id) => setTrackedIds((prev) => {
    const next = new Set(prev);
    if (next.has(String(id))) next.delete(String(id)); else next.add(String(id));
    return next;
  });

  const [search, setSearch] = useState(q);
  const handleSearch = (e) => {
    e.preventDefault();
    setSearchParams({ q: search, offset: 0 });
  };

  return (
    <div>
      <div style={{ background: 'linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%)', color: '#fff', padding: '1.75rem 1.5rem 1.5rem', borderRadius: '0.75rem', marginBottom: '1.25rem', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', top: -40, right: -40, width: 200, height: 200, background: 'rgba(255,255,255,.05)', borderRadius: '50%' }} />
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '0.3rem' }}>💼 Government Job Vacancies</h1>
        <p style={{ fontSize: '0.875rem', opacity: 0.85 }}>Latest central &amp; state government jobs — search, filter and track deadlines</p>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem', flexWrap: 'wrap' }}>
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search jobs..." style={{ flex: 1, minWidth: 180, padding: '0.5rem 0.75rem', borderRadius: '0.4rem', border: 'none', fontSize: '0.875rem', color: '#1e293b' }} />
          <button type="submit" style={{ padding: '0.5rem 1rem', borderRadius: '0.4rem', background: 'rgba(255,255,255,.2)', color: '#fff', border: '1px solid rgba(255,255,255,.3)', cursor: 'pointer', fontWeight: 600 }}>Search</button>
          {q && <button type="button" onClick={() => { setSearch(''); setSearchParams({}); }} style={{ padding: '0.5rem 0.75rem', borderRadius: '0.4rem', background: 'rgba(255,255,255,.1)', color: '#fff', border: '1px solid rgba(255,255,255,.2)', cursor: 'pointer' }}>✕ Clear</button>}
        </form>
      </div>

      <div className="list-page-grid">
        {/* Filter sidebar */}
        <aside className="filter-sidebar">
          <div className="filter-widget">
            <div className="filter-widget-header">🔽 Filters</div>
            <div className="filter-widget-body">
              <div style={{ marginBottom: '0.85rem' }}>
                <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94a3b8', marginBottom: '0.4rem' }}>Qualification</div>
                {['10th', '12th', 'Graduate', 'Post Graduate', 'Engineering'].map((ql) => (
                  <label key={ql} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.3rem 0', cursor: 'pointer', fontSize: '0.82rem', color: '#334155' }}>
                    <input type="radio" name="qual" checked={qualification === ql} onChange={() => setSearchParams({ q, qualification_level: ql, offset: 0 })} style={{ accentColor: '#2563eb' }} />
                    {ql}
                  </label>
                ))}
                {qualification && <button onClick={() => setSearchParams({ q, offset: 0 })} style={{ fontSize: '0.78rem', color: '#2563eb', background: 'none', border: 'none', cursor: 'pointer', padding: '0.25rem 0' }}>✕ Clear filter</button>}
              </div>
            </div>
          </div>
        </aside>

        {/* Job list */}
        <div>
          {loading && <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>Loading...</div>}
          {!loading && jobs.length === 0 && <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>No jobs found. Try a different search.</div>}
          {!loading && jobs.map((job) => <JobCard key={job.id} job={job} trackedIds={trackedIds} onToggle={toggleId} />)}

          {pagination.has_more && (
            <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
              <button onClick={() => setSearchParams({ q, qualification_level: qualification, offset: offset + limit })} className="btn btn-outline">Load More</button>
            </div>
          )}
          {offset > 0 && (
            <div style={{ textAlign: 'center', padding: '0.5rem 0' }}>
              <button onClick={() => setSearchParams({ q, qualification_level: qualification, offset: Math.max(0, offset - limit) })} className="btn btn-outline btn-sm">← Previous</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
