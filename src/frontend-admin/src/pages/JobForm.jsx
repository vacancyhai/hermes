import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import client from '../api/client';

const STATUSES = ['active', 'upcoming', 'closed', 'inactive'];
const QUALIFICATIONS = ['10th', '12th', 'Diploma', 'Graduation', 'Post Graduation', 'PhD', 'Any'];
const LINK_TYPES = ['official_notification', 'apply_online', 'admit_card', 'answer_key', 'result', 'syllabus', 'other'];
const PHASE_TABS = [
  { key: 'admit_cards', label: 'Admit Cards', color: '#1d4ed8', api: 'admit-cards', parentKey: 'job_id' },
  { key: 'answer_keys', label: 'Answer Keys', color: '#6d28d9', api: 'answer-keys', parentKey: 'job_id' },
  { key: 'results', label: 'Results', color: '#15803d', api: 'results', parentKey: 'job_id' },
];

const emptyFee = { general: '', obc: '', sc_st: '', ews: '', female: '' };
const emptyVacancy = { total: '', ur: '', obc: '', ews: '', sc: '', st: '', pwd: '', male: '', female: '' };
const emptyLink = { type: 'official_notification', text: '', url: '' };
const emptyDoc = { slug: '', title: '', links_json: '[]', start: '', end: '', published_at: '' };

function safeJson(val, fallback = '') {
  try { return JSON.stringify(JSON.parse(typeof val === 'string' ? val : JSON.stringify(val)), null, 2); }
  catch { return typeof val === 'object' ? JSON.stringify(val, null, 2) : (val || fallback); }
}

