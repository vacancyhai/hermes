import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import client from '../api/client';
import AdminPagination from '../components/AdminPagination';

export default function Organizations() {
  const [orgs, setOrgs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [deleting, setDeleting] = useState(null);
  const [flash, setFlash] = useState(null);
  const PER = 25;

  function load() {
    setLoading(true);
    const params = { limit: PER, offset: (page - 1) * PER };
    if (q) params.search = q;
    client.get('/admin/organizations', { params })
      .then((r) => { setOrgs(r.data.data || []); setTotal(r.data.total || 0); })
      .catch(() => setFlash({ type: 'error', msg: 'Failed to load organizations' }))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [page]);

  function handleSearch(e) { e.preventDefault(); setPage(1); load(); }

  async function handleDelete(org) {
    if (!confirm(`Delete organization "${org.name}"? Jobs linked to it will lose their org.`)) return;
    setDeleting(org.id);
    try {
      await client.delete(`/admin/organizations/${org.id}`);
      setFlash({ type: 'success', msg: 'Organization deleted.' });
      load();
    } catch (err) {
      setFlash({ type: 'error', msg: err.response?.data?.detail || 'Delete failed' });
    } finally { setDeleting(null); }
  }

  const totalPages = Math.ceil(total / PER);

  return (
    <div>
      <div className="page-header">
        <h1>Organizations <span style={{ fontWeight: 400, color: '#64748b', fontSize: '1rem' }}>({total})</span></h1>
        <Link to="/organizations/new" className="btn btn-primary">+ New Organization</Link>
      </div>

      {flash && <div className={flash.type === 'success' ? 'flash-success' : 'flash-error'}>{flash.msg}</div>}

      <form className="filters" onSubmit={handleSearch}>
        <input type="search" placeholder="Search name, slug…" value={q} onChange={(e) => setQ(e.target.value)} style={{ minWidth: 220 }} />
        <button type="submit" className="btn btn-outline">Search</button>
        {q && <button type="button" className="btn btn-outline" onClick={() => { setQ(''); setPage(1); }}>Clear</button>}
      </form>

      {loading && (
        <table className="data-table">
          <thead><tr><th>#</th><th>Name</th><th>Short Name</th><th>Type</th><th>Jobs</th><th>Followers</th><th>Actions</th></tr></thead>
          <tbody>
            {Array.from({ length: 8 }).map((_, i) => (
              <tr key={i} className="skeleton-row">
                <td><span className="skeleton" style={{ width: 18, height: 12 }} /></td>
                <td><div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><span className="skeleton" style={{ width: 24, height: 24, borderRadius: 4 }} /><div><div className="skeleton" style={{ width: 150, height: 13, marginBottom: 4 }} /><div className="skeleton" style={{ width: 100, height: 10 }} /></div></div></td>
                <td><span className="skeleton" style={{ width: 70, height: 13 }} /></td>
                <td><span className="skeleton" style={{ width: 60, height: 13 }} /></td>
                <td style={{ textAlign: 'center' }}><span className="skeleton" style={{ width: 24, height: 13 }} /></td>
                <td style={{ textAlign: 'center' }}><span className="skeleton" style={{ width: 24, height: 13 }} /></td>
                <td><div style={{ display: 'flex', gap: 4 }}><span className="skeleton" style={{ width: 36, height: 26, borderRadius: 4 }} /><span className="skeleton" style={{ width: 28, height: 26, borderRadius: 4 }} /></div></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {!loading && orgs.length === 0 && <p style={{ color: '#94a3b8' }}>No organizations found.</p>}
      {!loading && orgs.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Name</th>
              <th>Short Name</th>
              <th>Type</th>
              <th>Jobs</th>
              <th>Followers</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {orgs.map((o, idx) => (
              <tr key={o.id}>
                <td style={{ color: '#94a3b8', fontSize: '.8rem' }}>{(page - 1) * PER + idx + 1}</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '.5rem' }}>
                    {o.logo_url && <img src={o.logo_url} alt="" style={{ width: 24, height: 24, borderRadius: 4, objectFit: 'contain', background: '#f1f5f9' }} />}
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '.875rem' }}>{o.name}</div>
                      <div style={{ color: '#64748b', fontSize: '.75rem' }}>{o.slug}</div>
                    </div>
                  </div>
                </td>
                <td style={{ fontSize: '.85rem' }}>{o.short_name || '—'}</td>
                <td style={{ fontSize: '.82rem' }}>{o.org_type || '—'}</td>
                <td style={{ textAlign: 'center', fontSize: '.85rem' }}>{o.jobs_count ?? '—'}</td>
                <td style={{ textAlign: 'center', fontSize: '.85rem' }}>{o.followers_count ?? '—'}</td>
                <td>
                  <div style={{ display: 'flex', gap: '.35rem' }}>
                    <Link to={`/organizations/${o.id}/edit`} className="btn btn-sm btn-outline">Edit</Link>
                    <button className="btn btn-sm btn-danger" onClick={() => handleDelete(o)} disabled={deleting === o.id}>
                      {deleting === o.id ? '…' : 'Del'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <AdminPagination page={page} totalPages={totalPages} onPage={setPage} />
    </div>
  );
}
