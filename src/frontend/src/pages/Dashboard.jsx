import PropTypes from 'prop-types';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';

const STATUS_COLORS = {
  active: { bg: '#dcfce7', color: '#166534', label: 'Active' },
  upcoming: { bg: '#fef3c7', color: '#92400e', label: 'Soon' },
  closed: { bg: '#fee2e2', color: '#991b1b', label: 'Closed' },
};

function MiniStatus({ status }) {
  const s = STATUS_COLORS[status];
  if (!s) return null;
  return <span style={{ background: s.bg, color: s.color, fontSize: '0.65rem', fontWeight: 700, padding: '0.1rem 0.4rem', borderRadius: 9999, display: 'inline-block' }}>{s.label}</span>;
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

function MiniCard({ children, color, onClick }) {
  return (
    <button type="button" onClick={onClick} style={{
      background: '#fff', border: `1px solid #e2e8f0`, borderLeft: `3px solid ${color}`,
      borderRadius: '0.5rem', padding: '0.9rem 1rem', width: 210, minWidth: 210, maxWidth: 210,
      height: 140, flexShrink: 0, display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
      cursor: 'pointer', overflow: 'hidden', transition: 'box-shadow .15s, transform .15s', textAlign: 'left',
    }}
    onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,.08)'; e.currentTarget.style.transform = 'translateY(-1px)'; }}
    onMouseLeave={(e) => { e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'none'; }}
    >
      {children}
    </button>
  );
}

MiniCard.propTypes = {
  children: PropTypes.node.isRequired,
  color: PropTypes.string.isRequired,
  onClick: PropTypes.func.isRequired,
};

