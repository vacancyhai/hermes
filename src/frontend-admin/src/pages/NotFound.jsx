import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
      <div style={{ fontSize: '4rem', fontWeight: 900, color: '#e2e8f0' }}>404</div>
      <p style={{ color: '#64748b', marginTop: '.5rem', marginBottom: '1.5rem' }}>Page not found.</p>
      <Link to="/" className="btn btn-primary">← Back to Dashboard</Link>
    </div>
  );
}
