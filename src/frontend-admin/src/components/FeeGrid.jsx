import PropTypes from 'prop-types';
import { emptyFee } from '../lib/formUtils';

export default function FeeGrid({ prefix, fee, onChange }) {
  return (
    <div className="section-card">
      <div className="section-header section-header--orange">Application Fee (₹)</div>
      <div className="section-body">
        <div className="fee-grid">
          {Object.keys(emptyFee).map((k) => (
            <div className="fee-cell" key={k}>
              <label htmlFor={`${prefix}-fee-${k}`}>{k.toUpperCase().replaceAll('_', '/')}</label>
              <input id={`${prefix}-fee-${k}`} type="number" min="0" value={fee[k]} onChange={(e) => onChange(k, e.target.value)} placeholder="0" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

FeeGrid.propTypes = {
  prefix: PropTypes.string.isRequired,
  fee: PropTypes.objectOf(PropTypes.oneOfType([PropTypes.string, PropTypes.number])).isRequired,
  onChange: PropTypes.func.isRequired,
};
