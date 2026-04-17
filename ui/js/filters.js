import { IS_SERVED, STORE_KEYS, FIELD_DEFAULTS } from './config.js';
import { store } from './store.js';
import { getFilters, getSchemas, saveFilter, deleteFilter } from './api.js';
import { buildJqlLocally } from './jql-builder.js';

const SAVE_FILTER_BTN_IDLE = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg> Save Filter`;

const DEFAULT_FILTER_NAME = 'Default_Jira_Filter';
const DEFAULT_SCHEMA_NAME = 'Default_Jira_Cloud';
const NEW_FILTER_OPTION   = '__new__';

let _filterCache = [];

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
      const name       = entry.filter_name || entry.name || '(unnamed)';
      const slug       = entry.slug || entry.filename || '';
      const jql        = entry.jql || '';
      const reportName = entry.report_name || name;
      const opt        = document.createElement('option');
      opt.value              = slug;
      opt.textContent        = name;
      opt.dataset.jql        = jql;
      opt.dataset.reportName = reportName;
      genSel.appendChild(opt);
    });
    if (prevVal) genSel.value = prevVal;
  }
}

function populateFilterNameSelect(entries) {
  const sel = document.getElementById('filter-name-select');
  if (!sel) return;
  const prev = sel.value;
  sel.innerHTML = '';

  const newOpt = document.createElement('option');
  newOpt.value = NEW_FILTER_OPTION;
  newOpt.textContent = '— New filter —';
  sel.appendChild(newOpt);

  (entries || []).forEach((entry) => {
    const name = entry.filter_name || entry.name || '';
    if (!name) return;
    const opt = document.createElement('option');
    opt.value = name;
    opt.textContent = entry.is_default ? `${name} (default)` : name;
    sel.appendChild(opt);
  });

  if (prev && prev !== NEW_FILTER_OPTION) {
    const stillExists = Array.from(sel.options).some((o) => o.value === prev);
    sel.value = stillExists ? prev : NEW_FILTER_OPTION;
  } else {
    sel.value = NEW_FILTER_OPTION;
  }
}

export async function populateSchemaSelect() {
  const sel = document.getElementById('filter-schema-select');
  if (!sel) return;
  const prev = sel.value;
  let names = [DEFAULT_SCHEMA_NAME];

  if (IS_SERVED) {
    try {
      const data = await getSchemas();
      if (data.ok && Array.isArray(data.schemas) && data.schemas.length) {
        names = data.schemas;
      }
    } catch {
      // fall back to default-only
    }
  }

  sel.innerHTML = '';
  names.forEach((name) => {
    const opt = document.createElement('option');
    opt.value = name;
    opt.textContent = name;
    sel.appendChild(opt);
  });

  if (prev && names.includes(prev)) {
    sel.value = prev;
  } else {
    sel.value = names.includes(DEFAULT_SCHEMA_NAME) ? DEFAULT_SCHEMA_NAME : names[0];
  }
}

function setRadio(name, value) {
  const radios = document.querySelectorAll(`input[name="${name}"]`);
  if (!radios.length) return;
  let matched = false;
  radios.forEach((r) => {
    if (r.value === value) { r.checked = true; matched = true; }
  });
  if (!matched && radios[0]) radios[0].checked = true;
}

function clearFormFields() {
  const textIds = [
    'jira-project', 'jira-team-id', 'jira-issue-types',
    'jira-board-id', 'sprint-count', 'filter-id', 'jira-filter-page-size',
  ];
  textIds.forEach((id) => { const el = document.getElementById(id); if (el) el.value = ''; });
  const closed = document.getElementById('jira-closed-sprints-only');
  if (closed) closed.value = FIELD_DEFAULTS.JIRA_CLOSED_SPRINTS_ONLY || 'true';
  setRadio('filter-project-type',    'SCRUM');
  setRadio('filter-estimation-type', 'StoryPoints');
}

function loadFilterIntoForm(entry) {
  if (!entry) return;
  const params = entry.params || {};
  const setVal = (id, v) => { const el = document.getElementById(id); if (el) el.value = v ?? ''; };

  setVal('jira-project',           params.JIRA_PROJECT);
  setVal('jira-team-id',           params.JIRA_TEAM_ID);
  setVal('jira-issue-types',       params.JIRA_ISSUE_TYPES);
  setVal('jira-closed-sprints-only', params.JIRA_CLOSED_SPRINTS_ONLY || FIELD_DEFAULTS.JIRA_CLOSED_SPRINTS_ONLY || 'true');
  setVal('jira-board-id',          params.JIRA_BOARD_ID);
  setVal('sprint-count',           params.JIRA_SPRINT_COUNT);
  setVal('filter-id',              params.JIRA_FILTER_ID);
  setVal('jira-filter-page-size',  params.JIRA_FILTER_PAGE_SIZE);

  setRadio('filter-project-type',    params.PROJECT_TYPE    || 'SCRUM');
  setRadio('filter-estimation-type', params.ESTIMATION_TYPE || 'StoryPoints');

  const schemaSel = document.getElementById('filter-schema-select');
  if (schemaSel) {
    const desired = params.schema_name || DEFAULT_SCHEMA_NAME;
    const exists = Array.from(schemaSel.options).some((o) => o.value === desired);
    schemaSel.value = exists ? desired : (schemaSel.options[0]?.value || '');
  }

  const nameInput = document.getElementById('filter-name');
  if (nameInput) {
    nameInput.value = entry.filter_name || '';
    nameInput.hidden = true;
  }

  const reportNameInput = document.getElementById('report-name');
  if (reportNameInput) {
    reportNameInput.value = entry.report_name || entry.filter_name || '';
  }

  if (params.JIRA_BOARD_ID || params.JIRA_SPRINT_COUNT) {
    const det = document.getElementById('filter-report-scope');
    if (det) det.open = true;
  }

  if (params.JIRA_PROJECT || params.JIRA_TEAM_ID || params.JIRA_ISSUE_TYPES) {
    const det = document.getElementById('filter-jql-builder');
    if (det) det.open = true;
  }

  const filterIdEl = document.getElementById('filter-id');
  if (filterIdEl) filterIdEl.dispatchEvent(new Event('input'));
}

function resetFormForNewFilter() {
  clearFormFields();

  const schemaSel = document.getElementById('filter-schema-select');
  if (schemaSel) {
    const exists = Array.from(schemaSel.options).some((o) => o.value === DEFAULT_SCHEMA_NAME);
    if (exists) schemaSel.value = DEFAULT_SCHEMA_NAME;
  }

  const today = new Date().toISOString().slice(0, 10);
  const nameInput = document.getElementById('filter-name');
  if (nameInput) {
    nameInput.hidden = false;
    nameInput.value = `Default_Jira_Filter_${today}`;
  }

  const reportNameInput = document.getElementById('report-name');
  if (reportNameInput) reportNameInput.value = '';
}

function isDefaultFilterSelected() {
  const sel = document.getElementById('filter-name-select');
  return !!sel && sel.value === DEFAULT_FILTER_NAME;
}

function updateSaveButtonState() {
  const btn = document.getElementById('btn-save-jira-filter');
  if (!btn) return;
  btn.disabled = isDefaultFilterSelected();
  btn.title = btn.disabled
    ? 'The default filter is read-only. Pick "— New filter —" to create a copy.'
    : '';
}

export async function loadFilters() {
  if (IS_SERVED) {
    try {
      const data = await getFilters();
      if (data.ok && Array.isArray(data.filters)) {
        _filterCache = data.filters;
        renderFilters(data.filters);
        populateFilterNameSelect(data.filters);
        updateSaveButtonState();
        return;
      }
    } catch {
      // fall through to localStorage fallback
    }
  }
  const local = store.getJSON(STORE_KEYS.FILTERS) || [];
  _filterCache = local;
  renderFilters(local);
  populateFilterNameSelect(local);
  updateSaveButtonState();
}

export function initFilters(filterLog) {
  const btnSaveJiraFilter = document.getElementById('btn-save-jira-filter');
  if (!btnSaveJiraFilter) return;

  populateSchemaSelect();

  const nameSelect = document.getElementById('filter-name-select');
  if (nameSelect) {
    nameSelect.addEventListener('change', () => {
      if (nameSelect.value === NEW_FILTER_OPTION) {
        resetFormForNewFilter();
      } else {
        const entry = _filterCache.find((e) => (e.filter_name || e.name) === nameSelect.value);
        if (entry) loadFilterIntoForm(entry);
      }
      updateSaveButtonState();
    });
  }

  window.addEventListener('jira-schema-changed', () => { populateSchemaSelect(); });

  function resetBtn() {
    btnSaveJiraFilter.disabled = isDefaultFilterSelected();
    btnSaveJiraFilter.innerHTML = SAVE_FILTER_BTN_IDLE;
  }

  function setBusy() {
    btnSaveJiraFilter.disabled = true;
    btnSaveJiraFilter.innerHTML = '<span class="spinner" aria-hidden="true"></span> Saving…';
  }

  const filterNameInput = document.getElementById('filter-name');
  const reportNameInput = document.getElementById('report-name');
  if (filterNameInput && reportNameInput) {
    filterNameInput.addEventListener('input', () => {
      if (!reportNameInput.value || reportNameInput.dataset.syncedFrom === reportNameInput.value) {
        reportNameInput.value = filterNameInput.value;
        reportNameInput.dataset.syncedFrom = filterNameInput.value;
      }
    });
  }

  btnSaveJiraFilter.addEventListener('click', async () => {
    if (isDefaultFilterSelected()) {
      filterLog.clear();
      filterLog.line('⚠ The default filter is read-only. Pick "— New filter —" to create a copy.', 'log-error');
      return;
    }

    const filterName     = document.getElementById('filter-name').value.trim();
    const project        = document.getElementById('jira-project').value.trim();
    const teamId         = document.getElementById('jira-team-id').value.trim();
    const issueTypes     = document.getElementById('jira-issue-types').value.trim();
    const closedSprints  = document.getElementById('jira-closed-sprints-only').value;
    const projectType    = document.querySelector('input[name="filter-project-type"]:checked')?.value || 'SCRUM';
    const estimationType = document.querySelector('input[name="filter-estimation-type"]:checked')?.value || 'StoryPoints';
    const schemaName     = document.getElementById('filter-schema-select')?.value || DEFAULT_SCHEMA_NAME;

    filterLog.clear();

    const filterId = document.getElementById('filter-id').value.trim();

    if (!filterName) {
      filterLog.line('⚠ Filter Name is required. Enter a name in the field above before saving.', 'log-error');
      document.getElementById('filter-name').focus();
      return;
    }
    if (!schemaName) {
      filterLog.line('⚠ Active Schema is required. Pick a schema from the dropdown.', 'log-error');
      document.getElementById('filter-schema-select').focus();
      return;
    }
    if (!project && !filterId) {
      filterLog.line('⚠ Either a Jira Filter ID or a Project Key (in JQL Builder) is required.', 'log-error');
      document.getElementById('filter-id').focus();
      return;
    }
    const boardId = document.getElementById('jira-board-id').value.trim();
    if (!boardId) {
      filterLog.line('⚠ Board ID is required. Enter it in the Report Scope section.', 'log-error');
      document.getElementById('filter-report-scope').open = true;
      document.getElementById('jira-board-id').focus();
      return;
    }
    const sprintCount = document.getElementById('sprint-count').value.trim();
    if (!sprintCount) {
      filterLog.line('⚠ Sprint Count / Period Count is required. Enter it in the Report Scope section.', 'log-error');
      document.getElementById('filter-report-scope').open = true;
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
      schema_name:              schemaName,
      JIRA_BOARD_ID:            document.getElementById('jira-board-id').value.trim(),
      JIRA_SPRINT_COUNT:        document.getElementById('sprint-count').value.trim(),
      JIRA_FILTER_ID:           filterId,
      JIRA_FILTER_PAGE_SIZE:    document.getElementById('jira-filter-page-size').value.trim(),
    };

    const reportName = document.getElementById('report-name')?.value.trim() || filterName;

    if (IS_SERVED) {
      try {
        const res = await saveFilter(filterName, params, reportName);
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
          await loadFilters();
          const sel = document.getElementById('filter-name-select');
          if (sel) {
            const hasOpt = Array.from(sel.options).some((o) => o.value === filterName);
            if (hasOpt) {
              sel.value = filterName;
              const entry = _filterCache.find((e) => (e.filter_name || e.name) === filterName);
              if (entry) loadFilterIntoForm(entry);
            }
          }
          updateSaveButtonState();
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
        const entry = {
          filter_name: filterName,
          slug: filterName.toLowerCase().replace(/\W+/g, '_'),
          created_at: createdAt,
          jql: localJql,
          is_default: false,
          report_name: reportName,
          params,
        };
        if (idx !== -1) { saved[idx] = entry; } else { saved.unshift(entry); }
        store.setJSON(STORE_KEYS.FILTERS, saved.slice(0, 20));
        await loadFilters();
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

export function getActiveFilterSchemaName() {
  const sel = document.getElementById('filter-schema-select');
  return sel && sel.value ? sel.value : DEFAULT_SCHEMA_NAME;
}
