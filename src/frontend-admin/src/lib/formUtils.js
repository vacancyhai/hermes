export const STATUSES = ['active', 'upcoming', 'closed', 'inactive'];
export const LINK_TYPES = ['official_notification', 'apply_online', 'admit_card', 'answer_key', 'result', 'syllabus', 'other'];

export const emptyFee = { general: '', obc: '', sc_st: '', ews: '', female: '' };
export const emptyLink = { type: 'official_notification', text: '', url: '' };
export const emptyDoc = { slug: '', title: '', links_json: '[]', start: '', end: '', published_at: '' };

export function safeJson(val, fallback = '') {
  try { return JSON.stringify(JSON.parse(typeof val === 'string' ? val : JSON.stringify(val)), null, 2); }
  catch { return typeof val === 'object' ? JSON.stringify(val, null, 2) : (val || fallback); }
}

export function validateJson(val, setter, errSetter) {
  setter(val);
  try { JSON.parse(val); errSetter(''); }
  catch (e) { errSetter(e.message); }
}

export function buildFeeObj(fee) {
  const obj = {};
  if (fee.general !== '') obj.general = Number(fee.general);
  if (fee.obc !== '') obj.obc = Number(fee.obc);
  if (fee.sc_st !== '') obj.sc_st = Number(fee.sc_st);
  if (fee.ews !== '') obj.ews = Number(fee.ews);
  if (fee.female !== '') obj.female = Number(fee.female);
  return obj;
}

export const toDateInput = (v) => (v ? v.split('T')[0] : '');

export function makeSlug(title) {
  return title.toLowerCase().replaceAll(/[^a-z0-9]+/g, '-').replaceAll(/^-|-$/g, '');
}
