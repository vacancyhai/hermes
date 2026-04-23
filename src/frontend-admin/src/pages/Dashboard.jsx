import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import client from '../api/client';

const fadeUp = { hidden: { opacity: 0, y: 14 }, show: { opacity: 1, y: 0, transition: { duration: 0.28, ease: [0.16, 1, 0.3, 1] } } };
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.06, delayChildren: 0.02 } } };

const QUICK_LINKS = [
  { to: '/jobs/new', label: '+ New Job', bg: 'linear-gradient(135deg,#1e40af,#2563eb)', shadow: 'rgba(37,99,235,.35)' },
  { to: '/admissions/new', label: '+ New Admission', bg: 'linear-gradient(135deg,#5b21b6,#7c3aed)', shadow: 'rgba(124,58,237,.35)' },
  { to: '/organizations/new', label: '+ New Organization', bg: 'linear-gradient(135deg,#065f46,#059669)', shadow: 'rgba(5,150,105,.35)' },
  { to: '/logs', label: 'View Audit Logs', bg: 'linear-gradient(135deg,#92400e,#d97706)', shadow: 'rgba(217,119,6,.35)' },
];

const STAT_COLORS = [
  '#2563eb','#3b82f6','#7c3aed','#a78bfa',
  '#059669','#10b981','#d97706','#f59e0b',
  '#dc2626','#f87171',
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
    <motion.div variants={stagger} initial="hidden" animate="show">
      <motion.div variants={fadeUp} className="page-header">
        <h1>Dashboard</h1>
        <span style={{ fontSize: '.8rem', color: '#94a3b8', fontWeight: 500 }}>Overview &amp; Quick Actions</span>
      </motion.div>

      {/* Quick links */}
      <motion.div variants={fadeUp} style={{ display: 'flex', gap: '.65rem', marginBottom: '1.75rem', flexWrap: 'wrap' }}>
        {QUICK_LINKS.map((ql) => (
          <Link key={ql.to} to={ql.to} style={{ display: 'inline-flex', alignItems: 'center', gap: '.35rem', background: ql.bg, color: '#fff', padding: '.5rem 1rem', borderRadius: 'var(--radius)', fontSize: '.82rem', fontWeight: 700, textDecoration: 'none', boxShadow: `0 4px 14px ${ql.shadow}`, transition: 'opacity .15s, transform .15s' }}
            onMouseEnter={(e) => { e.currentTarget.style.opacity = '.88'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.opacity = '1'; e.currentTarget.style.transform = 'translateY(0)'; }}
          >
            {ql.label}
          </Link>
        ))}
      </motion.div>

      {/* Stats */}
      <motion.div variants={fadeUp}>
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
          {statItems.map((s, i) => (
            <div key={s.label} className="stat-card" style={{ borderTop: `3px solid ${STAT_COLORS[i % STAT_COLORS.length]}` }}>
              <div className="value" style={{ color: STAT_COLORS[i % STAT_COLORS.length] }}>{s.value}</div>
              <div className="label">{s.label}</div>
            </div>
          ))}
          {!stats && <p style={{ color: '#64748b', fontSize: '.875rem' }}>Stats not available</p>}
        </div>
      )}
      </motion.div>

      {/* Recent audit logs */}
      <motion.div variants={fadeUp} className="section-card">
        <div className="section-header section-header--slate" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Recent Activity</span>
          <Link to="/logs" style={{ color: '#fff', fontSize: '.75rem', opacity: .8, background: 'rgba(255,255,255,.1)', padding: '.2rem .6rem', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(255,255,255,.15)' }}>View all →</Link>
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
      </motion.div>
    </motion.div>
  );
}
