import PropTypes from 'prop-types';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Landmark, Users, Link2, Download, BookOpen, Globe, CheckCircle,
  Folder, GraduationCap, Briefcase,
} from 'lucide-react';

const fadeUp = { hidden: { opacity: 0, y: 14 }, show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] } } };

function PhaseCard({ step }) {
  if (typeof step !== 'object') return <div style={{ border: '1px solid #bfdbfe', background: '#eff6ff', borderRadius: '0.5rem', padding: '0.7rem 1rem', marginBottom: '0.85rem' }}><span style={{ fontWeight: 700, fontSize: '0.9rem' }}>{String(step)}</span></div>;
  const stype = step.type || '';
  const isDoc = stype === 'document';
  return (
    <div style={{ borderRadius: '0.5rem', marginBottom: '0.85rem', overflow: 'hidden', border: `1px solid ${isDoc ? '#bbf7d0' : '#bfdbfe'}`, background: isDoc ? '#f0fdf4' : '#eff6ff' }}>
      <div style={{ padding: '0.7rem 1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          {step.phase && <span style={{ background: isDoc ? '#16a34a' : '#2563eb', color: '#fff', fontSize: '0.7rem', fontWeight: 700, padding: '0.15rem 0.55rem', borderRadius: 9999 }}>Phase {step.phase}</span>}
          <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>{step.name || '—'}</span>
          {step.qualifying && <span className="meta-pill pill-green" style={{ fontSize: '0.72rem' }}>Qualifying Only</span>}
        </div>
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginTop: '0.3rem' }}>
          {step.mode && <span className="meta-pill pill-blue">{step.mode}</span>}
          {step.total_marks && <span className="meta-pill pill-purple">{step.total_marks} marks</span>}
          {step.duration_minutes && <span className="meta-pill pill-amber">{step.duration_minutes} min</span>}
          {step.negative_marking && <span className="meta-pill pill-red">–{step.negative_marking} per wrong</span>}
        </div>
      </div>
      {step.subjects?.length > 0 && (
        <table className="fee-table" style={{ marginTop: '0.6rem' }}>
          <thead><tr><th>Subject</th><th style={{ textAlign: 'right' }}>Questions</th><th style={{ textAlign: 'right' }}>Marks</th></tr></thead>
          <tbody>
            {step.subjects.map((sub) => <tr key={sub.name || sub.questions}><td>{sub.name || '—'}</td><td style={{ textAlign: 'right' }}>{sub.questions || '—'}</td><td style={{ textAlign: 'right' }}>{sub.marks || '—'}</td></tr>)}
          </tbody>
        </table>
      )}
    </div>
  );
}
PhaseCard.propTypes = { step: PropTypes.oneOfType([PropTypes.object, PropTypes.string]).isRequired };

