import { IS_SERVED, STORE_KEYS } from './config.js';
import { store } from './store.js';
import { getSchemas, getSchemaByName, postSchema, deleteSchema } from './api.js';

const DEFAULT_SCHEMA_NAME = 'Default_Jira_Cloud';

const TEMPLATE_SCHEMA = {
  schema_name: '',
  description: '',
  jira_url_pattern: '',
  fields: {
    story_points: { id: 'customfield_10016', type: 'number', description: 'Story point estimate' },
    sprint:       { id: 'customfield_10020', type: 'array',  description: 'Sprint(s) the issue belongs to' },
    team:         { id: 'customfield_10001', type: 'string', jql_name: 'Team[Team]', description: 'Team field' },
    labels:       { id: 'labels',            type: 'array',  description: 'Issue labels' },
    status:       { id: 'status',            type: 'string', description: 'Issue status' },
    resolution_date: { id: 'resolutiondate', type: 'string', description: 'Timestamp when the issue was resolved' },
  },
  status_mapping: {
    done_statuses:        ['Done', 'Closed', 'Resolved', 'Complete'],
    in_progress_statuses: ['In Progress'],
  },
};

let _activeSchemaCache = null;
const _schemaByNameCache = new Map();

function getFilterSchemaSelection() {
  const sel = document.getElementById('filter-schema-select');
  return (sel && sel.value) ? sel.value : DEFAULT_SCHEMA_NAME;
}

function schemaStatus(el, msg, isError) {
  if (!el) return;
  el.textContent = msg;
  el.style.color = isError ? 'var(--danger, #d32f2f)' : 'var(--success, #2e7d32)';
}

function writeLog(msg) {
  const log = document.getElementById('schema-log-output');
  if (!log) return;
  log.textContent = msg;
}

function clearLog() {
  const log = document.getElementById('schema-log-output');
  if (log) log.textContent = '';
}

export async function loadSchemas() {
  if (!IS_SERVED) return;
  const schemaSelect = document.getElementById('schema-select');
  if (!schemaSelect) return;
  try {
    const data = await getSchemas();
    if (!data.ok) return;
    const names = data.schemas || [];
    const saved = store.get(STORE_KEYS.JIRA_SCHEMA);

    schemaSelect.innerHTML = '';
    names.forEach((name) => {
      const opt = document.createElement('option');
      opt.value = name;
      opt.textContent = name;
      if (name === saved) opt.selected = true;
      schemaSelect.appendChild(opt);
    });
    if (!saved && names.length) {
      schemaSelect.value = names[0];
    }
    await loadSelectedIntoEditor();
  } catch {
    schemaSelect.innerHTML = `<option value="${DEFAULT_SCHEMA_NAME}">${DEFAULT_SCHEMA_NAME}</option>`;
  }
}

async function fetchSchemaDetails(name) {
  if (!IS_SERVED || !name) return null;
  try {
    const data = await getSchemaByName(name);
    return data.ok ? data.schema : null;
  } catch { return null; }
}

async function loadSelectedIntoEditor() {
  const schemaSelect = document.getElementById('schema-select');
  const editor       = document.getElementById('schema-json-editor');
  const deleteBtn    = document.getElementById('btn-schema-delete');
  if (!schemaSelect) return;

  const name = schemaSelect.value;
  store.set(STORE_KEYS.JIRA_SCHEMA, name);
  const schema = await fetchSchemaDetails(name);
  _activeSchemaCache = schema;

  if (editor) {
    editor.value = schema ? JSON.stringify(schema, null, 2) : '';
  }
  if (deleteBtn) {
    deleteBtn.disabled = !name || name === DEFAULT_SCHEMA_NAME;
  }
  clearLog();
}

function teamJqlFromSchema(schema) {
  if (schema && schema.fields && schema.fields.team) {
    return schema.fields.team.jql_name || schema.fields.team.id || 'Team[Team]';
  }
  return 'Team[Team]';
}

export function getActiveTeamJqlName() {
  const name = getFilterSchemaSelection();
  if (_schemaByNameCache.has(name)) {
    return teamJqlFromSchema(_schemaByNameCache.get(name));
  }
  if (IS_SERVED) {
    getSchemaByName(name)
      .then((data) => {
        if (data && data.ok && data.schema) {
          _schemaByNameCache.set(name, data.schema);
        }
      })
      .catch(() => {});
  }
  return teamJqlFromSchema(_activeSchemaCache);
}

