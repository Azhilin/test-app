export const store = {
  get: (k) => {
    try { return localStorage.getItem(k) ?? ''; } catch { return ''; }
  },
  set: (k, v) => {
    try { localStorage.setItem(k, v); } catch {}
  },
  getJSON: (k) => {
    try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch { return null; }
  },
  setJSON: (k, v) => {
    try { localStorage.setItem(k, JSON.stringify(v)); } catch {}
  },
};
