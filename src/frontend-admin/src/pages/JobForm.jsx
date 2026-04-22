import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import client from '../api/client';
import PhaseDocsPanel from '../components/PhaseDocsPanel';
import ImportantLinksEditor from '../components/ImportantLinksEditor';
import FeeGrid from '../components/FeeGrid';
import { STATUSES, emptyFee, emptyLink, safeJson, validateJson, buildFeeObj, toDateInput, makeSlug } from '../lib/formUtils';

const QUALIFICATIONS = ['10th', '12th', 'Diploma', 'Graduation', 'Post Graduation', 'PhD', 'Any'];
const emptyVacancy = { total: '', ur: '', obc: '', ews: '', sc: '', st: '', pwd: '', male: '', female: '' };

export default function JobForm() {
  const { jobId } = useParams();
  const isEdit = !!jobId;
  const navigate = useNavigate();
  const [orgs, setOrgs] = useState([]);
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [flash, setFlash] = useState(null);

  /* ── basic fields ── */
  const [jobTitle, setJobTitle] = useState('');
  const [slug, setSlug] = useState('');
  const [organization, setOrganization] = useState('');
  const [orgId, setOrgId] = useState('');
  const [department, setDepartment] = useState('');
  const [qualification, setQualification] = useState('');
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

  /* ── fee & vacancies ── */
  const [fee, setFee] = useState({ ...emptyFee });
  const [vacancy, setVacancy] = useState({ ...emptyVacancy });

  /* ── links ── */
  const [links, setLinks] = useState([{ ...emptyLink }]);

  /* ── posts JSON ── */
  const [postsJson, setPostsJson] = useState('[]');
  const [postsJsonErr, setPostsJsonErr] = useState('');

  /* ── zone vacancies JSON ── */
  const [zonesJson, setZonesJson] = useState('[]');
  const [zonesJsonErr, setZonesJsonErr] = useState('');

  /* ── load data ── */
  useEffect(() => {
    client.get('/admin/organizations', { params: { limit: 200 } }).then((r) => setOrgs(r.data.data || [])).catch(() => {});
  }, []);

  const populate = useCallback((j) => {
    setJobTitle(j.job_title || '');
    setSlug(j.slug || '');
    setOrganization(j.organization || '');
    setOrgId(j.organization_id || '');
    setDepartment(j.department || '');
    setQualification(j.qualification_level || '');
    setStatus(j.status || 'upcoming');
    setShortDesc(j.short_description || '');
    setDescription(j.description || '');
    setSourceUrl(j.source_url || '');
    setNotifDate(toDateInput(j.notification_date));
    setAppStart(toDateInput(j.application_start));
    setAppEnd(toDateInput(j.application_end));
    setExamStart(toDateInput(j.exam_start));
    setExamEnd(toDateInput(j.exam_end));
    setResultDate(toDateInput(j.result_date));
    const fee = j.fee || {};
    setFee({ general: fee.general ?? '', obc: fee.obc ?? '', sc_st: fee.sc_st ?? '', ews: fee.ews ?? '', female: fee.female ?? '' });
    const vb = j.vacancy_breakdown || {};
    const tv = vb.total_vacancy || {};
    setVacancy({ total: j.total_vacancies ?? '', ur: tv.ur ?? '', obc: tv.obc ?? '', ews: tv.ews ?? '', sc: tv.sc ?? '', st: tv.st ?? '', pwd: tv.pwd ?? '', male: tv.male ?? '', female: tv.female ?? '' });
    const appDetails = j.application_details || {};
    setLinks(Array.isArray(appDetails.important_links) && appDetails.important_links.length ? appDetails.important_links : [{ ...emptyLink }]);
    setPostsJson(safeJson(vb.posts || [], '[]'));
    setZonesJson(safeJson(vb.zonewise_vacancy || [], '[]'));
  }, []);

  useEffect(() => {
    if (isEdit) {
      client.get(`/admin/jobs/${jobId}`).then((r) => { populate(r.data); setLoading(false); }).catch(() => { setLoading(false); setFlash({ type: 'error', msg: 'Failed to load job' }); });
    }
  }, [isEdit, jobId, populate]);

  /* ── auto-slug ── */
  function handleTitleChange(v) {
    setJobTitle(v);
    if (isEdit === false) setSlug(makeSlug(v));
  }

  /* ── links helpers ── */
  function updateLink(i, field, val) { setLinks((l) => l.map((x, idx) => idx === i ? { ...x, [field]: val } : x)); }
  function addLink() { setLinks((l) => [...l, { ...emptyLink }]); }
  function removeLink(i) { setLinks((l) => l.filter((_, idx) => idx !== i)); }

  /* ── submit ── */
  async function handleSubmit(e) {
    e.preventDefault();
    if (postsJsonErr || zonesJsonErr) { setFlash({ type: 'error', msg: 'Fix JSON errors before saving.' }); return; }
    setSaving(true); setFlash(null);

    let parsedPosts = []; try { parsedPosts = JSON.parse(postsJson); } catch {}
    let parsedZones = []; try { parsedZones = JSON.parse(zonesJson); } catch {}

    const feeObj = buildFeeObj(fee);

    const totalVacancy = {};
    ['ur','obc','ews','sc','st','pwd','male','female'].forEach((k) => { if (vacancy[k] !== '') totalVacancy[k] = Number(vacancy[k]); });

    const vacancyBreakdown = {};
    if (parsedPosts.length) vacancyBreakdown.posts = parsedPosts;
    if (parsedZones.length) vacancyBreakdown.zonewise_vacancy = parsedZones;
    if (Object.keys(totalVacancy).length) vacancyBreakdown.total_vacancy = totalVacancy;

    const payload = {
      job_title: jobTitle, slug,
      organization: organization || jobTitle,
      organization_id: orgId || null,
      department, qualification_level: qualification, status,
      short_description: shortDesc, description, source_url: sourceUrl,
      notification_date: notifDate || null,
      application_start: appStart || null, application_end: appEnd || null,
      exam_start: examStart || null, exam_end: examEnd || null, result_date: resultDate || null,
      total_vacancies: vacancy.total === '' ? null : Number(vacancy.total),
      fee: feeObj,
      vacancy_breakdown: vacancyBreakdown,
      application_details: links.filter((l) => l.url).length ? { important_links: links.filter((l) => l.url) } : {},
    };

    try {
      if (isEdit) {
        await client.put(`/admin/jobs/${jobId}`, payload);
        setFlash({ type: 'success', msg: 'Job updated successfully.' });
        client.get(`/admin/jobs/${jobId}`).then((r) => populate(r.data)).catch(() => {});
      } else {
        const res = await client.post('/admin/jobs', payload);
        setFlash({ type: 'success', msg: 'Job created.' });
        navigate(`/jobs/${res.data.id}/edit`, { replace: true });
      }
    } catch (err) {
      setFlash({ type: 'error', msg: err.response?.data?.detail || 'Save failed' });
    } finally { setSaving(false); }
  }

  if (loading) return <p style={{ color: '#64748b' }}>Loading…</p>;

  const saveBtnLabel = isEdit ? 'Update Job' : 'Create Job';

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to="/jobs" style={{ color: '#64748b', fontSize: '.82rem' }}>← Jobs</Link>
          <h1 style={{ marginTop: '.25rem' }}>{isEdit ? 'Edit Job' : 'New Job'}</h1>
        </div>
        <div style={{ display: 'flex', gap: '.5rem' }}>
          <Link to="/jobs" className="btn btn-outline">Cancel</Link>
          <button className="btn btn-primary" form="job-form" type="submit" disabled={saving}>
            {saving ? <><span className="spinner" />{' '}Saving…</> : saveBtnLabel}
          </button>
        </div>
      </div>

      {flash && <div className={flash.type === 'success' ? 'flash-success' : 'flash-error'}>{flash.msg}</div>}

      <form id="job-form" onSubmit={handleSubmit}>
        {/* ── Basic Info ── */}
        <div className="section-card">
          <div className="section-header section-header--blue">Basic Information</div>
          <div className="section-body">
            <div className="form-grid-2">
              <div className="form-group col-span-2">
                <label htmlFor="job-title">Title <span className="req">*</span></label>
                <input id="job-title" type="text" value={jobTitle} onChange={(e) => handleTitleChange(e.target.value)} required />
              </div>
              <div className="form-group">
                <label htmlFor="job-slug">Slug <span className="req">*</span></label>
                <input id="job-slug" type="text" value={slug} onChange={(e) => setSlug(e.target.value)} required />
              </div>
              <div className="form-group">
                <label htmlFor="job-status">Status</label>
                <select id="job-status" value={status} onChange={(e) => setStatus(e.target.value)}>
                  {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="job-org-name">Organization Name <span className="req">*</span></label>
                <input id="job-org-name" type="text" value={organization} onChange={(e) => setOrganization(e.target.value)} required placeholder="e.g. UPSC" />
              </div>
              <div className="form-group">
                <label htmlFor="job-org-link">Organization (Link to record)</label>
                <select id="job-org-link" value={orgId} onChange={(e) => setOrgId(e.target.value)}>
                  <option value="">— None —</option>
                  {orgs.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="job-dept">Department</label>
                <input id="job-dept" type="text" value={department} onChange={(e) => setDepartment(e.target.value)} placeholder="e.g. UPSC, Railway Board" />
              </div>
              <div className="form-group">
                <label htmlFor="job-qual">Qualification Level</label>
                <select id="job-qual" value={qualification} onChange={(e) => setQualification(e.target.value)}>
                  <option value="">— Any —</option>
                  {QUALIFICATIONS.map((q) => <option key={q} value={q}>{q}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="job-source">Source URL</label>
                <input id="job-source" type="url" value={sourceUrl} onChange={(e) => setSourceUrl(e.target.value)} placeholder="https://…" />
              </div>
              <div className="form-group col-span-2">
                <label htmlFor="job-shortdesc">Short Description</label>
                <input id="job-shortdesc" type="text" value={shortDesc} onChange={(e) => setShortDesc(e.target.value)} placeholder="One-line summary" />
              </div>
              <div className="form-group col-span-2">
                <label htmlFor="job-desc">Full Description (HTML/Markdown)</label>
                <textarea id="job-desc" rows={5} value={description} onChange={(e) => setDescription(e.target.value)} />
              </div>
            </div>
          </div>
        </div>

        {/* ── Important Dates ── */}
        <div className="section-card">
          <div className="section-header section-header--purple">Important Dates</div>
          <div className="section-body">
            <div className="form-grid-3">
              {[['Notification Date', notifDate, setNotifDate, 'job-notif'],
                ['Application Start', appStart, setAppStart, 'job-app-start'],
                ['Application End', appEnd, setAppEnd, 'job-app-end'],
                ['Exam Start', examStart, setExamStart, 'job-exam-start'],
                ['Exam End', examEnd, setExamEnd, 'job-exam-end'],
                ['Result Date', resultDate, setResultDate, 'job-result']].map(([label, val, setter, id]) => (
                <div className="form-group" key={label}>
                  <label htmlFor={id}>{label}</label>
                  <input id={id} type="date" value={val} onChange={(e) => setter(e.target.value)} />
                </div>
              ))}
            </div>
          </div>
        </div>

        <FeeGrid prefix="job" fee={fee} onChange={(k, v) => setFee((f) => ({ ...f, [k]: v }))} />

        {/* ── Vacancy Summary ── */}
        <div className="section-card">
          <div className="section-header section-header--green">Vacancy Summary</div>
          <div className="section-body">
            <div className="vacancy-grid">
              {Object.keys(emptyVacancy).map((k) => (
                <div className="vacancy-cell" key={k}>
                  <label htmlFor={`job-vac-${k}`}>{k.toUpperCase()}</label>
                  <input id={`job-vac-${k}`} type="number" min="0" value={vacancy[k]} onChange={(e) => setVacancy((v) => ({ ...v, [k]: e.target.value }))} placeholder="0" />
                </div>
              ))}
            </div>
          </div>
        </div>

        <ImportantLinksEditor prefix="link" links={links} onUpdate={updateLink} onAdd={addLink} onRemove={removeLink} />

        {/* ── Posts JSON ── */}
        <div className="section-card">
          <div className="section-header section-header--teal">Posts (JSON Array)</div>
          <div className="section-body">
            <p style={{ fontSize: '.78rem', color: '#64748b', marginBottom: '.5rem' }}>
              Array of post objects: <code>{`[{"post_name":"","vacancy":0,"eligibility":"","salary":"","selection_process":""}]`}</code>
            </p>
            <textarea rows={8} value={postsJson} onChange={(e) => validateJson(e.target.value, setPostsJson, setPostsJsonErr)}
              style={{ width: '100%', fontFamily: 'monospace', fontSize: '.82rem', borderColor: postsJsonErr ? '#ef4444' : undefined }} />
            {postsJsonErr && <p style={{ color: '#ef4444', fontSize: '.78rem', marginTop: '.25rem' }}>JSON error: {postsJsonErr}</p>}
          </div>
        </div>

        {/* ── Zone Vacancies JSON ── */}
        <div className="section-card">
          <div className="section-header section-header--slate">Zone-wise Vacancies (JSON Array)</div>
          <div className="section-body">
            <p style={{ fontSize: '.78rem', color: '#64748b', marginBottom: '.5rem' }}>
              Array: <code>{`[{"zone":"","total":0,"ur":0,"obc":0,"sc":0,"st":0}]`}</code>
            </p>
            <textarea rows={5} value={zonesJson} onChange={(e) => validateJson(e.target.value, setZonesJson, setZonesJsonErr)}
              style={{ width: '100%', fontFamily: 'monospace', fontSize: '.82rem', borderColor: zonesJsonErr ? '#ef4444' : undefined }} />
            {zonesJsonErr && <p style={{ color: '#ef4444', fontSize: '.78rem', marginTop: '.25rem' }}>JSON error: {zonesJsonErr}</p>}
          </div>
        </div>
      </form>

      {isEdit && <PhaseDocsPanel parentKey="job_id" parentId={jobId} onFlash={setFlash} />}
    </div>
  );
}
