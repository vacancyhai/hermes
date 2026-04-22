import PropTypes from 'prop-types';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Briefcase, CreditCard, FileText, Trophy, GraduationCap, Landmark, Clock, Star, Search, CalendarDays, Users } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';

const STATUS_COLORS = {
  active: { bg: '#dcfce7', color: '#15803d', border: '#bbf7d0', label: 'Active' },
  upcoming: { bg: '#fef3c7', color: '#b45309', border: '#fde68a', label: 'Soon' },
  closed: { bg: '#fee2e2', color: '#b91c1c', border: '#fecaca', label: 'Closed' },
};

function MiniStatus({ status }) {
  const s = STATUS_COLORS[status];
  if (!s) return null;
  return (
    <span style={{
      background: s.bg,
      color: s.color,
      border: `1px solid ${s.border}`,
      fontSize: '0.6rem',
      fontWeight: 700,
      padding: '0.15rem 0.5rem',
      borderRadius: '9999px',
      display: 'inline-flex',
      alignItems: 'center',
      whiteSpace: 'nowrap',
      letterSpacing: '0.02em',
      lineHeight: 1.4,
      flexShrink: 0,
    }}>{s.label}</span>
  );
}

MiniStatus.propTypes = { status: PropTypes.string };
MiniStatus.defaultProps = { status: '' };

function ExamsDaysBadge({ days }) {
  if (days == null) return null;
  let bg, col;
  if (days === 0) { bg = '#ef4444'; col = '#fff'; }
  else if (days <= 7) { bg = '#fee2e2'; col = '#991b1b'; }
  else if (days <= 30) { bg = '#fef9c3'; col = '#854d0e'; }
  else { bg = '#eff6ff'; col = '#1d4ed8'; }
  return <span style={{ background: bg, color: col, borderRadius: 9999, padding: '0.1rem 0.4rem', fontSize: '0.65rem' }}>{days === 0 ? 'Today!' : `${days}d left`}</span>;
}

ExamsDaysBadge.propTypes = { days: PropTypes.number };
ExamsDaysBadge.defaultProps = { days: null };

function MiniCard({ children, color, onClick, accentBg }) {
  return (
    <button type="button" onClick={onClick} style={{
      background: '#fff',
      border: '1px solid #e2e8f0',
      borderTop: `3px solid ${color}`,
      borderRadius: '0.6rem',
      padding: '0.95rem 1rem 0.8rem',
      width: 220, minWidth: 220, maxWidth: 220,
      minHeight: 148, flexShrink: 0,
      display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
      cursor: 'pointer', overflow: 'visible',
      transition: 'box-shadow .18s, transform .15s, border-color .15s',
      textAlign: 'left',
      boxShadow: '0 1px 3px rgba(0,0,0,.05)',
      position: 'relative',
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.boxShadow = '0 6px 20px rgba(0,0,0,.1)';
      e.currentTarget.style.transform = 'translateY(-2px)';
      e.currentTarget.style.borderColor = color;
      if (accentBg) e.currentTarget.style.background = accentBg;
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,.05)';
      e.currentTarget.style.transform = 'none';
      e.currentTarget.style.borderColor = '#e2e8f0';
      e.currentTarget.style.background = '#fff';
    }}
    >
      {children}
    </button>
  );
}

MiniCard.propTypes = {
  children: PropTypes.node.isRequired,
  color: PropTypes.string.isRequired,
  onClick: PropTypes.func.isRequired,
  accentBg: PropTypes.string,
};
MiniCard.defaultProps = { accentBg: null };

