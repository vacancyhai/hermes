import PropTypes from 'prop-types';
import { X, Trash2, ClipboardList } from 'lucide-react';

/* ─── helpers ─── */
const num = (v) => (v === '' || v === undefined || v === null ? '' : Number(v));

const emptyVacancy = () => ({ total: '', ur: '', obc: '', ews: '', sc: '', st: '', pwd: '', male: '', female: '' });
const emptyElig = () => ({
  qualification: '', qualification_level: '10th',
  male_age_min: '', male_age_max: '', male_height: '', male_chest: '',
  female_age_min: '', female_age_max: '', female_height: '', female_weight: '',
});
const emptySalary = () => ({ min: '', max: '', pay_level: '' });
const emptyFeePost = () => ({ general: '', obc: '', sc_st: '', ews: '', female: '' });
const emptyPhase = () => ({ id: Math.random(), type: 'written_test', name: '', qualifying: false, details: {} });
const emptyPost = () => ({
  id: Math.random(),
  post_name: '',
  vacancy: emptyVacancy(),
  eligibility: emptyElig(),
  salary: emptySalary(),
  fee: emptyFeePost(),
  phases: [],
  activeTab: 'vacancy',
});

/* ─── convert saved JSON → state ─── */
export function postsToState(arr) {
  if (!Array.isArray(arr) || !arr.length) return [];
  return arr.map((p) => {
    const pv = p.postwise_vacancy || p.vacancy || {};
    const el = p.eligibility || {};
    const sal = p.salary || {};
    const fee = p.fee || {};
    const male = el.male || {};
    const female = el.female || {};
    const mAgeL = male.age_limit || {};
    const mPhys = (male.physical_standards || {}).general || {};
    const fAgeL = female.age_limit || {};
    const fPhys = (female.physical_standards || {}).all || {};
    return {
      id: Math.random(),
      post_name: p.post_name || '',
      vacancy: {
        total: num(pv.total), ur: num(pv.UR ?? pv.ur), obc: num(pv.OBC ?? pv.obc),
        ews: num(pv.EWS ?? pv.ews), sc: num(pv.SC ?? pv.sc), st: num(pv.ST ?? pv.st),
        pwd: num(pv.PWD ?? pv.pwd), male: num(pv.male), female: num(pv.female),
      },
      eligibility: {
        qualification: el.qualification || '',
        qualification_level: el.qualification_level || '10th',
        male_age_min: num(mAgeL.min), male_age_max: num(mAgeL.max),
        male_height: num(mPhys.height_cm), male_chest: num(mPhys.chest_cm),
        female_age_min: num(fAgeL.min), female_age_max: num(fAgeL.max),
        female_height: num(fPhys.height_cm), female_weight: num(fPhys.weight_kg),
      },
      salary: { min: num(sal.min), max: num(sal.max), pay_level: sal.pay_level || '' },
      fee: {
        general: num(fee.general), obc: num(fee.obc), sc_st: num(fee.sc_st),
        ews: num(fee.ews), female: num(fee.female),
      },
      phases: (p.selection_process || []).map((ph) => ({ id: Math.random(), type: ph.type || 'written_test', name: ph.name || '', qualifying: !!ph.qualifying, details: ph })),
      activeTab: 'vacancy',
    };
  });
}

/* ─── convert state → payload ─── */
export function postsToPayload(posts) {
  return posts.map((p) => {
    const v = p.vacancy;
    const e = p.eligibility;
    const s = p.salary;
    const f = p.fee;
    const n = (x) => (x === '' ? null : Number(x));
    return {
      post_name: p.post_name,
      postwise_vacancy: {
        total: n(v.total), UR: n(v.ur), OBC: n(v.obc), EWS: n(v.ews),
        SC: n(v.sc), ST: n(v.st), PWD: n(v.pwd), male: n(v.male), female: n(v.female), other: 0,
      },
      eligibility: {
        qualification: e.qualification, qualification_level: e.qualification_level,
        male: { age_limit: { min: n(e.male_age_min), max: n(e.male_age_max) }, physical_standards: { general: { height_cm: n(e.male_height), chest_cm: n(e.male_chest) } } },
        female: { age_limit: { min: n(e.female_age_min), max: n(e.female_age_max) }, physical_standards: { all: { height_cm: n(e.female_height), weight_kg: n(e.female_weight) } } },
      },
      salary: { min: n(s.min), max: n(s.max), pay_level: s.pay_level },
      fee: { general: n(f.general), obc: n(f.obc), sc_st: n(f.sc_st), ews: n(f.ews), female: n(f.female) },
      selection_process: p.phases.map((ph, i) => serializePhase(ph, i)),
    };
  });
}

