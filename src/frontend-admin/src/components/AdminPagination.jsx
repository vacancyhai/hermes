import PropTypes from 'prop-types';

export default function AdminPagination({ page, totalPages, onPage }) {
  if (totalPages <= 1) return null;
  return (
    <div style={{ display: 'flex', gap: '.5rem', alignItems: 'center', marginTop: '1rem', flexWrap: 'wrap' }}>
      <button className="btn btn-sm btn-outline" disabled={page === 1} onClick={() => onPage(page - 1)}>← Prev</button>
      <span style={{ fontSize: '.85rem', color: '#475569' }}>Page {page} of {totalPages}</span>
      <button className="btn btn-sm btn-outline" disabled={page === totalPages} onClick={() => onPage(page + 1)}>Next →</button>
    </div>
  );
}

AdminPagination.propTypes = {
  page: PropTypes.number.isRequired,
  totalPages: PropTypes.number.isRequired,
  onPage: PropTypes.func.isRequired,
};