function validateEditorContent(rawText) {
  let parsed;
  try {
    parsed = JSON.parse(rawText);
  } catch (err) {
    return { ok: false, error: `Invalid JSON: ${err.message}` };
  }
  if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
    return { ok: false, error: 'Schema must be a JSON object.' };
  }
  if (typeof parsed.schema_name !== 'string' || !parsed.schema_name.trim()) {
    return { ok: false, error: '"schema_name" must be a non-empty string.' };
  }
  if (!parsed.fields || typeof parsed.fields !== 'object' || Array.isArray(parsed.fields)) {
    return { ok: false, error: '"fields" must be an object.' };
  }
  const sm = parsed.status_mapping;
  if (
    !sm || typeof sm !== 'object'
    || !Array.isArray(sm.done_statuses)
    || !Array.isArray(sm.in_progress_statuses)
  ) {
    return {
      ok: false,
      error: '"status_mapping" must contain "done_statuses" and "in_progress_statuses" as arrays.',
    };
  }
  return { ok: true, parsed };
}

async function onSaveClick() {
  const editor   = document.getElementById('schema-json-editor');
  const statusEl = document.getElementById('schema-status');
  if (!editor) return;

  clearLog();
  const validation = validateEditorContent(editor.value);
  if (!validation.ok) {
    writeLog(validation.error);
    schemaStatus(statusEl, 'Schema not saved — see validation error.', true);
    return;
  }

  schemaStatus(statusEl, 'Saving…', false);
  try {
    const data = await postSchema({ schema: validation.parsed });
    if (data.ok) {
      const savedName = data.schema?.schema_name || validation.parsed.schema_name;
      _activeSchemaCache = null;
      store.set(STORE_KEYS.JIRA_SCHEMA, savedName);
      await loadSchemas();
      const schemaSelect = document.getElementById('schema-select');
      if (schemaSelect) schemaSelect.value = savedName;
      await loadSelectedIntoEditor();
      const verb = data.updated ? 'updated' : 'created';
      schemaStatus(statusEl, `Schema "${savedName}" ${verb}.`, false);
      writeLog(`JSON validation passed successfully. Schema "${savedName}" ${verb}.`);
      window.dispatchEvent(new Event('jira-schema-changed'));
    } else {
      writeLog(data.error || 'Unknown server error.');
      schemaStatus(statusEl, 'Save failed.', true);
    }
  } catch (err) {
    writeLog(`Request failed: ${err.message}`);
    schemaStatus(statusEl, 'Save failed.', true);
  }
}

function onNewClick() {
  const editor       = document.getElementById('schema-json-editor');
  const schemaSelect = document.getElementById('schema-select');
  const statusEl     = document.getElementById('schema-status');
  const deleteBtn    = document.getElementById('btn-schema-delete');
  if (!editor) return;

  editor.value = JSON.stringify(TEMPLATE_SCHEMA, null, 2);
  if (schemaSelect) schemaSelect.value = '';
  if (deleteBtn) deleteBtn.disabled = true;
  clearLog();
  schemaStatus(statusEl, 'Editing new schema — set schema_name and Save.', false);
  editor.focus();
}

async function onDeleteClick() {
  const schemaSelect = document.getElementById('schema-select');
  const statusEl     = document.getElementById('schema-status');
  if (!schemaSelect) return;

  const name = schemaSelect.value;
  if (!name || name === DEFAULT_SCHEMA_NAME) return;
  if (!window.confirm(`Delete schema "${name}"? This cannot be undone.`)) return;

  clearLog();
  try {
    const data = await deleteSchema(name);
    if (data.ok) {
      store.set(STORE_KEYS.JIRA_SCHEMA, DEFAULT_SCHEMA_NAME);
      _activeSchemaCache = null;
      await loadSchemas();
      schemaSelect.value = DEFAULT_SCHEMA_NAME;
      await loadSelectedIntoEditor();
      schemaStatus(statusEl, `Schema "${name}" deleted.`, false);
      window.dispatchEvent(new Event('jira-schema-changed'));
    } else {
      writeLog(data.error || 'Delete failed.');
      schemaStatus(statusEl, 'Delete failed.', true);
    }
  } catch (err) {
    writeLog(`Request failed: ${err.message}`);
    schemaStatus(statusEl, 'Delete failed.', true);
  }
}

export function initSchema() {
  const schemaSelect = document.getElementById('schema-select');
  const btnNew       = document.getElementById('btn-schema-new');
  const btnSave      = document.getElementById('btn-schema-save');
  const btnDelete    = document.getElementById('btn-schema-delete');
  if (!schemaSelect || !btnSave) return;

  schemaSelect.addEventListener('change', () => {
    loadSelectedIntoEditor();
  });
  if (btnNew)    btnNew.addEventListener('click', onNewClick);
  btnSave.addEventListener('click', onSaveClick);
  if (btnDelete) btnDelete.addEventListener('click', onDeleteClick);

  window.addEventListener('jira-schema-changed', () => {
    _schemaByNameCache.clear();
  });
}
