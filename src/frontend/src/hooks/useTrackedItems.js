import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../api/client';

export function useTrackedItems(endpoint, token) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState([]);
  const [pagination, setPagination] = useState({});
  const [trackedJobIds, setTrackedJobIds] = useState(new Set());
  const [trackedAdmIds, setTrackedAdmIds] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const offset = Number.parseInt(searchParams.get('offset') || '0', 10);
  const limit = 20;

  const fetchItems = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get(endpoint, { params: { limit, offset } });
      setItems(res.data.data || []);
      setPagination(res.data.pagination || {});
    } catch { } finally { setLoading(false); }
  }, [endpoint, offset]);

  useEffect(() => { fetchItems(); }, [fetchItems]);

  useEffect(() => {
    if (!token) return;
    api.get('/users/me/tracked').then((r) => {
      setTrackedJobIds(new Set((r.data.jobs || []).map((j) => String(j.id))));
      setTrackedAdmIds(new Set((r.data.admissions || []).map((a) => String(a.id))));
    }).catch(() => {});
  }, [token]);

  const track = async (type, id) => {
    const set = type === 'job' ? trackedJobIds : trackedAdmIds;
    const setFn = type === 'job' ? setTrackedJobIds : setTrackedAdmIds;
    const isTracking = set.has(String(id));
    try {
      if (isTracking) { await api.delete(`/${type}s/${id}/track`); }
      else { await api.post(`/${type}s/${id}/track`); }
      setFn((prev) => {
        const next = new Set(prev);
        if (isTracking) {
          next.delete(String(id));
        } else {
          next.add(String(id));
        }
        return next;
      });
    } catch { }
  };

  return {
    items, pagination, loading, offset, limit,
    trackedJobIds, trackedAdmIds, track, setSearchParams,
  };
}
