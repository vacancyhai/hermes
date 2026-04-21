import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import client from '../api/client';

export default function Users() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [flash, setFlash] = useState(null);
  const [acting, setActing] = useState(null);
  const PER = 25;

  function load() {
    setLoading(true);
    const params = { limit: PER, offset: (page - 1) * PER };
    if (q) params.q = q;
    if (statusFilter) params.status = statusFilter;
    client.get('/admin/users', { params })
      .then((r) => { setUsers(r.data.data || []); setTotal(r.data.pagination?.total || 0); })
      .catch(() => setFlash({ type: 'error', msg: 'Failed to load users' }))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [page, statusFilter]);

  function handleSearch(e) { e.preventDefault(); setPage(1); load(); }

  async function handleSuspend(user) {
    const isSuspended = user.status === 'suspended';
    const msg = isSuspended ? `Reactivate "${user.email}"?` : `Suspend "${user.email}"?`;
    if (!confirm(msg)) return;
    setActing(user.id);
    try {
      await client.put(`/admin/users/${user.id}/status`, { status: isSuspended ? 'active' : 'suspended' });
      setFlash({ type: 'success', msg: isSuspended ? 'User reactivated.' : 'User suspended.' });
      load();
    } catch (err) {
      setFlash({ type: 'error', msg: err.response?.data?.detail || 'Action failed' });
    } finally { setActing(null); }
  }

  async function handleDelete(user) {
    if (!confirm(`Permanently delete "${user.email}"? This cannot be undone.`)) return;
    setActing(user.id);
    try {
      await client.delete(`/admin/users/${user.id}`);
      setFlash({ type: 'success', msg: 'User deleted.' });
      load();
    } catch (err) {
      setFlash({ type: 'error', msg: err.response?.data?.detail || 'Delete failed' });
    } finally { setActing(null); }
  }

  const totalPages = Math.ceil(total / PER);

  return (
    <div>
      <div className="page-header">
        <h1>Users <span style={{ fontWeight: 400, color: '#64748b', fontSize: '1rem' }}>({total})</span></h1>
      </div>

      {flash && <div className={flash.type === 'success' ? 'flash-success' : 'flash-error'}>{flash.msg}</div>}

      <form className="filters" onSubmit={handleSearch}>
        <input type="search" placeholder="Search email, name, phone…" value={q} onChange={(e) => setQ(e.target.value)} style={{ minWidth: 250 }} />
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
          <option value="unverified">Unverified</option>
        </select>
        <button type="submit" className="btn btn-outline">Search</button>
        {(q || statusFilter) && <button type="button" className="btn btn-outline" onClick={() => { setQ(''); setStatusFilter(''); setPage(1); }}>Clear</button>}
      </form>

      {loading ? (
        <p style={{ color: '#64748b' }}>Loading…</p>
      ) : users.length === 0 ? (
        <p style={{ color: '#94a3b8' }}>No users found.</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>User</th>
              <th>Phone</th>
              <th>Status</th>
              <th>Auth Provider</th>
              <th>Joined</th>
              <th>Profile</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u, idx) => (
              <tr key={u.id}>
                <td style={{ color: '#94a3b8', fontSize: '.8rem' }}>{(page - 1) * PER + idx + 1}</td>
                <td>
                  <Link to={`/users/${u.id}`} style={{ fontWeight: 600, fontSize: '.875rem', color: '#1e40af' }}>{u.email || u.phone || 'N/A'}</Link>
                  {u.display_name && <div style={{ color: '#475569', fontSize: '.78rem' }}>{u.display_name}</div>}
                </td>
                <td style={{ fontSize: '.85rem' }}>{u.phone || '—'}</td>
                <td>
                  <span className={`badge ${u.status === 'active' ? 'badge-active' : u.status === 'suspended' ? 'badge-suspended' : 'badge-warning'}`}>
                    {u.status || 'unknown'}
                  </span>
                </td>
                <td style={{ fontSize: '.82rem', color: '#475569' }}>{u.auth_provider || '—'}</td>
                <td style={{ fontSize: '.8rem', color: '#475569' }}>{u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}</td>
                <td style={{ textAlign: 'center', fontSize: '.8rem' }}>
                  {u.profile_complete ? <span className="badge badge-success">Complete</span> : <span className="badge badge-warning">Incomplete</span>}
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '.3rem' }}>
                    <Link to={`/users/${u.id}`} className="btn btn-sm btn-outline">View</Link>
                    <button className="btn btn-sm btn-warning" onClick={() => handleSuspend(u)} disabled={acting === u.id}>
                      {acting === u.id ? '…' : u.status === 'suspended' ? 'Activate' : 'Suspend'}
                    </button>
                    <button className="btn btn-sm btn-danger" onClick={() => handleDelete(u)} disabled={acting === u.id}>Del</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
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