function serializePhase(ph, idx) {
  const d = ph.details || {};
  const base = { phase: idx + 1, type: ph.type, name: ph.name, qualifying: ph.qualifying };
  if (ph.type === 'written_test') return { ...base, mode: d.mode || 'Online', total_marks: d.total_marks || null, duration_minutes: d.duration_minutes || null, negative_marking: d.negative_marking || null, language: d.language || [], subjects: d.subjects || [] };
  if (ph.type === 'physical_test') return { ...base, male: d.male || {}, female: d.female || {} };
  if (ph.type === 'physical_standard') return { ...base, male: d.male || {}, female: d.female || {} };
  if (ph.type === 'skill_test') return { ...base, note: d.note || '' };
  if (ph.type === 'interview') return { ...base, marks: d.marks || null, note: d.note || '' };
  if (ph.type === 'medical') return { ...base, vision: d.vision || '', color_blindness: d.color_blindness || '', other: d.other || '' };
  if (ph.type === 'document') return { ...base, documents: d.documents || [] };
  return base;
}

/* ─── sub-components ─── */

function VacancyTab({ v, onChange }) {
  const cats = [
    { k: 'total', label: 'Total', cls: 'total-cell' },
    { k: 'ur', label: 'UR' }, { k: 'obc', label: 'OBC' }, { k: 'ews', label: 'EWS' },
    { k: 'sc', label: 'SC' }, { k: 'st', label: 'ST' }, { k: 'pwd', label: 'PWD' },
  ];
  return (
    <div>
      <p className="subsection-label">Category-wise</p>
      <div className="vacancy-grid">
        {cats.map(({ k, label, cls = '' }) => (
          <div key={k} className={`vacancy-cell ${cls}`}>
            <label>{label}</label>
            <input type="number" min="0" value={v[k]} onChange={(e) => onChange(k, e.target.value)} placeholder="0" />
          </div>
        ))}
      </div>
      <p className="subsection-label" style={{ marginTop: '.75rem' }}>Gender-wise</p>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.5rem' }}>
        <div className="vacancy-cell male-cell"><label>♂ Male</label><input type="number" min="0" value={v.male} onChange={(e) => onChange('male', e.target.value)} placeholder="0" /></div>
        <div className="vacancy-cell female-cell"><label>♀ Female</label><input type="number" min="0" value={v.female} onChange={(e) => onChange('female', e.target.value)} placeholder="0" /></div>
      </div>
    </div>
  );
}
VacancyTab.propTypes = { v: PropTypes.object.isRequired, onChange: PropTypes.func.isRequired };

