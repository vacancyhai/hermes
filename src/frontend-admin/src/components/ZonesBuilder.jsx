import PropTypes from 'prop-types';
import { Globe, X } from 'lucide-react';

const emptyZone = () => ({ id: Date.now() + Math.random(), zone: '', total: '', male: '', female: '', ur: '', obc: '', ews: '', sc: '', st: '' });

const NUM = (v) => v === '' || v === undefined || v === null ? '' : Number(v);

export function zonesToState(arr) {
  if (!Array.isArray(arr) || !arr.length) return [];
  return arr.map((z) => ({
    id: Math.random(),
    zone: z.zone || '',
    total: NUM(z.total),
    male: NUM(z.male),
    female: NUM(z.female),
    ur: NUM(z.UR ?? z.ur),
    obc: NUM(z.OBC ?? z.obc),
    ews: NUM(z.EWS ?? z.ews),
    sc: NUM(z.SC ?? z.sc),
    st: NUM(z.ST ?? z.st),
  }));
}

export function zonesToPayload(zones) {
  return zones.filter((z) => z.zone.trim()).map(({ id: _id, zone, total, male, female, ur, obc, ews, sc, st }) => ({
    zone,
    total: total === '' ? null : Number(total),
    male: male === '' ? null : Number(male),
    female: female === '' ? null : Number(female),
    other: 0,
    UR: ur === '' ? null : Number(ur),
    OBC: obc === '' ? null : Number(obc),
    EWS: ews === '' ? null : Number(ews),
    SC: sc === '' ? null : Number(sc),
    ST: st === '' ? null : Number(st),
  }));
}

export default function ZonesBuilder({ zones, onChange }) {
  function add() { onChange([...zones, emptyZone()]); }
  function remove(id) { onChange(zones.filter((z) => z.id !== id)); }
  function update(id, field, val) { onChange(zones.map((z) => z.id === id ? { ...z, [field]: val } : z)); }

  const vacancyCells = [
    { field: 'total', label: 'Total', cls: 'total-cell' },
    { field: 'male', label: '♂ Male', cls: 'male-cell' },
    { field: 'female', label: '♀ Female', cls: 'female-cell' },
    { field: 'ur', label: 'UR', cls: '' },
    { field: 'obc', label: 'OBC', cls: '' },
    { field: 'ews', label: 'EWS', cls: '' },
    { field: 'sc', label: 'SC', cls: '' },
    { field: 'st', label: 'ST', cls: '' },
  ];

  return (
    <div className="section-card">
      <div className="section-header section-header--teal" style={{ display: 'flex', alignItems: 'center' }}>
        Zone-wise Vacancy
        <button type="button" onClick={add} style={{ marginLeft: 'auto', background: 'rgba(255,255,255,.2)', border: '1px solid rgba(255,255,255,.4)', color: '#fff', borderRadius: '.375rem', padding: '.2rem .65rem', fontSize: '.8rem', cursor: 'pointer', fontWeight: 600 }}>+ Add Zone</button>
      </div>
      <div className="section-body">
        {zones.length === 0 && (
          <div style={{ textAlign: 'center', padding: '1.5rem', color: '#94a3b8' }}>
            <div style={{ marginBottom: '.5rem', display: 'flex', justifyContent: 'center' }}><Globe size={32} strokeWidth={1.5} /></div>
            <p style={{ fontSize: '.88rem', margin: '0 0 .75rem' }}>No zones added. Skip if not applicable.</p>
            <button type="button" className="btn btn-outline" onClick={add}>+ Add Zone</button>
          </div>
        )}
        {zones.map((z) => (
          <div key={z.id} style={{ border: '1px solid #e2e8f0', borderRadius: '.5rem', marginBottom: '.6rem', overflow: 'hidden', background: '#fff' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '.5rem', padding: '.5rem .75rem', background: '#f0fdfa', borderBottom: '1px solid #ccfbf1' }}>
              <input
                type="text"
                value={z.zone}
                onChange={(e) => update(z.id, 'zone', e.target.value)}
                placeholder="e.g. NR (Northern Region)"
                style={{ flex: 1, border: 'none', borderBottom: '2px solid #99f6e4', background: 'transparent', padding: '.25rem .2rem', fontSize: '.9rem', fontWeight: 600, color: '#134e4a', outline: 'none' }}
              />
              <button type="button" onClick={() => remove(z.id)} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '.2rem .4rem', display: 'flex' }} title="Remove zone"><X size={14} /></button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(8,1fr)', gap: '.4rem', padding: '.6rem' }}>
              {vacancyCells.map(({ field, label, cls }) => (
                <div key={field} className={`vacancy-cell ${cls}`}>
                  <label>{label}</label>
                  <input type="number" min="0" value={z[field]} onChange={(e) => update(z.id, field, e.target.value)} placeholder="0" />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

ZonesBuilder.propTypes = {
  zones: PropTypes.arrayOf(PropTypes.object).isRequired,
  onChange: PropTypes.func.isRequired,
};
