import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import client from '../api/client';

const STATUSES = ['active', 'upcoming', 'closed', 'inactive'];
const TYPES = ['undergraduate', 'postgraduate', 'diploma', 'phd', 'certificate', 'other'];
const STREAMS = ['engineering', 'medical', 'law', 'management', 'arts', 'science', 'commerce', 'other'];
const LINK_TYPES = ['official_notification', 'apply_online', 'admit_card', 'answer_key', 'result', 'syllabus', 'other'];
const PHASE_TABS = [
  { key: 'admit_cards', label: 'Admit Cards', color: '#1d4ed8', api: 'admit-cards', parentKey: 'admission_id' },
  { key: 'answer_keys', label: 'Answer Keys', color: '#6d28d9', api: 'answer-keys', parentKey: 'admission_id' },
  { key: 'results', label: 'Results', color: '#15803d', api: 'results', parentKey: 'admission_id' },
];

const emptyFee = { general: '', obc: '', sc_st: '', ews: '', female: '' };
const emptyLink = { type: 'official_notification', text: '', url: '' };
const emptyDoc = { slug: '', title: '', start: '', end: '', published_at: '' };

function safeJson(val, fallback = '{}') {
  try { return JSON.stringify(JSON.parse(typeof val === 'string' ? val : JSON.stringify(val)), null, 2); }
  catch { return typeof val === 'object' ? JSON.stringify(val, null, 2) : (val || fallback); }
}

