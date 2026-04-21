import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import client from '../api/client';

const STATUS_COLORS = { active: 'badge-active', upcoming: 'badge-upcoming', closed: 'badge-closed', inactive: 'badge-inactive' };

export default function Admissions() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [deleting, setDeleting] = useState(null);
  const [flash, setFlash] = useState(null);
  const PER = 20;

  function load() {
    setLoading(true);
    const params = { limit: PER, offset: (page - 1) * PER };
    if (q) params.q = q;
    if (status) params.status = status;
    client.get('/admin/admissions', { params })
      .then((r) => { setItems(r.data.data || []); setTotal(r.data.pagination?.total || 0); })
      .catch(() => setFlash({ type: 'error', msg: 'Failed to load admissions' }))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [page, status]);

  function handleSearch(e) { e.preventDefault(); setPage(1); load(); }

  async function handleDelete(item) {
    if (!confirm(`Delete admission "${item.admission_name}"?`)) return;
    setDeleting(item.id);
    try {
      await client.delete(`/admin/admissions/${item.id}`);
      setFlash({ type: 'success', msg: 'Admission deleted.' });
      load();
    } catch (err) {
      setFlash({ type: 'error', msg: err.response?.data?.detail || 'Delete failed' });
    } finally { setDeleting(null); }
  }

  const totalPages = Math.ceil(total / PER);

  return (
    <div>
      <div className="page-header">
        <h1>Admissions <span style={{ fontWeight: 400, color: '#64748b', fontSize: '1rem' }}>({total})</span></h1>
        <Link to="/admissions/new" className="btn btn-primary">+ New Admission</Link>
      </div>

      {flash && <div className={flash.type === 'success' ? 'flash-success' : 'flash-error'}>{flash.msg}</div>}

      <form className="filters" onSubmit={handleSearch}>
        <input type="search" placeholder="Search name, slug…" value={q} onChange={(e) => setQ(e.target.value)} style={{ minWidth: 220 }} />
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="upcoming">Upcoming</option>
          <option value="closed">Closed</option>
          <option value="inactive">Inactive</option>
        </select>
        <button type="submit" className="btn btn-outline">Search</button>
        {(q || status) && <button type="button" className="btn btn-outline" onClick={() => { setQ(''); setStatus(''); setPage(1); }}>Clear</button>}
      </form>

      {loading ? (
        <p style={{ color: '#64748b' }}>Loading…</p>
      ) : (
        items.length === 0 ? (
          <p style={{ color: '#94a3b8' }}>No admissions found.</p>
        ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Name</th>
              <th>Conducting Body</th>
              <th>Type / Stream</th>
              <th>Status</th>
              <th>App Deadline</th>
              <th>Docs</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((a, idx) => (
              <tr key={a.id}>
                <td style={{ color: '#94a3b8', fontSize: '.8rem' }}>{(page - 1) * PER + idx + 1}</td>
                <td>
                  <div style={{ fontWeight: 600, fontSize: '.875rem' }}>{a.admission_name}</div>
                  <div style={{ color: '#64748b', fontSize: '.75rem' }}>{a.slug}</div>
                </td>
                <td style={{ fontSize: '.85rem' }}>{a.conducting_body || '—'}</td>
                <td style={{ fontSize: '.82rem' }}>
                  {a.admission_type && <span className="badge badge-info" style={{ marginRight: 3 }}>{a.admission_type}</span>}
                  {a.stream && <span style={{ color: '#475569' }}>{a.stream}</span>}
                </td>
                <td><span className={`badge ${STATUS_COLORS[a.status] || 'badge-inactive'}`}>{a.status}</span></td>
                <td style={{ fontSize: '.8rem', color: '#475569' }}>{a.application_end ? new Date(a.application_end).toLocaleDateString() : '—'}</td>
                <td style={{ fontSize: '.75rem' }}>
                  {a.admit_cards_count > 0 && <span className="doc-btn doc-btn--ac">{a.admit_cards_count} AC</span>}
                  {a.answer_keys_count > 0 && <span className="doc-btn doc-btn--ak" style={{ marginLeft: 2 }}>{a.answer_keys_count} AK</span>}
                  {a.results_count > 0 && <span className="doc-btn doc-btn--rs" style={{ marginLeft: 2 }}>{a.results_count} RS</span>}
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '.35rem' }}>
                    <Link to={`/admissions/${a.id}/edit`} className="btn btn-sm btn-outline">Edit</Link>
                    <button className="btn btn-sm btn-danger" onClick={() => handleDelete(a)} disabled={deleting === a.id}>
                      {deleting === a.id ? '…' : 'Del'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        )
      )}

      {totalPages > 1 && (
        <div style={{ display: 'flex', gap: '.5rem', alignItems: 'center', marginTop: '1rem', flexWrap: 'wrap' }}>
          <button className="btn btn-sm btn-outline" disabled={page === 1} onClick={() => setPage(page - 1)}>← Prev</button>
          <span style={{ fontSize: '.85rem', color: '#475569' }}>Page {page} of {totalPages}</span>
          <button className="btn btn-sm btn-outline" disabled={page === totalPages} onClick={() => setPage(page + 1)}>Next →</button>
        </div>
      )}
    </div>
  );
}
