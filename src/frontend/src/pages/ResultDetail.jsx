import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Briefcase, GraduationCap, Download, Globe, Star, ClipboardList, BarChart2 } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import ParentDetail from '../components/ParentDetail';

const fadeUp = { hidden: { opacity: 0, y: 14 }, show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] } } };
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } } };

export default function ResultDetail() {
  const { slug } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [tracking, setTracking] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/results/${slug}`).then((r) => {
      setResult(r.data);
      setLoading(false);
      if (token) {
        if (r.data.job?.id) api.get(`/jobs/${r.data.job.id}/track`).then((tr) => setTracking(tr.data.tracking)).catch(() => {});
        else if (r.data.admission?.id) api.get(`/admissions/${r.data.admission.id}/track`).then((tr) => setTracking(tr.data.tracking)).catch(() => {});
      }
    }).catch(() => setLoading(false));
  }, [slug, token]);

  const toggleTrack = async () => {
    if (!token) { navigate(`/login?next=/results/${slug}`); return; }
    const type = result.job ? 'job' : 'admission';
    const id = result.job?.id || result.admission?.id;
    if (!id) return;
    try {
      if (tracking) await api.delete(`/${type}s/${id}/track`);
      else await api.post(`/${type}s/${id}/track`);
      setTracking(!tracking);
    } catch { }
  };

  if (loading) return (
    <div style={{ padding: '3rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div className="skeleton" style={{ height: 180, borderRadius: 'var(--radius-2xl)' }} />
      <div style={{ display: 'flex', gap: '0.5rem' }}>{[120, 90].map((w) => <div key={w} className="skeleton" style={{ height: 34, width: w, borderRadius: 'var(--radius)' }} />)}</div>
      <div className="skeleton" style={{ height: 120, borderRadius: 'var(--radius-lg)' }} />
    </div>
  );
  if (!result) return (
    <div style={{ textAlign: 'center', padding: '3rem' }}>
      <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.75rem' }}>Result not found</h2>
      <Link to="/results" className="btn btn-primary" style={{ display: 'inline-flex' }}>← Back</Link>
    </div>
  );

  return (
    <motion.div variants={stagger} initial="hidden" animate="show">
      <motion.div variants={fadeUp}>
        <Link to="/results" className="back-link">← Back to Results</Link>
      </motion.div>

      <motion.div variants={fadeUp} className="detail-hero hero-result">
        <h1>{result.title}</h1>
        {result.job && <div style={{ fontSize: '0.875rem', opacity: 0.88, marginTop: '0.3rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Briefcase size={14} strokeWidth={2} />{result.job.job_title} — {result.job.organization}</div>}
        {result.admission && <div style={{ fontSize: '0.875rem', opacity: 0.88, marginTop: '0.3rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}><GraduationCap size={14} strokeWidth={2} />{result.admission.admission_name}</div>}
      </motion.div>

      <div className="action-bar">
        {(result.job || result.admission) && (
          <button onClick={toggleTrack} className="share-btn" style={tracking ? { background: '#fef3c7', color: '#92400e', borderColor: '#fde68a' } : { background: '#dcfce7', color: '#166534', borderColor: '#bbf7d0' }}>
            {tracking ? <><Star size={14} strokeWidth={2} fill="currentColor" /> Tracking — Remove</> : <><Star size={14} strokeWidth={2} /> Track for Reminders</>}
          </button>
        )}
        {result.download_url && <a href={result.download_url} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ background: '#16a34a', color: '#fff', borderColor: '#16a34a', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}><Download size={13} strokeWidth={2} />Download</a>}
        {result.source_url && <a href={result.source_url} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}><Globe size={13} strokeWidth={2} />Official Website</a>}
      </div>

      <div className="detail-grid">
        {[['Published', result.published_at?.slice(0, 10)]].filter(([, v]) => v).map(([label, value]) => (
          <div key={label} className="detail-item"><div className="label">{label}</div><div className="value">{value}</div></div>
        ))}
      </div>

      {result.notes && <motion.div variants={fadeUp} className="detail-section"><h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><ClipboardList size={16} strokeWidth={2} />Notes</h2><p>{result.notes}</p></motion.div>}

      {result.cutoffs?.length > 0 && (
        <motion.div variants={fadeUp} className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><BarChart2 size={16} strokeWidth={2} />Cut-Off Marks</h2>
          <div style={{ overflowX: 'auto' }}>
            <table className="fee-table">
              <thead><tr><th>Category</th><th>Cut-off</th>{result.cutoffs[0]?.post && <th>Post</th>}</tr></thead>
              <tbody>
                {result.cutoffs.map((c) => (
                  <tr key={`${c.category}-${c.post || ''}`}><td>{c.category || '—'}</td><td>{c.marks ?? c.cutoff ?? '—'}</td>{c.post && <td>{c.post}</td>}</tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* Full parent job/admission inline */}
      {result.job && <ParentDetail type="job" data={result.job} currentSlug={slug} currentType="result" />}
      {result.admission && <ParentDetail type="admission" data={result.admission} currentSlug={slug} currentType="result" />}
    </motion.div>
  );
}
