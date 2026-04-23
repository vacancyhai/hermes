import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Briefcase, GraduationCap, Download, Globe, Star, ClipboardList } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useDetailTrack } from '../hooks/useDetailTrack';
import DetailSkeleton from '../components/DetailSkeleton';
import ParentDetail from '../components/ParentDetail';

const fadeUp = { hidden: { opacity: 0, y: 14 }, show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] } } };
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } } };

export default function AdmitCardDetail() {
  const { slug } = useParams();
  const { token } = useAuth();
  const { item: card, tracking, loading, toggleTrack } = useDetailTrack('admit-cards', slug, token);

  if (loading) return <DetailSkeleton />;
  if (!card) return (
    <div style={{ textAlign: 'center', padding: '3rem' }}>
      <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.75rem' }}>Admit Card not found</h2>
      <Link to="/admit-cards" className="btn btn-primary" style={{ display: 'inline-flex' }}>← Back</Link>
    </div>
  );

  return (
    <motion.div variants={stagger} initial="hidden" animate="show">
      <motion.div variants={fadeUp}>
        <Link to="/admit-cards" className="back-link">← Back to Admit Cards</Link>
      </motion.div>

      <motion.div variants={fadeUp} className="detail-hero hero-admit">
        <h1>{card.title}</h1>
        {card.job && <div style={{ fontSize: '0.875rem', opacity: 0.88, marginTop: '0.3rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Briefcase size={14} strokeWidth={2} />{card.job.job_title} — {card.job.organization}</div>}
        {card.admission && <div style={{ fontSize: '0.875rem', opacity: 0.88, marginTop: '0.3rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}><GraduationCap size={14} strokeWidth={2} />{card.admission.admission_name}</div>}
      </motion.div>

      <div className="action-bar">
        {(card.job || card.admission) && (
          <button onClick={() => toggleTrack(`/login?next=/admit-cards/${slug}`)} className="share-btn" style={tracking ? { background: '#fef3c7', color: '#92400e', borderColor: '#fde68a' } : { background: '#dbeafe', color: '#1e40af', borderColor: '#bfdbfe' }}>
            {tracking ? <><Star size={14} strokeWidth={2} fill="currentColor" /> Tracking — Remove</> : <><Star size={14} strokeWidth={2} /> Track for Reminders</>}
          </button>
        )}
        {card.download_url && <a href={card.download_url} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ background: '#2563eb', color: '#fff', borderColor: '#2563eb', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}><Download size={13} strokeWidth={2} />Download Admit Card</a>}
        {card.source_url && <a href={card.source_url} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}><Globe size={13} strokeWidth={2} />Official Website</a>}
      </div>

      <div className="detail-grid">
        {[['Exam Start', card.exam_start], ['Exam End', card.exam_end], ['Published', card.published_at?.slice(0, 10)]].filter(([, v]) => v).map(([label, value]) => (
          <div key={label} className="detail-item"><div className="label">{label}</div><div className="value">{value}</div></div>
        ))}
      </div>

      {card.notes && <motion.div variants={fadeUp} className="detail-section"><h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><ClipboardList size={16} strokeWidth={2} />Notes</h2><div style={{ fontSize: '0.9rem', color: '#334155', lineHeight: 1.65 }} dangerouslySetInnerHTML={{ __html: card.notes }} /></motion.div>}
      {card.instructions && <motion.div variants={fadeUp} className="detail-section"><h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><ClipboardList size={16} strokeWidth={2} />Instructions</h2><div style={{ fontSize: '0.9rem', color: '#334155', lineHeight: 1.65 }} dangerouslySetInnerHTML={{ __html: card.instructions }} /></motion.div>}

      {/* Full parent job/admission inline */}
      {card.job && <ParentDetail type="job" data={card.job} currentSlug={slug} currentType="admit-card" />}
      {card.admission && <ParentDetail type="admission" data={card.admission} currentSlug={slug} currentType="admit-card" />}
    </motion.div>
  );
}