function TrackBtn({ type, id, slug, isTracking, onToggle }) {
  const { token } = useAuth();
  if (!token) {
    return <a href={`/login?next=/${type}s/${slug}`} onClick={(e) => { e.stopPropagation(); }} style={{ fontSize: '0.7rem', padding: '0.2rem 0.5rem', borderRadius: 9999, border: '1px solid #bfdbfe', background: '#eff6ff', color: '#1d4ed8', textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}><Star size={11} strokeWidth={2} /></a>;
  }
  const track = async (e) => {
    e.stopPropagation();
    try {
      if (isTracking) await api.delete(`/${type}s/${id}/track`);
      else await api.post(`/${type}s/${id}/track`);
      onToggle(id);
    } catch { }
  };
  return (
    <button onClick={track} className={isTracking ? 'btn-tracking btn btn-sm' : 'btn btn-outline btn-sm'} style={{ fontSize: '0.7rem', padding: '0.2rem 0.5rem', display: 'inline-flex', alignItems: 'center' }}>
      <Star size={11} strokeWidth={2} fill={isTracking ? 'currentColor' : 'none'} />
    </button>
  );
}

TrackBtn.propTypes = {
  type: PropTypes.string.isRequired,
  id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  slug: PropTypes.string.isRequired,
  isTracking: PropTypes.bool.isRequired,
  onToggle: PropTypes.func.isRequired,
};

function SectionRow({ title, href, accent, children }) {
  return (
    <div style={{ marginBottom: '1.75rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
        <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#0f172a', display: 'inline-flex', alignItems: 'center', gap: '0.45rem', paddingLeft: '0.6rem', borderLeft: `3px solid ${accent || '#2563eb'}` }}>{title}</div>
        <Link to={href} style={{ fontSize: '0.75rem', fontWeight: 600, color: accent || '#2563eb', whiteSpace: 'nowrap', padding: '0.25rem 0.65rem', border: `1px solid ${accent || '#2563eb'}22`, borderRadius: '0.375rem', background: `${accent || '#2563eb'}0d`, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.2rem', transition: 'background 0.15s' }}>View All →</Link>
      </div>
      <div className="h-scroll-wrap"><div className="h-scroll">{children}</div></div>
    </div>
  );
}

SectionRow.propTypes = {
  title: PropTypes.oneOfType([PropTypes.string, PropTypes.node]).isRequired,
  href: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
  accent: PropTypes.string,
};
SectionRow.defaultProps = { accent: null };

function SkeletonMiniCard() {
  return (
    <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderTop: '3px solid #e2e8f0', borderRadius: '0.6rem', padding: '0.95rem 1rem 0.8rem', width: 220, minWidth: 220, maxWidth: 220, minHeight: 148, flexShrink: 0, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
          <div className="skeleton" style={{ height: 13, width: '65%', borderRadius: '0.3rem' }} />
          <div className="skeleton" style={{ height: 16, width: 36, borderRadius: '9999px' }} />
        </div>
        <div className="skeleton" style={{ height: 13, width: '55%', borderRadius: '0.3rem', marginTop: '0.2rem', marginBottom: '0.2rem' }} />
        <div className="skeleton" style={{ height: 11, width: '45%', borderRadius: '0.3rem', marginBottom: '0.2rem' }} />
        <div className="skeleton" style={{ height: 11, width: '35%', borderRadius: '0.3rem' }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '0.4rem' }}>
        <div className="skeleton" style={{ height: 22, width: 68, borderRadius: '9999px' }} />
        <div className="skeleton" style={{ height: 22, width: 26, borderRadius: '0.35rem' }} />
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState({ jobs: [], admissions: [], admit_cards: [], answer_keys: [], results: [], exams: [] });
  const [tracked, setTracked] = useState({ jobs: [], admissions: [], total: 0, jobIds: new Set(), admissionIds: new Set() });
  const [orgs, setOrgs] = useState([]);
  const [trackedOrgIds, setTrackedOrgIds] = useState(new Set());
  const [profileComplete, setProfileComplete] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params = { limit: 12, offset: 0 };
    Promise.all([
      api.get('/jobs', { params }).catch(() => ({ data: { data: [] } })),
      api.get('/admissions', { params }).catch(() => ({ data: { data: [] } })),
      api.get('/admit-cards', { params }).catch(() => ({ data: { data: [] } })),
      api.get('/answer-keys', { params }).catch(() => ({ data: { data: [] } })),
      api.get('/results', { params }).catch(() => ({ data: { data: [] } })),
      api.get('/exam-reminders').catch(() => ({ data: { data: [] } })),
      api.get('/organizations', { params: { limit: 100 } }).catch(() => ({ data: { data: [] } })),
    ]).then(([j, a, ac, ak, r, ex, og]) => {
      setData({
        jobs: j.data.data || [],
        admissions: a.data.data || [],
        admit_cards: ac.data.data || [],
        answer_keys: ak.data.data || [],
        results: r.data.data || [],
        exams: (ex.data.data || []).slice(0, 8),
      });
      setOrgs(og.data.data || []);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (!token) return;
    api.get('/users/me/tracked').then((r) => {
      const tj = r.data.jobs || [];
      const ta = r.data.admissions || [];
      setTracked({ jobs: tj, admissions: ta, total: r.data.total || 0, jobIds: new Set(tj.map((j) => String(j.id))), admissionIds: new Set(ta.map((a) => String(a.id))) });
    }).catch(() => {});
    api.get('/users/profile').then((r) => {
      const p = r.data.profile || {};
      setProfileComplete(Boolean(p.highest_qualification || p.category || p.date_of_birth));
    }).catch(() => {});
    api.get('/organizations/tracked').then((r) => {
      setTrackedOrgIds(new Set((r.data.data || []).map((o) => String(o.id))));
    }).catch(() => {});
  }, [token]);

  const toggleJobId = (id) => setTracked((prev) => {
    const next = new Set(prev.jobIds);
    if (next.has(String(id))) {
      next.delete(String(id));
    } else {
      next.add(String(id));
    }
    return { ...prev, jobIds: next };
  });
  const toggleAdmId = (id) => setTracked((prev) => {
    const next = new Set(prev.admissionIds);
    if (next.has(String(id))) {
      next.delete(String(id));
    } else {
      next.add(String(id));
    }
    return { ...prev, admissionIds: next };
  });

  function removeTrackedJob(p, item) {
    return { ...p, jobs: p.jobs.filter((j) => j.id !== item.id), jobIds: new Set([...p.jobIds].filter((x) => x !== String(item.id))) };
  }
  function removeTrackedAdmission(p, item) {
    return { ...p, admissions: p.admissions.filter((a) => a.id !== item.id), admissionIds: new Set([...p.admissionIds].filter((x) => x !== String(item.id))) };
  }
  const untrackJob = async (item) => {
    try {
      await api.delete(`/jobs/${item.id}/track`);
      setTracked((p) => removeTrackedJob(p, item));
    } catch { }
  };
  const untrackAdmission = async (item) => {
    try {
      await api.delete(`/admissions/${item.id}/track`);
      setTracked((p) => removeTrackedAdmission(p, item));
    } catch { }
  };

  return (
    <div>
      {/* Hero */}
      <div style={{ background: 'linear-gradient(135deg, #0f2440 0%, #1e3a5f 45%, #1d4ed8 100%)', color: '#fff', padding: '1.75rem 2rem', borderRadius: '1rem', marginBottom: '1.5rem', position: 'relative', overflow: 'hidden', boxShadow: '0 8px 32px rgba(30,58,95,.35)' }}>
        <div style={{ position: 'absolute', top: -50, right: -40, width: 220, height: 220, background: 'rgba(255,255,255,.06)', borderRadius: '50%', pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', bottom: -60, left: 40, width: 160, height: 160, background: 'rgba(255,255,255,.04)', borderRadius: '50%', pointerEvents: 'none' }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', background: 'rgba(255,255,255,.12)', borderRadius: '0.375rem', padding: '0.25rem 0.65rem', fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '0.75rem' }}>
            <LayoutDashboard size={11} strokeWidth={2.5} />Overview
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '0.35rem', letterSpacing: '-0.02em', lineHeight: 1.2 }}>Welcome to Vacancy Hai</h1>
          <p style={{ fontSize: '0.875rem', opacity: 0.78, maxWidth: 480 }}>Latest government jobs, admissions, admit cards, answer keys and results — all in one place.</p>
        </div>
      </div>

      {/* Org strip */}
      {loading && (
        <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.85rem', padding: '1rem 1.25rem', marginBottom: '1.5rem', boxShadow: '0 1px 4px rgba(0,0,0,.05)' }}>
          {/* header row — matches: <Landmark 13px> + "Organizations" (0.8rem) + count badge */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
              <div className="skeleton" style={{ width: 13, height: 13, borderRadius: '0.2rem', flexShrink: 0 }} />
              <div className="skeleton" style={{ height: 13, width: 88, borderRadius: '0.3rem' }} />
              <div className="skeleton" style={{ height: 13, width: 20, borderRadius: '9999px' }} />
            </div>
          </div>
          {/* tiles row — matches real overflowX:auto, paddingBottom:0.2rem */}
          <div style={{ display: 'flex', gap: '0.65rem', overflowX: 'auto', scrollbarWidth: 'none', paddingBottom: '0.2rem' }}>
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: '0.45rem', flexShrink: 0, width: 88 }}>
                {/* avatar: 48×48 with 2px border = 52px visual */}
                <div className="skeleton" style={{ width: 48, height: 48, borderRadius: '0.6rem' }} />
                {/* name: fontSize 0.65rem ≈ 10.4px + lineHeight 1.3 ≈ 13.5px */}
                <div className="skeleton" style={{ height: 10, width: 72, borderRadius: '0.3rem' }} />
                {/* follow button: padding 0.18rem 0.45rem + fontSize 0.6rem + Star 9px ≈ 22px tall, full width */}
                <div className="skeleton" style={{ height: 22, width: 88, borderRadius: '0.3rem' }} />
              </div>
            ))}
          </div>
        </div>
      )}
      {!loading && orgs.length > 0 && (
        <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.85rem', padding: '1rem 1.25rem', marginBottom: '1.5rem', boxShadow: '0 1px 4px rgba(0,0,0,.05)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#0f172a', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}><Landmark size={13} strokeWidth={2} />Organizations <span style={{ fontSize: '0.68rem', fontWeight: 700, background: '#f1f5f9', color: '#64748b', borderRadius: '9999px', padding: '0.1rem 0.5rem' }}>{orgs.length}</span></span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              {token && trackedOrgIds.size > 0 && <span style={{ fontSize: '0.72rem', color: '#64748b' }}>{trackedOrgIds.size} followed</span>}
              {orgs.length > 8 && <span style={{ fontSize: '0.7rem', color: '#94a3b8', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>scroll for more →</span>}
            </div>
          </div>
          <div style={{ position: 'relative' }}>
          <div style={{ display: 'flex', gap: '0.65rem', overflowX: 'auto', scrollbarWidth: 'none', paddingBottom: '0.2rem' }}>
            {orgs.map((org) => {
              const isTracking = trackedOrgIds.has(String(org.id));
              const displayName = org.short_name || org.name;
              const toggleOrg = async (e) => {
                e.preventDefault();
                if (!token) { navigate('/login?next=/'); return; }
                try {
                  if (isTracking) { await api.delete(`/organizations/${org.id}/track`); }
                  else { await api.post(`/organizations/${org.id}/track`); }
                  setTrackedOrgIds((prev) => {
                    const next = new Set(prev);
                    if (isTracking) next.delete(String(org.id));
                    else next.add(String(org.id));
                    return next;
                  });
                } catch { }
              };
              return (
                <div key={org.id} style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: '0.45rem', flexShrink: 0, width: 88, cursor: 'default' }}>
                  {org.logo_url
                    ? <img src={org.logo_url} alt={displayName} style={{ width: 48, height: 48, borderRadius: '0.6rem', objectFit: 'cover', border: isTracking ? '2px solid #f59e0b' : '2px solid #e2e8f0', transition: 'border-color .15s' }} />
                    : <div style={{ width: 48, height: 48, borderRadius: '0.6rem', background: isTracking ? 'linear-gradient(135deg,#b45309,#f59e0b)' : 'linear-gradient(135deg,#1e3a5f,#3b82f6)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem', fontWeight: 800, border: isTracking ? '2px solid #f59e0b' : '2px solid transparent', transition: 'border-color .15s', flexShrink: 0 }}>{displayName[0]?.toUpperCase()}</div>
                  }
                  <span style={{ fontSize: '0.65rem', fontWeight: 600, color: '#334155', textAlign: 'center', lineHeight: 1.3, width: '100%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={org.name}>{displayName}</span>
                  <button onClick={toggleOrg} style={{ fontSize: '0.6rem', fontWeight: 700, borderRadius: '0.3rem', padding: '0.18rem 0.45rem', border: `1px solid ${isTracking ? '#f59e0b' : '#e2e8f0'}`, background: isTracking ? '#fef3c7' : '#f8fafc', color: isTracking ? '#92400e' : '#64748b', cursor: 'pointer', whiteSpace: 'nowrap', width: '100%', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '0.2rem', transition: 'all .15s' }}>
                    {isTracking ? <><Star size={9} strokeWidth={2} fill="currentColor" />Following</> : <><Star size={9} strokeWidth={2} />Follow</>}
                  </button>
                </div>
              );
            })}
          </div>
          </div>{/* end position:relative wrapper */}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,210px) minmax(0,1fr)', gap: '1.5rem', alignItems: 'start' }} className="page-grid">

        {/* Upcoming Exams Sidebar */}
        <aside style={{ position: 'sticky', top: '4.5rem' }}>
          <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.85rem', overflow: 'hidden', boxShadow: '0 1px 4px rgba(0,0,0,.05)' }}>
            <div style={{ background: 'linear-gradient(90deg, #0f2440, #1e3a5f)', color: '#fff', padding: '0.75rem 1rem', fontSize: '0.78rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.4rem', letterSpacing: '0.02em' }}><CalendarDays size={13} strokeWidth={2} />Upcoming Exams</div>
            <div>
              {loading && Array.from({ length: 5 }).map((_, i) => (
                <div key={i} style={{ borderBottom: '1px solid #f8fafc', padding: '0.65rem 0.9rem' }}>
                  <div className="skeleton" style={{ height: 11, width: '88%', borderRadius: '0.3rem', marginBottom: '0.2rem' }} />
                  <div className="skeleton" style={{ height: 11, width: '60%', borderRadius: '0.3rem', marginBottom: '0.3rem' }} />
                  <div className="skeleton" style={{ height: 11, width: '45%', borderRadius: '0.3rem', marginBottom: '0.3rem' }} />
                  <div className="skeleton" style={{ height: 17, width: 48, borderRadius: '9999px' }} />
                </div>
              ))}
              {!loading && data.exams.length === 0 && <div style={{ padding: '1rem', textAlign: 'center', color: '#94a3b8', fontSize: '0.78rem' }}>No upcoming exams</div>}
              {!loading && data.exams.map((exam) => {
                const isJob = exam.type === 'job' || exam.parent_type === 'job';
                const url = isJob ? `/jobs/${exam.slug || exam.parent_slug}` : `/admissions/${exam.slug || exam.parent_slug}`;
                return (
                  <button type="button" key={exam.id} onClick={() => navigate(url)} style={{ display: 'block', width: '100%', textAlign: 'left', background: 'none', border: 'none', borderBottom: '1px solid #f8fafc', padding: '0.65rem 0.9rem', cursor: 'pointer', transition: 'background .12s' }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = '#f8fafc'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = ''; }}>
                    <div style={{ color: '#0f172a', fontWeight: 600, fontSize: '0.77rem', lineHeight: 1.4, marginBottom: '0.25rem' }}>{exam.title}</div>
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', color: '#64748b', fontSize: '0.68rem', fontWeight: 500 }}>
                      <CalendarDays size={10} strokeWidth={2} />{exam.exam_start || 'TBA'}
                    </div>
                    <div style={{ marginTop: '0.2rem' }}><ExamsDaysBadge days={exam.days_remaining} /></div>
                  </button>
                );
              })}
            </div>
          </div>
        </aside>

        {/* Main content */}
        <div>
          {/* Jobs */}
          <SectionRow title={<><Briefcase size={13} strokeWidth={2} />Latest Jobs</>} href="/jobs" accent="#1e3a5f">
            {loading && Array.from({ length: 6 }).map((_, i) => <SkeletonMiniCard key={i} />)}
            {!loading && data.jobs.length === 0 && <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>No jobs available.</p>}
            {!loading && data.jobs.map((job) => (
              <MiniCard key={job.id} color="#1e3a5f" accentBg="#f0f4ff" onClick={() => navigate(`/jobs/${job.slug}`)}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.3rem', marginBottom: '0.2rem' }}>
                    <div style={{ flex: 1, minWidth: 0, overflow: 'hidden' }}>
                      <div style={{ fontSize: '0.85rem', fontWeight: 700, lineHeight: 1.35, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>{job.job_title}</div>
                    </div>
                    <MiniStatus status={job.status} />
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.2rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: '0.25rem' }}><Landmark size={11} strokeWidth={2} />{job.organization}</div>
                  {job.application_end && <div style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.2rem' }}><Clock size={10} strokeWidth={2} />{job.application_end}</div>}
                  {job.total_vacancies && <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>{job.total_vacancies.toLocaleString()} vacancies</div>}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.4rem', flexWrap: 'wrap', gap: '0.3rem' }}>
                  {!token || !profileComplete
                    ? <Link to="/profile" onClick={(e) => e.stopPropagation()} style={{ fontSize: '0.65rem', padding: '0.15rem 0.5rem', border: '1px solid #e2e8f0', borderRadius: '9999px', background: '#f8fafc', color: '#64748b', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><Search size={10} strokeWidth={2} />Eligibility</Link>
                    : <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>checking…</span>}
                  <TrackBtn type="job" id={job.id} slug={job.slug} isTracking={tracked.jobIds.has(String(job.id))} onToggle={toggleJobId} />
                </div>
              </MiniCard>
            ))}
          </SectionRow>

          {/* Admit Cards */}
          <SectionRow title={<><CreditCard size={13} strokeWidth={2} />Latest Admit Cards</>} href="/admit-cards" accent="#2563eb">
            {loading && Array.from({ length: 6 }).map((_, i) => <SkeletonMiniCard key={i} />)}
            {!loading && data.admit_cards.length === 0 && <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>No admit cards available.</p>}
            {!loading && data.admit_cards.map((card) => (
              <MiniCard key={card.id} color="#2563eb" accentBg="#eff6ff" onClick={() => navigate(`/admit-cards/${card.slug}`)}>
                <div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, lineHeight: 1.35, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>{card.title}</div>
                  {(card.exam_start || card.exam_end) && <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Exam: {card.exam_start || '?'} – {card.exam_end || 'ongoing'}</div>}
                  {card.published_at && <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Published: {card.published_at.slice(0, 10)}</div>}
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: '0.4rem' }}>
                  {(card.job_id || card.admission_id) && (
                    <TrackBtn
                      type={card.job_id ? 'job' : 'admission'}
                      id={card.job_id || card.admission_id}
                      slug={card.slug}
                      isTracking={card.job_id ? tracked.jobIds.has(String(card.job_id)) : tracked.admissionIds.has(String(card.admission_id))}
                      onToggle={card.job_id ? toggleJobId : toggleAdmId}
                    />
                  )}
                </div>
              </MiniCard>
            ))}
          </SectionRow>

          {/* Answer Keys */}
          <SectionRow title={<><FileText size={13} strokeWidth={2} />Latest Answer Keys</>} href="/answer-keys" accent="#d97706">
            {loading && Array.from({ length: 6 }).map((_, i) => <SkeletonMiniCard key={i} />)}
            {!loading && data.answer_keys.length === 0 && <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>No answer keys available.</p>}
            {!loading && data.answer_keys.map((key) => (
              <MiniCard key={key.id} color="#d97706" accentBg="#fffbeb" onClick={() => navigate(`/answer-keys/${key.slug}`)}>
                <div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, lineHeight: 1.35, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>{key.title}</div>
                  {key.published_at && <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Published: {key.published_at.slice(0, 10)}</div>}
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: '0.4rem' }}>
                  {(key.job_id || key.admission_id) && (
                    <TrackBtn type={key.job_id ? 'job' : 'admission'} id={key.job_id || key.admission_id} slug={key.slug} isTracking={key.job_id ? tracked.jobIds.has(String(key.job_id)) : tracked.admissionIds.has(String(key.admission_id))} onToggle={key.job_id ? toggleJobId : toggleAdmId} />
                  )}
                </div>
              </MiniCard>
            ))}
          </SectionRow>

          {/* Results */}
          <SectionRow title={<><Trophy size={13} strokeWidth={2} />Latest Results</>} href="/results" accent="#16a34a">
            {loading && Array.from({ length: 6 }).map((_, i) => <SkeletonMiniCard key={i} />)}
            {!loading && data.results.length === 0 && <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>No results available.</p>}
            {!loading && data.results.map((res) => (
              <MiniCard key={res.id} color="#16a34a" accentBg="#f0fdf4" onClick={() => navigate(`/results/${res.slug}`)}>
                <div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, lineHeight: 1.35, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>{res.title}</div>
                  {res.published_at && <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Published: {res.published_at.slice(0, 10)}</div>}
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: '0.4rem' }}>
                  {(res.job_id || res.admission_id) && (
                    <TrackBtn type={res.job_id ? 'job' : 'admission'} id={res.job_id || res.admission_id} slug={res.slug} isTracking={res.job_id ? tracked.jobIds.has(String(res.job_id)) : tracked.admissionIds.has(String(res.admission_id))} onToggle={res.job_id ? toggleJobId : toggleAdmId} />
                  )}
                </div>
              </MiniCard>
            ))}
          </SectionRow>

          {/* Admissions */}
          <SectionRow title={<><GraduationCap size={13} strokeWidth={2} />Latest Admissions</>} href="/admissions" accent="#7c3aed">
            {loading && Array.from({ length: 6 }).map((_, i) => <SkeletonMiniCard key={i} />)}
            {!loading && data.admissions.length === 0 && <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>No admissions available.</p>}
            {!loading && data.admissions.map((adm) => (
              <MiniCard key={adm.id} color="#7c3aed" accentBg="#f5f3ff" onClick={() => navigate(`/admissions/${adm.slug}`)}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.3rem', marginBottom: '0.2rem' }}>
                    <div style={{ flex: 1, minWidth: 0, overflow: 'hidden' }}>
                      <div style={{ fontSize: '0.85rem', fontWeight: 700, lineHeight: 1.35, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>{adm.admission_name}</div>
                    </div>
                    <MiniStatus status={adm.status} />
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '0.25rem' }}><Landmark size={11} strokeWidth={2} />{adm.conducting_body}</div>
                  {adm.application_end && <div style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.2rem' }}><Clock size={10} strokeWidth={2} />{adm.application_end}</div>}
                  {adm.admission_type && <span style={{ background: '#ede9fe', color: '#5b21b6', border: '1px solid #ddd6fe', padding: '0.15rem 0.5rem', borderRadius: '9999px', fontSize: '0.6rem', fontWeight: 700, display: 'inline-flex', alignItems: 'center', whiteSpace: 'nowrap', lineHeight: 1.4 }}>{adm.admission_type.toUpperCase()}</span>}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.4rem', flexWrap: 'wrap', gap: '0.3rem' }}>
                  {!token || !profileComplete
                    ? <Link to="/profile" onClick={(e) => e.stopPropagation()} style={{ fontSize: '0.65rem', padding: '0.15rem 0.5rem', border: '1px solid #e2e8f0', borderRadius: '9999px', background: '#f8fafc', color: '#64748b', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><Search size={10} strokeWidth={2} />Eligibility</Link>
                    : <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>checking…</span>}
                  <TrackBtn type="admission" id={adm.id} slug={adm.slug} isTracking={tracked.admissionIds.has(String(adm.id))} onToggle={toggleAdmId} />
                </div>
              </MiniCard>
            ))}
          </SectionRow>

          {/* Tracked Items (logged-in) */}
          {token && (
            <div style={{ marginTop: '0.5rem', paddingTop: '1.5rem', borderTop: '2px solid #e8edf2' }}>
              {/* Stats row */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '0.75rem', marginBottom: '1.5rem' }}>
                {[
                  { label: 'Total Tracking', count: tracked.total, color: '#1e3a5f', bg: '#eff6ff', icon: Star },
                  { label: 'Jobs', count: tracked.jobs.length, color: '#1d4ed8', bg: '#dbeafe', icon: Briefcase },
                  { label: 'Admissions', count: tracked.admissions.length, color: '#6d28d9', bg: '#ede9fe', icon: GraduationCap },
                ].map(({ label, count, color, bg, icon: Icon }) => (
                  <div key={label} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.75rem', padding: '1rem 1.1rem', display: 'flex', alignItems: 'center', gap: '0.85rem', boxShadow: '0 1px 3px rgba(0,0,0,.05)' }}>
                    <div style={{ width: 40, height: 40, borderRadius: '0.6rem', background: bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <Icon size={18} strokeWidth={2} color={color} />
                    </div>
                    <div>
                      <div style={{ fontSize: '1.6rem', fontWeight: 800, color, lineHeight: 1 }}>{count}</div>
                      <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.2rem', fontWeight: 600 }}>{label}</div>
                    </div>
                  </div>
                ))}
              </div>

              {tracked.jobs.length > 0 && (
                <div style={{ marginBottom: '1.25rem' }}>
                  <div style={{ fontSize: '0.82rem', fontWeight: 700, marginBottom: '0.7rem', display: 'inline-flex', alignItems: 'center', gap: '0.4rem', paddingLeft: '0.6rem', borderLeft: '3px solid #1e3a5f', color: '#0f172a' }}><Briefcase size={13} strokeWidth={2} />Tracked Jobs</div>
                  {tracked.jobs.map((item) => (
                    <div key={item.id} style={{ background: '#fff', border: '1px solid #e2e8f0', borderLeft: '3px solid #1e3a5f', borderRadius: '0.6rem', padding: '0.85rem 1rem', marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.75rem', boxShadow: '0 1px 3px rgba(0,0,0,.04)', transition: 'box-shadow .15s' }}
                      onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,.08)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,.04)'; }}
                    >
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <h3 style={{ fontSize: '0.875rem', fontWeight: 700, marginBottom: '0.15rem' }}><Link to={`/jobs/${item.slug}`} style={{ color: '#0f172a', textDecoration: 'none' }}>{item.job_title}</Link></h3>
                        <div style={{ color: '#64748b', fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}><Landmark size={10} strokeWidth={2} />{item.organization}</div>
                        {item.application_end && <div style={{ fontSize: '0.73rem', color: '#b45309', fontWeight: 600, marginTop: '0.2rem', display: 'inline-flex', alignItems: 'center', gap: '0.2rem', background: '#fef3c7', padding: '0.1rem 0.4rem', borderRadius: '0.3rem' }}><Clock size={10} strokeWidth={2} />Deadline: {item.application_end}</div>}
                      </div>
                      <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexShrink: 0 }}>
                        <Link to={`/jobs/${item.slug}`} className="btn btn-outline btn-sm">View</Link>
                        <button onClick={() => untrackJob(item)} className="btn-tracking btn btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><Star size={11} strokeWidth={2} fill="currentColor" />Untrack</button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {tracked.admissions.length > 0 && (
                <div style={{ marginBottom: '1.25rem' }}>
                  <div style={{ fontSize: '0.82rem', fontWeight: 700, marginBottom: '0.7rem', display: 'inline-flex', alignItems: 'center', gap: '0.4rem', paddingLeft: '0.6rem', borderLeft: '3px solid #7c3aed', color: '#0f172a' }}><GraduationCap size={13} strokeWidth={2} />Tracked Admissions</div>
                  {tracked.admissions.map((item) => (
                    <div key={item.id} style={{ background: '#fff', border: '1px solid #e2e8f0', borderLeft: '3px solid #7c3aed', borderRadius: '0.6rem', padding: '0.85rem 1rem', marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.75rem', boxShadow: '0 1px 3px rgba(0,0,0,.04)', transition: 'box-shadow .15s' }}
                      onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,.08)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,.04)'; }}
                    >
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <h3 style={{ fontSize: '0.875rem', fontWeight: 700, marginBottom: '0.15rem' }}><Link to={`/admissions/${item.slug}`} style={{ color: '#0f172a', textDecoration: 'none' }}>{item.admission_name}</Link></h3>
                        <div style={{ color: '#64748b', fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}><Landmark size={10} strokeWidth={2} />{item.conducting_body}</div>
                        {item.application_end && <div style={{ fontSize: '0.73rem', color: '#b45309', fontWeight: 600, marginTop: '0.2rem', display: 'inline-flex', alignItems: 'center', gap: '0.2rem', background: '#fef3c7', padding: '0.1rem 0.4rem', borderRadius: '0.3rem' }}><Clock size={10} strokeWidth={2} />Deadline: {item.application_end}</div>}
                      </div>
                      <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexShrink: 0 }}>
                        <Link to={`/admissions/${item.slug}`} className="btn btn-outline btn-sm">View</Link>
                        <button onClick={() => untrackAdmission(item)} className="btn-tracking btn btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><Star size={11} strokeWidth={2} fill="currentColor" />Untrack</button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {tracked.jobs.length === 0 && tracked.admissions.length === 0 && (
                <div style={{ textAlign: 'center', padding: '2.5rem 1.5rem', color: '#64748b', background: '#fff', borderRadius: '0.85rem', border: '1.5px dashed #e2e8f0' }}>
                  <div style={{ width: 56, height: 56, background: '#f1f5f9', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 0.75rem' }}><Users size={26} strokeWidth={1.5} color="#94a3b8" /></div>
                  <p style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.35rem' }}>Nothing tracked yet</p>
                  <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1.25rem', maxWidth: 280, margin: '0 auto 1.25rem' }}>Track jobs and admissions to receive deadline reminders.</p>
                  <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                    <Link to="/jobs" className="btn btn-primary">Browse Jobs</Link>
                    <Link to="/admissions" className="btn btn-outline">Browse Admissions</Link>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
