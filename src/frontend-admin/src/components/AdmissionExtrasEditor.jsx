import PropTypes from 'prop-types';
import { X, Activity } from 'lucide-react';

/* ────────────────────────────────────────────────
   Helpers: convert between flat editor state and
   the backend JSONB blobs.
──────────────────────────────────────────────── */

export function eligibilityToState(obj) {
  obj = obj || {};
  return {
    qualification: obj.qualification || '',
    min_percent: obj.min_percent ?? '',
    age_min: obj.age_min ?? '',
    age_max: obj.age_max ?? '',
    attempts: obj.attempts ?? '',
    notes: obj.notes || '',
  };
}
export function eligibilityToPayload(s) {
  const n = (v) => (v === '' ? null : Number(v));
  const out = {};
  if (s.qualification) out.qualification = s.qualification;
  if (s.min_percent !== '') out.min_percent = n(s.min_percent);
  if (s.age_min !== '') out.age_min = n(s.age_min);
  if (s.age_max !== '') out.age_max = n(s.age_max);
  if (s.attempts !== '') out.attempts = n(s.attempts);
  if (s.notes) out.notes = s.notes;
  return out;
}

export function admDetailsToState(obj) {
  obj = obj || {};
  return {
    mode: obj.mode || '',
    duration: obj.duration_minutes ?? obj.duration ?? '',
    total_marks: obj.total_marks ?? '',
    total_questions: obj.total_questions ?? '',
    negative_marking: obj.negative_marking ?? '',
    language: Array.isArray(obj.language) ? obj.language.join(', ') : (obj.language || ''),
    subjects: Array.isArray(obj.subjects)
      ? obj.subjects.map((s) => `${s.name}, ${s.questions}, ${s.marks}`).join('\n')
      : '',
  };
}
export function admDetailsToPayload(s) {
  const n = (v) => (v === '' ? null : Number(v));
  const out = {};
  if (s.mode) out.mode = s.mode;
  if (s.duration !== '') out.duration_minutes = n(s.duration);
  if (s.total_marks !== '') out.total_marks = n(s.total_marks);
  if (s.total_questions !== '') out.total_questions = n(s.total_questions);
  if (s.negative_marking !== '') out.negative_marking = parseFloat(s.negative_marking) || null;
  if (s.language) out.language = s.language.split(',').map((x) => x.trim()).filter(Boolean);
  if (s.subjects) {
    out.subjects = s.subjects.split('\n').filter((l) => l.trim()).map((line) => {
      const p = line.split(',').map((x) => x.trim());
      return { name: p[0] || '', questions: parseInt(p[1]) || 0, marks: parseInt(p[2]) || 0 };
    });
  }
  return out;
}

export function seatsToState(obj) {
  obj = obj || {};
  return {
    total: obj.total ?? '',
    ur: obj.UR ?? obj.ur ?? '',
    obc: obj.OBC ?? obj.obc ?? '',
    ews: obj.EWS ?? obj.ews ?? '',
    sc: obj.SC ?? obj.sc ?? '',
    st: obj.ST ?? obj.st ?? '',
  };
}
export function seatsToPayload(s) {
  const n = (v) => (v === '' ? null : Number(v));
  const out = {};
  if (s.total !== '') out.total = n(s.total);
  if (s.ur !== '') out.UR = n(s.ur);
  if (s.obc !== '') out.OBC = n(s.obc);
  if (s.ews !== '') out.EWS = n(s.ews);
  if (s.sc !== '') out.SC = n(s.sc);
  if (s.st !== '') out.ST = n(s.st);
  return out;
}

const ADM_PHASE_TYPES = [
  { value: 'written_test', label: 'Written Test' },
  { value: 'counselling', label: 'Counselling' },
  { value: 'interview', label: 'Interview / Personality Test' },
  { value: 'document', label: 'Document Verification' },
  { value: 'seat_allotment', label: 'Seat Allotment' },
  { value: 'other', label: 'Other' },
];

const emptyPhase = () => ({
  id: Math.random(),
  type: 'written_test',
  name: '',
  qualifying: false,
  details: {},
});