function EligibilityTab({ e, onChange }) {
  const QUALS = ['10th', '12th', 'diploma', 'graduate', 'postgraduate', 'phd'];
  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.75rem', marginBottom: '.75rem' }}>
        <div className="form-group">
          <label>Qualification Description</label>
          <input type="text" value={e.qualification} onChange={(ev) => onChange('qualification', ev.target.value)} placeholder="e.g. 10th Pass from recognized board" />
        </div>
        <div className="form-group">
          <label>Qualification Level</label>
          <select value={e.qualification_level} onChange={(ev) => onChange('qualification_level', ev.target.value)}>
            {QUALS.map((q) => <option key={q} value={q}>{q}</option>)}
          </select>
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.75rem' }}>
        <div style={{ border: '1px solid #bfdbfe', borderRadius: '.5rem', padding: '.75rem', background: '#f0f7ff' }}>
          <div style={{ fontSize: '.8rem', fontWeight: 700, color: '#1d4ed8', marginBottom: '.6rem', paddingBottom: '.4rem', borderBottom: '1px solid #e2e8f0' }}>♂ Male</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.5rem' }}>
            <div className="form-group"><label>Age Min</label><input type="number" min="0" value={e.male_age_min} onChange={(ev) => onChange('male_age_min', ev.target.value)} placeholder="18" /></div>
            <div className="form-group"><label>Age Max</label><input type="number" min="0" value={e.male_age_max} onChange={(ev) => onChange('male_age_max', ev.target.value)} placeholder="25" /></div>
            <div className="form-group"><label>Height (cm)</label><input type="number" min="0" value={e.male_height} onChange={(ev) => onChange('male_height', ev.target.value)} placeholder="170" /></div>
            <div className="form-group"><label>Chest (cm)</label><input type="number" min="0" value={e.male_chest} onChange={(ev) => onChange('male_chest', ev.target.value)} placeholder="80" /></div>
          </div>
        </div>
        <div style={{ border: '1px solid #fbcfe8', borderRadius: '.5rem', padding: '.75rem', background: '#fdf4fb' }}>
          <div style={{ fontSize: '.8rem', fontWeight: 700, color: '#9d174d', marginBottom: '.6rem', paddingBottom: '.4rem', borderBottom: '1px solid #e2e8f0' }}>♀ Female</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.5rem' }}>
            <div className="form-group"><label>Age Min</label><input type="number" min="0" value={e.female_age_min} onChange={(ev) => onChange('female_age_min', ev.target.value)} placeholder="18" /></div>
            <div className="form-group"><label>Age Max</label><input type="number" min="0" value={e.female_age_max} onChange={(ev) => onChange('female_age_max', ev.target.value)} placeholder="25" /></div>
            <div className="form-group"><label>Height (cm)</label><input type="number" min="0" value={e.female_height} onChange={(ev) => onChange('female_height', ev.target.value)} placeholder="157" /></div>
            <div className="form-group"><label>Weight (kg)</label><input type="number" min="0" value={e.female_weight} onChange={(ev) => onChange('female_weight', ev.target.value)} placeholder="48" /></div>
          </div>
        </div>
      </div>
    </div>
  );
}
EligibilityTab.propTypes = { e: PropTypes.object.isRequired, onChange: PropTypes.func.isRequired };

function SalaryTab({ salary, fee, onSalary, onFee }) {
  return (
    <div>
      <p className="subsection-label">Salary</p>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '.75rem', marginBottom: '1rem' }}>
        <div className="form-group"><label>Min (₹/month)</label><input type="number" min="0" value={salary.min} onChange={(e) => onSalary('min', e.target.value)} placeholder="21700" /></div>
        <div className="form-group"><label>Max (₹/month)</label><input type="number" min="0" value={salary.max} onChange={(e) => onSalary('max', e.target.value)} placeholder="69100" /></div>
        <div className="form-group"><label>Pay Level</label><input type="text" value={salary.pay_level} onChange={(e) => onSalary('pay_level', e.target.value)} placeholder="Level-3" /></div>
      </div>
      <p className="subsection-label">Application Fee (INR) — Post-specific override</p>
      <div className="fee-grid">
        {[['general', 'General'], ['obc', 'OBC'], ['sc_st', 'SC/ST'], ['ews', 'EWS'], ['female', 'Female']].map(([k, lbl]) => (
          <div key={k} className="fee-cell">
            <label>{lbl}</label>
            <input type="number" min="0" value={fee[k]} onChange={(e) => onFee(k, e.target.value)} placeholder="0" />
          </div>
        ))}
      </div>
    </div>
  );
}
SalaryTab.propTypes = { salary: PropTypes.object.isRequired, fee: PropTypes.object.isRequired, onSalary: PropTypes.func.isRequired, onFee: PropTypes.func.isRequired };

const PHASE_TYPES = [
  { value: 'written_test', label: 'Written Test' },
  { value: 'physical_test', label: 'Physical Test (PET)' },
  { value: 'physical_standard', label: 'Physical Standard (PST)' },
  { value: 'skill_test', label: 'Skill / Typing Test' },
  { value: 'interview', label: 'Interview' },
  { value: 'medical', label: 'Medical Examination' },
  { value: 'document', label: 'Document Verification' },
];

