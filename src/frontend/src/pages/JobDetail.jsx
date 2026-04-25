import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Landmark, Users, Link2, Download, BookOpen, Globe, Share2, CheckCircle, Bell, Banknote } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import EligibilityBanner from '../components/EligibilityBanner';
import PhaseCard from '../components/PhaseCard';
import PhaseDocTabs from '../components/PhaseDocTabs';
import DetailSkeleton from '../components/DetailSkeleton';

const fadeUp = { hidden: { opacity: 0, y: 14 }, show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] } } };
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } } };

export default function JobDetail() {
  const { slug } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [tracking, setTracking] = useState(false);
  const [profileComplete, setProfileComplete] = useState(false);
  const [eligibility, setEligibility] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const fetchUserData = async (jobId) => {
      api.get(`/jobs/${jobId}/track`).then((tr) => setTracking(tr.data.tracking)).catch(() => {});
      try {
        const pr = await api.get('/users/profile');
        const p = pr.data.profile || {};
        const done = Boolean(p.highest_qualification || p.category || p.date_of_birth);
        setProfileComplete(done);
        if (done) api.get(`/jobs/eligibility/${slug}`).then((er) => setEligibility(er.data)).catch(() => {});
      } catch { }
    };
    api.get(`/jobs/${slug}`).then((r) => {
      setJob(r.data);
      setLoading(false);
      if (token) { fetchUserData(r.data.id); }
    }).catch(() => { setLoading(false); });
  }, [slug, token]);

  const toggleTrack = async () => {
    if (!token) { navigate(`/login?next=/jobs/${slug}`); return; }
    try {
      if (tracking) await api.delete(`/jobs/${job.id}/track`);
      else await api.post(`/jobs/${job.id}/track`);
      setTracking(!tracking);
    } catch { }
  };

  if (loading) return <DetailSkeleton skeletonWidths={[120, 90, 80]} />;
  if (!job) return (
    <div style={{ textAlign: 'center', padding: '3rem' }}>
      <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.75rem' }}>Job not found</h2>
      <Link to="/jobs" className="btn btn-primary" style={{ display: 'inline-flex' }}>← Back to Jobs</Link>
    </div>
  );

  const feeLabels = { general: 'General / UR', obc: 'OBC-NCL', sc_st: 'SC / ST', ews: 'EWS', female: 'Female / PwBD' };
  const impLinks = job.application_details?.important_links || [];
  const vb = job.vacancy_breakdown || {};
  const vbPosts = vb.posts || [];

  return (
    <motion.div variants={stagger} initial="hidden" animate="show">
      <motion.div variants={fadeUp}>
        <Link to="/jobs" className="back-link">← Back to Jobs</Link>
      </motion.div>

      {/* Hero */}
      <motion.div variants={fadeUp} className="detail-hero hero-job">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            {job.qualification_level && <span style={{ background: 'rgba(255,255,255,.2)', color: '#fff', padding: '0.15rem 0.55rem', borderRadius: 9999, fontSize: '0.75rem', fontWeight: 600, display: 'inline-block', marginBottom: '0.5rem' }}>{job.qualification_level}</span>}
            <h1>{job.job_title}</h1>
            <div style={{ fontSize: '0.875rem', opacity: 0.88, display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Landmark size={14} strokeWidth={2} />{job.organization}{job.department && job.department !== job.organization ? ` · ${job.department}` : ''}</div>
            {job.total_vacancies && <div style={{ marginTop: '0.4rem', fontSize: '0.875rem', opacity: 0.9 }}>{job.total_vacancies.toLocaleString()} vacancies</div>}
          </div>
          <div>
            {job.status && <span className={`status-pill status-${job.status}`}>{job.status.charAt(0).toUpperCase() + job.status.slice(1)}</span>}
          </div>
        </div>
      </motion.div>

      {/* Action bar */}
      <div className="action-bar">
        <button onClick={toggleTrack} className="share-btn" style={tracking ? { background: '#fef3c7', color: '#92400e', borderColor: '#fde68a' } : { background: '#dbeafe', color: '#1e40af', borderColor: '#bfdbfe' }}>
          {tracking ? <><Bell size={14} strokeWidth={2} fill="currentColor" /> Tracking — Remove</> : <><Bell size={14} strokeWidth={2} /> Track for Reminders</>}
        </button>
        {job.source_url && <a href={job.source_url} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}><Globe size={13} strokeWidth={2} />Official Website</a>}
        {job.application_details?.application_link && <a href={job.application_details.application_link} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ background: '#2563eb', color: '#fff', borderColor: '#2563eb' }}>Apply Online →</a>}
        <button onClick={() => navigator.share?.({ title: job.job_title, url: globalThis.location.href }).catch(() => {})} className="share-btn" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}><Share2 size={13} strokeWidth={2} />Share</button>
      </div>

      {/* Eligibility */}
      <EligibilityBanner eligibility={eligibility} profileComplete={profileComplete} token={token} slug={slug} loginPrefix="jobs" />

      {/* Key Dates */}
      <div className="detail-grid">
        {[['Notification Date', job.notification_date], ['Apply From', job.application_start], ['Last Date to Apply', job.application_end], ['Exam Start', job.exam_start], ['Exam End', job.exam_end], ['Result Date', job.result_date]].filter(([, v]) => v).map(([label, value]) => (
          <div key={label} className="detail-item">
            <div className="label">{label}</div>
            <div className={`value${label === 'Last Date to Apply' && job.status === 'active' ? ' urgent' : ''}`}>{value}</div>
          </div>
        ))}
        {job.salary_initial && (
          <div className="detail-item">
            <div className="label">Pay Scale</div>
            <div className="value">₹{job.salary_initial.toLocaleString()}{job.salary_max ? ` – ₹${job.salary_max.toLocaleString()}` : ''}</div>
          </div>
        )}
      </div>

      {/* Description */}
      {job.description && <div className="detail-section"><h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><BookOpen size={16} strokeWidth={2} />About This Recruitment</h2><div dangerouslySetInnerHTML={{ __html: job.description }} style={{ fontSize: '0.9rem', color: '#334155', lineHeight: 1.65 }} /></div>}

      {/* Eligibility criteria */}
      {job.eligibility && (job.eligibility.min_qualification || job.eligibility.age_limit || job.eligibility.qualification_details) && (
        <div className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><CheckCircle size={16} strokeWidth={2} />Eligibility Criteria</h2>
          {job.eligibility.min_qualification && <p><strong>Minimum Qualification:</strong> {job.eligibility.min_qualification}</p>}
          {job.eligibility.age_limit && (() => { const a = job.eligibility.age_limit; return <p style={{ marginTop: '0.4rem' }}><strong>Age Limit:</strong> {a.min && a.max ? `${a.min} – ${a.max} years` : ''}{a.cutoff_date ? ` (as on ${a.cutoff_date})` : ''}</p>; })()}
          {job.eligibility.qualification_details && <p style={{ marginTop: '0.4rem' }}>{job.eligibility.qualification_details}</p>}
        </div>
      )}

      {/* Vacancy Breakdown */}
      {(vb.total || vb.UR || vb.SC) && (
        <div className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Users size={16} strokeWidth={2} />Vacancy Breakdown</h2>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.5rem' }}>
            {['total', 'UR', 'OBC', 'EWS', 'SC', 'ST', 'PWD', 'male', 'female'].filter((c) => vb[c]).map((cat) => (
              <div key={cat} style={{ background: cat === 'total' ? '#dbeafe' : '#f1f5f9', borderRadius: '0.35rem', padding: '0.35rem 0.65rem', textAlign: 'center', minWidth: 54 }}>
                <div style={{ fontSize: '0.9rem', fontWeight: 700 }}>{(vb[cat] || 0).toLocaleString()}</div>
                <div style={{ fontSize: '0.66rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{cat}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Posts */}
      {vbPosts.length > 0 && vbPosts[0]?.post_name && (
        <div className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Users size={16} strokeWidth={2} />Posts &amp; Vacancies</h2>
          {vbPosts.map((post, i) => {
            const pv = post.postwise_vacancy || {};
            return (
              <div key={post.post_name || i} style={{ border: '1px solid #e2e8f0', borderRadius: '0.5rem', marginBottom: '0.85rem', overflow: 'hidden' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.6rem 0.95rem', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', flexWrap: 'wrap', gap: '0.35rem' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>{post.post_name}</span>
                  {pv.total && <span style={{ background: '#dbeafe', color: '#1e40af', fontSize: '0.78rem', fontWeight: 700, padding: '0.15rem 0.55rem', borderRadius: 9999 }}>{(pv.total).toLocaleString()} posts</span>}
                </div>
                <div style={{ padding: '0.75rem 0.95rem' }}>
                  {Object.keys(pv).length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.35rem' }}>
                      {['UR', 'OBC', 'EWS', 'SC', 'ST', 'PWD', 'male', 'female'].filter((c) => pv[c]).map((cat) => (
                        <div key={cat} style={{ background: '#f1f5f9', borderRadius: '0.35rem', padding: '0.35rem 0.65rem', textAlign: 'center', minWidth: 54 }}>
                          <div style={{ fontSize: '0.9rem', fontWeight: 700 }}>{pv[cat]}</div>
                          <div style={{ fontSize: '0.66rem', color: '#64748b', textTransform: 'uppercase' }}>{cat}</div>
                        </div>
                      ))}
                    </div>
                  )}
                  {post.selection_process?.map((step, si) => <PhaseCard key={typeof step === 'object' ? (step.name || si) : si} step={step} />)}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Selection Process (if no post_name in posts) */}
      {vbPosts.length > 0 && !vbPosts[0]?.post_name && (
        <div className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><CheckCircle size={16} strokeWidth={2} />Selection Process</h2>
          {vbPosts.map((step, si) => <PhaseCard key={typeof step === 'object' ? (step.name || si) : si} step={step} />)}
        </div>
      )}

      {/* Application Fee */}
      {job.fee && Object.keys(job.fee).length > 0 && (
        <div className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Banknote size={16} strokeWidth={2} />Application Fee</h2>
          <table className="fee-table">
            <thead><tr><th>Category</th><th>Fee</th></tr></thead>
            <tbody>
              {['general', 'obc', 'sc_st', 'ews', 'female'].filter((k) => k in job.fee).map((k) => (
                <tr key={k}><td>{feeLabels[k]}</td><td>{job.fee[k] === 0 ? 'Free' : `₹${job.fee[k]}`}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Important Links */}
      {impLinks.length > 0 && (
        <div className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Link2 size={16} strokeWidth={2} />Important Links</h2>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {impLinks.filter((l) => (typeof l === 'object' ? l.url : l)).map((link) => {
              const url = typeof link === 'object' ? link.url : link;
              const text = typeof link === 'object' ? (link.text || url) : url;
              const ltype = typeof link === 'object' ? (link.type || '') : '';
              const styles = {
                apply_online: { background: '#2563eb', color: '#fff', borderColor: '#2563eb' },
                download_notification: { background: '#7c3aed', color: '#fff', borderColor: '#7c3aed' },
                syllabus: { background: '#0891b2', color: '#fff', borderColor: '#0891b2' },
              };
              const icons = { apply_online: <BookOpen size={13} strokeWidth={2} />, download_notification: <Download size={13} strokeWidth={2} />, syllabus: <BookOpen size={13} strokeWidth={2} />, official_website: <Globe size={13} strokeWidth={2} /> };
              return (
                <a key={url} href={url} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ ...styles[ltype] || {}, display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
                  {icons[ltype] || <Link2 size={13} strokeWidth={2} />} {text}
                </a>
              );
            })}
          </div>
        </div>
      )}

      {/* Phase Documents */}
      <PhaseDocTabs admitCards={job.admit_cards || []} answerKeys={job.answer_keys || []} results={job.results || []} currentSlug="" />
    </motion.div>
  );
}
