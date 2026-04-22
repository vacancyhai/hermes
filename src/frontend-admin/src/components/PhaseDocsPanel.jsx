import PropTypes from 'prop-types';
import { useState } from 'react';
import client from '../api/client';

const PHASE_TABS = [
  { key: 'admit_cards', label: 'Admit Cards', color: '#1d4ed8', api: 'admit-cards' },
  { key: 'answer_keys', label: 'Answer Keys', color: '#6d28d9', api: 'answer-keys' },
  { key: 'results', label: 'Results', color: '#15803d', api: 'results' },
];

const emptyDoc = { slug: '', title: '', start: '', end: '', published_at: '' };

export default function PhaseDocsPanel({ parentKey, parentId, onFlash }) {
  const [activeTab, setActiveTab] = useState('admit_cards');
  const [phaseDocs, setPhaseDocs] = useState({ admit_cards: [], answer_keys: [], results: [] });
  const [newDoc, setNewDoc] = useState({ ...emptyDoc });
  const [saving, setSaving] = useState(false);

  const tab = PHASE_TABS.find((t) => t.key === activeTab);

  async function reloadDocs() {
    const [ac, ak, rs] = await Promise.all([
      client.get(`/admin/admit-cards?${parentKey}=${parentId}&limit=100`).catch(() => ({ data: { data: [] } })),
      client.get(`/admin/answer-keys?${parentKey}=${parentId}&limit=100`).catch(() => ({ data: { data: [] } })),
      client.get(`/admin/results?${parentKey}=${parentId}&limit=100`).catch(() => ({ data: { data: [] } })),
    ]);
    setPhaseDocs({ admit_cards: ac.data.data || [], answer_keys: ak.data.data || [], results: rs.data.data || [] });
  }

  async function handleAdd(e) {
    e.preventDefault();
    setSaving(true);
    const isAdmitCard = activeTab === 'admit_cards';
    const payload = {
      slug: newDoc.slug,
      title: newDoc.title,
      [parentKey]: parentId,
      links: [],
      published_at: newDoc.published_at || null,
      ...(isAdmitCard
        ? { exam_start: newDoc.start || null, exam_end: newDoc.end || null }
        : { start_date: newDoc.start || null, end_date: newDoc.end || null }),
    };
    try {
      await client.post(`/admin/${tab.api}`, payload);
      setNewDoc({ ...emptyDoc });
      await reloadDocs();
      onFlash({ type: 'success', msg: 'Document added.' });
    } catch (err) {
      onFlash({ type: 'error', msg: err.response?.data?.detail || 'Failed to add document' });
    } finally { setSaving(false); }
  }

  async function handleDelete(docId) {
    if (!confirm('Delete this document?')) return;
    try {
      await client.delete(`/admin/${tab.api}/${docId}`);
      setPhaseDocs((prev) => ({ ...prev, [activeTab]: prev[activeTab].filter((d) => d.id !== docId) }));
    } catch (err) {
      onFlash({ type: 'error', msg: err.response?.data?.detail || 'Delete failed' });
    }
  }

  return (
    <div className="section-card" style={{ marginTop: '1.5rem' }}>
      <div className="section-header section-header--slate">Phase Documents</div>
      <div style={{ borderBottom: '1px solid #e2e8f0', display: 'flex', gap: 0 }}>
        {PHASE_TABS.map((t) => (
          <button key={t.key} type="button" onClick={() => setActiveTab(t.key)}
            style={{ padding: '.6rem 1.25rem', border: 'none', background: activeTab === t.key ? '#fff' : '#f8fafc', borderBottom: activeTab === t.key ? `2px solid ${t.color}` : '2px solid transparent', color: activeTab === t.key ? t.color : '#64748b', fontWeight: activeTab === t.key ? 700 : 400, cursor: 'pointer', fontSize: '.83rem', transition: 'all .15s' }}>
            {t.label} <span style={{ background: '#e2e8f0', borderRadius: 9999, padding: '0 6px', fontSize: '.7rem' }}>{phaseDocs[t.key]?.length || 0}</span>
          </button>
        ))}
      </div>
      <div className="section-body">
        {phaseDocs[activeTab]?.length > 0 ? (
          <table className="data-table" style={{ marginBottom: '1rem' }}>
            <thead><tr><th>Slug</th><th>Title</th><th>Start</th><th>End</th><th>Published</th><th /></tr></thead>
            <tbody>
              {phaseDocs[activeTab].map((d) => (
                <tr key={d.id}>
                  <td style={{ fontSize: '.82rem' }}>{d.slug}</td>
                  <td style={{ fontSize: '.85rem' }}>{d.title || '—'}</td>
                  <td style={{ fontSize: '.8rem' }}>{d.exam_start || d.start_date || '—'}</td>
                  <td style={{ fontSize: '.8rem' }}>{d.exam_end || d.end_date || '—'}</td>
                  <td style={{ fontSize: '.8rem' }}>{d.published_at ? new Date(d.published_at).toLocaleDateString() : '—'}</td>
                  <td><button className="btn btn-sm btn-danger" onClick={() => handleDelete(d.id)}>Del</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <p style={{ color: '#94a3b8', fontSize: '.875rem', marginBottom: '1rem' }}>No documents yet.</p>}

        <form onSubmit={handleAdd}>
          <p style={{ fontWeight: 700, fontSize: '.83rem', marginBottom: '.5rem' }}>Add New Document</p>
          <div style={{ display: 'grid', gridTemplateColumns: '160px 1fr 120px 120px 120px auto', gap: '.5rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label htmlFor="pdoc-slug" style={{ fontSize: '.7rem' }}>Slug <span className="req">*</span></label>
              <input id="pdoc-slug" type="text" required value={newDoc.slug} onChange={(e) => setNewDoc((d) => ({ ...d, slug: e.target.value }))} placeholder="phase-2024" style={{ fontSize: '.82rem', padding: '.35rem .5rem' }} />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label htmlFor="pdoc-title" style={{ fontSize: '.7rem' }}>Title <span className="req">*</span></label>
              <input id="pdoc-title" type="text" required value={newDoc.title} onChange={(e) => setNewDoc((d) => ({ ...d, title: e.target.value }))} placeholder="Phase Admit Card 2024" style={{ fontSize: '.82rem', padding: '.35rem .5rem' }} />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label htmlFor="pdoc-start" style={{ fontSize: '.7rem' }}>{activeTab === 'admit_cards' ? 'Exam Start' : 'Start Date'}</label>
              <input id="pdoc-start" type="date" value={newDoc.start} onChange={(e) => setNewDoc((d) => ({ ...d, start: e.target.value }))} style={{ fontSize: '.82rem', padding: '.35rem .5rem' }} />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label htmlFor="pdoc-end" style={{ fontSize: '.7rem' }}>{activeTab === 'admit_cards' ? 'Exam End' : 'End Date'}</label>
              <input id="pdoc-end" type="date" value={newDoc.end} onChange={(e) => setNewDoc((d) => ({ ...d, end: e.target.value }))} style={{ fontSize: '.82rem', padding: '.35rem .5rem' }} />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label htmlFor="pdoc-published" style={{ fontSize: '.7rem' }}>Published At</label>
              <input id="pdoc-published" type="date" value={newDoc.published_at} onChange={(e) => setNewDoc((d) => ({ ...d, published_at: e.target.value }))} style={{ fontSize: '.82rem', padding: '.35rem .5rem' }} />
            </div>
            <button type="submit" className="btn btn-success btn-sm" disabled={saving}>
              {saving ? '…' : '+ Add'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

PhaseDocsPanel.propTypes = {
  parentKey: PropTypes.string.isRequired,
  parentId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  onFlash: PropTypes.func.isRequired,
};
