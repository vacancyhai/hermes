import PropTypes from 'prop-types';

export default function PhaseCard({ step }) {
  if (typeof step !== 'object') return (
    <div style={{ border: '1px solid #bfdbfe', background: '#eff6ff', borderRadius: '0.5rem', padding: '0.7rem 1rem', marginBottom: '0.85rem' }}>
      <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>{String(step)}</span>
    </div>
  );
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
            {step.subjects.map((sub) => (
              <tr key={sub.name || sub.questions}>
                <td>{sub.name || '—'}</td>
                <td style={{ textAlign: 'right' }}>{sub.questions || '—'}</td>
                <td style={{ textAlign: 'right' }}>{sub.marks || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

PhaseCard.propTypes = {
  step: PropTypes.oneOfType([PropTypes.object, PropTypes.string]).isRequired,
};
