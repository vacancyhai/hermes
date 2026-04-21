import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';

export default function AdmitCardDetail() {
  const { slug } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [card, setCard] = useState(null);
  const [tracking, setTracking] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/admit-cards/${slug}`).then((r) => {
      setCard(r.data);
      setLoading(false);
      if (token) {
        if (r.data.job?.id) api.get(`/jobs/${r.data.job.id}/track`).then((tr) => setTracking(tr.data.tracking)).catch(() => {});
        else if (r.data.admission?.id) api.get(`/admissions/${r.data.admission.id}/track`).then((tr) => setTracking(tr.data.tracking)).catch(() => {});
      }
    }).catch(() => setLoading(false));
  }, [slug, token]);

  const toggleTrack = async () => {
    if (!token) { navigate(`/login?next=/admit-cards/${slug}`); return; }
    const type = card.job ? 'job' : 'admission';
    const id = card.job?.id || card.admission?.id;
    if (!id) return;
    try {
      if (tracking) await api.delete(`/${type}s/${id}/track`);
      else await api.post(`/${type}s/${id}/track`);
      setTracking(!tracking);
    } catch (_) {}
  };

  if (loading) return <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>Loading...</div>;
  if (!card) return <div style={{ textAlign: 'center', padding: '3rem' }}><h2>404 — Admit Card not found</h2><Link to="/admit-cards" className="btn btn-primary" style={{ marginTop: '1rem', display: 'inline-flex' }}>Back</Link></div>;

  return (
    <div>
      <Link to="/admit-cards" className="back-link">← Back to Admit Cards</Link>

      <div className="detail-hero hero-admit">
        <h1>{card.title}</h1>
        {card.job && <div style={{ fontSize: '0.875rem', opacity: 0.88 }}>💼 {card.job.job_title} — {card.job.organization}</div>}
        {card.admission && <div style={{ fontSize: '0.875rem', opacity: 0.88 }}>🎓 {card.admission.admission_name}</div>}
      </div>

      <div className="action-bar">
        {(card.job || card.admission) && (
          <button onClick={toggleTrack} className="share-btn" style={tracking ? { background: '#fef3c7', color: '#92400e', borderColor: '#fde68a' } : { background: '#dbeafe', color: '#1e40af', borderColor: '#bfdbfe' }}>
            {tracking ? '★ Tracking — Remove' : '☆ Track for Reminders'}
          </button>
        )}
        {card.download_url && <a href={card.download_url} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ background: '#2563eb', color: '#fff', borderColor: '#2563eb' }}>📥 Download Admit Card</a>}
        {card.source_url && <a href={card.source_url} target="_blank" rel="noopener noreferrer" className="share-btn">🔗 Official Website</a>}
      </div>

      <div className="detail-grid">
        {[['Exam Start', card.exam_start], ['Exam End', card.exam_end], ['Published', card.published_at?.slice(0, 10)]].filter(([, v]) => v).map(([label, value]) => (
          <div key={label} className="detail-item"><div className="label">{label}</div><div className="value">{value}</div></div>
        ))}
      </div>

      {card.notes && <div className="detail-section"><h2>📋 Notes</h2><div style={{ fontSize: '0.9rem', color: '#334155', lineHeight: 1.65 }} dangerouslySetInnerHTML={{ __html: card.notes }} /></div>}

      {card.instructions && (
        <div className="detail-section">
          <h2>📋 Instructions</h2>
          <div style={{ fontSize: '0.9rem', color: '#334155', lineHeight: 1.65 }} dangerouslySetInnerHTML={{ __html: card.instructions }} />
        </div>
      )}

      <div style={{ marginTop: '1.5rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        {card.job && <Link to={`/jobs/${card.job.slug || card.job.id}`} className="btn btn-outline">← View Job Details</Link>}
        {card.admission && <Link to={`/admissions/${card.admission.slug || card.admission.id}`} className="btn btn-outline">← View Admission Details</Link>}
      </div>
    </div>
  );
}
