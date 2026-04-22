import { Link } from 'react-router-dom';
import AdminPagination from '../components/AdminPagination';
import { useAdminList } from '../hooks/useAdminList';

const STATUS_COLORS = { active: 'badge-active', upcoming: 'badge-upcoming', closed: 'badge-closed', inactive: 'badge-inactive' };

export default function Jobs() {
  const { items: jobs, loading, q, setQ, status, setStatus, page, setPage, total, totalPages, deleting, flash, handleSearch, handleDelete } = useAdminList('/admin/jobs');

  async function deleteJob(job) {
    await handleDelete(job.id, `Delete job "${job.job_title}"? This cannot be undone.`, 'Job deleted.', `/admin/jobs/${job.id}`);
  }

  const PER = 20;

  return (
    <div>
      <div className="page-header">
        <h1>Jobs <span style={{ fontWeight: 400, color: '#64748b', fontSize: '1rem' }}>({total})</span></h1>
        <Link to="/jobs/new" className="btn btn-primary">+ New Job</Link>
      </div>

      {flash && <div className={flash.type === 'success' ? 'flash-success' : 'flash-error'}>{flash.msg}</div>}

      <form className="filters" onSubmit={handleSearch}>
        <input type="search" placeholder="Search title, slug…" value={q} onChange={(e) => setQ(e.target.value)} style={{ minWidth: 220 }} />
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

      {loading && <p style={{ color: '#64748b' }}>Loading…</p>}
      {!loading && jobs.length === 0 && <p style={{ color: '#94a3b8' }}>No jobs found.</p>}
      {!loading && jobs.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Title</th>
              <th>Organization</th>
              <th>Status</th>
              <th>Vacancies</th>
              <th>App Deadline</th>
              <th>Docs</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((j, idx) => (
              <tr key={j.id}>
                <td style={{ color: '#94a3b8', fontSize: '.8rem' }}>{(page - 1) * PER + idx + 1}</td>
                <td>
                  <div style={{ fontWeight: 600, fontSize: '.875rem' }}>{j.job_title}</div>
                  <div style={{ color: '#64748b', fontSize: '.75rem' }}>{j.slug}</div>
                </td>
                <td style={{ fontSize: '.85rem' }}>{j.organization || '—'}</td>
                <td><span className={`badge ${STATUS_COLORS[j.status] || 'badge-inactive'}`}>{j.status}</span></td>
                <td style={{ textAlign: 'center' }}>{j.total_vacancies ?? '—'}</td>
                <td style={{ fontSize: '.8rem', color: '#475569' }}>{j.application_end ? new Date(j.application_end).toLocaleDateString() : '—'}</td>
                <td style={{ fontSize: '.75rem' }}>
                  {j.admit_cards_count > 0 && <span className="doc-btn doc-btn--ac">{j.admit_cards_count} AC</span>}
                  {j.answer_keys_count > 0 && <span className="doc-btn doc-btn--ak" style={{ marginLeft: 2 }}>{j.answer_keys_count} AK</span>}
                  {j.results_count > 0 && <span className="doc-btn doc-btn--rs" style={{ marginLeft: 2 }}>{j.results_count} RS</span>}
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '.35rem' }}>
                    <Link to={`/jobs/${j.id}/edit`} className="btn btn-sm btn-outline">Edit</Link>
                    <button className="btn btn-sm btn-danger" onClick={() => deleteJob(j)} disabled={deleting === j.id}>
                      {deleting === j.id ? '…' : 'Del'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <AdminPagination page={page} totalPages={totalPages} onPage={setPage} />
    </div>
  );
}
