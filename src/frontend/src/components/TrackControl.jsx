import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import { Star } from 'lucide-react';

export default function TrackControl({ token, isTracking, onTrack, loginPath }) {
  if (!token) {
    return (
      <Link to={loginPath} onClick={(e) => e.stopPropagation()} className="btn btn-outline btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
        <Star size={12} strokeWidth={2} />Keep Track
      </Link>
    );
  }
  return (
    <button onClick={(e) => { e.stopPropagation(); onTrack(); }} className={isTracking ? 'btn-tracking btn btn-sm' : 'btn btn-outline btn-sm'} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
      <Star size={12} strokeWidth={2} fill={isTracking ? 'currentColor' : 'none'} />
      {isTracking ? 'Tracking' : 'Keep Track'}
    </button>
  );
}

TrackControl.propTypes = {
  token: PropTypes.string,
  isTracking: PropTypes.bool.isRequired,
  onTrack: PropTypes.func.isRequired,
  loginPath: PropTypes.string.isRequired,
};
