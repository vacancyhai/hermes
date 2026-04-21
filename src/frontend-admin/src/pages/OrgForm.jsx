import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import client from '../api/client';

const ORG_TYPES = ['jobs', 'admissions', 'both'];

export default function OrgForm() {
  const { orgId } = useParams();
  const isEdit = !!orgId;
  const navigate = useNavigate();
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [flash, setFlash] = useState(null);

  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [shortName, setShortName] = useState('');
  const [orgType, setOrgType] = useState('both');
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [logoUrl, setLogoUrl] = useState('');

  useEffect(() => {
    if (!isEdit) return;
    client.get(`/admin/organizations/${orgId}`)
      .then((r) => {
        const o = r.data;
        setName(o.name || '');
        setSlug(o.slug || '');
        setShortName(o.short_name || '');
        setOrgType(o.org_type || 'both');
        setWebsiteUrl(o.website_url || '');
        setLogoUrl(o.logo_url || '');
        setLoading(false);
      })
      .catch(() => { setLoading(false); setFlash({ type: 'error', msg: 'Failed to load organization' }); });
  }, [isEdit, orgId]);

  function handleNameChange(v) {
    setName(v);
    if (!isEdit) setSlug(v.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true); setFlash(null);
    const payload = { name, slug, short_name: shortName || null, org_type: orgType || 'both', website_url: websiteUrl || null, logo_url: logoUrl || null };
    try {
      if (isEdit) {
        await client.put(`/admin/organizations/${orgId}`, payload);
        setFlash({ type: 'success', msg: 'Organization updated.' });
      } else {
        const res = await client.post('/admin/organizations', payload);
        setFlash({ type: 'success', msg: 'Organization created.' });
        navigate(`/organizations/${res.data.id}/edit`, { replace: true });
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
          <Link to="/organizations" style={{ color: '#64748b', fontSize: '.82rem' }}>← Organizations</Link>
          <h1 style={{ marginTop: '.25rem' }}>{isEdit ? 'Edit Organization' : 'New Organization'}</h1>
        </div>
        <div style={{ display: 'flex', gap: '.5rem' }}>
          <Link to="/organizations" className="btn btn-outline">Cancel</Link>
          <button className="btn btn-primary" form="org-form" type="submit" disabled={saving}>
            {saving ? <><span className="spinner" /> Saving…</> : (isEdit ? 'Update' : 'Create')}
          </button>
        </div>
      </div>

      {flash && <div className={flash.type === 'success' ? 'flash-success' : 'flash-error'}>{flash.msg}</div>}

      <form id="org-form" onSubmit={handleSubmit}>
        <div className="section-card">
          <div className="section-header section-header--green">Organization Details</div>
          <div className="section-body">
            <div className="form-grid-2">
              <div className="form-group col-span-2">
                <label>Name <span className="req">*</span></label>
                <input type="text" value={name} onChange={(e) => handleNameChange(e.target.value)} required />
              </div>
              <div className="form-group">
                <label>Slug <span className="req">*</span></label>
                <input type="text" value={slug} onChange={(e) => setSlug(e.target.value)} required placeholder="url-friendly-name" />
              </div>
              <div className="form-group">
                <label>Short Name / Abbreviation</label>
                <input type="text" value={shortName} onChange={(e) => setShortName(e.target.value)} placeholder="e.g. UPSC, ISRO" />
              </div>
              <div className="form-group">
                <label>Type <span className="req">*</span></label>
                <select value={orgType} onChange={(e) => setOrgType(e.target.value)} required>
                  {ORG_TYPES.map((t) => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Website URL</label>
                <input type="url" value={websiteUrl} onChange={(e) => setWebsiteUrl(e.target.value)} placeholder="https://…" />
              </div>
              <div className="form-group">
                <label>Logo URL</label>
                <input type="url" value={logoUrl} onChange={(e) => setLogoUrl(e.target.value)} placeholder="https://…/logo.png" />
              </div>
            </div>
            {logoUrl && (
              <div style={{ marginTop: '.5rem' }}>
                <p style={{ fontSize: '.78rem', color: '#64748b', marginBottom: '.25rem' }}>Logo preview:</p>
                <img src={logoUrl} alt="Logo preview" style={{ maxWidth: 80, maxHeight: 80, objectFit: 'contain', border: '1px solid #e2e8f0', borderRadius: '.375rem', padding: '.25rem' }} onError={(e) => { e.target.style.display = 'none'; }} />
              </div>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}
