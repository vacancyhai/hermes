import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';

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

  if (loading) return <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>Loading...</div>;
  if (!result) return <div style={{ textAlign: 'center', padding: '3rem' }}><h2>404 — Result not found</h2><Link to="/results" className="btn btn-primary" style={{ marginTop: '1rem', display: 'inline-flex' }}>Back</Link></div>;

  return (
    <div>
      <Link to="/results" className="back-link">← Back to Results</Link>

      <div className="detail-hero hero-result">
        <h1>{result.title}</h1>
        {result.job && <div style={{ fontSize: '0.875rem', opacity: 0.88 }}>💼 {result.job.job_title} — {result.job.organization}</div>}
        {result.admission && <div style={{ fontSize: '0.875rem', opacity: 0.88 }}>🎓 {result.admission.admission_name}</div>}
      </div>

      <div className="action-bar">
        {(result.job || result.admission) && (
          <button onClick={toggleTrack} className="share-btn" style={tracking ? { background: '#fef3c7', color: '#92400e', borderColor: '#fde68a' } : { background: '#dcfce7', color: '#166534', borderColor: '#bbf7d0' }}>
            {tracking ? '★ Tracking — Remove' : '☆ Track'}
          </button>
        )}
        {result.download_url && <a href={result.download_url} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ background: '#16a34a', color: '#fff', borderColor: '#16a34a' }}>📥 Download Result</a>}
        {result.source_url && <a href={result.source_url} target="_blank" rel="noopener noreferrer" className="share-btn">🔗 Official Website</a>}
      </div>

      <div className="detail-grid">
        {[['Published', result.published_at?.slice(0, 10)]].filter(([, v]) => v).map(([label, value]) => (
          <div key={label} className="detail-item"><div className="label">{label}</div><div className="value">{value}</div></div>
        ))}
      </div>

      {result.notes && <div className="detail-section"><h2>📋 Notes</h2><p>{result.notes}</p></div>}

      {result.cutoffs?.length > 0 && (
        <div className="detail-section">
          <h2>📊 Cut-off Marks</h2>
          <div style={{ overflowX: 'auto' }}>
            <table className="fee-table">
              <thead><tr><th>Category</th><th>Cut-off</th>{result.cutoffs[0]?.post && <th>Post</th>}</tr></thead>
              <tbody>
                {result.cutoffs.map((c, i) => (
                  <tr key={i}><td>{c.category || '—'}</td><td>{c.marks ?? c.cutoff ?? '—'}</td>{c.post && <td>{c.post}</td>}</tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div style={{ marginTop: '1.5rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        {result.job && <Link to={`/jobs/${result.job.slug || result.job.id}`} className="btn btn-outline">← View Job Details</Link>}
        {result.admission && <Link to={`/admissions/${result.admission.slug || result.admission.id}`} className="btn btn-outline">← View Admission Details</Link>}
      </div>
    </div>
  );
}
