import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';

export default function AnswerKeyDetail() {
  const { slug } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [key, setKey] = useState(null);
  const [tracking, setTracking] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/answer-keys/${slug}`).then((r) => {
      setKey(r.data);
      setLoading(false);
      if (token) {
        if (r.data.job?.id) api.get(`/jobs/${r.data.job.id}/track`).then((tr) => setTracking(tr.data.tracking)).catch(() => {});
        else if (r.data.admission?.id) api.get(`/admissions/${r.data.admission.id}/track`).then((tr) => setTracking(tr.data.tracking)).catch(() => {});
      }
    }).catch(() => setLoading(false));
  }, [slug, token]);

  const toggleTrack = async () => {
    if (!token) { navigate(`/login?next=/answer-keys/${slug}`); return; }
    const type = key.job ? 'job' : 'admission';
    const id = key.job?.id || key.admission?.id;
    if (!id) return;
    try {
      if (tracking) await api.delete(`/${type}s/${id}/track`);
      else await api.post(`/${type}s/${id}/track`);
      setTracking(!tracking);
    } catch (_) {}
  };

  if (loading) return <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>Loading...</div>;
  if (!key) return <div style={{ textAlign: 'center', padding: '3rem' }}><h2>404 — Answer Key not found</h2><Link to="/answer-keys" className="btn btn-primary" style={{ marginTop: '1rem', display: 'inline-flex' }}>Back</Link></div>;

  return (
    <div>
      <Link to="/answer-keys" className="back-link">← Back to Answer Keys</Link>

      <div className="detail-hero hero-answer">
        <h1>{key.title}</h1>
        {key.job && <div style={{ fontSize: '0.875rem', opacity: 0.88 }}>💼 {key.job.job_title} — {key.job.organization}</div>}
        {key.admission && <div style={{ fontSize: '0.875rem', opacity: 0.88 }}>🎓 {key.admission.admission_name}</div>}
      </div>

      <div className="action-bar">
        {(key.job || key.admission) && (
          <button onClick={toggleTrack} className="share-btn" style={tracking ? { background: '#fef3c7', color: '#92400e', borderColor: '#fde68a' } : { background: '#fef9c3', color: '#854d0e', borderColor: '#fde68a' }}>
            {tracking ? '★ Tracking — Remove' : '☆ Track'}
          </button>
        )}
        {key.download_url && <a href={key.download_url} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ background: '#d97706', color: '#fff', borderColor: '#d97706' }}>📥 Download Answer Key</a>}
        {key.source_url && <a href={key.source_url} target="_blank" rel="noopener noreferrer" className="share-btn">🔗 Official Website</a>}
      </div>

      <div className="detail-grid">
        {[['Published', key.published_at?.slice(0, 10)], ['Challenge Start', key.start_date], ['Challenge End', key.end_date]].filter(([, v]) => v).map(([label, value]) => (
          <div key={label} className="detail-item"><div className="label">{label}</div><div className="value">{value}</div></div>
        ))}
      </div>

      {key.notes && <div className="detail-section"><h2>📋 Notes</h2><div style={{ fontSize: '0.9rem', color: '#334155', lineHeight: 1.65 }} dangerouslySetInnerHTML={{ __html: key.notes }} /></div>}

      {key.sets?.length > 0 && (
        <div className="detail-section">
          <h2>📄 Answer Key Sets</h2>
          {key.sets.map((set, i) => (
            <div key={i} style={{ border: '1px solid #fde68a', background: '#fefce8', borderRadius: '0.5rem', padding: '0.8rem 1rem', marginBottom: '0.65rem', display: 'flex', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{set.set_name || `Set ${i + 1}`}</div>
                {set.subject && <div style={{ fontSize: '0.8rem', color: '#a16207' }}>{set.subject}</div>}
              </div>
              {set.download_url && <a href={set.download_url} target="_blank" rel="noopener noreferrer" style={{ background: '#d97706', color: '#fff', padding: '0.38rem 0.75rem', borderRadius: '0.5rem', fontSize: '0.78rem', fontWeight: 600, textDecoration: 'none' }}>Download →</a>}
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: '1.5rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        {key.job && <Link to={`/jobs/${key.job.slug || key.job.id}`} className="btn btn-outline">← View Job Details</Link>}
        {key.admission && <Link to={`/admissions/${key.admission.slug || key.admission.id}`} className="btn btn-outline">← View Admission Details</Link>}
      </div>
    </div>
  );
}
