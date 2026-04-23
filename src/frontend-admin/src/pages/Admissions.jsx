import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import AdminPagination from '../components/AdminPagination';
import { useAdminList } from '../hooks/useAdminList';

const fadeUp = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.26, ease: [0.16, 1, 0.3, 1] } } };
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.07, delayChildren: 0.02 } } };

const STATUS_COLORS = { active: 'badge-active', upcoming: 'badge-upcoming', closed: 'badge-closed', inactive: 'badge-inactive' };

export default function Admissions() {
  const { items, loading, q, setQ, status, setStatus, page, setPage, total, totalPages, deleting, flash, handleSearch, handleDelete } = useAdminList('/admin/admissions');

  async function deleteAdmission(item) {
    await handleDelete(item.id, `Delete admission "${item.admission_name}"?`, 'Admission deleted.', `/admin/admissions/${item.id}`);
  }

  const PER = 20;

  return (
    <motion.div variants={stagger} initial="hidden" animate="show">
      <motion.div variants={fadeUp} className="page-header">
        <h1>Admissions <span style={{ fontWeight: 400, color: '#64748b', fontSize: '1rem' }}>({total})</span></h1>
        <Link to="/admissions/new" className="btn btn-primary">+ New Admission</Link>
      </motion.div>

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

      {loading && (
        <table className="data-table">
          <thead><tr><th>#</th><th>Name</th><th>Conducting Body</th><th>Type / Stream</th><th>Status</th><th>App Deadline</th><th>Docs</th><th>Actions</th></tr></thead>
          <tbody>
            {Array.from({ length: 8 }).map((_, i) => (
              <tr key={i} className="skeleton-row">
                <td><span className="skeleton" style={{ width: 18, height: 12 }} /></td>
                <td><div className="skeleton" style={{ width: 190, height: 13, marginBottom: 4 }} /><div className="skeleton" style={{ width: 130, height: 10 }} /></td>
                <td><span className="skeleton" style={{ width: 120, height: 13 }} /></td>
                <td><span className="skeleton" style={{ width: 64, height: 20, borderRadius: 9999 }} /></td>
                <td><span className="skeleton" style={{ width: 52, height: 20, borderRadius: 9999 }} /></td>
                <td><span className="skeleton" style={{ width: 80, height: 13 }} /></td>
                <td><span className="skeleton" style={{ width: 60, height: 18, borderRadius: 4 }} /></td>
                <td><div style={{ display: 'flex', gap: 4 }}><span className="skeleton" style={{ width: 36, height: 26, borderRadius: 4 }} /><span className="skeleton" style={{ width: 28, height: 26, borderRadius: 4 }} /></div></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {!loading && items.length === 0 && <p style={{ color: '#94a3b8' }}>No admissions found.</p>}
      {!loading && items.length > 0 && (
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
                    <button className="btn btn-sm btn-danger" onClick={() => deleteAdmission(a)} disabled={deleting === a.id}>
                      {deleting === a.id ? '…' : 'Del'}
                    </button>
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
