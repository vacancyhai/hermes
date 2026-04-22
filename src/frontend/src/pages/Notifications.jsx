import { useState, useEffect } from 'react';
import { Briefcase, GraduationCap, CreditCard, FileText, Trophy, Bell, Check, CheckCheck, Trash2 } from 'lucide-react';
import api from '../api/client';

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
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div>
          <h1 style={{ fontSize: '1.3rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Bell size={18} strokeWidth={2.5} />Notifications</h1>
          {unreadCount > 0 && <span style={{ background: '#fee2e2', color: '#991b1b', padding: '0.15rem 0.55rem', borderRadius: 9999, fontSize: '0.75rem', fontWeight: 700 }}>{unreadCount} unread</span>}
        </div>
        {unreadCount > 0 && (
          <button onClick={markAllRead} className="btn btn-outline btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}><CheckCheck size={14} strokeWidth={2} />Mark all as read</button>
        )}
      </div>

      {notifications.length === 0 && (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b', background: '#f8fafc', borderRadius: '0.75rem', border: '1px dashed #e2e8f0' }}>
          <div style={{ marginBottom: '0.5rem' }}><Bell size={40} strokeWidth={1.5} color="#94a3b8" /></div>
          <p style={{ fontWeight: 600, color: '#1e293b' }}>No notifications yet.</p>
          <p style={{ fontSize: '0.875rem' }}>You'll receive alerts for tracked jobs and deadlines.</p>
        </div>
      )}

      {notifications.map((notif) => {
        const typeConf = typeColors[notif.type] || typeColors.system;
        return (
          <div key={notif.id} style={{
            background: notif.is_read ? '#fff' : '#eff6ff',
            border: `1px solid ${notif.is_read ? '#e2e8f0' : '#bfdbfe'}`,
            borderLeft: `4px solid ${notif.is_read ? '#e2e8f0' : '#2563eb'}`,
            borderRadius: '0.5rem', padding: '0.85rem 1rem', marginBottom: '0.5rem',
            display: 'flex', alignItems: 'flex-start', gap: '0.75rem',
          }}>
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
          </div>
        );
      })}

      {pagination.has_more && (
        <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
          <button onClick={loadMore} className="btn btn-outline">Load More</button>
        </div>
      )}
    </div>
  );
}
