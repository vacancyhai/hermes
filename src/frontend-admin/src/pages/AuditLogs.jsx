import { Fragment, useEffect, useState } from 'react';
import client from '../api/client';

const ACTION_COLORS = {
  create: 'badge-success', update: 'badge-info', delete: 'badge-danger',
  login: 'badge-warning', logout: 'badge-inactive', suspend: 'badge-suspended',
};

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');
  const [entityFilter, setEntityFilter] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [expanded, setExpanded] = useState(null);
  const PER = 30;

  function load() {
    setLoading(true);
    const params = { limit: PER, offset: (page - 1) * PER };
    if (actionFilter) params.action = actionFilter;
    if (entityFilter) params.resource_type = entityFilter;
    client.get('/admin/logs', { params })
      .then((r) => { setLogs(r.data.data || []); setTotal(r.data.pagination?.total || 0); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [page, actionFilter, entityFilter]);

  function handleSearch(e) { e.preventDefault(); setPage(1); load(); }

  const totalPages = Math.ceil(total / PER);

  return (
    <div>
      <div className="page-header">
        <h1>Audit Logs <span style={{ fontWeight: 400, color: '#64748b', fontSize: '1rem' }}>({total})</span></h1>
      </div>

      <form className="filters" onSubmit={handleSearch}>
        <select value={actionFilter} onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}>
          <option value="">All Actions</option>
          {['create', 'update', 'delete', 'login', 'logout', 'suspend'].map((a) => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>
        <select value={entityFilter} onChange={(e) => { setEntityFilter(e.target.value); setPage(1); }}>
          <option value="">All Entities</option>
          {['job', 'admission', 'user', 'organization', 'admin'].map((e) => (
            <option key={e} value={e}>{e}</option>
          ))}
        </select>
        <button type="submit" className="btn btn-outline">Filter</button>
        {(actionFilter || entityFilter) && (
          <button type="button" className="btn btn-outline" onClick={() => { setActionFilter(''); setEntityFilter(''); setPage(1); }}>Clear</button>
        )}
      </form>

      {loading ? (
        <p style={{ color: '#64748b' }}>Loading…</p>
      ) : (
        logs.length === 0 ? (
          <p style={{ color: '#94a3b8' }}>No logs found.</p>
        ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Admin</th>
              <th>Action</th>
              <th>Entity</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <Fragment key={log.id}>
                <tr style={{ cursor: log.changes ? 'pointer' : 'default' }} onClick={() => setExpanded(expanded === log.id ? null : log.id)}>
                  <td style={{ color: '#475569', fontSize: '.8rem', whiteSpace: 'nowrap' }}>
                    {log.timestamp ? new Date(log.timestamp).toLocaleString() : '—'}
                  </td>
                  <td style={{ fontSize: '.85rem', color: '#64748b' }}>{log.admin_id ? log.admin_id.slice(0, 8) + '…' : '—'}</td>
                  <td><span className={`badge ${ACTION_COLORS[log.action] || 'badge-inactive'}`}>{log.action}</span></td>
                  <td style={{ fontSize: '.85rem' }}>
                    <span style={{ color: '#1e40af', fontWeight: 600 }}>{log.resource_type}</span>
                    {log.resource_id && <span style={{ color: '#64748b' }}> #{log.resource_id.slice(0, 8)}…</span>}
                  </td>
                  <td style={{ fontSize: '.8rem', color: '#64748b', maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {log.details || (log.changes && Object.keys(log.changes).length ? '(click to expand)' : '—')}
                  </td>
                </tr>
                {expanded === log.id && log.changes && (
                  <tr key={`${log.id}-expanded`}>
                    <td colSpan={5} style={{ background: '#f8fafc', padding: '.75rem 1rem' }}>
                      <pre style={{ margin: 0, fontSize: '.78rem', overflowX: 'auto', color: '#1e293b', fontFamily: 'monospace' }}>
                        {JSON.stringify(log.changes, null, 2)}
                      </pre>
                    </td>
                  </tr>
                )}
              </Fragment>
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
