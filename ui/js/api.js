import { IS_SERVED } from './config.js';

async function jsonFetch(path, init) {
  const res = await fetch(path, init);
  let data = null;
  try { data = await res.json(); } catch {}
  return { ok: res.ok, status: res.status, headers: res.headers, data };
}

export async function getConfig(apiBase = '') {
  const res = await fetch(`${apiBase}/api/config`);
  if (!res.ok) throw new Error(`/api/config returned ${res.status}`);
  return res.json();
}

export function saveConfig(updates) {
  if (!IS_SERVED) return Promise.resolve();
  return fetch('/api/config', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(updates),
  }).catch(() => {
    // Server unreachable — localStorage already holds the value
  });
}

export async function getReports() {
  const res = await fetch('/api/reports');
  return res.json();
}

export async function getFilters() {
  const res = await fetch('/api/filters');
  return res.json();
}

export async function saveFilter(name, params) {
  const res = await fetch('/api/filters', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ name, params }),
  });
  return {
    httpOk: res.ok,
    status: res.status,
    contentType: res.headers.get('content-type') || '',
    json: async () => {
      try { return await res.json(); } catch { return null; }
    },
  };
}

export async function deleteFilter(slug) {
  return fetch(`/api/filters/${encodeURIComponent(slug)}`, { method: 'DELETE' });
}

export async function getSchemas() {
  const res = await fetch('/api/schemas');
  return res.json();
}

export async function getSchemaByName(name) {
  const res = await fetch(`/api/schemas?name=${encodeURIComponent(name)}`);
  return res.json();
}

export async function postSchema(body) {
  const res = await fetch('/api/schemas', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
  });
  return res.json();
}

export async function testConnection(body) {
  return jsonFetch('/api/test-connection', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
  });
}

export async function getCertStatus() {
  const res = await fetch('/api/cert-status');
  return res.json();
}

export async function fetchCert(url) {
  const res = await fetch('/api/fetch-cert', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ url }),
  });
  return res.json();
}

export function openGenerateStream(queryString) {
  return new EventSource('/api/generate?' + queryString);
}