function JobParent({ job, currentSlug, currentType }) {
  const [docTab, setDocTab] = useState('admit');
  const feeLabels = { general: 'General / UR', obc: 'OBC-NCL', sc_st: 'SC / ST', ews: 'EWS', female: 'Female / PwBD' };
  const impLinks = job.application_details?.important_links || [];
  const vb = job.vacancy_breakdown || {};
  const vbPosts = vb.posts || [];
  const hasAdmitCards = (job.admit_cards || []).length > 0;
  const hasAnswerKeys = (job.answer_keys || []).length > 0;
  const hasResults = (job.results || []).length > 0;

  return (
    <motion.div variants={fadeUp}>
      <div style={{ margin: '1.5rem 0 0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <div style={{ flex: 1, height: 1, background: '#e2e8f0' }} />
        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', display: 'flex', alignItems: 'center', gap: '0.3rem', whiteSpace: 'nowrap' }}><Briefcase size={12} strokeWidth={2} />Related Job Details</span>
        <div style={{ flex: 1, height: 1, background: '#e2e8f0' }} />
      </div>

      <div className="detail-hero hero-job" style={{ marginBottom: '0.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            {job.qualification_level && <span style={{ background: 'rgba(255,255,255,.2)', color: '#fff', padding: '0.15rem 0.55rem', borderRadius: 9999, fontSize: '0.75rem', fontWeight: 600, display: 'inline-block', marginBottom: '0.5rem' }}>{job.qualification_level}</span>}
            <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff', margin: 0 }}>{job.job_title}</h2>
            <div style={{ fontSize: '0.875rem', opacity: 0.88, display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.25rem' }}>
              <Landmark size={14} strokeWidth={2} />{job.organization}{job.department && job.department !== job.organization ? ` · ${job.department}` : ''}
            </div>
            {job.total_vacancies && <div style={{ marginTop: '0.35rem', fontSize: '0.875rem', opacity: 0.9 }}>{job.total_vacancies.toLocaleString()} vacancies</div>}
          </div>
          <div>
            {job.status && <span className={`status-pill status-${job.status}`}>{job.status.charAt(0).toUpperCase() + job.status.slice(1)}</span>}
          </div>
        </div>
      </div>

      <div className="action-bar" style={{ marginBottom: '0.75rem' }}>
        {job.source_url && <a href={job.source_url} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}><Globe size={13} strokeWidth={2} />Official Website</a>}
        {job.application_details?.application_link && <a href={job.application_details.application_link} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ background: '#2563eb', color: '#fff', borderColor: '#2563eb' }}>Apply Online →</a>}
      </div>

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

      {job.description && <div className="detail-section"><h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><BookOpen size={16} strokeWidth={2} />About This Recruitment</h2><div dangerouslySetInnerHTML={{ __html: job.description }} style={{ fontSize: '0.9rem', color: '#334155', lineHeight: 1.65 }} /></div>}

      {job.eligibility && (job.eligibility.min_qualification || job.eligibility.age_limit || job.eligibility.qualification_details) && (
        <div className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><CheckCircle size={16} strokeWidth={2} />Eligibility Criteria</h2>
          {job.eligibility.min_qualification && <p><strong>Minimum Qualification:</strong> {job.eligibility.min_qualification}</p>}
          {job.eligibility.age_limit && (() => { const a = job.eligibility.age_limit; return <p style={{ marginTop: '0.4rem' }}><strong>Age Limit:</strong> {a.min && a.max ? `${a.min} – ${a.max} years` : ''}{a.cutoff_date ? ` (as on ${a.cutoff_date})` : ''}</p>; })()}
          {job.eligibility.qualification_details && <p style={{ marginTop: '0.4rem' }}>{job.eligibility.qualification_details}</p>}
        </div>
      )}

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

      {vbPosts.length > 0 && vbPosts[0]?.post_name && (
        <div className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Users size={16} strokeWidth={2} />Posts &amp; Vacancies</h2>
          {vbPosts.map((post, i) => {
            const pv = post.postwise_vacancy || {};
            return (
              <div key={post.post_name || i} style={{ border: '1px solid #e2e8f0', borderRadius: '0.5rem', marginBottom: '0.85rem', overflow: 'hidden' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.6rem 0.95rem', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', flexWrap: 'wrap', gap: '0.35rem' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>{post.post_name}</span>
                  {pv.total && <span style={{ background: '#dbeafe', color: '#1e40af', fontSize: '0.78rem', fontWeight: 700, padding: '0.15rem 0.55rem', borderRadius: 9999 }}>{pv.total.toLocaleString()} posts</span>}
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

      {vbPosts.length > 0 && !vbPosts[0]?.post_name && (
        <div className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><CheckCircle size={16} strokeWidth={2} />Selection Process</h2>
          {vbPosts.map((step, si) => <PhaseCard key={typeof step === 'object' ? (step.name || si) : si} step={step} />)}
        </div>
      )}

      {job.fee && Object.keys(job.fee).length > 0 && (
        <div className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><CheckCircle size={16} strokeWidth={2} />Application Fee</h2>
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

      {(hasAdmitCards || hasAnswerKeys || hasResults) && (
        <div className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Folder size={16} strokeWidth={2} />Phase Documents</h2>
          <div className="doc-tabs-bar">
            {hasAdmitCards && <button className={`doc-tab-btn${docTab === 'admit' ? ' active' : ''}`} onClick={() => setDocTab('admit')}>Admit Cards ({job.admit_cards.length})</button>}
            {hasAnswerKeys && <button className={`doc-tab-btn${docTab === 'answer' ? ' active' : ''}`} onClick={() => setDocTab('answer')}>Answer Keys ({job.answer_keys.length})</button>}
            {hasResults && <button className={`doc-tab-btn${docTab === 'result' ? ' active' : ''}`} onClick={() => setDocTab('result')}>Results ({job.results.length})</button>}
          </div>
          {docTab === 'admit' && hasAdmitCards && (
            <div style={{ paddingTop: '0.85rem' }}>
              {job.admit_cards.map((c) => (
                <div key={c.id} style={{ border: '1px solid #bfdbfe', background: '#eff6ff', borderRadius: '0.5rem', padding: '0.8rem 1rem', marginBottom: '0.65rem', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <div><div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{c.title}</div>{(c.exam_start || c.exam_end) && <div style={{ fontSize: '0.8rem', color: '#b45309' }}>Exam: {c.exam_start || '?'} – {c.exam_end || '?'}</div>}</div>
                  {c.slug !== currentSlug && <Link to={`/admit-cards/${c.slug}`} style={{ background: '#2563eb', color: '#fff', padding: '0.38rem 0.75rem', borderRadius: '0.5rem', fontSize: '0.78rem', fontWeight: 600, textDecoration: 'none' }}>View →</Link>}
                  {c.slug === currentSlug && <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, padding: '0.38rem 0.75rem' }}>Current</span>}
                </div>
              ))}
            </div>
          )}
          {docTab === 'answer' && hasAnswerKeys && (
            <div style={{ paddingTop: '0.85rem' }}>
              {job.answer_keys.map((k) => (
                <div key={k.id} style={{ border: '1px solid #fde68a', background: '#fefce8', borderRadius: '0.5rem', padding: '0.8rem 1rem', marginBottom: '0.65rem', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{k.title}</div>
                  {k.slug !== currentSlug && <Link to={`/answer-keys/${k.slug}`} style={{ background: '#d97706', color: '#fff', padding: '0.38rem 0.75rem', borderRadius: '0.5rem', fontSize: '0.78rem', fontWeight: 600, textDecoration: 'none' }}>View →</Link>}
                  {k.slug === currentSlug && <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, padding: '0.38rem 0.75rem' }}>Current</span>}
                </div>
              ))}
            </div>
          )}
          {docTab === 'result' && hasResults && (
            <div style={{ paddingTop: '0.85rem' }}>
              {job.results.map((r) => (
                <div key={r.id} style={{ border: '1px solid #bbf7d0', background: '#f0fdf4', borderRadius: '0.5rem', padding: '0.8rem 1rem', marginBottom: '0.65rem', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{r.title}</div>
                  {r.slug !== currentSlug && <Link to={`/results/${r.slug}`} style={{ background: '#16a34a', color: '#fff', padding: '0.38rem 0.75rem', borderRadius: '0.5rem', fontSize: '0.78rem', fontWeight: 600, textDecoration: 'none' }}>View →</Link>}
                  {r.slug === currentSlug && <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, padding: '0.38rem 0.75rem' }}>Current</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
}
JobParent.propTypes = { job: PropTypes.object.isRequired, currentSlug: PropTypes.string.isRequired, currentType: PropTypes.string.isRequired };

function AdmissionParent({ admission, currentSlug, currentType }) {
  const [docTab, setDocTab] = useState('admit');
  const impLinks = admission.admission_details?.important_links || [];
  const hasAdmitCards = (admission.admit_cards || []).length > 0;
  const hasAnswerKeys = (admission.answer_keys || []).length > 0;
  const hasResults = (admission.results || []).length > 0;

  return (
    <motion.div variants={fadeUp}>
      <div style={{ margin: '1.5rem 0 0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <div style={{ flex: 1, height: 1, background: '#e2e8f0' }} />
        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', display: 'flex', alignItems: 'center', gap: '0.3rem', whiteSpace: 'nowrap' }}><GraduationCap size={12} strokeWidth={2} />Related Admission Details</span>
        <div style={{ flex: 1, height: 1, background: '#e2e8f0' }} />
      </div>

      <div className="detail-hero hero-admission" style={{ marginBottom: '0.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            {admission.stream && <span style={{ background: 'rgba(255,255,255,.2)', color: '#fff', padding: '0.15rem 0.55rem', borderRadius: 9999, fontSize: '0.75rem', fontWeight: 600, display: 'inline-block', marginBottom: '0.5rem' }}>{admission.stream}</span>}
            <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff', margin: 0 }}>{admission.admission_name}</h2>
            <div style={{ fontSize: '0.875rem', opacity: 0.88, display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.25rem' }}>
              <Landmark size={14} strokeWidth={2} />{admission.conducting_body}
            </div>
          </div>
          <div>
            {admission.status && <span className={`status-pill status-${admission.status}`}>{admission.status.charAt(0).toUpperCase() + admission.status.slice(1)}</span>}
          </div>
        </div>
      </div>

      <div className="action-bar" style={{ marginBottom: '0.75rem' }}>
        {admission.source_url && <a href={admission.source_url} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}><Globe size={13} strokeWidth={2} />Official Website</a>}
        {admission.admission_details?.application_link && <a href={admission.admission_details.application_link} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ background: '#7c3aed', color: '#fff', borderColor: '#7c3aed' }}>Apply Online →</a>}
      </div>

      <div className="detail-grid">
        {[['Apply From', admission.application_start], ['Last Date to Apply', admission.application_end], ['Exam Start', admission.exam_start], ['Exam End', admission.exam_end], ['Counselling Start', admission.counselling_start], ['Result Date', admission.result_date]].filter(([, v]) => v).map(([label, value]) => (
          <div key={label} className="detail-item">
            <div className="label">{label}</div>
            <div className={`value${label === 'Last Date to Apply' && admission.status === 'active' ? ' urgent' : ''}`}>{value}</div>
          </div>
        ))}
      </div>

      {admission.description && <div className="detail-section"><h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><BookOpen size={16} strokeWidth={2} />About This Admission</h2><div dangerouslySetInnerHTML={{ __html: admission.description }} style={{ fontSize: '0.9rem', color: '#334155', lineHeight: 1.65 }} /></div>}

      {admission.eligibility && Object.keys(admission.eligibility).length > 0 && (
        <div className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><CheckCircle size={16} strokeWidth={2} />Eligibility Criteria</h2>
          {admission.eligibility.min_qualification && <p><strong>Minimum Qualification:</strong> {admission.eligibility.min_qualification}</p>}
          {admission.eligibility.age_limit && (() => { const a = admission.eligibility.age_limit; return <p style={{ marginTop: '0.4rem' }}><strong>Age Limit:</strong> {a.min && a.max ? `${a.min} – ${a.max} years` : ''}{a.cutoff_date ? ` (as on ${a.cutoff_date})` : ''}</p>; })()}
          {admission.eligibility.qualification_details && <p style={{ marginTop: '0.4rem' }}>{admission.eligibility.qualification_details}</p>}
        </div>
      )}

      {admission.fee && Object.keys(admission.fee).length > 0 && (
        <div className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><CheckCircle size={16} strokeWidth={2} />Application Fee</h2>
          <table className="fee-table">
            <thead><tr><th>Category</th><th>Fee</th></tr></thead>
            <tbody>
              {Object.entries(admission.fee).map(([k, v]) => (
                <tr key={k}><td>{k}</td><td>{v === 0 ? 'Free' : `₹${v}`}</td></tr>
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
              {admission.admit_cards.map((c) => (
                <div key={c.id} style={{ border: '1px solid #bfdbfe', background: '#eff6ff', borderRadius: '0.5rem', padding: '0.8rem 1rem', marginBottom: '0.65rem', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <div><div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{c.title}</div>{(c.exam_start || c.exam_end) && <div style={{ fontSize: '0.8rem', color: '#b45309' }}>Exam: {c.exam_start || '?'} – {c.exam_end || '?'}</div>}</div>
                  {c.slug !== currentSlug && <Link to={`/admit-cards/${c.slug}`} style={{ background: '#2563eb', color: '#fff', padding: '0.38rem 0.75rem', borderRadius: '0.5rem', fontSize: '0.78rem', fontWeight: 600, textDecoration: 'none' }}>View →</Link>}
                  {c.slug === currentSlug && <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, padding: '0.38rem 0.75rem' }}>Current</span>}
                </div>
              ))}
            </div>
          )}
          {docTab === 'answer' && hasAnswerKeys && (
            <div style={{ paddingTop: '0.85rem' }}>
              {admission.answer_keys.map((k) => (
                <div key={k.id} style={{ border: '1px solid #fde68a', background: '#fefce8', borderRadius: '0.5rem', padding: '0.8rem 1rem', marginBottom: '0.65rem', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{k.title}</div>
                  {k.slug !== currentSlug && <Link to={`/answer-keys/${k.slug}`} style={{ background: '#d97706', color: '#fff', padding: '0.38rem 0.75rem', borderRadius: '0.5rem', fontSize: '0.78rem', fontWeight: 600, textDecoration: 'none' }}>View →</Link>}
                  {k.slug === currentSlug && <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, padding: '0.38rem 0.75rem' }}>Current</span>}
                </div>
              ))}
            </div>
          )}
          {docTab === 'result' && hasResults && (
            <div style={{ paddingTop: '0.85rem' }}>
              {admission.results.map((r) => (
                <div key={r.id} style={{ border: '1px solid #bbf7d0', background: '#f0fdf4', borderRadius: '0.5rem', padding: '0.8rem 1rem', marginBottom: '0.65rem', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{r.title}</div>
                  {r.slug !== currentSlug && <Link to={`/results/${r.slug}`} style={{ background: '#16a34a', color: '#fff', padding: '0.38rem 0.75rem', borderRadius: '0.5rem', fontSize: '0.78rem', fontWeight: 600, textDecoration: 'none' }}>View →</Link>}
                  {r.slug === currentSlug && <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, padding: '0.38rem 0.75rem' }}>Current</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
}
AdmissionParent.propTypes = { admission: PropTypes.object.isRequired, currentSlug: PropTypes.string.isRequired, currentType: PropTypes.string.isRequired };

export default function ParentDetail({ type, data, currentSlug, currentType }) {
  if (type === 'job') return <JobParent job={data} currentSlug={currentSlug} currentType={currentType} />;
  if (type === 'admission') return <AdmissionParent admission={data} currentSlug={currentSlug} currentType={currentType} />;
  return null;
}

ParentDetail.propTypes = {
  type: PropTypes.oneOf(['job', 'admission']).isRequired,
  data: PropTypes.object.isRequired,
  currentSlug: PropTypes.string.isRequired,
  currentType: PropTypes.string.isRequired,
};
