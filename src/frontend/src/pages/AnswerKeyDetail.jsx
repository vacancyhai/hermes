import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Briefcase, GraduationCap, Download, Globe, Bell, ClipboardList, FileText } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useDetailTrack } from '../hooks/useDetailTrack';
import DetailSkeleton from '../components/DetailSkeleton';
import ParentDetail from '../components/ParentDetail';

const fadeUp = { hidden: { opacity: 0, y: 14 }, show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] } } };
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } } };

export default function AnswerKeyDetail() {
  const { slug } = useParams();
  const { token } = useAuth();
  const { item: key, tracking, loading, toggleTrack } = useDetailTrack('answer-keys', slug, token);

  if (loading) return <DetailSkeleton />;
  if (!key) return (
    <div style={{ textAlign: 'center', padding: '3rem' }}>
      <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.75rem' }}>Answer Key not found</h2>
      <Link to="/answer-keys" className="btn btn-primary" style={{ display: 'inline-flex' }}>← Back</Link>
    </div>
  );

  return (
    <motion.div variants={stagger} initial="hidden" animate="show">
      <motion.div variants={fadeUp}>
        <Link to="/answer-keys" className="back-link">← Back to Answer Keys</Link>
      </motion.div>

      <motion.div variants={fadeUp} className="detail-hero hero-answer">
        <h1>{key.title}</h1>
        {key.job && <div style={{ fontSize: '0.875rem', opacity: 0.88, marginTop: '0.3rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Briefcase size={14} strokeWidth={2} />{key.job.job_title} — {key.job.organization}</div>}
        {key.admission && <div style={{ fontSize: '0.875rem', opacity: 0.88, marginTop: '0.3rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}><GraduationCap size={14} strokeWidth={2} />{key.admission.admission_name}</div>}
      </motion.div>

      <div className="action-bar">
        {(key.job || key.admission) && (
          <button onClick={() => toggleTrack(`/login?next=/answer-keys/${slug}`)} className="share-btn" style={tracking ? { background: '#fef3c7', color: '#92400e', borderColor: '#fde68a' } : { background: '#fef9c3', color: '#854d0e', borderColor: '#fde68a' }}>
            {tracking ? <><Bell size={14} strokeWidth={2} fill="currentColor" /> Tracking — Remove</> : <><Bell size={14} strokeWidth={2} /> Track for Reminders</>}
          </button>
        )}
        {key.download_url && <a href={key.download_url} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ background: '#d97706', color: '#fff', borderColor: '#d97706', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}><Download size={13} strokeWidth={2} />Download</a>}
        {key.source_url && <a href={key.source_url} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}><Globe size={13} strokeWidth={2} />Official Website</a>}
      </div>

      <div className="detail-grid">
        {[['Published', key.published_at?.slice(0, 10)], ['Challenge Start', key.start_date], ['Challenge End', key.end_date]].filter(([, v]) => v).map(([label, value]) => (
          <div key={label} className="detail-item"><div className="label">{label}</div><div className="value">{value}</div></div>
        ))}
      </div>

      {key.notes && <motion.div variants={fadeUp} className="detail-section"><h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><ClipboardList size={16} strokeWidth={2} />Notes</h2><div style={{ fontSize: '0.9rem', color: '#334155', lineHeight: 1.65 }} dangerouslySetInnerHTML={{ __html: key.notes }} /></motion.div>}

      {key.sets?.length > 0 && (
        <motion.div variants={fadeUp} className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><FileText size={16} strokeWidth={2} />Answer Key Sets</h2>
          {key.sets.map((set) => (
            <div key={set.set_name || set.download_url} style={{ border: '1px solid #fde68a', background: '#fefce8', borderRadius: '0.5rem', padding: '0.8rem 1rem', marginBottom: '0.65rem', display: 'flex', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{set.set_name || 'Answer Key Set'}</div>
                {set.subject && <div style={{ fontSize: '0.8rem', color: '#a16207' }}>{set.subject}</div>}
              </div>
              {set.download_url && <a href={set.download_url} target="_blank" rel="noopener noreferrer" style={{ background: '#d97706', color: '#fff', padding: '0.38rem 0.75rem', borderRadius: '0.5rem', fontSize: '0.78rem', fontWeight: 600, textDecoration: 'none' }}>Download →</a>}
            </div>
          ))}
        </motion.div>
      )}

      {/* Full parent job/admission inline */}
      {key.job && <ParentDetail type="job" data={key.job} currentSlug={slug} currentType="answer-key" />}
      {key.admission && <ParentDetail type="admission" data={key.admission} currentSlug={slug} currentType="answer-key" />}
    </motion.div>
  );
}