function TrackBtn({ type, id, slug, isTracking, onToggle }) {
  const { token } = useAuth();
  if (!token) {
    return <a href={`/login?next=/${type}s/${slug}`} onClick={(e) => { e.stopPropagation(); }} style={{ fontSize: '0.7rem', padding: '0.2rem 0.5rem', borderRadius: 9999, border: '1px solid #bfdbfe', background: '#eff6ff', color: '#1d4ed8', textDecoration: 'none' }}>☆</a>;
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
    <button onClick={track} className={isTracking ? 'btn-tracking btn btn-sm' : 'btn btn-outline btn-sm'} style={{ fontSize: '0.7rem', padding: '0.2rem 0.5rem' }}>
      {isTracking ? '★' : '☆'}
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

function SectionRow({ title, href, children }) {
  return (
    <div style={{ marginBottom: '2rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#1e293b', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>{title}</div>
        <Link to={href} style={{ fontSize: '0.8rem', fontWeight: 600, color: '#2563eb', whiteSpace: 'nowrap', padding: '0.25rem 0.6rem', border: '1px solid #e2e8f0', borderRadius: '0.35rem' }}>View All →</Link>
      </div>
      <div className="h-scroll">{children}</div>
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

  useEffect(() => {
    const params = { limit: 12, offset: 0 };
    Promise.all([
      api.get('/jobs', { params }).catch(() => ({ data: { data: [] } })),
      api.get('/admissions', { params }).catch(() => ({ data: { data: [] } })),
      api.get('/admit-cards', { params }).catch(() => ({ data: { data: [] } })),
      api.get('/answer-keys', { params }).catch(() => ({ data: { data: [] } })),
      api.get('/results', { params }).catch(() => ({ data: { data: [] } })),
      api.get('/exam-reminders').catch(() => ({ data: { data: [] } })),
      api.get('/organizations', { params: { limit: 50 } }).catch(() => ({ data: { data: [] } })),
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
    if (next.has(String(id))) next.delete(String(id)); else next.add(String(id));
    return { ...prev, jobIds: next };
  });
  const toggleAdmId = (id) => setTracked((prev) => {
    const next = new Set(prev.admissionIds);
    if (next.has(String(id))) next.delete(String(id)); else next.add(String(id));
    return { ...prev, admissionIds: next };
  });

  return (
    <div>
      {/* Hero */}
      <div style={{ background: 'linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%)', color: '#fff', padding: '1.5rem 1.5rem 1.3rem', borderRadius: '0.75rem', marginBottom: '1.5rem', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', top: -30, right: -30, width: 180, height: 180, background: 'rgba(255,255,255,.05)', borderRadius: '50%', pointerEvents: 'none' }} />
        <h1 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: '0.2rem' }}>📊 Dashboard</h1>
        <p style={{ fontSize: '0.875rem', opacity: 0.85 }}>Latest government jobs, admissions, admit cards, answer keys and results</p>
      </div>

      {/* Org strip */}
      {orgs.length > 0 && (
        <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.75rem', padding: '0.8rem 1rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.7rem' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.07em' }}>🏛 Organizations</span>
            <span style={{ fontSize: '0.68rem', fontWeight: 700, background: '#f1f5f9', color: '#64748b', borderRadius: 9999, padding: '0.1rem 0.45rem' }}>{orgs.length}</span>
          </div>
          <div style={{ display: 'flex', gap: '0.55rem', overflowX: 'auto', scrollbarWidth: 'none', paddingBottom: '0.15rem' }}>
            {orgs.map((org) => {
              const isTracking = trackedOrgIds.has(String(org.id));
              const displayName = org.short_name || org.name;
              const toggleOrg = async (e) => {
                e.preventDefault();
                if (!token) { navigate('/login?next=/'); return; }
                try {
                  if (isTracking) await api.delete(`/organizations/${org.id}/track`);
                  else await api.post(`/organizations/${org.id}/track`);
                  setTrackedOrgIds((prev) => { const next = new Set(prev); if (isTracking) next.delete(String(org.id)); else next.add(String(org.id)); return next; });
                } catch { }
              };
              return (
                <div key={org.id} style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: '0.4rem', flexShrink: 0, width: 120, background: isTracking ? '#fffbeb' : '#f8fafc', border: `1.5px solid ${isTracking ? '#f59e0b' : '#e2e8f0'}`, borderRadius: '0.6rem', padding: '0.7rem 0.6rem 0.55rem', transition: 'border-color .15s', cursor: 'auto' }}>
                  {org.logo_url
                    ? <img src={org.logo_url} alt={displayName} style={{ width: 42, height: 42, borderRadius: '0.4rem', objectFit: 'cover' }} />
                    : <div style={{ width: 42, height: 42, borderRadius: '0.4rem', background: isTracking ? 'linear-gradient(135deg,#92400e,#f59e0b)' : 'linear-gradient(135deg,#1e3a5f,#2563eb)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.1rem', fontWeight: 800 }}>{displayName[0]?.toUpperCase()}</div>
                  }
                  <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#334155', textAlign: 'center', lineHeight: 1.3, width: '100%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={org.name}>{displayName}</span>
                  <button onClick={toggleOrg} style={{ fontSize: '0.6rem', fontWeight: 700, borderRadius: '0.35rem', padding: '0.2rem 0.5rem', border: `1px solid ${isTracking ? '#f59e0b' : '#e2e8f0'}`, background: isTracking ? '#fef3c7' : '#fff', color: isTracking ? '#92400e' : '#64748b', cursor: 'pointer', whiteSpace: 'nowrap', width: '100%' }}>
                    {isTracking ? '★ Following' : '☆ Follow'}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 4fr', gap: '1.25rem', alignItems: 'start' }} className="page-grid">

        {/* Upcoming Exams Sidebar */}
        <aside style={{ position: 'sticky', top: '5rem' }}>
          <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.75rem', overflow: 'hidden' }}>
            <div style={{ background: '#1e3a5f', color: '#fff', padding: '0.7rem 1rem', fontSize: '0.875rem', fontWeight: 700 }}>⏰ Upcoming Exams</div>
            <div>
              {data.exams.length === 0 && <div style={{ padding: '0.75rem', textAlign: 'center', color: '#94a3b8', fontSize: '0.78rem' }}>No upcoming exams</div>}
              {data.exams.map((exam) => {
                const isJob = exam.type === 'job' || exam.parent_type === 'job';
                const url = isJob ? `/jobs/${exam.slug || exam.parent_slug}` : `/admissions/${exam.slug || exam.parent_slug}`;
                return (
                  <button type="button" key={exam.id} onClick={() => navigate(url)} style={{ display: 'block', width: '100%', textAlign: 'left', background: 'none', border: 'none', borderBottom: '1px solid #f1f5f9', padding: '0.6rem 0.85rem', cursor: 'pointer', transition: 'background .12s' }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = '#f8fafc'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = ''; }}>
                    <div style={{ color: '#1e293b', fontWeight: 600, fontSize: '0.78rem', lineHeight: 1.35 }}>{exam.title}</div>
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', color: '#64748b', fontSize: '0.7rem', fontWeight: 500, marginTop: '0.2rem' }}>
                      📅 {exam.exam_start || 'TBA'} <ExamsDaysBadge days={exam.days_remaining} />
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </aside>

        {/* Main content */}
        <div>
          {/* Jobs */}
          <SectionRow title="💼 Latest Jobs" href="/jobs">
            {data.jobs.length === 0 && <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>No jobs available.</p>}
            {data.jobs.map((job) => (
              <MiniCard key={job.id} color="#1e3a5f" onClick={() => navigate(`/jobs/${job.slug}`)}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.3rem', marginBottom: '0.2rem' }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: 700, lineHeight: 1.35, flex: 1, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>{job.job_title}</div>
                    <MiniStatus status={job.status} />
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.2rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>🏛 {job.organization}</div>
                  {job.application_end && <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>⏰ {job.application_end}</div>}
                  {job.total_vacancies && <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>{job.total_vacancies.toLocaleString()} vacancies</div>}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.4rem', flexWrap: 'wrap', gap: '0.3rem' }}>
                  {!token || !profileComplete
                    ? <Link to="/profile" onClick={(e) => e.stopPropagation()} style={{ fontSize: '0.65rem', padding: '0.15rem 0.4rem', border: '1px solid #e2e8f0', borderRadius: '0.35rem', background: '#fff', color: '#64748b', textDecoration: 'none' }}>🔍 Eligibility</Link>
                    : <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>checking…</span>}
                  <TrackBtn type="job" id={job.id} slug={job.slug} isTracking={tracked.jobIds.has(String(job.id))} onToggle={toggleJobId} />
                </div>
              </MiniCard>
            ))}
          </SectionRow>

          {/* Admit Cards */}
          <SectionRow title="🪪 Latest Admit Cards" href="/admit-cards">
            {data.admit_cards.length === 0 && <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>No admit cards available.</p>}
            {data.admit_cards.map((card) => (
              <MiniCard key={card.id} color="#2563eb" onClick={() => navigate(`/admit-cards/${card.slug}`)}>
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
          <SectionRow title="📝 Latest Answer Keys" href="/answer-keys">
            {data.answer_keys.length === 0 && <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>No answer keys available.</p>}
            {data.answer_keys.map((key) => (
              <MiniCard key={key.id} color="#d97706" onClick={() => navigate(`/answer-keys/${key.slug}`)}>
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
          <SectionRow title="🏆 Latest Results" href="/results">
            {data.results.length === 0 && <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>No results available.</p>}
            {data.results.map((res) => (
              <MiniCard key={res.id} color="#16a34a" onClick={() => navigate(`/results/${res.slug}`)}>
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
          <SectionRow title="🎓 Latest Admissions" href="/admissions">
            {data.admissions.length === 0 && <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>No admissions available.</p>}
            {data.admissions.map((adm) => (
              <MiniCard key={adm.id} color="#7c3aed" onClick={() => navigate(`/admissions/${adm.slug}`)}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.3rem', marginBottom: '0.2rem' }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: 700, lineHeight: 1.35, flex: 1, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>{adm.admission_name}</div>
                    <MiniStatus status={adm.status} />
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>🏛 {adm.conducting_body}</div>
                  {adm.application_end && <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>⏰ {adm.application_end}</div>}
                  {adm.admission_type && <span style={{ background: '#ede9fe', color: '#5b21b6', padding: '0.1rem 0.4rem', borderRadius: 9999, fontSize: '0.68rem', fontWeight: 700 }}>{adm.admission_type.toUpperCase()}</span>}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.4rem', flexWrap: 'wrap', gap: '0.3rem' }}>
                  {!token || !profileComplete
                    ? <Link to="/profile" onClick={(e) => e.stopPropagation()} style={{ fontSize: '0.65rem', padding: '0.15rem 0.4rem', border: '1px solid #e2e8f0', borderRadius: '0.35rem', background: '#fff', color: '#64748b', textDecoration: 'none' }}>🔍 Eligibility</Link>
                    : <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>checking…</span>}
                  <TrackBtn type="admission" id={adm.id} slug={adm.slug} isTracking={tracked.admissionIds.has(String(adm.id))} onToggle={toggleAdmId} />
                </div>
              </MiniCard>
            ))}
          </SectionRow>

          {/* Tracked Items (logged-in) */}
          {token && (
            <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '2px solid #e2e8f0' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '0.75rem', marginBottom: '1.35rem' }}>
                {[['Tracking', tracked.total], ['Jobs', tracked.jobs.length], ['Admissions', tracked.admissions.length]].map(([label, count]) => (
                  <div key={label} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.5rem', padding: '0.9rem', textAlign: 'center' }}>
                    <div style={{ fontSize: '1.85rem', fontWeight: 800, color: '#1e3a5f' }}>{count}</div>
                    <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '0.15rem', fontWeight: 500 }}>{label}</div>
                  </div>
                ))}
              </div>

              {tracked.jobs.length > 0 && (
                <>
                  <div style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>💼 Tracked Jobs</div>
                  {tracked.jobs.map((item) => (
                    <div key={item.id} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.5rem', padding: '0.85rem 1rem', marginBottom: '0.6rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem' }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.15rem' }}><Link to={`/jobs/${item.slug}`} style={{ color: '#1e293b' }}>{item.job_title}</Link></h3>
                        <div style={{ color: '#64748b', fontSize: '0.8rem' }}>{item.organization}</div>
                        {item.application_end && <div style={{ fontSize: '0.77rem', color: '#b45309', fontWeight: 600, marginTop: '0.2rem' }}>⏰ {item.application_end}</div>}
                      </div>
                      <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexShrink: 0, flexWrap: 'wrap' }}>
                        <span style={{ background: '#dbeafe', color: '#1e40af', padding: '0.15rem 0.5rem', borderRadius: 9999, fontSize: '0.7rem', fontWeight: 700 }}>Job</span>
                        <Link to={`/jobs/${item.slug}`} className="btn btn-outline btn-sm">View →</Link>
                        <button onClick={() => { api.delete(`/jobs/${item.id}/track`).then(() => setTracked((p) => ({ ...p, jobs: p.jobs.filter((j) => j.id !== item.id), jobIds: new Set([...p.jobIds].filter((x) => x !== String(item.id))) }))).catch(() => {}); }} className="btn-tracking btn btn-sm">★ Untrack</button>
                      </div>
                    </div>
                  ))}
                </>
              )}

              {tracked.admissions.length > 0 && (
                <>
                  <div style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>🎓 Tracked Admissions</div>
                  {tracked.admissions.map((item) => (
                    <div key={item.id} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.5rem', padding: '0.85rem 1rem', marginBottom: '0.6rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem' }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.15rem' }}><Link to={`/admissions/${item.slug}`} style={{ color: '#1e293b' }}>{item.admission_name}</Link></h3>
                        <div style={{ color: '#64748b', fontSize: '0.8rem' }}>{item.conducting_body}</div>
                        {item.application_end && <div style={{ fontSize: '0.77rem', color: '#b45309', fontWeight: 600, marginTop: '0.2rem' }}>⏰ {item.application_end}</div>}
                      </div>
                      <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexShrink: 0, flexWrap: 'wrap' }}>
                        <span style={{ background: '#d1fae5', color: '#065f46', padding: '0.15rem 0.5rem', borderRadius: 9999, fontSize: '0.7rem', fontWeight: 700 }}>Admission</span>
                        <Link to={`/admissions/${item.slug}`} className="btn btn-outline btn-sm">View →</Link>
                        <button onClick={() => { api.delete(`/admissions/${item.id}/track`).then(() => setTracked((p) => ({ ...p, admissions: p.admissions.filter((a) => a.id !== item.id), admissionIds: new Set([...p.admissionIds].filter((x) => x !== String(item.id))) }))).catch(() => {}); }} className="btn-tracking btn btn-sm">★ Untrack</button>
                      </div>
                    </div>
                  ))}
                </>
              )}

              {tracked.jobs.length === 0 && tracked.admissions.length === 0 && (
                <div style={{ textAlign: 'center', padding: '2.5rem 1rem', color: '#64748b', background: '#f8fafc', borderRadius: '0.75rem', border: '1px dashed #e2e8f0' }}>
                  <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>👀</div>
                  <p style={{ fontSize: '0.975rem', fontWeight: 600, color: '#1e293b', marginBottom: '0.3rem' }}>No items tracked yet.</p>
                  <p style={{ fontSize: '0.875rem', marginBottom: '1.1rem' }}>Track jobs and admissions to get deadline reminders.</p>
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