export default function JobForm() {
  const { jobId } = useParams();
  const isEdit = !!jobId;
  const navigate = useNavigate();
  const [orgs, setOrgs] = useState([]);
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [flash, setFlash] = useState(null);
  const [activePhaseTab, setActivePhaseTab] = useState('admit_cards');
  const [phaseDocSaving, setPhaseDocSaving] = useState(false);

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

  /* ── phase docs ── */
  const [phaseDocs, setPhaseDocs] = useState({ admit_cards: [], answer_keys: [], results: [] });
  const [newDoc, setNewDoc] = useState({ ...emptyDoc });

  /* ── load data ── */
  useEffect(() => {
    client.get('/admin/organizations', { params: { limit: 200 } }).then((r) => setOrgs(r.data.data || [])).catch(() => {});
  }, []);

  const toDateInput = (v) => (v ? v.split('T')[0] : '');

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
    // Load phase docs separately
    if (j.id) {
      Promise.all([
        client.get(`/admin/admit-cards?job_id=${j.id}&limit=100`).catch(() => ({ data: { data: [] } })),
        client.get(`/admin/answer-keys?job_id=${j.id}&limit=100`).catch(() => ({ data: { data: [] } })),
        client.get(`/admin/results?job_id=${j.id}&limit=100`).catch(() => ({ data: { data: [] } })),
      ]).then(([ac, ak, rs]) => setPhaseDocs({
        admit_cards: ac.data.data || [],
        answer_keys: ak.data.data || [],
        results: rs.data.data || [],
      }));
    }
  }, []);

  useEffect(() => {
    if (!isEdit) return;
    client.get(`/admin/jobs/${jobId}`).then((r) => { populate(r.data); setLoading(false); }).catch(() => { setLoading(false); setFlash({ type: 'error', msg: 'Failed to load job' }); });
  }, [isEdit, jobId, populate]);

  /* ── auto-slug ── */
  function handleTitleChange(v) {
    setJobTitle(v);
    if (!isEdit) setSlug(v.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''));
  }

  /* ── links helpers ── */
  function updateLink(i, field, val) { setLinks((l) => l.map((x, idx) => idx === i ? { ...x, [field]: val } : x)); }
  function addLink() { setLinks((l) => [...l, { ...emptyLink }]); }
  function removeLink(i) { setLinks((l) => l.filter((_, idx) => idx !== i)); }

  /* ── validate JSON ── */
  function validateJson(val, setter, errSetter) {
    setter(val);
    try { JSON.parse(val); errSetter(''); }
    catch (e) { errSetter(e.message); }
  }

  /* ── submit ── */
  async function handleSubmit(e) {
    e.preventDefault();
    if (postsJsonErr || zonesJsonErr) { setFlash({ type: 'error', msg: 'Fix JSON errors before saving.' }); return; }
    setSaving(true); setFlash(null);

    let parsedPosts = []; try { parsedPosts = JSON.parse(postsJson); } catch {}
    let parsedZones = []; try { parsedZones = JSON.parse(zonesJson); } catch {}

    const feeObj = {};
    if (fee.general !== '') feeObj.general = Number(fee.general);
    if (fee.obc !== '') feeObj.obc = Number(fee.obc);
    if (fee.sc_st !== '') feeObj.sc_st = Number(fee.sc_st);
    if (fee.ews !== '') feeObj.ews = Number(fee.ews);
    if (fee.female !== '') feeObj.female = Number(fee.female);

    const totalVacancy = {};
    ['ur','obc','ews','sc','st','pwd','male','female'].forEach((k) => { if (vacancy[k] !== '') totalVacancy[k] = Number(vacancy[k]); });

    const vacancyBreakdown = {};
    if (parsedPosts.length) vacancyBreakdown.posts = parsedPosts;
    if (parsedZones.length) vacancyBreakdown.zonewise_vacancy = parsedZones;
    if (Object.keys(totalVacancy).length) vacancyBreakdown.total_vacancy = totalVacancy;

    const validLinks = links.filter((l) => l.url);

    const payload = {
      job_title: jobTitle, slug,
      organization: organization || jobTitle,
      organization_id: orgId || null,
      department, qualification_level: qualification, status,
      short_description: shortDesc, description, source_url: sourceUrl,
      notification_date: notifDate || null,
      application_start: appStart || null, application_end: appEnd || null,
      exam_start: examStart || null, exam_end: examEnd || null, result_date: resultDate || null,
      total_vacancies: vacancy.total !== '' ? Number(vacancy.total) : null,
      fee: feeObj,
      vacancy_breakdown: vacancyBreakdown,
      application_details: validLinks.length ? { important_links: validLinks } : {},
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

  const activeTab = PHASE_TABS.find((t) => t.key === activePhaseTab);

  /* ── phase doc add ── */
  async function handleAddPhaseDoc(e) {
    e.preventDefault();
    setPhaseDocSaving(true);
    let links = []; try { links = JSON.parse(newDoc.links_json || '[]'); } catch {}
    const isAdmitCard = activePhaseTab === 'admit_cards';
    const docPayload = {
      slug: newDoc.slug,
      title: newDoc.title,
      [activeTab.parentKey]: jobId,
      links,
      published_at: newDoc.published_at || null,
      ...(isAdmitCard
        ? { exam_start: newDoc.start || null, exam_end: newDoc.end || null }
        : { start_date: newDoc.start || null, end_date: newDoc.end || null }),
    };
    try {
      await client.post(`/admin/${activeTab.api}`, docPayload);
      setNewDoc({ ...emptyDoc });
      const [ac, ak, rs] = await Promise.all([
        client.get(`/admin/admit-cards?job_id=${jobId}&limit=100`).catch(() => ({ data: { data: [] } })),
        client.get(`/admin/answer-keys?job_id=${jobId}&limit=100`).catch(() => ({ data: { data: [] } })),
        client.get(`/admin/results?job_id=${jobId}&limit=100`).catch(() => ({ data: { data: [] } })),
      ]);
      setPhaseDocs({ admit_cards: ac.data.data || [], answer_keys: ak.data.data || [], results: rs.data.data || [] });
      setFlash({ type: 'success', msg: 'Document added.' });
    } catch (err) {
      setFlash({ type: 'error', msg: err.response?.data?.detail || 'Failed to add document' });
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
          <Link to="/jobs" style={{ color: '#64748b', fontSize: '.82rem' }}>← Jobs</Link>
          <h1 style={{ marginTop: '.25rem' }}>{isEdit ? 'Edit Job' : 'New Job'}</h1>
        </div>
        <div style={{ display: 'flex', gap: '.5rem' }}>
          <Link to="/jobs" className="btn btn-outline">Cancel</Link>
          <button className="btn btn-primary" form="job-form" type="submit" disabled={saving}>
            {saving ? <><span className="spinner" /> Saving…</> : (isEdit ? 'Update Job' : 'Create Job')}
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
                <label>Title <span className="req">*</span></label>
                <input type="text" value={jobTitle} onChange={(e) => handleTitleChange(e.target.value)} required />
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
                <label>Organization Name <span className="req">*</span></label>
                <input type="text" value={organization} onChange={(e) => setOrganization(e.target.value)} required placeholder="e.g. UPSC" />
              </div>
              <div className="form-group">
                <label>Organization (Link to record)</label>
                <select value={orgId} onChange={(e) => setOrgId(e.target.value)}>
                  <option value="">— None —</option>
                  {orgs.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Department</label>
                <input type="text" value={department} onChange={(e) => setDepartment(e.target.value)} placeholder="e.g. UPSC, Railway Board" />
              </div>
              <div className="form-group">
                <label>Qualification Level</label>
                <select value={qualification} onChange={(e) => setQualification(e.target.value)}>
                  <option value="">— Any —</option>
                  {QUALIFICATIONS.map((q) => <option key={q} value={q}>{q}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Source URL</label>
                <input type="url" value={sourceUrl} onChange={(e) => setSourceUrl(e.target.value)} placeholder="https://…" />
              </div>
              <div className="form-group col-span-2">
                <label>Short Description</label>
                <input type="text" value={shortDesc} onChange={(e) => setShortDesc(e.target.value)} placeholder="One-line summary" />
              </div>
              <div className="form-group col-span-2">
                <label>Full Description (HTML/Markdown)</label>
                <textarea rows={5} value={description} onChange={(e) => setDescription(e.target.value)} />
              </div>
            </div>
          </div>
        </div>

        {/* ── Important Dates ── */}
        <div className="section-card">
          <div className="section-header section-header--purple">Important Dates</div>
          <div className="section-body">
            <div className="form-grid-3">
              {[['Notification Date', notifDate, setNotifDate],
                ['Application Start', appStart, setAppStart],
                ['Application End', appEnd, setAppEnd],
                ['Exam Start', examStart, setExamStart],
                ['Exam End', examEnd, setExamEnd],
                ['Result Date', resultDate, setResultDate]].map(([label, val, setter]) => (
                <div className="form-group" key={label}>
                  <label>{label}</label>
                  <input type="date" value={val} onChange={(e) => setter(e.target.value)} />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Application Fee ── */}
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

        {/* ── Vacancy Summary ── */}
        <div className="section-card">
          <div className="section-header section-header--green">Vacancy Summary</div>
          <div className="section-body">
            <div className="vacancy-grid">
              {Object.keys(emptyVacancy).map((k) => (
                <div className="vacancy-cell" key={k}>
                  <label>{k.toUpperCase()}</label>
                  <input type="number" min="0" value={vacancy[k]} onChange={(e) => setVacancy((v) => ({ ...v, [k]: e.target.value }))} placeholder="0" />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Important Links ── */}
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
                <button type="button" className="btn btn-sm btn-danger" onClick={() => removeLink(i)} style={{ marginBottom: 0 }}>✕</button>
              </div>
            ))}
          </div>
        </div>

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

      {/* ── Phase Documents (edit only) ── */}
      {isEdit && (
        <div className="section-card" style={{ marginTop: '1.5rem' }}>
          <div className="section-header section-header--slate">Phase Documents</div>
          <div style={{ borderBottom: '1px solid #e2e8f0', display: 'flex', gap: 0 }}>
            {PHASE_TABS.map((tab) => (
              <button key={tab.key} type="button" onClick={() => setActivePhaseTab(tab.key)}
                style={{ padding: '.6rem 1.25rem', border: 'none', background: activePhaseTab === tab.key ? '#fff' : '#f8fafc', borderBottom: activePhaseTab === tab.key ? '2px solid ' + tab.color : '2px solid transparent', color: activePhaseTab === tab.key ? tab.color : '#64748b', fontWeight: activePhaseTab === tab.key ? 700 : 400, cursor: 'pointer', fontSize: '.83rem', transition: 'all .15s' }}>
                {tab.label} <span style={{ background: '#e2e8f0', borderRadius: 9999, padding: '0 6px', fontSize: '.7rem' }}>{phaseDocs[tab.key]?.length || 0}</span>
              </button>
            ))}
          </div>
          <div className="section-body">
            {/* existing docs */}
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

            {/* Add new doc */}
            <form onSubmit={handleAddPhaseDoc}>
              <p style={{ fontWeight: 700, fontSize: '.83rem', marginBottom: '.5rem' }}>Add New Document</p>
              <div style={{ display: 'grid', gridTemplateColumns: '160px 1fr 120px 120px 120px auto', gap: '.5rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label style={{ fontSize: '.7rem' }}>Slug <span className="req">*</span></label>
                  <input type="text" required value={newDoc.slug} onChange={(e) => setNewDoc((d) => ({ ...d, slug: e.target.value }))} placeholder="prelims-2024" style={{ fontSize: '.82rem', padding: '.35rem .5rem' }} />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label style={{ fontSize: '.7rem' }}>Title <span className="req">*</span></label>
                  <input type="text" required value={newDoc.title} onChange={(e) => setNewDoc((d) => ({ ...d, title: e.target.value }))} placeholder="Prelims Admit Card 2024" style={{ fontSize: '.82rem', padding: '.35rem .5rem' }} />
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
                <button type="submit" className="btn btn-success btn-sm" disabled={phaseDocSaving}>
                  {phaseDocSaving ? '…' : '+ Add'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
