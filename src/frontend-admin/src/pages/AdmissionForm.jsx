import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import client from '../api/client';
import PhaseDocsPanel from '../components/PhaseDocsPanel';
import ImportantLinksEditor from '../components/ImportantLinksEditor';
import FeeGrid from '../components/FeeGrid';
import { STATUSES, emptyFee, emptyLink, safeJson, validateJson, buildFeeObj, toDateInput, makeSlug } from '../lib/formUtils';

const TYPES = ['undergraduate', 'postgraduate', 'diploma', 'phd', 'certificate', 'other'];
const STREAMS = ['engineering', 'medical', 'law', 'management', 'arts', 'science', 'commerce', 'other'];

export default function AdmissionForm() {
  const { admissionId } = useParams();
  const isEdit = !!admissionId;
  const navigate = useNavigate();
  const [orgs, setOrgs] = useState([]);
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [flash, setFlash] = useState(null);

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

  useEffect(() => {
    client.get('/admin/organizations', { params: { limit: 200 } }).then((r) => setOrgs(r.data.data || [])).catch(() => {});
  }, []);

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
    const appLinks = a.application_details?.important_links;
    setLinks(Array.isArray(appLinks) && appLinks.length ? appLinks : [{ ...emptyLink }]);
    setEligibilityJson(safeJson(a.eligibility, '{}'));
    setSelectionJson(safeJson(a.selection_process, '{}'));
    setAdmDetailsJson(safeJson(a.admission_details, '{}'));
    setSeatsJson(safeJson(a.seats_info, '{}'));
  }, []);

  useEffect(() => {
    if (isEdit) {
      client.get(`/admin/admissions/${admissionId}`).then((r) => { populate(r.data); setLoading(false); }).catch(() => { setLoading(false); setFlash({ type: 'error', msg: 'Failed to load admission' }); });
    }
  }, [isEdit, admissionId, populate]);

  function handleNameChange(v) {
    setAdmissionName(v);
    if (isEdit === false) setSlug(makeSlug(v));
  }

  function updateLink(i, field, val) { setLinks((l) => l.map((x, idx) => idx === i ? { ...x, [field]: val } : x)); }
  function addLink() { setLinks((l) => [...l, { ...emptyLink }]); }
  function removeLink(i) { setLinks((l) => l.filter((_, idx) => idx !== i)); }

  const hasJsonErrors = () => eligibilityErr || selectionErr || admDetailsErr || seatsErr;

  async function handleSubmit(e) {
    e.preventDefault();
    if (hasJsonErrors()) { setFlash({ type: 'error', msg: 'Fix JSON errors before saving.' }); return; }
    setSaving(true); setFlash(null);

    let eligibility = {}; try { eligibility = JSON.parse(eligibilityJson); } catch {}
    let selectionProcess = {}; try { selectionProcess = JSON.parse(selectionJson); } catch {}
    let admissionDetails = {}; try { admissionDetails = JSON.parse(admDetailsJson); } catch {}
    let seatsInfo = {}; try { seatsInfo = JSON.parse(seatsJson); } catch {}

    const feeObj = buildFeeObj(fee);

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
            {saving ? <><span className="spinner" />{' '}Saving…</> : isEdit ? 'Update' : 'Create'}
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
                <label htmlFor="adm-name">Admission Name <span className="req">*</span></label>
                <input id="adm-name" type="text" value={admissionName} onChange={(e) => handleNameChange(e.target.value)} required />
              </div>
              <div className="form-group">
                <label htmlFor="adm-slug">Slug <span className="req">*</span></label>
                <input id="adm-slug" type="text" value={slug} onChange={(e) => setSlug(e.target.value)} required />
              </div>
              <div className="form-group">
                <label htmlFor="adm-status">Status</label>
                <select id="adm-status" value={status} onChange={(e) => setStatus(e.target.value)}>
                  {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="adm-conducting">Conducting Body</label>
                <input id="adm-conducting" type="text" value={conductingBody} onChange={(e) => setConductingBody(e.target.value)} placeholder="e.g. NTA, JoSAA" />
              </div>
              <div className="form-group">
                <label htmlFor="adm-counselling">Counselling Body</label>
                <input id="adm-counselling" type="text" value={counsellingBody} onChange={(e) => setCounsellingBody(e.target.value)} />
              </div>
              <div className="form-group">
                <label htmlFor="adm-type">Admission Type</label>
                <select id="adm-type" value={admissionType} onChange={(e) => setAdmissionType(e.target.value)}>
                  <option value="">— Any —</option>
                  {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="adm-stream">Stream</label>
                <select id="adm-stream" value={stream} onChange={(e) => setStream(e.target.value)}>
                  <option value="">— Any —</option>
                  {STREAMS.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="adm-org">Organization</label>
                <select id="adm-org" value={orgId} onChange={(e) => setOrgId(e.target.value)}>
                  <option value="">— None —</option>
                  {orgs.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="adm-source">Source URL</label>
                <input id="adm-source" type="url" value={sourceUrl} onChange={(e) => setSourceUrl(e.target.value)} placeholder="https://…" />
              </div>
              <div className="form-group col-span-2">
                <label htmlFor="adm-shortdesc">Short Description</label>
                <input id="adm-shortdesc" type="text" value={shortDesc} onChange={(e) => setShortDesc(e.target.value)} />
              </div>
              <div className="form-group col-span-2">
                <label htmlFor="adm-desc">Full Description</label>
                <textarea id="adm-desc" rows={4} value={description} onChange={(e) => setDescription(e.target.value)} />
              </div>
            </div>
          </div>
        </div>

        {/* Dates */}
        <div className="section-card">
          <div className="section-header section-header--blue">Important Dates</div>
          <div className="section-body">
            <div className="form-grid-3">
              {[['Notification Date', notifDate, setNotifDate, 'adm-notif'],
                ['Application Start', appStart, setAppStart, 'adm-app-start'],
                ['Application End', appEnd, setAppEnd, 'adm-app-end'],
                ['Exam Start', examStart, setExamStart, 'adm-exam-start'],
                ['Exam End', examEnd, setExamEnd, 'adm-exam-end'],
                ['Result Date', resultDate, setResultDate, 'adm-result'],
                ['Counselling Start', counsellingStart, setCounsellingStart, 'adm-counsel-start']].map(([label, val, setter, id]) => (
                <div className="form-group" key={label}>
                  <label htmlFor={id}>{label}</label>
                  <input id={id} type="date" value={val} onChange={(e) => setter(e.target.value)} />
                </div>
              ))}
            </div>
          </div>
        </div>

        <FeeGrid prefix="adm" fee={fee} onChange={(k, v) => setFee((f) => ({ ...f, [k]: v }))} />

        <ImportantLinksEditor prefix="alink" links={links} onUpdate={updateLink} onAdd={addLink} onRemove={removeLink} />

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

      {isEdit && <PhaseDocsPanel parentKey="admission_id" parentId={admissionId} onFlash={setFlash} />}
    </div>
  );
}