export function selectionToState(obj) {
  if (!obj) return [];
  const arr = Array.isArray(obj) ? obj : (obj.phases || []);
  return arr.map((ph) => ({ id: Math.random(), type: ph.type || 'written_test', name: ph.name || '', qualifying: !!ph.qualifying, details: ph }));
}
export function selectionToPayload(phases) {
  return phases.map((ph, i) => {
    const d = ph.details || {};
    const base = { phase: i + 1, type: ph.type, name: ph.name, qualifying: ph.qualifying };
    if (ph.type === 'written_test') return { ...base, total_marks: d.total_marks || null, duration_minutes: d.duration_minutes || null, negative_marking: d.negative_marking || null, subjects: d.subjects || [] };
    if (ph.type === 'counselling') return { ...base, note: d.note || '' };
    if (ph.type === 'interview') return { ...base, marks: d.marks || null, note: d.note || '' };
    if (ph.type === 'document') return { ...base, documents: d.documents || [] };
    if (ph.type === 'seat_allotment') return { ...base, note: d.note || '' };
    return { ...base, note: d.note || '' };
  });
}

/* ────────────────────────────────────────────────
   Sub-component: phase detail fields
──────────────────────────────────────────────── */
function PhaseDetail({ ph, onChange }) {
  const d = ph.details || {};
  const upd = (field, val) => onChange({ ...ph, details: { ...d, [field]: val } });

  if (ph.type === 'written_test') return (
    <div style={{ padding: '.75rem', background: '#fafafa', borderTop: '1px solid #f1f5f9' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '.75rem' }}>
        <div className="form-group"><label>Total Marks</label><input type="number" min="0" value={d.total_marks || ''} onChange={(e) => upd('total_marks', e.target.value ? Number(e.target.value) : null)} placeholder="360" /></div>
        <div className="form-group"><label>Duration (min)</label><input type="number" min="0" value={d.duration_minutes || ''} onChange={(e) => upd('duration_minutes', e.target.value ? Number(e.target.value) : null)} placeholder="180" /></div>
        <div className="form-group"><label>Negative Marking</label><input type="number" step="0.01" value={d.negative_marking || ''} onChange={(e) => upd('negative_marking', e.target.value ? parseFloat(e.target.value) : null)} placeholder="1.0" /></div>
      </div>
      <div className="form-group" style={{ marginTop: '.5rem' }}>
        <label>Subjects <span style={{ fontSize: '.7rem', color: '#94a3b8' }}>(one per line: Subject, Questions, Marks)</span></label>
        <textarea rows={3} value={(d.subjects || []).map((s) => `${s.name}, ${s.questions}, ${s.marks}`).join('\n')}
          onChange={(e) => upd('subjects', e.target.value.split('\n').filter((l) => l.trim()).map((line) => { const p = line.split(',').map((x) => x.trim()); return { name: p[0] || '', questions: parseInt(p[1]) || 0, marks: parseInt(p[2]) || 0 }; }))}
          placeholder={'Physics, 50, 180\nChemistry, 50, 180\nBiology, 100, 360'} />
      </div>
    </div>
  );

  if (ph.type === 'interview') return (
    <div style={{ padding: '.75rem', background: '#fafafa', borderTop: '1px solid #f1f5f9' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '.75rem' }}>
        <div className="form-group"><label>Marks</label><input type="number" min="0" value={d.marks || ''} onChange={(e) => upd('marks', e.target.value ? Number(e.target.value) : null)} /></div>
        <div className="form-group"><label>Note</label><input type="text" value={d.note || ''} onChange={(e) => upd('note', e.target.value)} placeholder="e.g. Personality test / Demo teaching" /></div>
      </div>
    </div>
  );

  if (ph.type === 'document') return (
    <div style={{ padding: '.75rem', background: '#fafafa', borderTop: '1px solid #f1f5f9' }}>
      <div className="form-group">
        <label>Documents Required <span style={{ fontSize: '.7rem', color: '#94a3b8' }}>(one per line)</span></label>
        <textarea rows={3} value={(d.documents || []).join('\n')} onChange={(e) => upd('documents', e.target.value.split('\n').map((s) => s.trim()).filter(Boolean))} placeholder={'10th Certificate\nAadhar Card\nCategory Certificate'} />
      </div>
    </div>
  );

  /* counselling, seat_allotment, other */
  return (
    <div style={{ padding: '.75rem', background: '#fafafa', borderTop: '1px solid #f1f5f9' }}>
      <div className="form-group"><label>Note</label><input type="text" value={d.note || ''} onChange={(e) => upd('note', e.target.value)} placeholder="e.g. JoSAA rounds 1-6" /></div>
    </div>
  );
}
PhaseDetail.propTypes = { ph: PropTypes.object.isRequired, onChange: PropTypes.func.isRequired };

