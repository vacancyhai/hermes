import PropTypes from 'prop-types';
import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import client from '../api/client';

function Row({ label, value }) {
  return (
    <tr>
      <td style={{ fontWeight: 600, color: '#374151', padding: '.45rem .75rem', width: '38%', fontSize: '.85rem', background: '#f8fafc', borderBottom: '1px solid #f1f5f9' }}>{label}</td>
      <td style={{ padding: '.45rem .75rem', fontSize: '.85rem', borderBottom: '1px solid #f1f5f9', color: '#1e293b' }}>{value ?? '—'}</td>
    </tr>
  );
}

Row.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.node,
};

Row.defaultProps = { value: null };

function statusBadgeClass(status) {
  if (status === 'active') return 'badge-active';
  if (status === 'suspended') return 'badge-suspended';
  return 'badge-warning';
}

export default function UserDetail() {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [trackedJobs, setTrackedJobs] = useState([]);
  const [trackedAdmissions, setTrackedAdmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [flash, setFlash] = useState(null);
  const [acting, setActing] = useState(false);

  useEffect(() => {
    Promise.all([
      client.get(`/admin/users/${userId}`),
      client.get(`/admin/users/${userId}/tracked`).catch(() => ({ data: { data: { jobs: [], admissions: [] } } })),
    ]).then(([u, t]) => {
      setUser(u.data);
      setProfile(u.data.profile);
      setTrackedJobs(t.data.jobs || []);
      setTrackedAdmissions(t.data.admissions || []);
    }).catch(() => setFlash({ type: 'error', msg: 'Failed to load user' }))
      .finally(() => setLoading(false));
  }, [userId]);

  async function handleStatusChange(newStatus) {
    if (!confirm(`Set user status to "${newStatus}"?`)) return;
    setActing(true);
    try {
      await client.put(`/admin/users/${userId}/status`, { status: newStatus });
      setUser((u) => ({ ...u, status: newStatus }));
      setFlash({ type: 'success', msg: `Status updated to ${newStatus}.` });
    } catch (err) {
      setFlash({ type: 'error', msg: err.response?.data?.detail || 'Action failed' });
    } finally { setActing(false); }
  }

  async function handleDelete() {
    if (!confirm(`Permanently delete this user (${user?.email})? This cannot be undone.`)) return;
    setActing(true);
    try {
      await client.delete(`/admin/users/${userId}`);
      navigate('/users', { replace: true });
    } catch (err) {
      setFlash({ type: 'error', msg: err.response?.data?.detail || 'Delete failed' });
      setActing(false);
    }
  }

  if (loading) return <p style={{ color: '#64748b' }}>Loading…</p>;
  if (!user) return <p style={{ color: '#ef4444' }}>User not found.</p>;

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to="/users" style={{ color: '#64748b', fontSize: '.82rem' }}>← Users</Link>
          <h1 style={{ marginTop: '.25rem' }}>{user.display_name || user.email || user.phone}</h1>
        </div>
        <div style={{ display: 'flex', gap: '.5rem', flexWrap: 'wrap' }}>
          {user.status !== 'suspended' && (
            <button className="btn btn-warning" onClick={() => handleStatusChange('suspended')} disabled={acting}>Suspend</button>
          )}
          {user.status === 'suspended' && (
            <button className="btn btn-success" onClick={() => handleStatusChange('active')} disabled={acting}>Reactivate</button>
          )}
          <button className="btn btn-danger" onClick={handleDelete} disabled={acting}>Delete User</button>
        </div>
      </div>

      {flash && <div className={flash.type === 'success' ? 'flash-success' : 'flash-error'}>{flash.msg}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        {/* Account Info */}
        <div className="section-card">
          <div className="section-header section-header--blue">Account Information</div>
          <div style={{ padding: 0 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <tbody>
                <Row label="ID" value={user.id} />
                <Row label="Email" value={user.email} />
                <Row label="Phone" value={user.phone} />
                <Row label="Display Name" value={user.display_name} />
                <Row label="Status" value={<span className={`badge ${statusBadgeClass(user.status)}`}>{user.status}</span>} />
                <Row label="Auth Provider" value={user.auth_provider} />
                <Row label="Firebase UID" value={user.firebase_uid} />
                <Row label="Email Verified" value={user.email_verified ? '✅ Yes' : '❌ No'} />
                <Row label="Phone Verified" value={user.phone_verified ? '✅ Yes' : '❌ No'} />
                <Row label="Joined" value={user.created_at ? new Date(user.created_at).toLocaleString() : '—'} />
                <Row label="Last Login" value={user.last_login_at ? new Date(user.last_login_at).toLocaleString() : '—'} />
              </tbody>
            </table>
          </div>
        </div>

        {/* Profile */}
        <div className="section-card">
          <div className="section-header section-header--purple">Profile</div>
          <div style={{ padding: 0 }}>
            {profile ? (
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <tbody>
                  <Row label="Full Name" value={profile.full_name} />
                  <Row label="Date of Birth" value={profile.date_of_birth} />
                  <Row label="Gender" value={profile.gender} />
                  <Row label="Category" value={profile.category} />
                  <Row label="Nationality" value={profile.nationality} />
                  <Row label="State" value={profile.state} />
                  <Row label="City" value={profile.city} />
                  <Row label="Qualification" value={profile.qualification} />
                  <Row label="PWD" value={profile.is_pwd ? 'Yes' : 'No'} />
                  <Row label="Ex-Serviceman" value={profile.is_ex_serviceman ? 'Yes' : 'No'} />
                  {(() => {
                    const cls = user.profile_complete ? 'badge-active' : 'badge-warning';
                    const lbl = user.profile_complete ? 'Complete' : 'Incomplete';
                    return <Row label="Complete" value={<span className={`badge ${cls}`}>{lbl}</span>} />;
                  })()}
                </tbody>
              </table>
            ) : (
              <p style={{ padding: '1rem', color: '#94a3b8', fontSize: '.875rem' }}>No profile data.</p>
            )}
          </div>
        </div>
      </div>

      {/* Tracked items */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <div className="section-card">
          <div className="section-header section-header--green">Tracked Jobs ({trackedJobs.length})</div>
          <div style={{ padding: 0, maxHeight: 280, overflowY: 'auto' }}>
            {trackedJobs.length === 0 ? (
              <p style={{ padding: '1rem', color: '#94a3b8', fontSize: '.875rem' }}>None.</p>
            ) : (
              <table className="data-table">
                <thead><tr><th>Title</th><th>Status</th></tr></thead>
                <tbody>
                  {trackedJobs.map((j) => (
                    <tr key={j.id}>
                      <td style={{ fontSize: '.85rem' }}>{j.title}</td>
                      <td><span className="badge badge-info">{j.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
        <div className="section-card">
          <div className="section-header section-header--indigo">Tracked Admissions ({trackedAdmissions.length})</div>
          <div style={{ padding: 0, maxHeight: 280, overflowY: 'auto' }}>
            {trackedAdmissions.length === 0 ? (
              <p style={{ padding: '1rem', color: '#94a3b8', fontSize: '.875rem' }}>None.</p>
            ) : (
              <table className="data-table">
                <thead><tr><th>Name</th><th>Status</th></tr></thead>
                <tbody>
                  {trackedAdmissions.map((a) => (
                    <tr key={a.id}>
                      <td style={{ fontSize: '.85rem' }}>{a.name}</td>
                      <td><span className="badge badge-info">{a.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
