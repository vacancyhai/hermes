import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import client from '../api/client';

const QUICK_LINKS = [
  { to: '/jobs/new', label: '+ New Job', color: '#2563eb' },
  { to: '/admissions/new', label: '+ New Admission', color: '#7c3aed' },
  { to: '/organizations/new', label: '+ New Organization', color: '#059669' },
  { to: '/logs', label: 'Audit Logs', color: '#d97706' },
];

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [recentLogs, setRecentLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      client.get('/admin/stats').catch(() => ({ data: null })),
      client.get('/admin/logs?limit=5').catch(() => ({ data: { data: [] } })),
    ]).then(([s, l]) => {
      setStats(s.data);
      setRecentLogs(l.data?.data || []);
    }).finally(() => setLoading(false));
  }, []);

  const statItems = stats
    ? [
        { label: 'Total Jobs', value: stats.jobs?.total ?? '—' },
        { label: 'Active Jobs', value: stats.jobs?.active ?? '—' },
        { label: 'Admissions', value: stats.admissions?.total ?? '—' },
        { label: 'Active Admissions', value: stats.admissions?.active ?? '—' },
        { label: 'Users', value: stats.users?.total ?? '—' },
        { label: 'Active Users', value: stats.users?.active ?? '—' },
        { label: 'New This Week', value: stats.users?.new_this_week ?? '—' },
        { label: 'Admit Cards', value: stats.admit_cards?.total ?? '—' },
        { label: 'Answer Keys', value: stats.answer_keys?.total ?? '—' },
        { label: 'Results', value: stats.results?.total ?? '—' },
      ]
    : [];

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
      </div>

      {/* Quick links */}
      <div style={{ display: 'flex', gap: '.75rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        {QUICK_LINKS.map((ql) => (
          <Link key={ql.to} to={ql.to} className="btn btn-primary" style={{ background: ql.color, borderColor: ql.color }}>
            {ql.label}
          </Link>
        ))}
      </div>

      {/* Stats */}
      {loading ? (
        <div className="stats-grid">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="stat-card">
              <div className="skeleton" style={{ width: 60, height: 28, borderRadius: 6, margin: '0 auto 8px' }} />
              <div className="skeleton" style={{ width: 90, height: 11, borderRadius: 4, margin: '0 auto' }} />
            </div>
          ))}
        </div>
      ) : (
        <div className="stats-grid">
          {statItems.map((s) => (
            <div key={s.label} className="stat-card">
              <div className="value">{s.value}</div>
              <div className="label">{s.label}</div>
            </div>
          ))}
          {!stats && <p style={{ color: '#64748b', fontSize: '.875rem' }}>Stats not available</p>}
        </div>
      )}

      {/* Recent audit logs */}
      <div className="section-card">
        <div className="section-header section-header--slate">
          <span>Recent Activity</span>
          <Link to="/logs" style={{ color: '#fff', fontSize: '.75rem', opacity: .8 }}>View all →</Link>
        </div>
        <div style={{ padding: 0 }}>
          {loading ? (
            <table className="data-table">
              <thead><tr><th>Admin</th><th>Action</th><th>Entity</th><th>Time</th></tr></thead>
              <tbody>
                {Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="skeleton-row">
                    <td><span className="skeleton" style={{ width: 70, height: 12 }} /></td>
                    <td><span className="skeleton" style={{ width: 52, height: 20, borderRadius: 9999 }} /></td>
                    <td><span className="skeleton" style={{ width: 100, height: 12 }} /></td>
                    <td><span className="skeleton" style={{ width: 120, height: 12 }} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : recentLogs.length === 0 ? (
            <p style={{ color: '#94a3b8', fontSize: '.875rem', padding: '1rem' }}>No recent activity</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Admin</th>
                  <th>Action</th>
                  <th>Entity</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {recentLogs.map((log) => (
                  <tr key={log.id}>
                    <td style={{ fontSize: '.82rem', color: '#64748b' }}>{log.admin_id ? log.admin_id.slice(0, 8) + '…' : '—'}</td>
                    <td><span className="badge badge-info">{log.action}</span></td>
                    <td>{log.resource_type} {log.resource_id ? `#${log.resource_id.slice(0, 8)}…` : ''}</td>
                    <td style={{ color: '#64748b', fontSize: '.8rem', whiteSpace: 'nowrap' }}>
                      {log.timestamp ? new Date(log.timestamp).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
