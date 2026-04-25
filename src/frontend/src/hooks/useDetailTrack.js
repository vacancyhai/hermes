import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';

export function useDetailTrack(endpoint, slug, token) {
  const navigate = useNavigate();
  const [item, setItem] = useState(null);
  const [tracking, setTracking] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/${endpoint}/${slug}`).then((r) => {
      setItem(r.data);
      setLoading(false);
      if (token) {
        if (r.data.job?.id) api.get(`/jobs/${r.data.job.id}/track`).then((tr) => setTracking(tr.data.tracking)).catch(() => {});
        else if (r.data.admission?.id) api.get(`/admissions/${r.data.admission.id}/track`).then((tr) => setTracking(tr.data.tracking)).catch(() => {});
      }
    }).catch(() => setLoading(false));
  }, [slug, token, endpoint]);

  const toggleTrack = async (loginPath) => {
    if (!token) { navigate(loginPath); return; }
    const type = item.job ? 'job' : 'admission';
    const id = item.job?.id || item.admission?.id;
    if (!id) return;
    try {
      if (tracking) await api.delete(`/${type}s/${id}/track`);
      else await api.post(`/${type}s/${id}/track`);
      setTracking(!tracking);
    } catch { }
  };

  return { item, tracking, loading, toggleTrack };
}