/* ────────────────────────────────────────────────
   Main export: composed of 4 sections
──────────────────────────────────────────────── */
export default function AdmissionExtrasEditor({
  eligibility, onEligibility,
  admDetails, onAdmDetails,
  seats, onSeats,
  phases, onPhases,
}) {
  function addPhase() { onPhases([...phases, emptyPhase()]); }
  function removePhase(id) { onPhases(phases.filter((p) => p.id !== id)); }
  function updatePhase(id, updated) { onPhases(phases.map((p) => p.id === id ? updated : p)); }

  return (
    <>
      {/* ── Admission Pattern & Details ── */}
      <div className="section-card">
        <div className="section-header section-header--teal">Admission Pattern &amp; Details</div>
        <div className="section-body">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '.75rem' }}>
            <div className="form-group">
              <label>Mode</label>
              <select value={admDetails.mode} onChange={(e) => onAdmDetails('mode', e.target.value)}>
                <option value="">— select —</option>
                <option value="Online">Online (CBT)</option>
                <option value="Offline">Offline (OMR)</option>
                <option value="Online + Offline">Online + Offline</option>
              </select>
            </div>
            <div className="form-group">
              <label>Duration (minutes)</label>
              <input type="number" min="0" value={admDetails.duration} onChange={(e) => onAdmDetails('duration', e.target.value)} placeholder="180" />
            </div>
            <div className="form-group">
              <label>Total Marks</label>
              <input type="number" min="0" value={admDetails.total_marks} onChange={(e) => onAdmDetails('total_marks', e.target.value)} placeholder="720" />
            </div>
            <div className="form-group">
              <label>Total Questions</label>
              <input type="number" min="0" value={admDetails.total_questions} onChange={(e) => onAdmDetails('total_questions', e.target.value)} placeholder="200" />
            </div>
            <div className="form-group">
              <label>Negative Marking</label>
              <input type="number" step="0.01" value={admDetails.negative_marking} onChange={(e) => onAdmDetails('negative_marking', e.target.value)} placeholder="0.25" />
            </div>
            <div className="form-group">
              <label>Language(s) <span style={{ fontSize: '.7rem', color: '#94a3b8' }}>(comma separated)</span></label>
              <input type="text" value={admDetails.language} onChange={(e) => onAdmDetails('language', e.target.value)} placeholder="Hindi, English" />
            </div>
          </div>
          <div className="form-group" style={{ marginTop: '.75rem' }}>
            <label>Subjects <span style={{ fontSize: '.7rem', color: '#94a3b8' }}>(one per line: Subject, Questions, Marks)</span></label>
            <textarea rows={4} value={admDetails.subjects} onChange={(e) => onAdmDetails('subjects', e.target.value)} placeholder={'Physics, 50, 180\nChemistry, 50, 180\nBiology, 100, 360'} />
          </div>
        </div>
      </div>

      {/* ── Eligibility ── */}
      <div className="section-card">
        <div className="section-header section-header--orange">Eligibility</div>
        <div className="section-body">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '.75rem' }}>
            <div className="form-group" style={{ gridColumn: 'span 2' }}>
              <label>Qualification Required</label>
              <input type="text" value={eligibility.qualification} onChange={(e) => onEligibility('qualification', e.target.value)} placeholder="e.g. MBBS / BDS from MCI recognised institution" />
            </div>
            <div className="form-group">
              <label>Min % in Qualifying</label>
              <input type="number" min="0" max="100" value={eligibility.min_percent} onChange={(e) => onEligibility('min_percent', e.target.value)} placeholder="50" />
            </div>
            <div className="form-group">
              <label>Min Age</label>
              <input type="number" min="0" value={eligibility.age_min} onChange={(e) => onEligibility('age_min', e.target.value)} placeholder="17" />
            </div>
            <div className="form-group">
              <label>Max Age (General)</label>
              <input type="number" min="0" value={eligibility.age_max} onChange={(e) => onEligibility('age_max', e.target.value)} placeholder="25" />
            </div>
            <div className="form-group">
              <label>Attempts Allowed</label>
              <input type="number" min="0" value={eligibility.attempts} onChange={(e) => onEligibility('attempts', e.target.value)} placeholder="3" />
            </div>
          </div>
          <div className="form-group" style={{ marginTop: '.75rem' }}>
            <label>Additional Notes</label>
            <input type="text" value={eligibility.notes} onChange={(e) => onEligibility('notes', e.target.value)} placeholder="e.g. NRI / OCI candidates must apply through MCC" />
          </div>
        </div>
      </div>

      {/* ── Seats Info ── */}
      <div className="section-card">
        <div className="section-header section-header--indigo">Seats Information</div>
        <div className="section-body">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6,1fr)', gap: '.5rem' }}>
            {[['total', 'Total', 'total-cell'], ['ur', 'UR', ''], ['obc', 'OBC', ''], ['ews', 'EWS', ''], ['sc', 'SC', ''], ['st', 'ST', '']].map(([k, lbl, cls]) => (
              <div key={k} className={`vacancy-cell ${cls}`}>
                <label>{lbl}</label>
                <input type="number" min="0" value={seats[k]} onChange={(e) => onSeats(k, e.target.value)} placeholder="0" />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Selection Process ── */}
      <div className="section-card">
        <div className="section-header section-header--orange" style={{ display: 'flex', alignItems: 'center' }}>
          Selection Process
          <button type="button" onClick={addPhase} style={{ marginLeft: 'auto', background: 'rgba(255,255,255,.2)', border: '1px solid rgba(255,255,255,.4)', color: '#fff', borderRadius: '.375rem', padding: '.2rem .65rem', fontSize: '.8rem', cursor: 'pointer', fontWeight: 600 }}>+ Add Phase</button>
        </div>
        <div className="section-body">
          {phases.length === 0 && (
            <div style={{ textAlign: 'center', padding: '1.5rem', color: '#94a3b8' }}>
              <div style={{ marginBottom: '.5rem', display: 'flex', justifyContent: 'center' }}><Activity size={32} strokeWidth={1.5} /></div>
              <p style={{ fontSize: '.88rem', margin: '0 0 .75rem' }}>No phases added. Skip if not applicable.</p>
              <button type="button" className="btn btn-outline" onClick={addPhase}>+ Add Phase</button>
            </div>
          )}
          {phases.map((ph, i) => (
            <div key={ph.id} style={{ border: '1px solid #e2e8f0', borderRadius: '.5rem', marginBottom: '.75rem', overflow: 'hidden', background: '#fafafa' }}>
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: '.75rem', padding: '.75rem', background: '#fff', borderBottom: '1px solid #f1f5f9' }}>
                <div style={{ width: 28, height: 28, background: '#f59e0b', color: '#fff', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '.7rem', fontWeight: 700, flexShrink: 0, marginBottom: '.25rem' }}>{i + 1}</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '.75rem', flex: 1 }}>
                  <div className="form-group">
                    <label>Phase Type</label>
                    <select value={ph.type} onChange={(e) => updatePhase(ph.id, { ...ph, type: e.target.value, details: {} })}>
                      {ADM_PHASE_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Phase Name</label>
                    <input type="text" value={ph.name} onChange={(e) => updatePhase(ph.id, { ...ph, name: e.target.value })} placeholder="e.g. JEE Advanced Paper 1 & 2" />
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
        </div>
      </div>
    </>
  );
}

AdmissionExtrasEditor.propTypes = {
  eligibility: PropTypes.object.isRequired,
  onEligibility: PropTypes.func.isRequired,
  admDetails: PropTypes.object.isRequired,
  onAdmDetails: PropTypes.func.isRequired,
  seats: PropTypes.object.isRequired,
  onSeats: PropTypes.func.isRequired,
  phases: PropTypes.array.isRequired,
  onPhases: PropTypes.func.isRequired,
};
