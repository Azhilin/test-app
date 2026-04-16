import { IS_SERVED, STORE_KEYS } from './config.js';
import { store } from './store.js';
import { getReports } from './api.js';

const reportsList  = () => document.getElementById('reports-list');
const reportsEmpty = () => document.getElementById('reports-empty');

function renderReports(entries) {
  const listEl  = reportsList();
  const emptyEl = reportsEmpty();
  listEl.innerHTML = '';
  if (!entries || entries.length === 0) {
    emptyEl.hidden = false;
    return;
  }
  emptyEl.hidden = true;
  entries.slice(0, 10).forEach(({ ts, html_file }) => {
    const hFile = html_file || 'report.html';
    const li = document.createElement('li');
    const tsSpan = document.createElement('span');
    tsSpan.className = 'report-ts';
    tsSpan.textContent = ts;

    const linksDiv = document.createElement('div');
    linksDiv.className = 'report-links';

    const htmlLink = document.createElement('a');
    htmlLink.href = `generated/reports/${ts}/${hFile}`;
    htmlLink.target = '_blank';
    htmlLink.rel = 'noopener';
    htmlLink.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg> ${hFile}`;

    linksDiv.appendChild(htmlLink);
    li.appendChild(tsSpan);
    li.appendChild(linksDiv);
    listEl.appendChild(li);
  });
}

export async function loadReports() {
  if (IS_SERVED) {
    try {
      const data = await getReports();
      if (Array.isArray(data.reports)) {
        const serverTs  = new Set(data.reports.map((r) => r.ts));
        const local     = store.getJSON(STORE_KEYS.REPORTS) || [];
        const localOnly = local.filter((r) => !serverTs.has(r.ts));
        renderReports([...data.reports, ...localOnly]);
        return;
      }
    } catch {
      // fall through to localStorage fallback
    }
  }
  renderReports(store.getJSON(STORE_KEYS.REPORTS) || []);
}

export function addReport(ts, htmlFile, mdFile) {
  const saved = store.getJSON(STORE_KEYS.REPORTS) || [];
  if (!saved.find((r) => r.ts === ts)) {
    saved.unshift({ ts, html_file: htmlFile || null, md_file: mdFile || null });
    store.setJSON(STORE_KEYS.REPORTS, saved.slice(0, 10));
  }
  loadReports();
}
