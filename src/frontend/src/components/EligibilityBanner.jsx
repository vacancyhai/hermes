import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import { Search, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

export default function EligibilityBanner({ token, profileComplete, eligibility, slug, loginPrefix }) {
  if (!token) return (
    <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '0.5rem', padding: '1rem 1.25rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
      <Search size={18} strokeWidth={2} />
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>Check Your Eligibility</div>
        <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.15rem' }}>Login and complete your profile to see if you qualify.</div>
      </div>
      <Link to={`/login?next=/${loginPrefix}/${slug}`} className="btn btn-primary btn-sm">Login to Check</Link>
    </div>
  );
  if (!profileComplete) return (
    <div style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '0.5rem', padding: '1rem 1.25rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
      <AlertTriangle size={18} strokeWidth={2} color="#92400e" />
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#92400e' }}>Profile Incomplete</div>
        <div style={{ fontSize: '0.8rem', color: '#a16207', marginTop: '0.15rem' }}>Complete your profile to check eligibility.</div>
      </div>
      <Link to="/profile" className="btn btn-sm" style={{ background: '#fef3c7', color: '#92400e', border: '1px solid #fde68a' }}>Complete Profile</Link>
    </div>
  );
  if (!eligibility) return null;
  const cfg = {
    eligible: { bg: '#f0fdf4', border: '#bbf7d0', Icon: CheckCircle, color: '#166534', label: 'You are Eligible' },
    partially_eligible: { bg: '#fffbeb', border: '#fde68a', Icon: AlertTriangle, color: '#92400e', label: 'Partially Eligible' },
    not_eligible: { bg: '#fef2f2', border: '#fecaca', Icon: XCircle, color: '#991b1b', label: 'Not Eligible' },
  }[eligibility.status];
  if (!cfg) return null;
  const Icon = cfg.Icon;
  return (
    <div style={{ background: cfg.bg, border: `1px solid ${cfg.border}`, borderRadius: '0.5rem', padding: '1rem 1.25rem', marginBottom: '1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: eligibility.reasons?.length ? '0.6rem' : 0 }}>
        <Icon size={18} strokeWidth={2} color={cfg.color} />
        <span style={{ fontWeight: 700, fontSize: '0.95rem', color: cfg.color }}>{cfg.label}</span>
      </div>
      {eligibility.reasons?.length > 0 && (
        <ul style={{ margin: 0, paddingLeft: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          {eligibility.reasons.map((r) => <li key={r} style={{ fontSize: '0.82rem', color: cfg.color }}>{r}</li>)}
        </ul>
      )}
    </div>
  );
}

EligibilityBanner.propTypes = {
  token: PropTypes.string,
  profileComplete: PropTypes.bool.isRequired,
  eligibility: PropTypes.shape({ status: PropTypes.string, reasons: PropTypes.arrayOf(PropTypes.string) }),
  slug: PropTypes.string.isRequired,
  loginPrefix: PropTypes.string.isRequired,
};
EligibilityBanner.defaultProps = { token: null, eligibility: null };