export default function AdmissionForm() {
  const { admissionId } = useParams();
  const isEdit = !!admissionId;
  const navigate = useNavigate();
  const [orgs, setOrgs] = useState([]);
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [flash, setFlash] = useState(null);
  const [activePhaseTab, setActivePhaseTab] = useState('admit_cards');
  const [phaseDocSaving, setPhaseDocSaving] = useState(false);

  /* ── basic fields ── */
  const [admissionName, setAdmissionName] = useState('');
  const [slug, setSlug] = useState('');
  const [orgId, setOrgId] = useState('');
  const [conductingBody, setConductingBody] = useState('');
  const [counsellingBody, setCounsellingBody] = useState('');
  const [admissionType, setAdmissionType] = useState('');
  const [stream, setStream] = useState('');
  const [status, setStatus] = useState('upcoming');
  const [shortDesc, setShortDesc] = useState('');
  const [description, setDescription] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');

  /* ── dates ── */
  const [notifDate, setNotifDate] = useState('');
  const [appStart, setAppStart] = useState('');
  const [appEnd, setAppEnd] = useState('');
  const [examStart, setExamStart] = useState('');
  const [examEnd, setExamEnd] = useState('');
  const [resultDate, setResultDate] = useState('');
  const [counsellingStart, setCounsellingStart] = useState('');

  /* ── fee ── */
  const [fee, setFee] = useState({ ...emptyFee });

  /* ── links ── */
  const [links, setLinks] = useState([{ ...emptyLink }]);

  /* ── JSON fields ── */
  const [eligibilityJson, setEligibilityJson] = useState('{}');
  const [eligibilityErr, setEligibilityErr] = useState('');
  const [selectionJson, setSelectionJson] = useState('{}');
  const [selectionErr, setSelectionErr] = useState('');
  const [admDetailsJson, setAdmDetailsJson] = useState('{}');
  const [admDetailsErr, setAdmDetailsErr] = useState('');
  const [seatsJson, setSeatsJson] = useState('{}');
  const [seatsErr, setSeatsErr] = useState('');

  /* ── phase docs ── */
  const [phaseDocs, setPhaseDocs] = useState({ admit_cards: [], answer_keys: [], results: [] });
  const [newDoc, setNewDoc] = useState({ ...emptyDoc });

  useEffect(() => {
    client.get('/admin/organizations', { params: { limit: 200 } }).then((r) => setOrgs(r.data.data || [])).catch(() => {});
  }, []);

  const toDateInput = (v) => (v ? v.split('T')[0] : '');

  const populate = useCallback((a) => {
    setAdmissionName(a.admission_name || '');
    setSlug(a.slug || '');
    setOrgId(a.organization_id || '');
    setConductingBody(a.conducting_body || '');
    setCounsellingBody(a.counselling_body || '');
    setAdmissionType(a.admission_type || '');
    setStream(a.stream || '');
    setStatus(a.status || 'upcoming');
    setShortDesc(a.short_description || '');
    setDescription(a.description || '');
    setSourceUrl(a.source_url || '');
    setNotifDate(toDateInput(a.notification_date));
    setAppStart(toDateInput(a.application_start));
    setAppEnd(toDateInput(a.application_end));
    setExamStart(toDateInput(a.exam_start));
    setExamEnd(toDateInput(a.exam_end));
    setResultDate(toDateInput(a.result_date));
    setCounsellingStart(toDateInput(a.counselling_start));
    const f = a.fee || {};
    setFee({ general: f.general ?? '', obc: f.obc ?? '', sc_st: f.sc_st ?? '', ews: f.ews ?? '', female: f.female ?? '' });
    const appLinks = (a.application_details || {}).important_links;
    setLinks(Array.isArray(appLinks) && appLinks.length ? appLinks : [{ ...emptyLink }]);
    setEligibilityJson(safeJson(a.eligibility, '{}'));
    setSelectionJson(safeJson(a.selection_process, '{}'));
    setAdmDetailsJson(safeJson(a.admission_details, '{}'));
    setSeatsJson(safeJson(a.seats_info, '{}'));
    if (a.id) {
      Promise.all([
        client.get(`/admin/admit-cards?admission_id=${a.id}&limit=100`).catch(() => ({ data: { data: [] } })),
        client.get(`/admin/answer-keys?admission_id=${a.id}&limit=100`).catch(() => ({ data: { data: [] } })),
        client.get(`/admin/results?admission_id=${a.id}&limit=100`).catch(() => ({ data: { data: [] } })),
      ]).then(([ac, ak, rs]) => setPhaseDocs({ admit_cards: ac.data.data || [], answer_keys: ak.data.data || [], results: rs.data.data || [] }));
    }
  }, []);

  useEffect(() => {
    if (!isEdit) return;
    client.get(`/admin/admissions/${admissionId}`).then((r) => { populate(r.data); setLoading(false); }).catch(() => { setLoading(false); setFlash({ type: 'error', msg: 'Failed to load admission' }); });
  }, [isEdit, admissionId, populate]);

  function handleNameChange(v) {
    setAdmissionName(v);
    if (!isEdit) setSlug(v.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''));
  }

  function updateLink(i, field, val) { setLinks((l) => l.map((x, idx) => idx === i ? { ...x, [field]: val } : x)); }
  function addLink() { setLinks((l) => [...l, { ...emptyLink }]); }
  function removeLink(i) { setLinks((l) => l.filter((_, idx) => idx !== i)); }

  function validateJson(val, setter, errSetter) {
    setter(val);
    try { JSON.parse(val); errSetter(''); } catch (e) { errSetter(e.message); }
  }

  const hasJsonErrors = () => eligibilityErr || selectionErr || admDetailsErr || seatsErr;

  async function handleSubmit(e) {
    e.preventDefault();
    if (hasJsonErrors()) { setFlash({ type: 'error', msg: 'Fix JSON errors before saving.' }); return; }
    setSaving(true); setFlash(null);

    let eligibility = {}; try { eligibility = JSON.parse(eligibilityJson); } catch {}
    let selectionProcess = {}; try { selectionProcess = JSON.parse(selectionJson); } catch {}
    let admissionDetails = {}; try { admissionDetails = JSON.parse(admDetailsJson); } catch {}
    let seatsInfo = {}; try { seatsInfo = JSON.parse(seatsJson); } catch {}

    const feeObj = {};
    if (fee.general !== '') feeObj.general = Number(fee.general);
    if (fee.obc !== '') feeObj.obc = Number(fee.obc);
    if (fee.sc_st !== '') feeObj.sc_st = Number(fee.sc_st);
    if (fee.ews !== '') feeObj.ews = Number(fee.ews);
    if (fee.female !== '') feeObj.female = Number(fee.female);

    const validLinks = links.filter((l) => l.url);

    const payload = {
      admission_name: admissionName, slug, organization_id: orgId || null,
      conducting_body: conductingBody, counselling_body: counsellingBody,
      admission_type: admissionType || null, stream: stream || null, status,
      short_description: shortDesc, description, source_url: sourceUrl,
      application_start: appStart || null, application_end: appEnd || null,
      exam_start: examStart || null, exam_end: examEnd || null, result_date: resultDate || null,
      counselling_start: counsellingStart || null,
      fee: feeObj,
      eligibility, selection_process: selectionProcess,
      admission_details: admissionDetails, seats_info: seatsInfo,
    };

    try {
      if (isEdit) {
        await client.put(`/admin/admissions/${admissionId}`, payload);
        setFlash({ type: 'success', msg: 'Admission updated.' });
        client.get(`/admin/admissions/${admissionId}`).then((r) => populate(r.data)).catch(() => {});
      } else {
        const res = await client.post('/admin/admissions', payload);
        setFlash({ type: 'success', msg: 'Admission created.' });
        navigate(`/admissions/${res.data.id}/edit`, { replace: true });
      }
    } catch (err) {
      setFlash({ type: 'error', msg: err.response?.data?.detail || 'Save failed' });
    } finally { setSaving(false); }
  }

  const activeTab = PHASE_TABS.find((t) => t.key === activePhaseTab);

  async function handleAddPhaseDoc(e) {
    e.preventDefault(); setPhaseDocSaving(true);
    const isAdmitCard = activePhaseTab === 'admit_cards';
    const docPayload = {
      slug: newDoc.slug,
      title: newDoc.title,
      [activeTab.parentKey]: admissionId,
      links: [],
      published_at: newDoc.published_at || null,
      ...(isAdmitCard
        ? { exam_start: newDoc.start || null, exam_end: newDoc.end || null }
        : { start_date: newDoc.start || null, end_date: newDoc.end || null }),
    };
    try {
      await client.post(`/admin/${activeTab.api}`, docPayload);
      setNewDoc({ ...emptyDoc });
      const [ac, ak, rs] = await Promise.all([
        client.get(`/admin/admit-cards?admission_id=${admissionId}&limit=100`).catch(() => ({ data: { data: [] } })),
        client.get(`/admin/answer-keys?admission_id=${admissionId}&limit=100`).catch(() => ({ data: { data: [] } })),
        client.get(`/admin/results?admission_id=${admissionId}&limit=100`).catch(() => ({ data: { data: [] } })),
      ]);
      setPhaseDocs({ admit_cards: ac.data.data || [], answer_keys: ak.data.data || [], results: rs.data.data || [] });
      setFlash({ type: 'success', msg: 'Document added.' });
    } catch (err) {
      setFlash({ type: 'error', msg: err.response?.data?.detail || 'Failed' });
    } finally { setPhaseDocSaving(false); }
  }

  async function handleDeletePhaseDoc(docId) {
    if (!confirm('Delete this document?')) return;
    try {
      await client.delete(`/admin/${activeTab.api}/${docId}`);
      setPhaseDocs((prev) => ({ ...prev, [activePhaseTab]: prev[activePhaseTab].filter((d) => d.id !== docId) }));
    } catch (err) {
      setFlash({ type: 'error', msg: err.response?.data?.detail || 'Delete failed' });
    }
  }

  if (loading) return <p style={{ color: '#64748b' }}>Loading…</p>;

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to="/admissions" style={{ color: '#64748b', fontSize: '.82rem' }}>← Admissions</Link>
          <h1 style={{ marginTop: '.25rem' }}>{isEdit ? 'Edit Admission' : 'New Admission'}</h1>
        </div>
        <div style={{ display: 'flex', gap: '.5rem' }}>
          <Link to="/admissions" className="btn btn-outline">Cancel</Link>
          <button className="btn btn-primary" form="admission-form" type="submit" disabled={saving}>
            {saving ? <><span className="spinner" /> Saving…</> : (isEdit ? 'Update' : 'Create')}
          </button>
        </div>
      </div>

      {flash && <div className={flash.type === 'success' ? 'flash-success' : 'flash-error'}>{flash.msg}</div>}

      <form id="admission-form" onSubmit={handleSubmit}>
        {/* Basic Info */}
        <div className="section-card">
          <div className="section-header section-header--purple">Basic Information</div>
          <div className="section-body">
            <div className="form-grid-2">
              <div className="form-group col-span-2">
                <label>Admission Name <span className="req">*</span></label>
                <input type="text" value={admissionName} onChange={(e) => handleNameChange(e.target.value)} required />
              </div>
              <div className="form-group">
                <label>Slug <span className="req">*</span></label>
                <input type="text" value={slug} onChange={(e) => setSlug(e.target.value)} required />
              </div>
              <div className="form-group">
                <label>Status</label>
                <select value={status} onChange={(e) => setStatus(e.target.value)}>
                  {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Conducting Body</label>
                <input type="text" value={conductingBody} onChange={(e) => setConductingBody(e.target.value)} placeholder="e.g. NTA, JoSAA" />
              </div>
              <div className="form-group">
                <label>Counselling Body</label>
                <input type="text" value={counsellingBody} onChange={(e) => setCounsellingBody(e.target.value)} />
              </div>
              <div className="form-group">
                <label>Admission Type</label>
                <select value={admissionType} onChange={(e) => setAdmissionType(e.target.value)}>
                  <option value="">— Any —</option>
                  {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Stream</label>
                <select value={stream} onChange={(e) => setStream(e.target.value)}>
                  <option value="">— Any —</option>
                  {STREAMS.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Organization</label>
                <select value={orgId} onChange={(e) => setOrgId(e.target.value)}>
                  <option value="">— None —</option>
                  {orgs.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Source URL</label>
                <input type="url" value={sourceUrl} onChange={(e) => setSourceUrl(e.target.value)} placeholder="https://…" />
              </div>
              <div className="form-group col-span-2">
                <label>Short Description</label>
                <input type="text" value={shortDesc} onChange={(e) => setShortDesc(e.target.value)} />
              </div>
              <div className="form-group col-span-2">
                <label>Full Description</label>
                <textarea rows={4} value={description} onChange={(e) => setDescription(e.target.value)} />
              </div>
            </div>
          </div>
        </div>

        {/* Dates */}
        <div className="section-card">
          <div className="section-header section-header--blue">Important Dates</div>
          <div className="section-body">
            <div className="form-grid-3">
              {[['Notification Date', notifDate, setNotifDate],
                ['Application Start', appStart, setAppStart],
                ['Application End', appEnd, setAppEnd],
                ['Exam Start', examStart, setExamStart],
                ['Exam End', examEnd, setExamEnd],
                ['Result Date', resultDate, setResultDate],
                ['Counselling Start', counsellingStart, setCounsellingStart]].map(([label, val, setter]) => (
                <div className="form-group" key={label}>
                  <label>{label}</label>
                  <input type="date" value={val} onChange={(e) => setter(e.target.value)} />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Fee */}
        <div className="section-card">
          <div className="section-header section-header--orange">Application Fee (₹)</div>
          <div className="section-body">
            <div className="fee-grid">
              {Object.keys(emptyFee).map((k) => (
                <div className="fee-cell" key={k}>
                  <label>{k.toUpperCase().replace('_', '/')}</label>
                  <input type="number" min="0" value={fee[k]} onChange={(e) => setFee((f) => ({ ...f, [k]: e.target.value }))} placeholder="0" />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Important Links */}
        <div className="section-card">
          <div className="section-header section-header--indigo">
            Important Links
            <button type="button" className="btn btn-sm" style={{ background: 'rgba(255,255,255,.2)', color: '#fff', border: '1px solid rgba(255,255,255,.4)' }} onClick={addLink}>+ Add</button>
          </div>
          <div className="section-body" style={{ display: 'flex', flexDirection: 'column', gap: '.5rem' }}>
            {links.map((link, i) => (
              <div key={i} style={{ display: 'grid', gridTemplateColumns: '180px 1fr 2fr auto', gap: '.5rem', alignItems: 'flex-end' }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label style={{ fontSize: '.7rem' }}>Type</label>
                  <select value={link.type} onChange={(e) => updateLink(i, 'type', e.target.value)} style={{ padding: '.35rem .5rem', fontSize: '.82rem' }}>
                    {LINK_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label style={{ fontSize: '.7rem' }}>Display Text</label>
                  <input type="text" value={link.text} onChange={(e) => updateLink(i, 'text', e.target.value)} placeholder="Click here" style={{ padding: '.35rem .5rem', fontSize: '.82rem' }} />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label style={{ fontSize: '.7rem' }}>URL</label>
                  <input type="url" value={link.url} onChange={(e) => updateLink(i, 'url', e.target.value)} placeholder="https://…" style={{ padding: '.35rem .5rem', fontSize: '.82rem' }} />
                </div>
                <button type="button" className="btn btn-sm btn-danger" onClick={() => removeLink(i)}>✕</button>
              </div>
            ))}
          </div>
        </div>

        {/* JSON fields */}
        {[
          ['Eligibility Criteria (JSON)', eligibilityJson, setEligibilityJson, eligibilityErr, setEligibilityErr, 'section-header--green'],
          ['Selection Process (JSON)', selectionJson, setSelectionJson, selectionErr, setSelectionErr, 'section-header--teal'],
          ['Admission Details (JSON)', admDetailsJson, setAdmDetailsJson, admDetailsErr, setAdmDetailsErr, 'section-header--slate'],
          ['Seats Info (JSON)', seatsJson, setSeatsJson, seatsErr, setSeatsErr, 'section-header--red'],
        ].map(([label, val, setter, err, errSetter, colorClass]) => (
          <div className="section-card" key={label}>
            <div className={`section-header ${colorClass}`}>{label}</div>
            <div className="section-body">
              <textarea rows={5} value={val}
                onChange={(e) => validateJson(e.target.value, setter, errSetter)}
                style={{ width: '100%', fontFamily: 'monospace', fontSize: '.82rem', borderColor: err ? '#ef4444' : undefined }} />
              {err && <p style={{ color: '#ef4444', fontSize: '.78rem', marginTop: '.25rem' }}>JSON error: {err}</p>}
            </div>
          </div>
        ))}
      </form>

      {/* Phase Documents (edit only) */}
      {isEdit && (
        <div className="section-card" style={{ marginTop: '1.5rem' }}>
          <div className="section-header section-header--slate">Phase Documents</div>
          <div style={{ borderBottom: '1px solid #e2e8f0', display: 'flex', gap: 0 }}>
            {PHASE_TABS.map((tab) => (
              <button key={tab.key} type="button" onClick={() => setActivePhaseTab(tab.key)}
                style={{ padding: '.6rem 1.25rem', border: 'none', background: activePhaseTab === tab.key ? '#fff' : '#f8fafc', borderBottom: activePhaseTab === tab.key ? '2px solid ' + tab.color : '2px solid transparent', color: activePhaseTab === tab.key ? tab.color : '#64748b', fontWeight: activePhaseTab === tab.key ? 700 : 400, cursor: 'pointer', fontSize: '.83rem' }}>
                {tab.label} <span style={{ background: '#e2e8f0', borderRadius: 9999, padding: '0 6px', fontSize: '.7rem' }}>{phaseDocs[tab.key]?.length || 0}</span>
              </button>
            ))}
          </div>
          <div className="section-body">
            {phaseDocs[activePhaseTab]?.length > 0 ? (
              <table className="data-table" style={{ marginBottom: '1rem' }}>
                <thead><tr><th>Slug</th><th>Title</th><th>Start</th><th>End</th><th>Published</th><th></th></tr></thead>
                <tbody>
                  {phaseDocs[activePhaseTab].map((d) => (
                    <tr key={d.id}>
                      <td style={{ fontSize: '.82rem' }}>{d.slug}</td>
                      <td style={{ fontSize: '.85rem' }}>{d.title || '—'}</td>
                      <td style={{ fontSize: '.8rem' }}>{d.exam_start || d.start_date || '—'}</td>
                      <td style={{ fontSize: '.8rem' }}>{d.exam_end || d.end_date || '—'}</td>
                      <td style={{ fontSize: '.8rem' }}>{d.published_at ? new Date(d.published_at).toLocaleDateString() : '—'}</td>
                      <td><button className="btn btn-sm btn-danger" onClick={() => handleDeletePhaseDoc(d.id)}>Del</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <p style={{ color: '#94a3b8', fontSize: '.875rem', marginBottom: '1rem' }}>No documents yet.</p>}

            <form onSubmit={handleAddPhaseDoc}>
              <p style={{ fontWeight: 700, fontSize: '.83rem', marginBottom: '.5rem' }}>Add New Document</p>
              <div style={{ display: 'grid', gridTemplateColumns: '160px 1fr 120px 120px 120px auto', gap: '.5rem', alignItems: 'flex-end' }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label style={{ fontSize: '.7rem' }}>Slug <span className="req">*</span></label>
                  <input type="text" required value={newDoc.slug} onChange={(e) => setNewDoc((d) => ({ ...d, slug: e.target.value }))} placeholder="jee-main-2024-ac" style={{ fontSize: '.82rem', padding: '.35rem .5rem' }} />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label style={{ fontSize: '.7rem' }}>Title <span className="req">*</span></label>
                  <input type="text" required value={newDoc.title} onChange={(e) => setNewDoc((d) => ({ ...d, title: e.target.value }))} placeholder="JEE Main Admit Card 2024" style={{ fontSize: '.82rem', padding: '.35rem .5rem' }} />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label style={{ fontSize: '.7rem' }}>{activePhaseTab === 'admit_cards' ? 'Exam Start' : 'Start Date'}</label>
                  <input type="date" value={newDoc.start} onChange={(e) => setNewDoc((d) => ({ ...d, start: e.target.value }))} style={{ fontSize: '.82rem', padding: '.35rem .5rem' }} />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label style={{ fontSize: '.7rem' }}>{activePhaseTab === 'admit_cards' ? 'Exam End' : 'End Date'}</label>
                  <input type="date" value={newDoc.end} onChange={(e) => setNewDoc((d) => ({ ...d, end: e.target.value }))} style={{ fontSize: '.82rem', padding: '.35rem .5rem' }} />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label style={{ fontSize: '.7rem' }}>Published At</label>
                  <input type="date" value={newDoc.published_at} onChange={(e) => setNewDoc((d) => ({ ...d, published_at: e.target.value }))} style={{ fontSize: '.82rem', padding: '.35rem .5rem' }} />
                </div>
                <button type="submit" className="btn btn-success btn-sm" disabled={phaseDocSaving}>{phaseDocSaving ? '…' : '+ Add'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
