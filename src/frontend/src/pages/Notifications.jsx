import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Briefcase, GraduationCap, CreditCard, FileText, Trophy, Bell, Check, CheckCheck, Trash2 } from 'lucide-react';
import api from '../api/client';

const rowVariants = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.24, ease: [0.16, 1, 0.3, 1] } },
};
const listVariants = { hidden: {}, show: { transition: { staggerChildren: 0.05, delayChildren: 0.04 } } };

export default function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [pagination, setPagination] = useState({});
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [offset, setOffset] = useState(0);
  const limit = 20;

  const fetchNotifications = async (off = 0, append = false) => {
    try {
      const res = await api.get('/notifications', { params: { limit, offset: off } });
      const items = res.data.data || [];
      setNotifications(append ? (prev) => [...prev, ...items] : items);
      setPagination(res.data.pagination || {});
    } catch { } finally { setLoading(false); }
  };

  const fetchCount = async () => {
    try {
      const res = await api.get('/notifications/count');
      setUnreadCount(res.data.count || 0);
    } catch { }
  };

  useEffect(() => { fetchNotifications(0); fetchCount(); }, []);

  const markRead = async (id) => {
    try {
      await api.put(`/notifications/${id}/read`);
      setNotifications((prev) => prev.map((n) => n.id === id ? { ...n, is_read: true } : n));
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch { }
  };

  const markAllRead = async () => {
    try {
      await api.put('/notifications/read-all');
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch { }
  };

  const deleteNotif = async (id) => {
    try {
      await api.delete(`/notifications/${id}`);
      setNotifications((prev) => {
        const n = prev.find((n) => n.id === id);
        if (n && !n.is_read) setUnreadCount((c) => Math.max(0, c - 1));
        return prev.filter((n) => n.id !== id);
      });
    } catch { }
  };

  const loadMore = () => {
    const newOffset = offset + limit;
    setOffset(newOffset);
    fetchNotifications(newOffset, true);
  };

  const typeColors = {
    job_deadline: { bg: '#dbeafe', color: '#1e40af', icon: Briefcase },
    admission_deadline: { bg: '#ede9fe', color: '#5b21b6', icon: GraduationCap },
    admit_card: { bg: '#eff6ff', color: '#1d4ed8', icon: CreditCard },
    answer_key: { bg: '#fef3c7', color: '#92400e', icon: FileText },
    result: { bg: '#dcfce7', color: '#166534', icon: Trophy },
    system: { bg: '#f1f5f9', color: '#475569', icon: Bell },
  };

  if (loading) return <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>Loading...</div>;

  return (
    <div style={{ maxWidth: 720, margin: '0 auto' }}>
      {/* Hero Header */}
      <motion.div
        initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
        style={{ background: 'linear-gradient(135deg, #0f2440 0%, #1e3a5f 50%, #2563eb 100%)', color: '#fff', padding: '1.5rem 1.75rem', borderRadius: 'var(--radius-2xl)', marginBottom: '1.5rem', position: 'relative', overflow: 'hidden', boxShadow: '0 16px 48px rgba(15,36,64,.4), 0 4px 12px rgba(15,36,64,.2)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}
      >
        <div style={{ position: 'absolute', top: -50, right: -30, width: 180, height: 180, background: 'rgba(255,255,255,.06)', borderRadius: '50%', pointerEvents: 'none' }} />
        <div style={{ position: 'relative', zIndex: 1, display: 'flex', alignItems: 'center', gap: '0.9rem' }}>
          <div style={{ width: 44, height: 44, background: 'rgba(255,255,255,.14)', backdropFilter: 'blur(8px)', borderRadius: 'var(--radius)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(255,255,255,.15)', flexShrink: 0 }}>
            <Bell size={20} strokeWidth={2.5} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
              <h1 style={{ fontSize: '1.3rem', fontWeight: 800, letterSpacing: '-0.02em' }}>Notifications</h1>
              {unreadCount > 0 && <span style={{ background: 'rgba(239,68,68,.85)', color: '#fff', padding: '0.12rem 0.55rem', borderRadius: '9999px', fontSize: '0.68rem', fontWeight: 700, lineHeight: 1.4 }}>{unreadCount} unread</span>}
            </div>
            <p style={{ fontSize: '0.8rem', opacity: 0.72, marginTop: '0.1rem' }}>Alerts for tracked jobs, deadlines and results</p>
          </div>
        </div>
        {unreadCount > 0 && (
          <motion.button whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.96 }} onClick={markAllRead}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', background: 'rgba(255,255,255,.14)', color: '#fff', border: '1px solid rgba(255,255,255,.22)', borderRadius: 'var(--radius)', padding: '0.45rem 0.9rem', fontSize: '0.82rem', fontWeight: 600, cursor: 'pointer', backdropFilter: 'blur(4px)', position: 'relative', zIndex: 1 }}>
            <CheckCheck size={14} strokeWidth={2} />Mark all read
          </motion.button>
        )}
      </motion.div>

      {notifications.length === 0 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 }}
          style={{ textAlign: 'center', padding: '3.5rem 2rem', color: '#64748b', background: '#f8fafc', borderRadius: 'var(--radius-xl)', border: '1px dashed #e2e8f0' }}
        >
          <div style={{ width: 64, height: 64, background: '#f1f5f9', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem' }}><Bell size={28} strokeWidth={1.5} color="#94a3b8" /></div>
          <p style={{ fontWeight: 700, color: '#1e293b', marginBottom: '0.3rem', fontSize: '1rem' }}>No notifications yet.</p>
          <p style={{ fontSize: '0.875rem' }}>You&apos;ll receive alerts for tracked jobs and deadlines.</p>
        </motion.div>
      )}

      <motion.div variants={listVariants} initial="hidden" animate="show">
      {notifications.map((notif) => {
        const typeConf = typeColors[notif.type] || typeColors.system;
        return (
          <motion.div key={notif.id}
            variants={rowVariants}
            whileHover={{ y: -2, boxShadow: '0 6px 18px rgba(15,23,42,.08)' }}
            style={{
              background: notif.is_read ? '#fff' : '#f0f7ff',
              border: `1px solid ${notif.is_read ? '#e2e8f0' : '#bfdbfe'}`,
              borderLeft: `3px solid ${notif.is_read ? '#cbd5e1' : '#2563eb'}`,
              borderRadius: 'var(--radius-lg)', padding: '0.9rem 1rem', marginBottom: '0.55rem',
              display: 'flex', alignItems: 'flex-start', gap: '0.75rem',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            {/* Icon */}
            <div style={{ background: typeConf.bg, color: typeConf.color, width: 36, height: 36, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              {(() => { const Icon = typeConf.icon; return <Icon size={16} strokeWidth={2} />; })()}
            </div>

            {/* Content */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '0.9rem', fontWeight: notif.is_read ? 500 : 700, color: '#1e293b', marginBottom: '0.2rem' }}>{notif.title}</div>
              {notif.message && <div style={{ fontSize: '0.82rem', color: '#475569', lineHeight: 1.5 }}>{notif.message}</div>}
              {notif.created_at && <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem' }}>{new Date(notif.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</div>}
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', gap: '0.35rem', flexShrink: 0, flexDirection: 'column', alignItems: 'flex-end' }}>
              {!notif.is_read && (
                <button onClick={() => markRead(notif.id)} style={{ fontSize: '0.72rem', padding: '0.2rem 0.5rem', borderRadius: '0.35rem', background: '#dbeafe', color: '#1e40af', border: 'none', cursor: 'pointer', fontWeight: 600, whiteSpace: 'nowrap', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}><Check size={11} strokeWidth={2.5} />Mark read</button>
              )}
              <button onClick={() => deleteNotif(notif.id)} style={{ fontSize: '0.72rem', padding: '0.2rem 0.5rem', borderRadius: '0.35rem', background: '#fee2e2', color: '#991b1b', border: 'none', cursor: 'pointer', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}><Trash2 size={11} strokeWidth={2} />Delete</button>
            </div>
          </motion.div>
        );
      })}
      </motion.div>

      {pagination.has_more && (
        <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
          <button onClick={loadMore} className="btn btn-outline">Load More</button>
        </div>
      )}
    </div>
  );
}