function PhaseDetail({ ph, onChange }) {
  const d = ph.details || {};
  const upd = (field, val) => onChange({ ...ph, details: { ...d, [field]: val } });

  if (ph.type === 'written_test') return (
    <div style={{ padding: '.75rem', background: '#fafafa', borderTop: '1px solid #f1f5f9' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '.75rem' }}>
        <div className="form-group"><label>Total Marks</label><input type="number" min="0" value={d.total_marks || ''} onChange={(e) => upd('total_marks', e.target.value ? Number(e.target.value) : null)} placeholder="160" /></div>
        <div className="form-group"><label>Duration (min)</label><input type="number" min="0" value={d.duration_minutes || ''} onChange={(e) => upd('duration_minutes', e.target.value ? Number(e.target.value) : null)} placeholder="120" /></div>
        <div className="form-group"><label>Negative Marking</label><input type="number" step="0.01" value={d.negative_marking || ''} onChange={(e) => upd('negative_marking', e.target.value ? parseFloat(e.target.value) : null)} placeholder="0.25" /></div>
        <div className="form-group"><label>Mode</label><input type="text" value={d.mode || ''} onChange={(e) => upd('mode', e.target.value)} placeholder="Online" /></div>
      </div>
      <div className="form-group" style={{ marginTop: '.5rem' }}>
        <label>Language(s) <span style={{ fontSize: '.7rem', color: '#94a3b8' }}>(comma separated)</span></label>
        <input type="text" value={(d.language || []).join(', ')} onChange={(e) => upd('language', e.target.value.split(',').map((s) => s.trim()).filter(Boolean))} placeholder="Hindi, English" />
      </div>
      <div className="form-group" style={{ marginTop: '.5rem' }}>
        <label>Subjects <span style={{ fontSize: '.7rem', color: '#94a3b8' }}>(one per line: Subject, Questions, Marks)</span></label>
        <textarea rows={4} value={(d.subjects || []).map((s) => `${s.name}, ${s.questions}, ${s.marks}`).join('\n')}
          onChange={(e) => upd('subjects', e.target.value.split('\n').filter((l) => l.trim()).map((line) => { const p = line.split(',').map((s) => s.trim()); return { name: p[0] || '', questions: parseInt(p[1]) || 0, marks: parseInt(p[2]) || 0 }; }))}
          placeholder={'General Intelligence, 40, 40\nGeneral Knowledge, 40, 40\nMathematics, 40, 40'} />
      </div>
    </div>
  );

  if (ph.type === 'physical_test') {
    const male = d.male || {}; const female = d.female || {};
    const um = (f, v) => upd('male', { ...male, [f]: v });
    const uf = (f, v) => upd('female', { ...female, [f]: v });
    return (
      <div style={{ padding: '.75rem', background: '#fafafa', borderTop: '1px solid #f1f5f9' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.75rem' }}>
          <div style={{ border: '1px solid #bfdbfe', borderRadius: '.5rem', padding: '.75rem', background: '#f0f7ff' }}>
            <div style={{ fontSize: '.8rem', fontWeight: 700, color: '#1d4ed8', marginBottom: '.5rem' }}>♂ Male Criteria</div>
            <div className="form-group"><label>Race</label><input type="text" value={male.race || ''} onChange={(e) => um('race', e.target.value)} placeholder="5 km in 24 min" /></div>
            <div className="form-group" style={{ marginTop: '.4rem' }}><label>Long Jump</label><input type="text" value={male.long_jump || ''} onChange={(e) => um('long_jump', e.target.value)} placeholder="3.65 m" /></div>
            <div className="form-group" style={{ marginTop: '.4rem' }}><label>High Jump</label><input type="text" value={male.high_jump || ''} onChange={(e) => um('high_jump', e.target.value)} placeholder="1.2 m" /></div>
          </div>
          <div style={{ border: '1px solid #fbcfe8', borderRadius: '.5rem', padding: '.75rem', background: '#fdf4fb' }}>
            <div style={{ fontSize: '.8rem', fontWeight: 700, color: '#9d174d', marginBottom: '.5rem' }}>♀ Female Criteria</div>
            <div className="form-group"><label>Race</label><input type="text" value={female.race || ''} onChange={(e) => uf('race', e.target.value)} placeholder="1.6 km in 8.5 min" /></div>
            <div className="form-group" style={{ marginTop: '.4rem' }}><label>Long Jump</label><input type="text" value={female.long_jump || ''} onChange={(e) => uf('long_jump', e.target.value)} placeholder="2.7 m" /></div>
            <div className="form-group" style={{ marginTop: '.4rem' }}><label>High Jump</label><input type="text" value={female.high_jump || ''} onChange={(e) => uf('high_jump', e.target.value)} placeholder="0.9 m" /></div>
          </div>
        </div>
      </div>
    );
  }

  if (ph.type === 'physical_standard') {
    const mg = (d.male || {}).general || {}; const ms = (d.male || {}).sc_st || {}; const fa = (d.female || {}).all || {};
    const ug = (f, v) => upd('male', { ...d.male, general: { ...mg, [f]: v } });
    const us = (f, v) => upd('male', { ...d.male, sc_st: { ...ms, [f]: v } });
    const ua = (f, v) => upd('female', { ...d.female, all: { ...fa, [f]: v } });
    return (
      <div style={{ padding: '.75rem', background: '#fafafa', borderTop: '1px solid #f1f5f9' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.75rem' }}>
          <div style={{ border: '1px solid #bfdbfe', borderRadius: '.5rem', padding: '.75rem', background: '#f0f7ff' }}>
            <div style={{ fontSize: '.8rem', fontWeight: 700, color: '#1d4ed8', marginBottom: '.5rem' }}>♂ Male Standards</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.5rem' }}>
              <div className="form-group"><label>Height General (cm)</label><input type="number" min="0" value={mg.height_cm || ''} onChange={(e) => ug('height_cm', Number(e.target.value))} placeholder="170" /></div>
              <div className="form-group"><label>Chest General (cm)</label><input type="number" min="0" value={mg.chest_cm || ''} onChange={(e) => ug('chest_cm', Number(e.target.value))} placeholder="80" /></div>
              <div className="form-group"><label>Height SC/ST (cm)</label><input type="number" min="0" value={ms.height_cm || ''} onChange={(e) => us('height_cm', Number(e.target.value))} placeholder="165" /></div>
              <div className="form-group"><label>Chest SC/ST (cm)</label><input type="number" min="0" value={ms.chest_cm || ''} onChange={(e) => us('chest_cm', Number(e.target.value))} placeholder="78" /></div>
            </div>
          </div>
          <div style={{ border: '1px solid #fbcfe8', borderRadius: '.5rem', padding: '.75rem', background: '#fdf4fb' }}>
            <div style={{ fontSize: '.8rem', fontWeight: 700, color: '#9d174d', marginBottom: '.5rem' }}>♀ Female Standards</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.5rem' }}>
              <div className="form-group"><label>Height (cm)</label><input type="number" min="0" value={fa.height_cm || ''} onChange={(e) => ua('height_cm', Number(e.target.value))} placeholder="157" /></div>
              <div className="form-group"><label>Weight (kg)</label><input type="number" min="0" value={fa.weight_kg || ''} onChange={(e) => ua('weight_kg', Number(e.target.value))} placeholder="48" /></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (ph.type === 'skill_test') return (
    <div style={{ padding: '.75rem', background: '#fafafa', borderTop: '1px solid #f1f5f9' }}>
      <div className="form-group"><label>Criteria / Note</label><input type="text" value={d.note || ''} onChange={(e) => upd('note', e.target.value)} placeholder="e.g. 35 wpm English or 30 wpm Hindi on computer" /></div>
    </div>
  );

  if (ph.type === 'interview') return (
    <div style={{ padding: '.75rem', background: '#fafafa', borderTop: '1px solid #f1f5f9' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.75rem' }}>
        <div className="form-group"><label>Total Marks</label><input type="number" min="0" value={d.marks || ''} onChange={(e) => upd('marks', e.target.value ? Number(e.target.value) : null)} placeholder="100" /></div>
        <div className="form-group"><label>Note / Criteria</label><input type="text" value={d.note || ''} onChange={(e) => upd('note', e.target.value)} placeholder="e.g. Personality test" /></div>
      </div>
    </div>
  );

  if (ph.type === 'medical') return (
    <div style={{ padding: '.75rem', background: '#fafafa', borderTop: '1px solid #f1f5f9' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.75rem' }}>
        <div className="form-group"><label>Vision Standard</label><input type="text" value={d.vision || ''} onChange={(e) => upd('vision', e.target.value)} placeholder="6/6 in one eye, 6/9 in other" /></div>
        <div className="form-group"><label>Colour Blindness</label><input type="text" value={d.color_blindness || ''} onChange={(e) => upd('color_blindness', e.target.value)} placeholder="Not permitted" /></div>
        <div className="form-group" style={{ gridColumn: 'span 2' }}><label>Other Criteria</label><input type="text" value={d.other || ''} onChange={(e) => upd('other', e.target.value)} placeholder="No flat foot, knock knee, squint eyes" /></div>
      </div>
    </div>
  );

  if (ph.type === 'document') return (
    <div style={{ padding: '.75rem', background: '#fafafa', borderTop: '1px solid #f1f5f9' }}>
      <div className="form-group">
        <label>Documents Required <span style={{ fontSize: '.7rem', color: '#94a3b8' }}>(one per line)</span></label>
        <textarea rows={4} value={(d.documents || []).join('\n')} onChange={(e) => upd('documents', e.target.value.split('\n').map((s) => s.trim()).filter(Boolean))} placeholder={'10th Certificate\nAadhar Card\nPhotograph (JPG)\nCategory Certificate'} />
      </div>
    </div>
  );

  return null;
}
PhaseDetail.propTypes = { ph: PropTypes.object.isRequired, onChange: PropTypes.func.isRequired };

function SelectionProcessTab({ phases, onChange }) {
  function addPhase() { onChange([...phases, emptyPhase()]); }
  function removePhase(id) { onChange(phases.filter((p) => p.id !== id)); }
  function updatePhase(id, updated) { onChange(phases.map((p) => p.id === id ? updated : p)); }

  return (
    <div>
      {phases.map((ph, i) => (
        <div key={ph.id} style={{ border: '1px solid #e2e8f0', borderRadius: '.5rem', marginBottom: '.75rem', overflow: 'hidden', background: '#fafafa' }}>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: '.75rem', padding: '.75rem', background: '#fff', borderBottom: '1px solid #f1f5f9' }}>
            <div style={{ width: 28, height: 28, background: '#6366f1', color: '#fff', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '.7rem', fontWeight: 700, flexShrink: 0, marginBottom: '.25rem' }}>{i + 1}</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '.75rem', flex: 1 }}>
              <div className="form-group">
                <label>Phase Type</label>
                <select value={ph.type} onChange={(e) => updatePhase(ph.id, { ...ph, type: e.target.value, details: {} })}>
                  {PHASE_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Phase Name</label>
                <input type="text" value={ph.name} onChange={(e) => updatePhase(ph.id, { ...ph, name: e.target.value })} placeholder="e.g. Computer Based Test (CBT)" />
              </div>
              <div className="form-group">
                <label>Qualifying Only?</label>
                <select value={ph.qualifying ? 'true' : 'false'} onChange={(e) => updatePhase(ph.id, { ...ph, qualifying: e.target.value === 'true' })}>
                  <option value="false">No — Marks count</option>
                  <option value="true">Yes — Pass / Fail</option>
                </select>
              </div>
            </div>
            <button type="button" onClick={() => removePhase(ph.id)} style={{ background: 'none', border: 'none', color: '#cbd5e1', cursor: 'pointer', padding: '.3rem', borderRadius: '.25rem', marginBottom: '.25rem', display: 'flex' }} title="Remove phase"><X size={14} /></button>
          </div>
          <PhaseDetail ph={ph} onChange={(updated) => updatePhase(ph.id, updated)} />
        </div>
      ))}
      <button type="button" onClick={addPhase} style={{ display: 'flex', alignItems: 'center', gap: '.35rem', background: 'none', border: '1.5px dashed #d1d5db', borderRadius: '.5rem', padding: '.5rem 1rem', fontSize: '.82rem', fontWeight: 600, color: '#64748b', cursor: 'pointer', width: '100%', justifyContent: 'center', marginTop: '.25rem' }}>+ Add Phase</button>
    </div>
  );
}
SelectionProcessTab.propTypes = { phases: PropTypes.array.isRequired, onChange: PropTypes.func.isRequired };

/* ─── PostCard ─── */
function PostCard({ post, idx, onUpdate, onRemove }) {
  const TABS = ['vacancy', 'eligibility', 'salary', 'process'];
  const TAB_LABELS = { vacancy: 'Vacancy', eligibility: 'Eligibility', salary: 'Salary & Fee', process: 'Selection Process' };

  function upd(field, val) { onUpdate({ ...post, [field]: val }); }

  return (
    <div style={{ border: '1px solid #e2e8f0', borderRadius: '.625rem', marginBottom: '1rem', background: '#fff', boxShadow: '0 1px 3px rgba(0,0,0,.05)', overflow: 'hidden' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '.75rem', padding: '.75rem 1rem', background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
        <span style={{ background: '#f59e0b', color: '#fff', fontSize: '.65rem', fontWeight: 800, padding: '.15rem .45rem', borderRadius: '.25rem', letterSpacing: '.05em', whiteSpace: 'nowrap', flexShrink: 0 }}>POST #{idx + 1}</span>
        <input
          type="text"
          value={post.post_name}
          onChange={(e) => upd('post_name', e.target.value)}
          placeholder="Post name, e.g. Constable GD"
          style={{ border: 'none', borderBottom: '2px solid #e2e8f0', borderRadius: 0, padding: '.3rem .2rem', fontSize: '.95rem', fontWeight: 600, color: '#111827', flex: 1, background: 'transparent', outline: 'none' }}
        />
        <button type="button" onClick={onRemove} style={{ background: 'none', border: 'none', color: '#d1d5db', cursor: 'pointer', padding: '.2rem .4rem', borderRadius: '.25rem', display: 'flex' }} title="Remove post"><Trash2 size={15} /></button>
      </div>

      <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', background: '#f9fafb', padding: '0 .5rem', gap: '.1rem' }}>
        {TABS.map((t) => (
          <button key={t} type="button" onClick={() => upd('activeTab', t)}
            style={{ background: 'none', border: 'none', padding: '.55rem .9rem', fontSize: '.8rem', fontWeight: 600, color: post.activeTab === t ? '#f59e0b' : '#6b7280', cursor: 'pointer', borderBottom: post.activeTab === t ? '2px solid #f59e0b' : '2px solid transparent', marginBottom: -1 }}>
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>

      <div style={{ padding: '1rem' }}>
        {post.activeTab === 'vacancy' && <VacancyTab v={post.vacancy} onChange={(k, v) => upd('vacancy', { ...post.vacancy, [k]: v })} />}
        {post.activeTab === 'eligibility' && <EligibilityTab e={post.eligibility} onChange={(k, v) => upd('eligibility', { ...post.eligibility, [k]: v })} />}
        {post.activeTab === 'salary' && <SalaryTab salary={post.salary} fee={post.fee} onSalary={(k, v) => upd('salary', { ...post.salary, [k]: v })} onFee={(k, v) => upd('fee', { ...post.fee, [k]: v })} />}
        {post.activeTab === 'process' && <SelectionProcessTab phases={post.phases} onChange={(phases) => upd('phases', phases)} />}
      </div>
    </div>
  );
}
PostCard.propTypes = {
  post: PropTypes.object.isRequired,
  idx: PropTypes.number.isRequired,
  onUpdate: PropTypes.func.isRequired,
  onRemove: PropTypes.func.isRequired,
};

/* ─── Main export ─── */
export default function PostsBuilder({ posts, onChange }) {
  function add() { onChange([...posts, emptyPost()]); }
  function remove(id) { onChange(posts.filter((p) => p.id !== id)); }
  function update(id, updated) { onChange(posts.map((p) => p.id === id ? updated : p)); }

  return (
    <div className="section-card">
      <div className="section-header section-header--orange" style={{ display: 'flex', alignItems: 'center' }}>
        Posts &amp; Vacancies
        <button type="button" onClick={add} style={{ marginLeft: 'auto', background: 'rgba(255,255,255,.2)', border: '1px solid rgba(255,255,255,.4)', color: '#fff', borderRadius: '.375rem', padding: '.2rem .65rem', fontSize: '.8rem', cursor: 'pointer', fontWeight: 600 }}>+ Add Post</button>
      </div>
      <div className="section-body">
        {posts.length === 0 && (
          <div style={{ textAlign: 'center', padding: '1.5rem', color: '#94a3b8' }}>
            <div style={{ marginBottom: '.5rem', display: 'flex', justifyContent: 'center' }}><ClipboardList size={32} strokeWidth={1.5} /></div>
            <p style={{ fontSize: '.88rem', margin: '0 0 .75rem' }}>No posts added yet. Add posts with their vacancy breakdown and selection process.</p>
            <button type="button" className="btn btn-outline" onClick={add}>+ Add First Post</button>
          </div>
        )}
        {posts.map((p, i) => (
          <PostCard key={p.id} post={p} idx={i} onUpdate={(updated) => update(p.id, updated)} onRemove={() => remove(p.id)} />
        ))}
      </div>
    </div>
  );
}

PostsBuilder.propTypes = {
  posts: PropTypes.arrayOf(PropTypes.object).isRequired,
  onChange: PropTypes.func.isRequired,
};
