import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Landmark, Link2, BookOpen, Globe, Share2, CheckCircle, Bell } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import EligibilityBanner from '../components/EligibilityBanner';
import PhaseDocTabs from '../components/PhaseDocTabs';
import DetailSkeleton from '../components/DetailSkeleton';

const fadeUp = { hidden: { opacity: 0, y: 14 }, show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] } } };
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } } };

export default function AdmissionDetail() {
  const { slug } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [admission, setAdmission] = useState(null);
  const [tracking, setTracking] = useState(false);
  const [profileComplete, setProfileComplete] = useState(false);
  const [eligibility, setEligibility] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUserData = async (admId) => {
      api.get(`/admissions/${admId}/track`).then((tr) => setTracking(tr.data.tracking)).catch(() => {});
      try {
        const pr = await api.get('/users/profile');
        const p = pr.data.profile || {};
        const done = Boolean(p.highest_qualification || p.category || p.date_of_birth);
        setProfileComplete(done);
        if (done) api.get(`/admissions/eligibility/${slug}`).then((er) => setEligibility(er.data)).catch(() => {});
      } catch { }
    };
    api.get(`/admissions/${slug}`).then((r) => {
      setAdmission(r.data);
      setLoading(false);
      if (token) { fetchUserData(r.data.id); }
    }).catch(() => setLoading(false));
  }, [slug, token]);

  const toggleTrack = async () => {
    if (!token) { navigate(`/login?next=/admissions/${slug}`); return; }
    try {
      if (tracking) await api.delete(`/admissions/${admission.id}/track`);
      else await api.post(`/admissions/${admission.id}/track`);
      setTracking(!tracking);
    } catch { }
  };

  if (loading) return <DetailSkeleton skeletonWidths={[120, 90, 80]} />;
  if (!admission) return (
    <div style={{ textAlign: 'center', padding: '3rem' }}>
      <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.75rem' }}>Admission not found</h2>
      <Link to="/admissions" className="btn btn-primary" style={{ display: 'inline-flex' }}>← Back to Admissions</Link>
    </div>
  );

  const impLinks = admission.application_details?.important_links || [];
  const feeLabels = { general: 'General / UR', obc: 'OBC-NCL', sc_st: 'SC / ST', ews: 'EWS', female: 'Female / PwBD' };

  return (
    <motion.div variants={stagger} initial="hidden" animate="show">
      <motion.div variants={fadeUp}>
        <Link to="/admissions" className="back-link">← Back to Admissions</Link>
      </motion.div>

      <motion.div variants={fadeUp} className="detail-hero hero-admission">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            {admission.admission_type && <span style={{ background: 'rgba(255,255,255,.2)', color: '#fff', padding: '0.15rem 0.55rem', borderRadius: 9999, fontSize: '0.75rem', fontWeight: 600, display: 'inline-block', marginBottom: '0.5rem' }}>{admission.admission_type.toUpperCase()}</span>}
            <h1>{admission.admission_name}</h1>
            <div style={{ fontSize: '0.875rem', opacity: 0.88, display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Landmark size={14} strokeWidth={2} />{admission.conducting_body}</div>
          </div>
          {admission.status && <span className={`status-pill status-${admission.status}`}>{admission.status}</span>}
        </div>
      </motion.div>

      <div className="action-bar">
        <button onClick={toggleTrack} className="share-btn" style={tracking ? { background: '#fef3c7', color: '#92400e', borderColor: '#fde68a' } : { background: '#ede9fe', color: '#5b21b6', borderColor: '#ddd6fe' }}>
          {tracking ? <><Bell size={14} strokeWidth={2} fill="currentColor" /> Tracking — Remove</> : <><Bell size={14} strokeWidth={2} /> Track for Reminders</>}
        </button>
        {admission.source_url && <a href={admission.source_url} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}><Globe size={13} strokeWidth={2} />Official Website</a>}
        {admission.application_details?.application_link && <a href={admission.application_details.application_link} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ background: '#7c3aed', color: '#fff', borderColor: '#7c3aed' }}>Apply Online →</a>}
      </div>

      <EligibilityBanner token={token} profileComplete={profileComplete} eligibility={eligibility} slug={slug} loginPrefix="admissions" />

      {/* Key Dates */}
      <div className="detail-grid">
        {[['Application Start', admission.application_start], ['Last Date to Apply', admission.application_end], ['Exam Date', admission.exam_start], ['Result Date', admission.result_date], ['Counselling Start', admission.counselling_start]].filter(([, v]) => v).map(([label, value]) => (
          <div key={label} className="detail-item">
            <div className="label">{label}</div>
            <div className={`value${label === 'Last Date to Apply' && admission.status === 'active' ? ' urgent' : ''}`}>{value}</div>
          </div>
        ))}
      </div>

      {admission.description && <div className="detail-section"><h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><BookOpen size={16} strokeWidth={2} />About This Admission</h2><div dangerouslySetInnerHTML={{ __html: admission.description }} style={{ fontSize: '0.9rem', color: '#334155', lineHeight: 1.65 }} /></div>}

      {admission.eligibility && (admission.eligibility.min_qualification || admission.eligibility.age_limit) && (
        <div className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><CheckCircle size={16} strokeWidth={2} />Eligibility Criteria</h2>
          {admission.eligibility.min_qualification && <p><strong>Minimum Qualification:</strong> {admission.eligibility.min_qualification}</p>}
          {admission.eligibility.age_limit && (() => { const a = admission.eligibility.age_limit; return <p style={{ marginTop: '0.4rem' }}><strong>Age Limit:</strong> {a.min && a.max ? `${a.min} – ${a.max} years` : ''}</p>; })()}
        </div>
      )}

      {admission.fee && Object.keys(admission.fee).length > 0 && (
        <div className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Star size={16} strokeWidth={2} />Application Fee</h2>
          <table className="fee-table">
            <thead><tr><th>Category</th><th>Fee</th></tr></thead>
            <tbody>
              {['general', 'obc', 'sc_st', 'ews', 'female'].filter((k) => k in admission.fee).map((k) => (
                <tr key={k}><td>{feeLabels[k]}</td><td>{admission.fee[k] === 0 ? 'Free' : `₹${admission.fee[k]}`}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {impLinks.length > 0 && (
        <div className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Link2 size={16} strokeWidth={2} />Important Links</h2>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {impLinks.filter((l) => (typeof l === 'object' ? l.url : l)).map((link) => {
              const url = typeof link === 'object' ? link.url : link;
              const text = typeof link === 'object' ? (link.text || url) : url;
              return <a key={url} href={url} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}><Link2 size={13} strokeWidth={2} />{text}</a>;
            })}
          </div>
        </div>
      )}

      <PhaseDocTabs admitCards={admission.admit_cards || []} answerKeys={admission.answer_keys || []} results={admission.results || []} currentSlug="" />
    </motion.div>
  );
}
