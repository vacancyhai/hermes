import PropTypes from 'prop-types';

export default function DetailSkeleton({ skeletonWidths = [120, 90] }) {
  return (
    <div style={{ padding: '3rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div className="skeleton" style={{ height: 180, borderRadius: 'var(--radius-2xl)' }} />
      <div style={{ display: 'flex', gap: '0.5rem' }}>
        {skeletonWidths.map((w) => (
          <div key={w} className="skeleton" style={{ height: 34, width: w, borderRadius: 'var(--radius)' }} />
        ))}
      </div>
      <div className="skeleton" style={{ height: 120, borderRadius: 'var(--radius-lg)' }} />
    </div>
  );
}

DetailSkeleton.propTypes = {
  skeletonWidths: PropTypes.arrayOf(PropTypes.number),
};
