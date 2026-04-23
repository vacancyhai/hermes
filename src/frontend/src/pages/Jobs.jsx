import PropTypes from 'prop-types';
import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Landmark, Users, Clock, Star, SlidersHorizontal, X } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';

const cardVariants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.28, ease: [0.16, 1, 0.3, 1] } },
};

const listVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06, delayChildren: 0.04 } },
};

function JobCard({ job, trackedIds, onToggle }) {
  const { token } = useAuth();
  const navigate = useNavigate();
  const isTracking = trackedIds.has(String(job.id));

  const track = async (e) => {
    e.stopPropagation();
    try {
      if (isTracking) await api.delete(`/jobs/${job.id}/track`);
      else await api.post(`/jobs/${job.id}/track`);
      onToggle(job.id);
    } catch { }
  };

  const statusMap = {
    active:   { bg: '#dcfce7', color: '#15803d', border: '#bbf7d0', label: 'Active' },
    upcoming: { bg: '#fef3c7', color: '#b45309', border: '#fde68a', label: 'Upcoming' },
    closed:   { bg: '#fee2e2', color: '#b91c1c', border: '#fecaca', label: 'Closed' },
  };

  const s = statusMap[job.status];
  const initials = (job.organization || '?')[0].toUpperCase();
  return (
    <motion.div
      variants={cardVariants}
      onClick={() => navigate(`/jobs/${job.slug}`)}
      whileHover={{ y: -3, boxShadow: '0 8px 24px rgba(15,23,42,.1), 0 2px 8px rgba(15,23,42,.06)', borderColor: '#93c5fd' }}
      whileTap={{ scale: 0.99 }}
      style={{ background: '#fff', border: '1px solid #e2e8f0', borderLeft: '3px solid #1e3a5f', borderRadius: '0.75rem', padding: '1rem 1.1rem', marginBottom: '0.6rem', boxShadow: '0 1px 4px rgba(15,23,42,.05)', transition: 'border-color 0.15s', cursor: 'pointer' }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', marginBottom: '0.3rem' }}>
        {/* Org logo circle */}
        <div style={{ flexShrink: 0, width: 40, height: 40, borderRadius: '50%', overflow: 'hidden', border: '1.5px solid #e2e8f0', background: 'linear-gradient(135deg,#1e3a5f,#3b82f6)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 1px 4px rgba(15,23,42,.1)' }}>
          {job.organization_logo_url
            ? <img src={job.organization_logo_url} alt={job.organization} style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={(e) => { e.target.style.display = 'none'; e.target.parentNode.dataset.fallback = '1'; }} />
            : <span style={{ color: '#fff', fontWeight: 800, fontSize: '0.95rem', lineHeight: 1 }}>{initials}</span>}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '0.5rem' }}>
            <h3 style={{ fontSize: '0.975rem', fontWeight: 700, lineHeight: 1.4, flex: 1, minWidth: 0, margin: 0, color: '#0f172a' }}>
              {job.job_title}
            </h3>
            {s && <span style={{ background: s.bg, color: s.color, border: `1px solid ${s.border}`, fontSize: '0.65rem', fontWeight: 700, padding: '0.15rem 0.55rem', borderRadius: '9999px', whiteSpace: 'nowrap', flexShrink: 0, display: 'inline-flex', alignItems: 'center', lineHeight: 1.4 }}>{s.label}</span>}
          </div>
          <div style={{ fontSize: '0.82rem', color: '#64748b', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '0.3rem', marginTop: '0.15rem' }}><Landmark size={12} strokeWidth={2} />{job.organization}</div>
        </div>
      </div>
      {job.short_description && <div style={{ fontSize: '0.845rem', color: '#475569', marginBottom: '0.35rem', lineHeight: 1.55, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>{job.short_description}</div>}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem', marginBottom: '0.6rem' }}>
        {job.total_vacancies && <span style={{ background: '#f1f5f9', color: '#334155', padding: '0.15rem 0.5rem', borderRadius: '9999px', fontSize: '0.72rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.25rem', border: '1px solid #e2e8f0' }}><Users size={11} strokeWidth={2} />{job.total_vacancies.toLocaleString()} posts</span>}
        {job.qualification_level && <span style={{ background: '#dbeafe', color: '#1e40af', border: '1px solid #bfdbfe', padding: '0.15rem 0.5rem', borderRadius: '9999px', fontSize: '0.72rem', fontWeight: 600 }}>{job.qualification_level}</span>}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.55rem', borderTop: '1px solid #f1f5f9', flexWrap: 'wrap', gap: '0.4rem' }}>
        {job.application_end
          ? <span style={{ fontSize: '0.75rem', color: '#b45309', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.25rem', background: '#fef3c7', border: '1px solid #fde68a', padding: '0.15rem 0.5rem', borderRadius: '9999px' }}><Clock size={11} strokeWidth={2} />Deadline: {job.application_end}</span>
          : <span />}
        <div style={{ display: 'flex', gap: '0.4rem' }}>
          {token ? (
            <button onClick={track} className={isTracking ? 'btn-tracking btn btn-sm' : 'btn btn-outline btn-sm'} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
              {isTracking ? <><Star size={12} strokeWidth={2} fill="currentColor" />Tracking</> : <><Star size={12} strokeWidth={2} />Keep Track</>}
            </button>
          ) : (
            <Link to={`/login?next=/jobs/${job.slug}`} onClick={(e) => e.stopPropagation()} className="btn btn-outline btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}><Star size={12} strokeWidth={2} />Keep Track</Link>
          )}
        </div>
      </div>
    </motion.div>
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
      <div style={{ background: 'linear-gradient(135deg, #0f2440 0%, #1e3a5f 50%, #1d4ed8 100%)', color: '#fff', padding: '1.75rem 2rem', borderRadius: '1rem', marginBottom: '1.5rem', position: 'relative', overflow: 'hidden', boxShadow: '0 8px 28px rgba(30,58,95,.3)' }}>
        <div style={{ position: 'absolute', top: -50, right: -30, width: 200, height: 200, background: 'rgba(255,255,255,.06)', borderRadius: '50%', pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', bottom: -50, left: 30, width: 140, height: 140, background: 'rgba(255,255,255,.04)', borderRadius: '50%', pointerEvents: 'none' }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 800, marginBottom: '0.25rem', letterSpacing: '-0.02em' }}>Government Job Vacancies</h1>
          <p style={{ fontSize: '0.875rem', opacity: 0.78, marginBottom: '1rem' }}>Latest central &amp; state government jobs — search, filter and track deadlines</p>
          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search jobs..." style={{ flex: 1, minWidth: 180, padding: '0.5rem 0.8rem', borderRadius: '0.45rem', border: 'none', fontSize: '0.875rem', color: '#1e293b', outline: 'none' }} />
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
                <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94a3b8', marginBottom: '0.4rem' }}>Qualification</div>
                {['10th', '12th', 'Graduate', 'Post Graduate', 'Engineering'].map((ql) => (
                  <label key={ql} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.3rem 0', cursor: 'pointer', fontSize: '0.82rem', color: '#334155' }}>
                    <input type="radio" name="qual" checked={qualification === ql} onChange={() => setSearchParams({ q, qualification_level: ql, offset: 0 })} style={{ accentColor: '#2563eb' }} />
                    {ql}
                  </label>
                ))}
                {qualification && <button onClick={() => setSearchParams({ q, offset: 0 })} style={{ fontSize: '0.78rem', color: '#2563eb', background: 'none', border: 'none', cursor: 'pointer', padding: '0.25rem 0', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}><X size={11} strokeWidth={2.5} />Clear filter</button>}
              </div>
            </div>
          </div>
        </aside>

        {/* Job list */}
        <div>
          {loading && Array.from({ length: 6 }).map((_, i) => (
            <div key={i} style={{ background: '#fff', border: '1px solid #e2e8f0', borderLeft: '3px solid #e2e8f0', borderRadius: '0.65rem', padding: '1rem 1.1rem', marginBottom: '0.6rem' }}>
              <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.5rem', alignItems: 'flex-start' }}>
                <div className="skeleton" style={{ width: 40, height: 40, borderRadius: '50%', flexShrink: 0 }} />
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                    <div className="skeleton" style={{ height: 16, width: '60%', borderRadius: '0.4rem' }} />
                    <div className="skeleton" style={{ height: 16, width: 52, borderRadius: '9999px' }} />
                  </div>
                  <div className="skeleton" style={{ height: 13, width: '40%', borderRadius: '0.4rem' }} />
                </div>
              </div>
              <div className="skeleton" style={{ height: 13, width: '80%', borderRadius: '0.4rem', marginBottom: '0.4rem' }} />
              <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.55rem' }}>
                <div className="skeleton" style={{ height: 22, width: 80, borderRadius: '9999px' }} />
                <div className="skeleton" style={{ height: 22, width: 64, borderRadius: '9999px' }} />
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
          {!loading && jobs.length === 0 && <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>No jobs found. Try a different search.</div>}
          {!loading && (
            <motion.div variants={listVariants} initial="hidden" animate="show">
              {jobs.map((job) => <JobCard key={job.id} job={job} trackedIds={trackedIds} onToggle={toggleId} />)}
            </motion.div>
          )}

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
