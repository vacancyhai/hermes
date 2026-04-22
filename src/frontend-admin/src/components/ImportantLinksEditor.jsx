import PropTypes from 'prop-types';
import { LINK_TYPES } from '../lib/formUtils';

export default function ImportantLinksEditor({ prefix, links, onUpdate, onAdd, onRemove }) {
  return (
    <div className="section-card">
      <div className="section-header section-header--indigo">
        Important Links{' '}
        <button type="button" className="btn btn-sm" style={{ background: 'rgba(255,255,255,.2)', color: '#fff', border: '1px solid rgba(255,255,255,.4)', marginLeft: '.5rem' }} onClick={onAdd}>+ Add</button>
      </div>
      <div className="section-body" style={{ display: 'flex', flexDirection: 'column', gap: '.5rem' }}>
        {links.map((link, i) => (
          <div key={`link-${link.type}-${i}`} style={{ display: 'grid', gridTemplateColumns: '180px 1fr 2fr auto', gap: '.5rem', alignItems: 'flex-end' }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label htmlFor={`${prefix}-type-${i}`} style={{ fontSize: '.7rem' }}>Type</label>
              <select id={`${prefix}-type-${i}`} value={link.type} onChange={(e) => onUpdate(i, 'type', e.target.value)} style={{ padding: '.35rem .5rem', fontSize: '.82rem' }}>
                {LINK_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label htmlFor={`${prefix}-text-${i}`} style={{ fontSize: '.7rem' }}>Display Text</label>
              <input id={`${prefix}-text-${i}`} type="text" value={link.text} onChange={(e) => onUpdate(i, 'text', e.target.value)} placeholder="Click here" style={{ padding: '.35rem .5rem', fontSize: '.82rem' }} />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label htmlFor={`${prefix}-url-${i}`} style={{ fontSize: '.7rem' }}>URL</label>
              <input id={`${prefix}-url-${i}`} type="url" value={link.url} onChange={(e) => onUpdate(i, 'url', e.target.value)} placeholder="https://…" style={{ padding: '.35rem .5rem', fontSize: '.82rem' }} />
            </div>
            <button type="button" className="btn btn-sm btn-danger" onClick={() => onRemove(i)} style={{ marginBottom: 0 }}>✕</button>
          </div>
        ))}
      </div>
    </div>
  );
}

ImportantLinksEditor.propTypes = {
  prefix: PropTypes.string.isRequired,
  links: PropTypes.arrayOf(PropTypes.shape({ type: PropTypes.string, text: PropTypes.string, url: PropTypes.string })).isRequired,
  onUpdate: PropTypes.func.isRequired,
  onAdd: PropTypes.func.isRequired,
  onRemove: PropTypes.func.isRequired,
};
