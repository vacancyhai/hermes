import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import client from '../api/client';
import AdminPagination from '../components/AdminPagination';

const fadeUp = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.26, ease: [0.16, 1, 0.3, 1] } } };
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.07, delayChildren: 0.02 } } };

function statusBadgeClass(s) {
  if (s === 'active') return 'badge-active';
  if (s === 'suspended') return 'badge-suspended';
  return 'badge-warning';
}
function suspendBtnLabel(acting, userId, status) {
  if (acting === userId) return '…';
  return status === 'suspended' ? 'Activate' : 'Suspend';
}
function statusBadge(s) {
  return <span className={`badge ${statusBadgeClass(s)}`}>{s || 'unknown'}</span>;
}

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
    <motion.div variants={stagger} initial="hidden" animate="show">
      <motion.div variants={fadeUp} className="page-header">
        <h1>Users <span style={{ fontWeight: 400, color: '#64748b', fontSize: '1rem' }}>({total})</span></h1>
      </motion.div>

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

      {loading && (
        <table className="data-table">
          <thead><tr><th>#</th><th>User</th><th>Phone</th><th>Status</th><th>Auth Provider</th><th>Joined</th><th>Profile</th><th>Actions</th></tr></thead>
          <tbody>
            {Array.from({ length: 10 }).map((_, i) => (
              <tr key={i} className="skeleton-row">
                <td><span className="skeleton" style={{ width: 18, height: 12 }} /></td>
                <td><div className="skeleton" style={{ width: 160, height: 13, marginBottom: 4 }} /><div className="skeleton" style={{ width: 100, height: 10 }} /></td>
                <td><span className="skeleton" style={{ width: 90, height: 13 }} /></td>
                <td><span className="skeleton" style={{ width: 52, height: 20, borderRadius: 9999 }} /></td>
                <td><span className="skeleton" style={{ width: 60, height: 13 }} /></td>
                <td><span className="skeleton" style={{ width: 75, height: 13 }} /></td>
                <td style={{ textAlign: 'center' }}><span className="skeleton" style={{ width: 64, height: 20, borderRadius: 9999 }} /></td>
                <td><div style={{ display: 'flex', gap: 4 }}><span className="skeleton" style={{ width: 36, height: 26, borderRadius: 4 }} /><span className="skeleton" style={{ width: 52, height: 26, borderRadius: 4 }} /><span className="skeleton" style={{ width: 28, height: 26, borderRadius: 4 }} /></div></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {!loading && users.length === 0 && <p style={{ color: '#94a3b8' }}>No users found.</p>}
      {!loading && users.length > 0 && (
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
                  {statusBadge(u.status)}
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
                      {suspendBtnLabel(acting, u.id, u.status)}
                    </button>
                    <button className="btn btn-sm btn-danger" onClick={() => handleDelete(u)} disabled={acting === u.id}>Del</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <AdminPagination page={page} totalPages={totalPages} onPage={setPage} />
    </motion.div>
  );
}
