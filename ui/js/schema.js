import { IS_SERVED, STORE_KEYS } from './config.js';
import { store } from './store.js';
import { getSchemas, getSchemaByName, postSchema } from './api.js';

let _activeSchemaCache = null;

function schemaStatus(el, msg, isError) {
  el.textContent = msg;
  el.style.color = isError ? 'var(--danger, #d32f2f)' : 'var(--success, #2e7d32)';
}

export async function loadSchemas() {
  if (!IS_SERVED) return;
  const schemaSelect  = document.getElementById('schema-select');
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
    await applyActiveSchema();
  } catch {
    schemaSelect.innerHTML = '<option value="">Default (Jira Cloud)</option>';
  }
}

async function fetchSchemaDetails(name) {
  if (!IS_SERVED || !name) return null;
  try {
    const data = await getSchemaByName(name);
    return data.ok ? data.schema : null;
  } catch { return null; }
}

async function applyActiveSchema() {
  const schemaSelect = document.getElementById('schema-select');
  const schemaSPBadge = document.getElementById('schema-sp-badge');
  const name = schemaSelect.value;
  store.set(STORE_KEYS.JIRA_SCHEMA, name);
  const schema = await fetchSchemaDetails(name);
  _activeSchemaCache = schema;

  const spId = schema?.fields?.story_points?.id;
  ['badge-neutral', 'badge-success'].forEach((c) => schemaSPBadge.classList.remove(c));
  schemaSPBadge.textContent = spId ? `Story Points: ${spId}` : 'Story Points: not detected';
  schemaSPBadge.classList.add(spId ? 'badge-success' : 'badge-neutral');
}

export function getActiveTeamJqlName() {
  if (_activeSchemaCache && _activeSchemaCache.fields && _activeSchemaCache.fields.team) {
    return _activeSchemaCache.fields.team.jql_name || _activeSchemaCache.fields.team.id || 'Team[Team]';
  }
  return 'Team[Team]';
}

export function initSchema() {
  const schemaSelect    = document.getElementById('schema-select');
  const schemaNameInput = document.getElementById('schema-name-input');
  const btnFetchSchema  = document.getElementById('btn-fetch-schema');
  const schemaStatusEl  = document.getElementById('schema-status');
  if (!schemaSelect || !btnFetchSchema) return;

  schemaSelect.addEventListener('change', async () => {
    await applyActiveSchema();
    schemaStatus(schemaStatusEl, '');
  });

  btnFetchSchema.addEventListener('click', async () => {
    const name = schemaNameInput.value.trim();
    if (!name) {
      schemaStatus(schemaStatusEl, 'Schema name is required.', true);
      schemaNameInput.focus();
      return;
    }

    const url   = store.get(STORE_KEYS.JIRA_URL);
    const email = store.get(STORE_KEYS.JIRA_EMAIL);
    const token = store.get(STORE_KEYS.JIRA_API_TOKEN);
    if (!url || !email || !token) {
      schemaStatus(schemaStatusEl, 'Save Jira credentials on the Connection tab first.', true);
      return;
    }

    btnFetchSchema.disabled = true;
    const origText = btnFetchSchema.innerHTML;
    btnFetchSchema.innerHTML = '<span class="spinner" aria-hidden="true"></span> Fetching…';
    schemaStatus(schemaStatusEl, '');

    try {
      const projectKeys = document.getElementById('schema-project-keys').value.trim();
      const boardIdRaw  = document.getElementById('schema-board-id').value.trim();
      const boardId     = boardIdRaw ? parseInt(boardIdRaw, 10) : null;
      const filterId    = store.get(STORE_KEYS.JIRA_FILTER_ID) || null;
      const data = await postSchema({
        schema_name:   name,
        jira_url:      url,
        jira_email:    email,
        jira_token:    token,
        project_keys:  projectKeys || null,
        board_id:      boardId,
        filter_id:     filterId,
      });
      if (data.ok) {
        schemaStatus(schemaStatusEl, `Schema "${name}" saved successfully.`, false);
        schemaNameInput.value = '';
        await loadSchemas();
        schemaSelect.value = name;
        store.set(STORE_KEYS.JIRA_SCHEMA, name);
        await applyActiveSchema();
      } else {
        schemaStatus(schemaStatusEl, data.error || 'Failed to fetch schema.', true);
      }
    } catch (err) {
      schemaStatus(schemaStatusEl, `Request failed: ${err.message}`, true);
    } finally {
      btnFetchSchema.disabled = false;
      btnFetchSchema.innerHTML = origText;
    }
  });
}
