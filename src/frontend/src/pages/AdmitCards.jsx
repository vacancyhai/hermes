import { Link } from 'react-router-dom';
import { CreditCard, Star } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTrackedItems } from '../hooks/useTrackedItems';

export default function AdmitCards() {
  const { token } = useAuth();
  const { items: cards, pagination, loading, offset, limit, trackedJobIds, trackedAdmIds, track, setSearchParams } = useTrackedItems('/admit-cards', token);

  return (
    <div>
      <div style={{ background: 'linear-gradient(135deg,#1e40af 0%,#3b82f6 100%)', color: '#fff', padding: '1.75rem 1.5rem 1.5rem', borderRadius: '0.75rem', marginBottom: '1.25rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '0.3rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><CreditCard size={20} strokeWidth={2.5} />Admit Cards</h1>
        <p style={{ fontSize: '0.875rem', opacity: 0.85 }}>Download hall tickets and admit cards for upcoming examinations</p>
      </div>

      {loading && <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>Loading...</div>}
      {!loading && cards.length === 0 && <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>No admit cards available.</div>}
      {!loading && cards.map((card) => {
        const type = card.job_id ? 'job' : 'admission';
        const tid = card.job_id || card.admission_id;
        const isTracking = type === 'job' ? trackedJobIds.has(String(tid)) : trackedAdmIds.has(String(tid));
        return (
          <div key={card.id} style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderLeft: '4px solid #2563eb', borderRadius: '0.5rem', padding: '1rem 1.1rem', marginBottom: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem', flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, lineHeight: 1.4, marginBottom: '0.25rem' }}>
                  <Link to={`/admit-cards/${card.slug}`} style={{ color: '#1e40af' }}>{card.title}</Link>
                </h3>
                {(card.exam_start || card.exam_end) && <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Exam: {card.exam_start || '?'} – {card.exam_end || 'ongoing'}</div>}
                {card.published_at && <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>Published: {card.published_at.slice(0, 10)}</div>}
              </div>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', alignItems: 'center' }}>
                <Link to={`/admit-cards/${card.slug}`} className="btn btn-outline btn-sm" style={{ borderColor: '#bfdbfe' }}>View →</Link>
                {tid && (token ? (
                  <button onClick={() => track(type, tid)} className={isTracking ? 'btn-tracking btn btn-sm' : 'btn btn-outline btn-sm'} style={{ display: 'inline-flex', alignItems: 'center' }}>
                    <Star size={13} strokeWidth={2} fill={isTracking ? 'currentColor' : 'none'} />
                  </button>
                ) : (
                  <Link to={`/login?next=/admit-cards/${card.slug}`} className="btn btn-outline btn-sm" style={{ display: 'inline-flex', alignItems: 'center' }}><Star size={13} strokeWidth={2} /></Link>
                ))}
              </div>
            </div>
          </div>
        );
      })}

      {pagination.has_more && (
        <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
          <button onClick={() => setSearchParams({ offset: offset + limit })} className="btn btn-outline">Load More</button>
        </div>
      )}
    </div>
  );
}
