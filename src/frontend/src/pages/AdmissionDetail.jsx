import PropTypes from 'prop-types';
import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Search, AlertTriangle, CheckCircle, XCircle, Landmark, Link2, BookOpen, Globe, Share2, Folder, Star } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';

function EligBanner({ token, profileComplete, eligibility, slug }) {
  if (!token) return (
    <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '0.5rem', padding: '1rem 1.25rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
      <Search size={18} strokeWidth={2} />
      <div style={{ flex: 1 }}><div style={{ fontWeight: 600, fontSize: '0.9rem' }}>Check Your Eligibility</div><div style={{ fontSize: '0.8rem', color: '#64748b' }}>Login and complete your profile to see if you qualify.</div></div>
      <Link to={`/login?next=/admissions/${slug}`} className="btn btn-primary btn-sm">Login to Check</Link>
    </div>
  );
  if (!profileComplete) return (
    <div style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '0.5rem', padding: '1rem 1.25rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
      <AlertTriangle size={18} strokeWidth={2} color="#92400e" />
      <div style={{ flex: 1 }}><div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#92400e' }}>Profile Incomplete</div><div style={{ fontSize: '0.8rem', color: '#a16207' }}>Complete your profile to check eligibility.</div></div>
      <Link to="/profile" className="btn btn-sm" style={{ background: '#fef3c7', color: '#92400e', border: '1px solid #fde68a' }}>Complete Profile</Link>
    </div>
  );
  if (!eligibility) return null;
  const cfg = {
    eligible: { bg: '#f0fdf4', border: '#bbf7d0', Icon: CheckCircle, color: '#166534', label: 'You are Eligible' },
    partially_eligible: { bg: '#fffbeb', border: '#fde68a', Icon: AlertTriangle, color: '#92400e', label: 'Partially Eligible' },
    not_eligible: { bg: '#fef2f2', border: '#fecaca', Icon: XCircle, color: '#991b1b', label: 'Not Eligible' },
  }[eligibility.status];
  if (!cfg) return null;
  return (
    <div style={{ background: cfg.bg, border: `1px solid ${cfg.border}`, borderRadius: '0.5rem', padding: '1rem 1.25rem', marginBottom: '1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: eligibility.reasons?.length ? '0.6rem' : 0 }}>
        {(() => { const Icon = cfg.Icon; return <Icon size={18} strokeWidth={2} color={cfg.color} />; })()}
        <span style={{ fontWeight: 700, fontSize: '0.95rem', color: cfg.color }}>{cfg.label}</span>
      </div>
      {eligibility.reasons?.length > 0 && <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>{eligibility.reasons.map((r) => <li key={r} style={{ fontSize: '0.82rem', color: cfg.color }}>{r}</li>)}</ul>}
    </div>
  );
}

EligBanner.propTypes = {
  token: PropTypes.string,
  profileComplete: PropTypes.bool.isRequired,
  eligibility: PropTypes.shape({ status: PropTypes.string, reasons: PropTypes.arrayOf(PropTypes.string) }),
  slug: PropTypes.string.isRequired,
};
EligBanner.defaultProps = { token: null, eligibility: null };

export default function AdmissionDetail() {
  const { slug } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [admission, setAdmission] = useState(null);
  const [tracking, setTracking] = useState(false);
  const [profileComplete, setProfileComplete] = useState(false);
  const [eligibility, setEligibility] = useState(null);
  const [loading, setLoading] = useState(true);
  const [docTab, setDocTab] = useState('admit');

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

  if (loading) return <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>Loading...</div>;
  if (!admission) return <div style={{ textAlign: 'center', padding: '3rem' }}><h2>404 — Admission not found</h2><Link to="/admissions" className="btn btn-primary" style={{ marginTop: '1rem', display: 'inline-flex' }}>Back to Admissions</Link></div>;

  const hasAdmitCards = admission.admit_cards?.length > 0;
  const hasAnswerKeys = admission.answer_keys?.length > 0;
  const hasResults = admission.results?.length > 0;
  const impLinks = admission.application_details?.important_links || [];
  const feeLabels = { general: 'General / UR', obc: 'OBC-NCL', sc_st: 'SC / ST', ews: 'EWS', female: 'Female / PwBD' };

  return (
    <div>
      <Link to="/admissions" className="back-link">← Back to Admissions</Link>

      <div className="detail-hero hero-admission">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            {admission.admission_type && <span style={{ background: 'rgba(255,255,255,.2)', color: '#fff', padding: '0.15rem 0.55rem', borderRadius: 9999, fontSize: '0.75rem', fontWeight: 600, display: 'inline-block', marginBottom: '0.5rem' }}>{admission.admission_type.toUpperCase()}</span>}
            <h1>{admission.admission_name}</h1>
            <div style={{ fontSize: '0.875rem', opacity: 0.88, display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Landmark size={14} strokeWidth={2} />{admission.conducting_body}</div>
          </div>
          {admission.status && <span className={`status-pill status-${admission.status}`}>{admission.status}</span>}
        </div>
      </div>

      <div className="action-bar">
        <button onClick={toggleTrack} className="share-btn" style={tracking ? { background: '#fef3c7', color: '#92400e', borderColor: '#fde68a' } : { background: '#ede9fe', color: '#5b21b6', borderColor: '#ddd6fe' }}>
          {tracking ? <><Star size={14} strokeWidth={2} fill="currentColor" /> Tracking — Remove</> : <><Star size={14} strokeWidth={2} /> Track for Reminders</>}
        </button>
        {admission.source_url && <a href={admission.source_url} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}><Globe size={13} strokeWidth={2} />Official Website</a>}
        {admission.application_details?.application_link && <a href={admission.application_details.application_link} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ background: '#7c3aed', color: '#fff', borderColor: '#7c3aed' }}>Apply Online →</a>}
      </div>

      <EligBanner token={token} profileComplete={profileComplete} eligibility={eligibility} slug={slug} />

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

      {(hasAdmitCards || hasAnswerKeys || hasResults) && (
        <div className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Folder size={16} strokeWidth={2} />Phase Documents</h2>
          <div className="doc-tabs-bar">
            {hasAdmitCards && <button className={`doc-tab-btn${docTab === 'admit' ? ' active' : ''}`} onClick={() => setDocTab('admit')}>Admit Cards ({admission.admit_cards.length})</button>}
            {hasAnswerKeys && <button className={`doc-tab-btn${docTab === 'answer' ? ' active' : ''}`} onClick={() => setDocTab('answer')}>Answer Keys ({admission.answer_keys.length})</button>}
            {hasResults && <button className={`doc-tab-btn${docTab === 'result' ? ' active' : ''}`} onClick={() => setDocTab('result')}>Results ({admission.results.length})</button>}
          </div>
          {docTab === 'admit' && hasAdmitCards && (
            <div style={{ paddingTop: '0.85rem' }}>
              {admission.admit_cards.map((card) => (
                <div key={card.id} style={{ border: '1px solid #bfdbfe', background: '#eff6ff', borderRadius: '0.5rem', padding: '0.8rem 1rem', marginBottom: '0.65rem', display: 'flex', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{card.title}</div>
                  <Link to={`/admit-cards/${card.slug}`} style={{ background: '#2563eb', color: '#fff', padding: '0.38rem 0.75rem', borderRadius: '0.5rem', fontSize: '0.78rem', fontWeight: 600, textDecoration: 'none' }}>View →</Link>
                </div>
              ))}
            </div>
          )}
          {docTab === 'answer' && hasAnswerKeys && (
            <div style={{ paddingTop: '0.85rem' }}>
              {admission.answer_keys.map((key) => (
                <div key={key.id} style={{ border: '1px solid #fde68a', background: '#fefce8', borderRadius: '0.5rem', padding: '0.8rem 1rem', marginBottom: '0.65rem', display: 'flex', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{key.title}</div>
                  <Link to={`/answer-keys/${key.slug}`} style={{ background: '#d97706', color: '#fff', padding: '0.38rem 0.75rem', borderRadius: '0.5rem', fontSize: '0.78rem', fontWeight: 600, textDecoration: 'none' }}>View →</Link>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
