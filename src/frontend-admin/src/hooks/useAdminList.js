import { useState, useEffect } from 'react';
import client from '../api/client';

export function useAdminList(endpoint, perPage = 20) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [deleting, setDeleting] = useState(null);
  const [flash, setFlash] = useState(null);

  function load(overrides = {}) {
    setLoading(true);
    const params = { limit: perPage, offset: (page - 1) * perPage, ...overrides };
    if (q) params.q = q;
    if (status) params.status = status;
    client.get(endpoint, { params })
      .then((r) => { setItems(r.data.data || []); setTotal(r.data.pagination?.total || 0); })
      .catch(() => setFlash({ type: 'error', msg: 'Failed to load' }))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [page, status]); // eslint-disable-line react-hooks/exhaustive-deps

  function handleSearch(e) { e.preventDefault(); setPage(1); load(); }

  async function handleDelete(id, confirmMsg, successMsg, deleteEndpoint) {
    if (!confirm(confirmMsg)) return;
    setDeleting(id);
    try {
      await client.delete(deleteEndpoint);
      setFlash({ type: 'success', msg: successMsg });
      load();
    } catch (err) {
      setFlash({ type: 'error', msg: err.response?.data?.detail || 'Delete failed' });
    } finally { setDeleting(null); }
  }

  const totalPages = Math.ceil(total / perPage);

  return { items, loading, q, setQ, status, setStatus, page, setPage, total, totalPages, deleting, flash, setFlash, load, handleSearch, handleDelete };
}
