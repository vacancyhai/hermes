import PropTypes from 'prop-types';

export default function OrgLogoCircle({ logoUrl, orgName, title, gradient, size = 40 }) {
  const initials = (orgName || title || '?')[0].toUpperCase();
  return (
    <div style={{ flexShrink: 0, width: size, height: size, borderRadius: '50%', overflow: 'hidden', border: '1.5px solid #e2e8f0', background: gradient, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 1px 4px rgba(15,23,42,.1)' }}>
      {logoUrl
        ? <img src={logoUrl} alt={orgName} style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={(e) => { e.target.style.display = 'none'; }} />
        : <span style={{ color: '#fff', fontWeight: 800, fontSize: '0.95rem', lineHeight: 1 }}>{initials}</span>}
    </div>
  );
}

OrgLogoCircle.propTypes = {
  logoUrl: PropTypes.string,
  orgName: PropTypes.string,
  title: PropTypes.string,
  gradient: PropTypes.string.isRequired,
  size: PropTypes.number,
};
