import { IS_SERVED, STORE_KEYS } from './config.js';
import { store } from './store.js';
import { getFilters, saveFilter, deleteFilter } from './api.js';
import { buildJqlLocally } from './jql-builder.js';

const SAVE_FILTER_BTN_IDLE = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg> Save Filter`;

function renderFilters(entries) {
  const filtersList  = document.getElementById('filters-list');
  const filtersEmpty = document.getElementById('filters-empty');
  filtersList.innerHTML = '';
  if (!entries || entries.length === 0) {
    filtersEmpty.hidden = false;
    return;
  }
  filtersEmpty.hidden = true;
  entries.slice(0, 20).forEach((entry) => {
    const name      = entry.filter_name || entry.name || '(unnamed)';
    const slug      = entry.slug || entry.filename || '';
    const jql       = entry.jql || '';
    const filterId  = entry.params?.JIRA_FILTER_ID || '';
    const jqlOrId   = jql || (filterId ? `Jira native filter ID: ${filterId}` : '');
    const createdAt = entry.created_at || '';
    const isDefault = !!entry.is_default;

    const li = document.createElement('li');

    const tsSpan = document.createElement('span');
    tsSpan.className = 'report-ts';
    tsSpan.textContent = createdAt;

    const nameSpan = document.createElement('span');
    nameSpan.style.cssText = 'font-weight:600;color:var(--text);flex-shrink:0;';
    nameSpan.textContent = name;

    const jqlPreview = document.createElement('span');
    jqlPreview.style.cssText = 'color:var(--text-muted);font-size:0.78rem;font-family:monospace;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;min-width:0;';
    jqlPreview.title = jqlOrId;
    jqlPreview.textContent = jqlOrId
      ? (jqlOrId.length > 80 ? jqlOrId.slice(0, 80) + '…' : jqlOrId)
      : '(no JQL — set Project Key or Filter ID and save)';

    const copyBtn = document.createElement('button');
    copyBtn.className = 'btn btn-secondary';
    copyBtn.style.cssText = 'font-size:0.72rem;padding:4px 10px;flex-shrink:0;';
    copyBtn.textContent = 'Copy JQL';
    copyBtn.type = 'button';
    copyBtn.title = 'Copy JQL to clipboard';
    copyBtn.disabled = !jql;
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(jql).then(() => {
        copyBtn.textContent = 'Copied!';
        setTimeout(() => { copyBtn.textContent = 'Copy JQL'; }, 1800);
      }).catch(() => {
        copyBtn.textContent = 'Failed';
        setTimeout(() => { copyBtn.textContent = 'Copy JQL'; }, 1800);
      });
    });

    li.style.cssText = 'flex-wrap:wrap;gap:8px;align-items:center;';
    li.appendChild(tsSpan);
    li.appendChild(nameSpan);
    li.appendChild(jqlPreview);
    li.appendChild(copyBtn);

    if (!isDefault) {
      const removeBtn = document.createElement('button');
      removeBtn.className = 'btn btn-danger';
      removeBtn.style.cssText = 'font-size:0.72rem;padding:4px 10px;flex-shrink:0;';
      removeBtn.textContent = 'Remove';
      removeBtn.type = 'button';
      removeBtn.title = 'Delete this filter';
      removeBtn.addEventListener('click', async () => {
        removeBtn.disabled = true;
        removeBtn.textContent = 'Removing…';
        if (IS_SERVED && slug) {
          try { await deleteFilter(slug); } catch {}
        }
        const saved = store.getJSON(STORE_KEYS.FILTERS) || [];
        store.setJSON(STORE_KEYS.FILTERS, saved.filter((f) => (f.filter_name || f.name) !== name));
        loadFilters();
      });
      li.appendChild(removeBtn);
    }

    filtersList.appendChild(li);
  });

  const genSel = document.getElementById('generate-filter-select');
  if (genSel) {
    const prevVal = genSel.value;
    genSel.innerHTML = '<option value="">— Select a saved filter —</option>';
    entries.slice(0, 20).forEach((entry) => {
      const name = entry.filter_name || entry.name || '(unnamed)';
      const slug = entry.slug || entry.filename || '';
      const jql  = entry.jql || '';
      const opt  = document.createElement('option');
      opt.value       = slug;
      opt.textContent = name;
      opt.dataset.jql = jql;
      genSel.appendChild(opt);
    });
    if (prevVal) genSel.value = prevVal;
  }
}

export async function loadFilters() {
  if (IS_SERVED) {
    try {
      const data = await getFilters();
      if (data.ok && Array.isArray(data.filters)) {
        renderFilters(data.filters);
        return;
      }
    } catch {
      // fall through to localStorage fallback
    }
  }
  renderFilters(store.getJSON(STORE_KEYS.FILTERS) || []);
}

export function initFilters(filterLog) {
  const btnSaveJiraFilter = document.getElementById('btn-save-jira-filter');
  if (!btnSaveJiraFilter) return;

  function resetBtn() {
    btnSaveJiraFilter.disabled = false;
    btnSaveJiraFilter.innerHTML = SAVE_FILTER_BTN_IDLE;
  }

  function setBusy() {
    btnSaveJiraFilter.disabled = true;
    btnSaveJiraFilter.innerHTML = '<span class="spinner" aria-hidden="true"></span> Saving…';
  }

  btnSaveJiraFilter.addEventListener('click', async () => {
    const filterName     = document.getElementById('filter-name').value.trim();
    const project        = document.getElementById('jira-project').value.trim();
    const teamId         = document.getElementById('jira-team-id').value.trim();
    const issueTypes     = document.getElementById('jira-issue-types').value.trim();
    const closedSprints  = document.getElementById('jira-closed-sprints-only').value;
    const projectType    = document.querySelector('input[name="filter-project-type"]:checked')?.value || 'SCRUM';
    const estimationType = document.querySelector('input[name="filter-estimation-type"]:checked')?.value || 'StoryPoints';

    filterLog.clear();

    const filterId = document.getElementById('filter-id').value.trim();

    if (!filterName) {
      filterLog.line('⚠ Filter Name is required. Enter a name in the field above before saving.', 'log-error');
      document.getElementById('filter-name').focus();
      return;
    }
    if (!project && !filterId) {
      filterLog.line('⚠ Either a Jira Filter ID or a Project Key (in JQL Builder) is required.', 'log-error');
      document.getElementById('filter-id').focus();
      return;
    }
    const boardId = document.getElementById('jira-board-id').value.trim();
    if (!boardId) {
      filterLog.line('⚠ Board ID is required. Enter it in the Agile Board & Sprint Count section.', 'log-error');
      document.getElementById('filter-board-settings').open = true;
      document.getElementById('jira-board-id').focus();
      return;
    }
    const sprintCount = document.getElementById('sprint-count').value.trim();
    if (!sprintCount) {
      filterLog.line('⚠ Sprint Count / Period Count is required. Enter it in the Agile Board & Sprint Count section.', 'log-error');
      document.getElementById('filter-board-settings').open = true;
      document.getElementById('sprint-count').focus();
      return;
    }

    setBusy();
    filterLog.line(`[ ${new Date().toLocaleTimeString()} ] Building JQL for "${filterName}"…`, 'log-info');

    const params = {
      JIRA_PROJECT:             project,
      JIRA_TEAM_ID:             teamId,
      JIRA_ISSUE_TYPES:         issueTypes,
      JIRA_CLOSED_SPRINTS_ONLY: closedSprints,
      PROJECT_TYPE:             projectType,
      ESTIMATION_TYPE:          estimationType,
      schema_name:              store.get(STORE_KEYS.JIRA_SCHEMA) || '',
      JIRA_BOARD_ID:            document.getElementById('jira-board-id').value.trim(),
      JIRA_SPRINT_COUNT:        document.getElementById('sprint-count').value.trim(),
      JIRA_FILTER_ID:           filterId,
      JIRA_FILTER_PAGE_SIZE:    document.getElementById('jira-filter-page-size').value.trim(),
    };

    if (IS_SERVED) {
      try {
        const res = await saveFilter(filterName, params);
        if (!res.httpOk && !res.contentType.includes('json')) {
          filterLog.line(`✗ Server returned HTTP ${res.status}. Make sure server.py is restarted with the latest version.`, 'log-error');
          resetBtn();
          return;
        }
        const data = await res.json();
        if (!data) {
          filterLog.line(`✗ Server returned an empty or non-JSON response (HTTP ${res.status}). Restart server.py and try again.`, 'log-error');
          resetBtn();
          return;
        }
        if (data.ok) {
          const verb = data.updated ? 'Updated' : 'Saved';
          if (data.jql) {
            filterLog.line(data.jql, 'log-ok');
          } else if (filterId) {
            filterLog.line(`Jira native filter ID: ${filterId}`, 'log-ok');
          }
          filterLog.line(`✓ ${verb} to config/jira_filters.json`, 'log-ok');
          loadFilters();
        } else {
          filterLog.line(`✗ Error: ${data.error || 'Unknown error'}`, 'log-error');
        }
      } catch (err) {
        filterLog.line(`✗ Request failed: ${err.message}`, 'log-error');
      }
    } else {
      filterLog.line('⚠ File:// mode — filter is saved to browser localStorage only (no disk persistence).', 'log-info');
      const localJql = buildJqlLocally(params);
      if (!localJql && !filterId) {
        filterLog.line('✗ Either a Jira Filter ID or a Project Key is required to save a filter.', 'log-error');
      } else {
        const createdAt = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
        if (localJql) filterLog.line(localJql, 'log-ok');
        if (filterId) filterLog.line(`Using Jira native filter ID: ${filterId}`, 'log-ok');
        const saved = store.getJSON(STORE_KEYS.FILTERS) || [];
        const idx = saved.findIndex((f) => (f.filter_name || f.name || '').toLowerCase() === filterName.toLowerCase());
        const entry = { filter_name: filterName, slug: filterName.toLowerCase().replace(/\W+/g, '_'), created_at: createdAt, jql: localJql, is_default: false };
        if (idx !== -1) { saved[idx] = entry; } else { saved.unshift(entry); }
        store.setJSON(STORE_KEYS.FILTERS, saved.slice(0, 20));
        loadFilters();
      }
    }

    resetBtn();
  });

  const copyBtn = document.getElementById('btn-copy-filter-jql');
  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      const text = filterLog.el.textContent.trim();
      if (!text) return;
      const jqlLines = Array.from(filterLog.el.querySelectorAll('.log-ok'))
        .map((el) => el.textContent.trim())
        .filter((t) => t && !t.startsWith('✓'));
      const toCopy = jqlLines[0] || text;
      navigator.clipboard.writeText(toCopy).then(() => {
        const orig = copyBtn.textContent;
        copyBtn.textContent = 'Copied!';
        setTimeout(() => { copyBtn.textContent = orig; }, 1800);
      }).catch(() => {});
    });
  }
}
